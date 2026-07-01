from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.domain.models.network import Node, Edge

class GraphEngine(ABC):
    """
    GraphEngine is the port that abstracts graph topological calculations.
    It isolates CPU-based (NetworkX) or GPU-based (cuGraph) details from the Domain layer.
    """

    @abstractmethod
    def build_graph(self, nodes: List[Node], edges: List[Edge]) -> None:
        """
        Populates or builds the internal graph structure from domain nodes and edges.
        """
        pass

    @abstractmethod
    def get_nodes(self) -> List[Node]:
        """
        Returns the nodes as managed within the graph engine.
        """
        pass

    @abstractmethod
    def get_edges(self) -> List[Edge]:
        """
        Returns the edges as managed within the graph engine.
        """
        pass

    @abstractmethod
    def find_alternative_paths(self, source: str, target: str, blocked_node_id: str) -> List[List[str]]:
        """
        Finds candidate alternative pathways between two nodes, bypassing a blocked node.
        """
        pass

    @abstractmethod
    def get_shortest_path_lead_time(self, source: str, target: str) -> Optional[int]:
        """
        Calculates the minimum lead time (sum of lead_time_days along shortest path) between nodes.
        """
        pass
