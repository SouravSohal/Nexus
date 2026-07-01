import os
import sys
from datetime import datetime, timezone

# Append project roots to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.app.infrastructure.db.sqlite_repo import SQLiteRepository
from backend.app.infrastructure.graph.networkx_engine import NetworkXGraphEngine
from backend.app.domain.services.simulation_engine import TemporalSimulationEngine
from backend.app.domain.services.decision_engine import DecisionEngine
from backend.app.infrastructure.external.gemini_client import GeminiClient
from backend.app.domain.models.event import RiskEvent, EventStatus

def main():
    db_path = os.path.join(project_root, "backend", "nexus.db")
    print(f"Reading database at: {db_path}")
    repo = SQLiteRepository(db_path)
    
    nodes = repo.get_nodes()
    edges = repo.get_edges()
    
    print(f"Loaded {len(nodes)} nodes and {len(edges)} edges.")
    
    # 1. Initialize Engines
    graph_engine = NetworkXGraphEngine()
    sim_engine = TemporalSimulationEngine(graph_engine)
    decision_engine = DecisionEngine()
    ai_client = GeminiClient()
    
    # 2. Define Disruption Event
    strike_event = RiskEvent(
        id="evt-antwerp-strike-2026",
        title="Port of Antwerp Worker Strike",
        description="Workers at Antwerp announce a 5-day walkout halting container shipments.",
        location="Antwerp, Belgium",
        affected_node_id="port-antwerp",
        severity=0.85,
        duration_days=5,
        confidence_score=0.95,
        status=EventStatus.COMMITTED,
        created_at=datetime.now(timezone.utc)
    )
    
    # 3. Run Simulation
    print("\n[Step 1] Running Disruption Simulation...")
    sim_run = sim_engine.run_simulation(strike_event, nodes, edges, duration_days=10)
    print(f"        -> Simulation finished. ID: {sim_run.id}")
    
    # 4. Run Decision Engine Optimization
    print("\n[Step 2] Running Decision Engine Optimization...")
    recommendation = decision_engine.evaluate_mitigation(strike_event, sim_run, nodes)
    
    # Verify outputs
    print(f"        -> Optimization finished. ID: {recommendation.id}")
    print(f"        -> Earliest Stockout Day: Day {recommendation.do_nothing_impact.earliest_stockout_day}")
    print(f"        -> Financial Risk of Doing Nothing: ${recommendation.do_nothing_impact.total_financial_loss:,.2f}")
    print(f"        -> Delayed Products: {recommendation.do_nothing_impact.delayed_products_count} units")
    
    print("\nRanked Mitigation Options:")
    for idx, opt in enumerate(recommendation.options):
        rec_str = "[RECOMMENDED]" if opt.is_recommended else ""
        print(f"  {idx+1}. {opt.title} {rec_str}")
        print(f"     Score: {opt.calculated_score} | Cost: ${opt.cost_impact:,.2f} | Transit Delay: {opt.lead_time_surcharge_days}d | Feasibility: {opt.feasibility_score * 100:.0f}%")
    
    # 5. Generate AI Executive Summary Narrative
    print("\n[Step 3] Querying AI Recommendation Client...")
    briefing = ai_client.generate_executive_recommendation(strike_event, recommendation.do_nothing_impact, recommendation.options)
    recommendation.gemini_explanation = briefing
    
    print("\nAI Generated Recommendation Briefing:")
    print("=" * 60)
    print(briefing)
    print("=" * 60)
    
    # 6. Save Recommendation to Database
    print("\n[Step 4] Saving Recommendation Bundle to Repository...")
    repo.create_recommendation(recommendation)
    
    # Fetch back from DB to verify persistence
    db_rec = repo.get_recommendation_by_event(strike_event.id)
    assert db_rec is not None, "Failed to retrieve recommendation from database"
    print("        -> DB Persistence Verified successfully.")

if __name__ == "__main__":
    main()
