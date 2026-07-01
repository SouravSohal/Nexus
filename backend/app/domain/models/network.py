from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any

class NodeType(str, Enum):
    SUPPLIER = "SUPPLIER"
    PORT = "PORT"
    WAREHOUSE = "WAREHOUSE"
    FACTORY = "FACTORY"
    DISTRIBUTION_CENTER = "DISTRIBUTION_CENTER"
    PRODUCT = "PRODUCT"

class EdgeType(str, Enum):
    SUPPLIES = "SUPPLIES"
    SHIPS_TO = "SHIPS_TO"
    DEPENDS_ON = "DEPENDS_ON"
    MANUFACTURES = "MANUFACTURES"

class Node(BaseModel):
    """
    Node represents a physical or logical entity in the supply chain digital twin.
    It carries operational state (health, inventory level) which can deteriorate
    during simulations.
    """
    id: str = Field(..., description="Unique code identifier for the node")
    name: str = Field(..., description="Human readable name of the node")
    type: NodeType = Field(..., description="The operational type of the node")
    location: str = Field(..., description="City or region where the node is located")
    latitude: float = Field(..., description="Decimal latitude for map visualization")
    longitude: float = Field(..., description="Decimal longitude for map visualization")
    base_cost: float = Field(default=0.0, description="Base daily operating cost of the node in USD")
    capacity: float = Field(default=100.0, description="Maximum daily throughput/processing capability")
    health: float = Field(default=1.0, ge=0.0, le=1.0, description="Current health status (1.0 = fully healthy, 0.0 = completely down)")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Propagated risk score (0.0 = safe, 1.0 = highly vulnerable)")
    inventory: float = Field(default=100.0, ge=0.0, description="Current stock of inventory units on hand")
    safety_stock: float = Field(default=50.0, ge=0.0, description="Safety stock threshold. Going below increases risk")
    daily_consumption: float = Field(default=10.0, ge=0.0, description="Daily rate of inventory consumed or shipped out")
    replenishment_rate: float = Field(default=10.0, ge=0.0, description="Baseline daily quantity received from suppliers")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom JSON fields for specific node attributes")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "port-antwerp",
                "name": "Port of Antwerp-Bruges",
                "type": "PORT",
                "location": "Antwerp, Belgium",
                "latitude": 51.2194,
                "longitude": 4.4025,
                "base_cost": 25000.0,
                "capacity": 500.0,
                "health": 1.0,
                "risk_score": 0.0,
                "inventory": 200.0,
                "safety_stock": 100.0,
                "daily_consumption": 80.0,
                "replenishment_rate": 80.0,
                "metadata": {"vessel_slots": 50}
            }
        }

class Edge(BaseModel):
    """
    Edge represents a dependency flow between two nodes in the digital twin.
    It carries attributes that govern temporal delay and impact size (dependency ratio).
    """
    source: str = Field(..., description="Origin node ID")
    target: str = Field(..., description="Destination node ID")
    type: EdgeType = Field(..., description="The dependency relationship type")
    dependency_ratio: float = Field(default=1.0, ge=0.0, le=1.0, description="Weight proportion (how much target relies on source, 0.0 to 1.0)")
    lead_time_days: int = Field(default=1, ge=0, description="Transit delay or manufacturing duration in days")
    transport_mode: str = Field(default="road", description="Mode of transport: road, ocean, rail, air")

    class Config:
        frozen = True
        json_schema_extra = {
            "example": {
                "source": "port-antwerp",
                "target": "warehouse-munich",
                "type": "SHIPS_TO",
                "dependency_ratio": 0.8,
                "lead_time_days": 2,
                "transport_mode": "road"
            }
        }
