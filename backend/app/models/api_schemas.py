from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.app.domain.models.event import EventStatus
from backend.app.domain.models.network import NodeType, EdgeType

class NewsIngestionRequest(BaseModel):
    """Payload for submitting a news article for structured extraction."""
    news_text: str = Field(
        ...,
        description="Raw text of the breaking news article or incident report.",
        json_schema_extra={
            "example": "Dockworkers at the Port of Antwerp launch a 5-day strike halting container flows."
        }
    )

class MitigationSelectionRequest(BaseModel):
    """Payload for executing a mitigation option."""
    option_id: str = Field(
        ...,
        description="The ID of the selected mitigation playbook (e.g. 'opt-reroute-rotterdam').",
        json_schema_extra={
            "example": "opt-reroute-rotterdam"
        }
    )

class AffectedNodeResponse(BaseModel):
    node_id: str
    severity: float
    confidence: float
    disruption_type: str

class EventResponse(BaseModel):
    """Committed RiskEvent representation."""
    id: str
    title: str
    description: str
    location: str
    affected_node_id: str
    severity: float
    duration_days: int
    confidence_score: float
    status: EventStatus
    created_at: datetime
    affected_nodes: List[AffectedNodeResponse] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "evt-7f9a2b1c",
                "title": "Port of Antwerp Strike",
                "description": "5-day dockworker walkout halting shipping container logistics.",
                "location": "Antwerp, Belgium",
                "affected_node_id": "port-antwerp",
                "severity": 0.85,
                "duration_days": 5,
                "confidence_score": 0.95,
                "status": "COMMITTED",
                "created_at": "2026-07-01T18:07:00Z"
            }
        }

class NodeStateResponse(BaseModel):
    health: float
    inventory: float
    risk_score: float
    replenishment_rate: float

class StepMetricsResponse(BaseModel):
    resilience_score: float
    financial_loss: float
    delayed_products: int
    disrupted_nodes_count: int

class TemporalStepResponse(BaseModel):
    day: int
    metrics: StepMetricsResponse
    node_states: Dict[str, NodeStateResponse]

class SimulationRunResponse(BaseModel):
    """Simulation run time-series representation."""
    id: str
    event_id: str
    timeline: List[TemporalStepResponse]
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sim-3f9d0c2a",
                "event_id": "evt-7f9a2b1c",
                "timeline": [
                    {
                        "day": 0,
                        "metrics": {
                            "resilience_score": 90.6,
                            "financial_loss": 25500.0,
                            "delayed_products": 0,
                            "disrupted_nodes_count": 1
                        },
                        "node_states": {
                            "port-antwerp": {
                                "health": 0.15,
                                "inventory": 300.0,
                                "risk_score": 0.85,
                                "replenishment_rate": 40.0
                            }
                        }
                    }
                ],
                "created_at": "2026-07-01T18:08:00Z"
            }
        }

class MitigationOptionResponse(BaseModel):
    option_id: str
    title: str
    description: str
    cost_impact: float
    lead_time_surcharge_days: int
    feasibility_score: float
    calculated_score: float
    is_recommended: bool

class CompositeConfidenceResponse(BaseModel):
    extraction: float
    simulation: float
    optimization: float
    overall: float

class DoNothingImpactResponse(BaseModel):
    earliest_stockout_day: int
    total_financial_loss: float
    delayed_products_count: int

class RecommendationResponse(BaseModel):
    """Decision Optimization and Recommendation representation."""
    id: str
    event_id: str
    do_nothing_impact: DoNothingImpactResponse
    options: List[MitigationOptionResponse]
    composite_confidence: CompositeConfidenceResponse
    gemini_explanation: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rec-52f9e5b3",
                "event_id": "evt-7f9a2b1c",
                "do_nothing_impact": {
                    "earliest_stockout_day": 6,
                    "total_financial_loss": 363093.75,
                    "delayed_products_count": 0
                },
                "options": [
                    {
                        "option_id": "opt-reroute-rotterdam",
                        "title": "Reroute via Port of Rotterdam",
                        "description": "Divert container vessels to Rotterdam.",
                        "cost_impact": 45000.0,
                        "lead_time_surcharge_days": 1,
                        "feasibility_score": 0.95,
                        "calculated_score": 0.873,
                        "is_recommended": True
                    }
                ],
                "composite_confidence": {
                    "extraction": 0.95,
                    "simulation": 0.90,
                    "optimization": 0.95,
                    "overall": 0.81
                },
                "gemini_explanation": "We recommend rerouting cargo to Rotterdam to bypass Antwerp.",
                "created_at": "2026-07-01T18:09:00Z"
            }
        }

class NodeResponse(BaseModel):
    id: str
    name: str
    type: NodeType
    location: str
    latitude: float
    longitude: float
    base_cost: float
    capacity: float
    health: float
    risk_score: float
    inventory: float
    safety_stock: float
    daily_consumption: float
    replenishment_rate: float
    metadata: Dict[str, Any]

class EdgeResponse(BaseModel):
    source: str
    target: str
    type: EdgeType
    dependency_ratio: float
    lead_time_days: int
    transport_mode: str

class GraphResponse(BaseModel):
    """Digital Twin Graph topology representation."""
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]

class MetricsResponse(BaseModel):
    """Global active executive dashboard metrics representation."""
    overall_resilience: float = Field(..., description="Average health percentage across active supply nodes")
    total_financial_loss: float = Field(..., description="Total financial loss incurred in active timeline in USD")
    delayed_products_count: int = Field(..., description="Total delayed assembly products count")
    disrupted_nodes_count: int = Field(..., description="Number of nodes currently reporting health < 1.0")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_resilience": 77.8,
                "total_financial_loss": 363093.75,
                "delayed_products_count": 0,
                "disrupted_nodes_count": 2
            }
        }
