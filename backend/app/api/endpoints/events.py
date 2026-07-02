from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from backend.app.api.dependencies import get_orchestrator, get_repository, get_ai_client
from backend.app.application.event_orchestrator import EventOrchestrator
from backend.app.infrastructure.external.ai.orchestrator import AIOrchestrator
from backend.app.domain.interfaces.repository import SupplyChainRepository
from backend.app.api.mappers import (
    map_event_to_response,
    map_simulation_to_response,
    map_recommendation_to_response
)
from backend.app.models.api_schemas import (
    NewsIngestionRequest,
    MitigationSelectionRequest,
    EventResponse,
    SimulationRunResponse,
    RecommendationResponse
)

router = APIRouter()

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def ingest_news(
    payload: NewsIngestionRequest,
    orchestrator: EventOrchestrator = Depends(get_orchestrator)
):
    """
    Ingests raw news article text, extracts structured threat parameters
    via Gemini, commits the RiskEvent, and triggers downstream simulations.
    """
    try:
        event = orchestrator.ingest_news_alert(payload.news_text)
        return map_event_to_response(event)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"News ingestion and extraction failed: {str(e)}"
        )

@router.get("/", response_model=List[EventResponse])
def list_events(repo: SupplyChainRepository = Depends(get_repository)):
    """Lists all ingested and committed RiskEvents."""
    events = repo.get_risk_events()
    return [map_event_to_response(e) for e in events]

@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    repo: SupplyChainRepository = Depends(get_repository)
):
    """Retrieves metadata of a specific RiskEvent."""
    event = repo.get_risk_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found."
        )
    return map_event_to_response(event)

@router.post("/{event_id}/simulate", response_model=SimulationRunResponse)
def run_simulation(
    event_id: str,
    orchestrator: EventOrchestrator = Depends(get_orchestrator)
):
    """Manually triggers a 10-day temporal simulation run for a specific RiskEvent."""
    try:
        run = orchestrator.run_manual_simulation(event_id, duration_days=10)
        return map_simulation_to_response(run)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{event_id}/impact", response_model=SimulationRunResponse)
def get_impact_timeline(
    event_id: str,
    repo: SupplyChainRepository = Depends(get_repository),
    orchestrator: EventOrchestrator = Depends(get_orchestrator)
):
    """Retrieves the step-by-step propagation timeline for a RiskEvent."""
    run = repo.get_latest_simulation_run_by_event(event_id)
    if not run:
        try:
            run = orchestrator.run_manual_simulation(event_id, duration_days=10)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return map_simulation_to_response(run)

@router.get("/{event_id}/decision", response_model=RecommendationResponse)
def get_decisions(
    event_id: str,
    orchestrator: EventOrchestrator = Depends(get_orchestrator)
):
    """Calculates algebraic utility rankings and fetches Gemini executive summary briefing."""
    rec = orchestrator.get_decision_recommendations(event_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No event found matching ID '{event_id}'"
        )
    return map_recommendation_to_response(rec)

@router.post("/{event_id}/decision/mitigate", status_code=status.HTTP_200_OK)
def apply_mitigation(
    event_id: str,
    payload: MitigationSelectionRequest,
    orchestrator: EventOrchestrator = Depends(get_orchestrator)
):
    """Applies a mitigation playbook choice, executing reroutes in the Digital Twin graph."""
    try:
        orchestrator.apply_mitigation_action(event_id, payload.option_id)
        return {"status": "success", "message": f"Applied option '{payload.option_id}' to event '{event_id}' successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply mitigation action: {str(e)}"
        )

@router.post("/system/reset", status_code=status.HTTP_200_OK)
def reset_network(orchestrator: EventOrchestrator = Depends(get_orchestrator)):
    """Resets the entire Digital Twin graph database state back to its baseline seed parameters."""
    try:
        orchestrator.reset_system()
        return {"status": "success", "message": "Digital Twin reset to baseline healthy state."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset twin state: {str(e)}"
        )

@router.get("/system/ai-status", status_code=status.HTTP_200_OK)
def get_ai_status(ai_client: AIOrchestrator = Depends(get_ai_client)):
    """Retrieves active AI engine provider state (gemini, ollama, offline)."""
    return {"provider": ai_client.get_provider_status()}

from pydantic import BaseModel

class AskRequest(BaseModel):
    question: str

@router.post("/system/ask", status_code=status.HTTP_200_OK)
def ask_nexus(
    payload: AskRequest,
    repo: SupplyChainRepository = Depends(get_repository),
    ai_client: AIOrchestrator = Depends(get_ai_client)
):
    """Answers an operational question about the current state of the Digital Twin."""
    try:
        # Load all nodes
        db_nodes = repo.get_nodes()
        nodes_list = []
        for n in db_nodes:
            nodes_list.append({
                "id": n.id,
                "name": n.name,
                "type": n.type,
                "location": n.location,
                "health": n.health,
                "inventory": n.inventory,
                "capacity": n.capacity
            })

        # Load all edges
        db_edges = repo.get_edges()
        edges_list = []
        for e in db_edges:
            edges_list.append({
                "source": e.source,
                "target": e.target,
                "transport_mode": e.transport_mode,
                "dependency_ratio": e.dependency_ratio
            })

        # Load active disruption event
        db_events = repo.get_risk_events()
        committed_events = [evt for evt in db_events if evt.status == "COMMITTED"]
        active_event = None
        metrics = {"overall_resilience": 100.0, "total_financial_loss": 0.0}

        if committed_events:
            evt = committed_events[0]
            active_event = {
                "id": evt.id,
                "title": evt.title,
                "affected_node_id": evt.affected_node_id,
                "severity": evt.severity,
                "duration_days": evt.duration_days,
                "affected_nodes": [an.model_dump() for an in evt.affected_nodes]
            }
            # Load active metrics from latest simulation run
            run = repo.get_latest_simulation_run_by_event(evt.id)
            if run and run.timeline:
                day_metrics = run.timeline[0].metrics
                metrics = {
                    "overall_resilience": day_metrics.resilience_score,
                    "total_financial_loss": day_metrics.financial_loss
                }

        system_state = {
            "nodes": nodes_list,
            "edges": edges_list,
            "active_event": active_event,
            "metrics": metrics
        }

        answer = ai_client.ask_question(payload.question, system_state)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )
