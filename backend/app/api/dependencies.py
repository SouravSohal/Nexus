from backend.app.core.config import settings
from backend.app.infrastructure.db.sqlite_repo import SQLiteRepository
from backend.app.infrastructure.graph.networkx_engine import NetworkXGraphEngine
from backend.app.infrastructure.external.ai.orchestrator import AIOrchestrator
from backend.app.domain.services.simulation_engine import TemporalSimulationEngine
from backend.app.domain.services.decision_engine import DecisionEngine
from backend.app.application.event_bus import EventBus
from backend.app.application.event_orchestrator import EventOrchestrator

# Core Singletons configured from global settings
repo = SQLiteRepository(settings.DB_PATH)
graph_engine = NetworkXGraphEngine()
sim_engine = TemporalSimulationEngine(graph_engine)
decision_engine = DecisionEngine()
ai_client = AIOrchestrator()
event_bus = EventBus()

# Application Orchestrator
orchestrator = EventOrchestrator(
    repository=repo,
    ai_client=ai_client,
    simulation_engine=sim_engine,
    decision_engine=decision_engine,
    event_bus=event_bus
)

def get_orchestrator() -> EventOrchestrator:
    """Dependency provider for the application orchestrator."""
    return orchestrator

def get_repository() -> SQLiteRepository:
    """Dependency provider for the database repository."""
    return repo

def get_ai_client() -> AIOrchestrator:
    """Dependency provider for the AI orchestrator."""
    return ai_client
