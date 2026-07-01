from fastapi import APIRouter
from backend.app.api.endpoints import events, graph, metrics

api_router = APIRouter()

# Wire context routes
api_router.include_router(events.router, prefix="/events", tags=["Events & Simulations"])
api_router.include_router(graph.router, prefix="/graph", tags=["Digital Twin Topology"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Dashboard Metrics"])
