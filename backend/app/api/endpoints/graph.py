from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.api.dependencies import get_repository
from backend.app.domain.interfaces.repository import SupplyChainRepository
from backend.app.api.mappers import map_node_to_response, map_edge_to_response
from backend.app.models.api_schemas import GraphResponse

router = APIRouter()

@router.get("/", response_model=GraphResponse)
def get_graph_topology(repo: SupplyChainRepository = Depends(get_repository)):
    """
    Returns the current topology of the Digital Twin supply chain, 
    including nodes (positions, capacities, current inventories, risk scores)
    and edges (lead times, dependency ratios, modes).
    """
    try:
        nodes = repo.get_nodes()
        edges = repo.get_edges()
        
        mapped_nodes = [map_node_to_response(n) for n in nodes]
        mapped_edges = [map_edge_to_response(e) for e in edges]
        
        return GraphResponse(nodes=mapped_nodes, edges=mapped_edges)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query graph: {str(e)}"
        )
