import networkx as nx
from typing import List, Optional
from backend.app.domain.interfaces.graph_engine import GraphEngine
from backend.app.domain.models.network import Node, Edge, NodeType, EdgeType

class NetworkXGraphEngine(GraphEngine):
    """
    NetworkXGraphEngine implements GraphEngine using the CPU-bound NetworkX library.
    It builds a directed graph (DiGraph) to model topological flows and compute routing paths.
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph(self, nodes: List[Node], edges: List[Edge]) -> None:
        self.graph.clear()
        
        # Add Nodes with attributes
        for node in nodes:
            self.graph.add_node(
                node.id,
                domain_model=node
            )
            
        # Add Edges with attributes
        for edge in edges:
            self.graph.add_edge(
                edge.source,
                edge.target,
                type=edge.type.value,
                dependency_ratio=edge.dependency_ratio,
                lead_time_days=edge.lead_time_days,
                transport_mode=edge.transport_mode
            )

    def get_nodes(self) -> List[Node]:
        nodes = []
        for n_id, attrs in self.graph.nodes(data=True):
            if "domain_model" in attrs:
                nodes.append(attrs["domain_model"])
        return nodes

    def get_edges(self) -> List[Edge]:
        edges = []
        for u, v, attrs in self.graph.edges(data=True):
            edges.append(Edge(
                source=u,
                target=v,
                type=EdgeType(attrs["type"]),
                dependency_ratio=attrs["dependency_ratio"],
                lead_time_days=attrs["lead_time_days"],
                transport_mode=attrs["transport_mode"]
            ))
        return edges

    def find_alternative_paths(self, source: str, target: str, blocked_node_id: str) -> List[List[str]]:
        """
        Finds all simple paths from source to target that do not pass through the blocked node.
        Used by the Decision Engine to calculate rerouting logistics.
        """
        if source not in self.graph or target not in self.graph:
            return []
            
        try:
            # Generate all simple paths between source and target
            all_paths = list(nx.all_simple_paths(self.graph, source, target))
            
            # Filter out paths that contain the blocked node
            valid_paths = [path for path in all_paths if blocked_node_id not in path]
            return valid_paths
        except Exception:
            return []

    def get_shortest_path_lead_time(self, source: str, target: str) -> Optional[int]:
        """
        Calculates the sum of edge lead times along the shortest path (by weight = lead_time_days).
        """
        if source not in self.graph or target not in self.graph:
            return None
            
        try:
            path = nx.shortest_path(self.graph, source=source, target=target, weight="lead_time_days")
            total_lead_time = 0
            for i in range(len(path) - 1):
                edge_data = self.graph.get_edge_data(path[i], path[i+1])
                total_lead_time += edge_data.get("lead_time_days", 0)
            return total_lead_time
        except nx.NetworkXNoPath:
            return None
