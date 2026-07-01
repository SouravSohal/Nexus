from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.domain.models.event import RiskEvent, EventStatus
from backend.app.domain.models.network import Node, Edge
from backend.app.domain.models.simulation import SimulationRun
from backend.app.domain.models.decision import RecommendationBundle

class SupplyChainRepository(ABC):
    """
    SupplyChainRepository is the port defining all persistent data access routines.
    It isolates the core application from the choice of database (SQLite, PostgreSQL, BigQuery).
    """

    @abstractmethod
    def get_nodes(self) -> List[Node]:
        """Fetch all digital twin nodes currently in the system."""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Node]:
        """Fetch a specific digital twin node by its ID."""
        pass

    @abstractmethod
    def get_edges(self) -> List[Edge]:
        """Fetch all digital twin edges/routing pathways."""
        pass

    @abstractmethod
    def update_node(self, node: Node) -> None:
        """Update operational parameters (health, inventory) of an existing node."""
        pass

    @abstractmethod
    def reset_network_to_baseline(self) -> None:
        """Restore all nodes and edges back to their healthy seed data state."""
        pass

    @abstractmethod
    def create_risk_event(self, event: RiskEvent) -> None:
        """Commit a newly parsed RiskEvent to the database."""
        pass

    @abstractmethod
    def get_risk_event(self, event_id: str) -> Optional[RiskEvent]:
        """Retrieve a committed RiskEvent by its unique ID."""
        pass

    @abstractmethod
    def get_risk_events(self) -> List[RiskEvent]:
        """Fetch a list of all committed and drafted RiskEvents."""
        pass

    @abstractmethod
    def update_risk_event_status(self, event_id: str, status: EventStatus) -> None:
        """Transition the lifecycle status of a RiskEvent."""
        pass

    @abstractmethod
    def create_simulation_run(self, run: SimulationRun) -> None:
        """Store a simulation execution timeline for audit and analysis."""
        pass

    @abstractmethod
    def get_simulation_run(self, run_id: str) -> Optional[SimulationRun]:
        """Retrieve a specific past simulation run timeline."""
        pass

    @abstractmethod
    def get_latest_simulation_run_by_event(self, event_id: str) -> Optional[SimulationRun]:
        """Retrieve the latest simulation run associated with a specific event."""
        pass

    @abstractmethod
    def create_recommendation(self, recommendation: RecommendationBundle) -> None:
        """Store a decision recommendation bundle."""
        pass

    @abstractmethod
    def get_recommendation_by_event(self, event_id: str) -> Optional[RecommendationBundle]:
        """Retrieve the decision recommendations associated with a specific event."""
        pass
