from backend.app.domain.models.network import Node as DomainNode, Edge as DomainEdge
from backend.app.domain.models.event import RiskEvent as DomainRiskEvent
from backend.app.domain.models.simulation import SimulationRun as DomainSimulationRun
from backend.app.domain.models.decision import RecommendationBundle as DomainRecommendationBundle

from backend.app.models.api_schemas import (
    NodeResponse,
    EdgeResponse,
    EventResponse,
    SimulationRunResponse,
    TemporalStepResponse,
    StepMetricsResponse,
    NodeStateResponse,
    RecommendationResponse,
    MitigationOptionResponse,
    CompositeConfidenceResponse,
    DoNothingImpactResponse
)

def map_node_to_response(node: DomainNode) -> NodeResponse:
    """Maps a Domain Node model to a Presentation NodeResponse DTO."""
    return NodeResponse(
        id=node.id,
        name=node.name,
        type=node.type,
        location=node.location,
        latitude=node.latitude,
        longitude=node.longitude,
        base_cost=node.base_cost,
        capacity=node.capacity,
        health=node.health,
        risk_score=node.risk_score,
        inventory=node.inventory,
        safety_stock=node.safety_stock,
        daily_consumption=node.daily_consumption,
        replenishment_rate=node.replenishment_rate,
        metadata=node.metadata
    )

def map_edge_to_response(edge: DomainEdge) -> EdgeResponse:
    """Maps a Domain Edge model to a Presentation EdgeResponse DTO."""
    return EdgeResponse(
        source=edge.source,
        target=edge.target,
        type=edge.type,
        dependency_ratio=edge.dependency_ratio,
        lead_time_days=edge.lead_time_days,
        transport_mode=edge.transport_mode
    )

def map_event_to_response(event: DomainRiskEvent) -> EventResponse:
    """Maps a Domain RiskEvent aggregate to a Presentation EventResponse DTO."""
    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        location=event.location,
        affected_node_id=event.affected_node_id,
        severity=event.severity,
        duration_days=event.duration_days,
        confidence_score=event.confidence_score,
        status=event.status,
        created_at=event.created_at
    )

def map_simulation_to_response(run: DomainSimulationRun) -> SimulationRunResponse:
    """Maps a Domain SimulationRun model to a Presentation SimulationRunResponse DTO."""
    timeline_response = []
    for step in run.timeline:
        node_states_response = {}
        for n_id, state in step.node_states.items():
            node_states_response[n_id] = NodeStateResponse(
                health=state.health,
                inventory=state.inventory,
                risk_score=state.risk_score,
                replenishment_rate=state.replenishment_rate
            )
        
        metrics_response = StepMetricsResponse(
            resilience_score=step.metrics.resilience_score,
            financial_loss=step.metrics.financial_loss,
            delayed_products=step.metrics.delayed_products,
            disrupted_nodes_count=step.metrics.disrupted_nodes_count
        )
        
        timeline_response.append(
            TemporalStepResponse(
                day=step.day,
                metrics=metrics_response,
                node_states=node_states_response
            )
        )
        
    return SimulationRunResponse(
        id=run.id,
        event_id=run.event_id,
        timeline=timeline_response,
        created_at=run.created_at
    )

def map_recommendation_to_response(rec: DomainRecommendationBundle) -> RecommendationResponse:
    """Maps a Domain RecommendationBundle to a Presentation RecommendationResponse DTO."""
    options_response = [
        MitigationOptionResponse(
            option_id=opt.option_id,
            title=opt.title,
            description=opt.description,
            cost_impact=opt.cost_impact,
            lead_time_surcharge_days=opt.lead_time_surcharge_days,
            feasibility_score=opt.feasibility_score,
            calculated_score=opt.calculated_score,
            is_recommended=opt.is_recommended
        )
        for opt in rec.options
    ]
    
    return RecommendationResponse(
        id=rec.id,
        event_id=rec.event_id,
        do_nothing_impact=DoNothingImpactResponse(
            earliest_stockout_day=rec.do_nothing_impact.earliest_stockout_day,
            total_financial_loss=rec.do_nothing_impact.total_financial_loss,
            delayed_products_count=rec.do_nothing_impact.delayed_products_count
        ),
        options=options_response,
        composite_confidence=CompositeConfidenceResponse(
            extraction=rec.composite_confidence.extraction,
            simulation=rec.composite_confidence.simulation,
            optimization=rec.composite_confidence.optimization,
            overall=rec.composite_confidence.overall
        ),
        gemini_explanation=rec.gemini_explanation,
        created_at=rec.created_at
    )
