from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class MitigationOption(BaseModel):
    """
    MitigationOption represents a candidate operational adjustment
    (e.g., rerouting cargo, air freighting parts) evaluated by the Decision Engine.
    """
    option_id: str = Field(..., description="Unique identifier for the mitigation option")
    title: str = Field(..., description="Short name of the mitigation option")
    description: str = Field(..., description="Details of the operational change")
    cost_impact: float = Field(..., description="Added logistics fee or surcharge in USD")
    lead_time_surcharge_days: int = Field(..., description="Additional transit delay compared to normal operations")
    feasibility_score: float = Field(..., ge=0.0, le=1.0, description="Carrier/resource availability likelihood (0.0 to 1.0)")
    calculated_score: float = Field(default=0.0, description="Computed utility score where higher is better")
    is_recommended: bool = Field(default=False, description="Flag indicating if this option is the optimal rank")

class CompositeConfidence(BaseModel):
    """
    Confidence metrics propagated through the stages of extraction, simulation, and optimization.
    """
    extraction: float = Field(..., ge=0.0, le=1.0, description="Confidence of the event parsing (Ce)")
    simulation: float = Field(..., ge=0.0, le=1.0, description="Confidence of the graph telemetry visibility (Cs)")
    optimization: float = Field(..., ge=0.0, le=1.0, description="Feasibility confidence of resources/contracts (Co)")
    overall: float = Field(..., ge=0.0, le=1.0, description="Aggregated confidence rating (Cd = Ce * Cs * Co)")

class DoNothingImpact(BaseModel):
    """
    Calculated penalty if no mitigation action is taken.
    """
    earliest_stockout_day: int = Field(..., description="The day downstream factories run completely dry")
    total_financial_loss: float = Field(..., description="Lost production and penalty costs in USD")
    delayed_products_count: int = Field(..., description="Number of end products delayed")

class RecommendationBundle(BaseModel):
    """
    Aggregate root for the Decision Optimization Context. Bundles mathematical
    ranking results with AI-synthesized narrative explanations for business leaders.
    """
    id: str = Field(..., description="Unique recommendation ID")
    event_id: str = Field(..., description="Reference ID of the triggering RiskEvent")
    do_nothing_impact: DoNothingImpact = Field(..., description="Metrics showing the baseline disruption damage")
    options: List[MitigationOption] = Field(..., description="Evaluated mitigation options ranked by score")
    composite_confidence: CompositeConfidence = Field(..., description="Propagated confidence details")
    gemini_explanation: str = Field(..., description="Executive plain-language reasoning comparing the options")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")

