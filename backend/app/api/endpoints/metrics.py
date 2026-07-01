from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.api.dependencies import get_repository
from backend.app.domain.interfaces.repository import SupplyChainRepository
from backend.app.models.api_schemas import MetricsResponse

router = APIRouter()

@router.get("/", response_model=MetricsResponse)
def get_dashboard_metrics(repo: SupplyChainRepository = Depends(get_repository)):
    """
    Computes and returns the overall active supply chain KPIs.
    If a simulation is running, it returns the final-day accumulated statistics.
    Otherwise, it returns the baseline healthy values.
    """
    try:
        events = repo.get_risk_events()
        
        # If there are active events, find the latest committed/active one
        active_event = next((e for e in events if e.status.value in ("COMMITTED", "ACTIVE")), None)
        
        if active_event:
            run = repo.get_latest_simulation_run_by_event(active_event.id)
            if run and run.timeline:
                final_step = run.timeline[-1]
                return MetricsResponse(
                    overall_resilience=final_step.metrics.resilience_score,
                    total_financial_loss=final_step.metrics.financial_loss,
                    delayed_products_count=final_step.metrics.delayed_products,
                    disrupted_nodes_count=final_step.metrics.disrupted_nodes_count
                )
        
        # Default Baseline Healthy State
        return MetricsResponse(
            overall_resilience=100.0,
            total_financial_loss=0.0,
            delayed_products_count=0,
            disrupted_nodes_count=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate metrics: {str(e)}"
        )
