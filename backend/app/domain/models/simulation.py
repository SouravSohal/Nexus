from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Dict

class NodeState(BaseModel):
    """
    State of a specific node at a particular point in time during a simulation.
    """
    health: float = Field(..., ge=0.0, le=1.0, description="Health value of the node (0.0 to 1.0)")
    inventory: float = Field(..., ge=0.0, description="Inventory quantity on hand")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Propagated risk score (0.0 to 1.0)")
    replenishment_rate: float = Field(..., ge=0.0, description="Effective replenishment rate on this day")

class StepMetrics(BaseModel):
    """
    Aggregated global supply chain performance metrics on a simulated day.
    """
    resilience_score: float = Field(..., ge=0.0, le=100.0, description="Overall health rating of the network from 0% to 100%")
    financial_loss: float = Field(..., ge=0.0, description="Cumulative financial risk / revenue loss incurred in USD")
    delayed_products: int = Field(..., ge=0, description="Number of end products delayed due to part stockouts")
    disrupted_nodes_count: int = Field(..., ge=0, description="Count of nodes experiencing disruption (health < 1.0)")

class TemporalStep(BaseModel):
    """
    Represents the full system snapshot on a single day of the simulation.
    """
    day: int = Field(..., ge=0, description="Day offset from the start of the simulation (0, 1, 2, ...)")
    metrics: StepMetrics = Field(..., description="Global KPIs computed for this day")
    node_states: Dict[str, NodeState] = Field(..., description="Mapping of node ID to its state on this day")

class SimulationRun(BaseModel):
    """
    Aggregate root representing a full simulation execution for a specific RiskEvent.
    """
    id: str = Field(..., description="Unique simulation execution identifier")
    event_id: str = Field(..., description="Reference ID of the triggering RiskEvent")
    timeline: List[TemporalStep] = Field(..., description="Day-by-day progression list of graph states")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")

