from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List

class EventStatus(str, Enum):
    DRAFTED = "DRAFTED"
    COMMITTED = "COMMITTED"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"

class AffectedNodeImpact(BaseModel):
    """
    Represents the details of a disruption on a specific node.
    """
    node_id: str = Field(..., description="ID of the affected digital twin node")
    severity: float = Field(..., ge=0.0, le=1.0, description="Disruption impact ratio (0.0 to 1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence for this specific node (0.0 to 1.0)")
    disruption_type: str = Field(default="shutdown", description="Type of disruption (e.g., shutdown, power_loss, congestion)")

class RiskEvent(BaseModel):
    """
    RiskEvent represents an unstructured disruption event that has been parsed,
    classified, and committed to the Event Store. It supports multi-node impact.
    """
    id: str = Field(..., description="Unique UUID string representing the event")
    title: str = Field(..., description="Short descriptive title of the event")
    description: str = Field(..., description="Detailed description of the news text or incident")
    location: str = Field(..., description="Geographical location of the disruption")
    affected_node_id: str = Field(..., description="The primary ID (fallback) of the disrupted node")
    severity: float = Field(..., ge=0.0, le=1.0, description="Primary disruption impact ratio (fallback)")
    duration_days: int = Field(..., gt=0, description="Estimated duration of the disruption in days")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Primary confidence score (fallback)")
    status: EventStatus = Field(default=EventStatus.DRAFTED, description="The current lifecycle stage of the risk event")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="The UTC timestamp when the event was ingested")
    affected_nodes: List[AffectedNodeImpact] = Field(default_factory=list, description="Collection of all nodes affected by this event")

    @model_validator(mode="before")
    @classmethod
    def populate_affected_nodes_and_fallback(cls, data):
        if isinstance(data, dict):
            # If affected_nodes is not present or empty but affected_node_id is present, populate affected_nodes
            if "affected_nodes" not in data or not data["affected_nodes"]:
                if "affected_node_id" in data and data["affected_node_id"]:
                    data["affected_nodes"] = [{
                        "node_id": data["affected_node_id"],
                        "severity": data.get("severity", 1.0),
                        "confidence": data.get("confidence_score", 1.0),
                        "disruption_type": data.get("disruption_type", "shutdown")
                    }]
            # Conversely, if affected_nodes is present but affected_node_id is not, populate fallback fields from the first entry
            if "affected_nodes" in data and data["affected_nodes"] and ("affected_node_id" not in data or not data["affected_node_id"]):
                first_impact = data["affected_nodes"][0]
                if isinstance(first_impact, dict):
                    data["affected_node_id"] = first_impact.get("node_id")
                    data["severity"] = first_impact.get("severity", 1.0)
                    data["confidence_score"] = first_impact.get("confidence", 1.0)
                else:
                    data["affected_node_id"] = first_impact.node_id
                    data["severity"] = first_impact.severity
                    data["confidence_score"] = first_impact.confidence
        return data

    class Config:
        frozen = True
        json_schema_extra = {
            "example": {
                "id": "evt-regional-typhoon-2026",
                "title": "East Asia Typhoon Outage",
                "description": "Category 3 typhoon strikes East Asia, disrupting Port of Kaohsiung and Port of Singapore.",
                "location": "East Asia",
                "affected_node_id": "port-kaohsiung",
                "severity": 1.0,
                "duration_days": 3,
                "confidence_score": 0.95,
                "status": "COMMITTED",
                "created_at": "2026-07-01T01:44:00Z",
                "affected_nodes": [
                    {
                        "node_id": "port-kaohsiung",
                        "severity": 1.0,
                        "confidence": 0.95,
                        "disruption_type": "weather_shutdown"
                    },
                    {
                        "node_id": "port-singapore",
                        "severity": 0.8,
                        "confidence": 0.90,
                        "disruption_type": "congestion"
                    }
                ]
            }
        }
