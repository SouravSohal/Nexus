import uuid
from datetime import datetime, timezone
from typing import List, Optional
from backend.app.domain.models.event import RiskEvent
from backend.app.domain.models.network import Node, Edge
from backend.app.domain.models.simulation import SimulationRun
from backend.app.domain.models.decision import RecommendationBundle, MitigationOption, CompositeConfidence, DoNothingImpact

class DecisionEngine:
    """
    DecisionEngine performs algebraic optimization over simulation timelines.
    It evaluates candidate mitigation options, scores them, ranks them,
    and packages them for executive decision making.
    """

    def __init__(self, cost_weight: float = 0.5, delay_weight: float = 0.2, feasibility_weight: float = 0.3):
        self.w_cost = cost_weight
        self.w_delay = delay_weight
        self.w_feasibility = feasibility_weight

    def evaluate_mitigation(
        self,
        event: RiskEvent,
        simulation_run: SimulationRun,
        nodes: List[Node]
    ) -> RecommendationBundle:
        """
        Evaluates the simulation run of a disrupted state, calculates the penalty of doing nothing,
        rates playbooks, and returns the sorted recommendations.
        """
        # 1. Calculate Do Nothing Impact
        earliest_stockout_day = -1
        total_loss = 0.0
        delayed_products = 0
        
        # Scan timeline to find when stockouts occur (health == 0.0 for assembly/hub) and record final metrics
        for step in simulation_run.timeline:
            # Record final cumulative metrics at the end of the simulation
            total_loss = step.metrics.financial_loss
            delayed_products = step.metrics.delayed_products
            
            if earliest_stockout_day == -1:
                # Check if Munich hub or factory assembly are starved
                hub_health = step.node_states.get("warehouse-munich").health
                factory_health = step.node_states.get("factory-assembly").health
                if hub_health == 0.0 or factory_health == 0.0:
                    earliest_stockout_day = step.day

        do_nothing = DoNothingImpact(
            earliest_stockout_day=earliest_stockout_day if earliest_stockout_day != -1 else len(simulation_run.timeline),
            total_financial_loss=total_loss,
            delayed_products_count=delayed_products
        )

        # 2. Define Mitigation Options (Playbooks)
        candidate_options = [
            MitigationOption(
                option_id="opt-reroute-rotterdam",
                title="Reroute via Port of Rotterdam",
                description="Divert container ships bound for Antwerp to the Port of Rotterdam. Truck cargo from Rotterdam to Munich Hub. Bypasses the Antwerp strike with a slight 1-day transport delay.",
                cost_impact=45000.0,
                lead_time_surcharge_days=1,
                feasibility_score=0.95
            ),
            MitigationOption(
                option_id="opt-air-freight",
                title="Establish Air Freight Supply Link",
                description="Fly critical semiconductor components directly from Taiwan airports to Munich Airport. Completely bypasses ocean ports, cutting transit lead time by 4 days, but cost is high.",
                cost_impact=220000.0,
                lead_time_surcharge_days=-4,
                feasibility_score=0.60
            ),
            MitigationOption(
                option_id="opt-backup-supplier",
                title="Switch to Backup European Supplier",
                description="Source raw parts from a secondary supplier located in France. Eliminates international shipping lanes and cuts lead time by 5 days, but unit sourcing cost increases.",
                cost_impact=95000.0,
                lead_time_surcharge_days=-5,
                feasibility_score=0.80
            )
        ]

        # 3. Score Options
        # Score = w1 * (1.0 - Cost/LostRevenue) + w2 * (1.0 - Surcharge/MaxSafetyDays) + w3 * Feasibility
        safety_buffer_days = 4.0  # Munich Hub safety stock covers 4 days of production
        max_avoidable_loss = max(100.0, do_nothing.total_financial_loss)

        for opt in candidate_options:
            # A. Cost Utility (cost vs doing nothing)
            # If the option costs more than the loss itself, cost utility is negative. We clamp it.
            cost_utility = max(0.0, 1.0 - (opt.cost_impact / max_avoidable_loss))
            
            # B. Lead Time Surcharge Utility
            # Surcharge represents added days. If negative (reduces lead time), utility rises above 1.0.
            # We normalize delay relative to safety buffer days.
            delay_utility = max(0.0, 1.0 - (opt.lead_time_surcharge_days / safety_buffer_days))
            
            # C. Feasibility Utility
            feasibility_utility = opt.feasibility_score
            
            # D. Weighted Score
            score = (
                self.w_cost * cost_utility +
                self.w_delay * delay_utility +
                self.w_feasibility * feasibility_utility
            )
            opt.calculated_score = round(score, 3)

        # Sort options: higher score is better
        ranked_options = sorted(candidate_options, key=lambda x: x.calculated_score, reverse=True)
        if ranked_options:
            ranked_options[0].is_recommended = True

        # 4. Formulate Composite Confidence
        # Ingestion confidence is parsed from event. Telemetry confidence is 0.90 for sqlite.
        # Feasibility is the feasibility score of the recommended option.
        best_feasibility = ranked_options[0].feasibility_score if ranked_options else 0.90
        composite_confidence = CompositeConfidence(
            extraction=event.confidence_score,
            simulation=0.90,  # Constant representing baseline telemetry visibility
            optimization=best_feasibility,
            overall=round(event.confidence_score * 0.90 * best_feasibility, 2)
        )

        rec_bundle_id = f"rec-{uuid.uuid4().hex[:8]}"
        return RecommendationBundle(
            id=rec_bundle_id,
            event_id=event.id,
            do_nothing_impact=do_nothing,
            options=ranked_options,
            composite_confidence=composite_confidence,
            gemini_explanation="",  # Generated by external LLM service later
            created_at=datetime.now(timezone.utc)
        )
