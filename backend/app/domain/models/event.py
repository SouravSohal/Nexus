from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class EventStatus(str, Enum):
    DRAFTED = "DRAFTED"
    COMMITTED = "COMMITTED"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"

class RiskEvent(BaseModel):
    """
    RiskEvent represents an unstructured disruption event that has been parsed,
    classified, and committed to the Event Store. It acts as the initiator
    of the digital twin simulation and optimization flow.
    """
    id: str = Field(..., description="Unique UUID string representing the event")
    title: str = Field(..., description="Short descriptive title of the event")
    description: str = Field(..., description="Detailed description of the news text or incident")
    location: str = Field(..., description="Geographical location of the disruption")
    affected_node_id: str = Field(..., description="The ID of the Digital Twin Node that is directly disrupted")
    severity: float = Field(..., ge=0.0, le=1.0, description="Disruption impact ratio, where 1.0 is a complete shutdown and 0.0 is healthy")
    duration_days: int = Field(..., gt=0, description="Estimated duration of the disruption in days")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score from the AI parser (0.0 to 1.0)")
    status: EventStatus = Field(default=EventStatus.DRAFTED, description="The current lifecycle stage of the risk event")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="The UTC timestamp when the event was ingested")


    class Config:
        frozen = True
        json_schema_extra = {
            "example": {
                "id": "evt-antwerp-strike-2026",
                "title": "Port of Antwerp Strike",
                "description": "Port of Antwerp dockworkers launch a five-day strike halting container activities.",
                "location": "Antwerp, Belgium",
                "affected_node_id": "port-antwerp",
                "severity": 0.85,
                "duration_days": 5,
                "confidence_score": 0.95,
                "status": "COMMITTED",
                "created_at": "2026-07-01T01:44:00Z"
            }
        }
