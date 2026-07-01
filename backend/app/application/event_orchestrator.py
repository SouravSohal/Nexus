import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.core.logging import logger
from backend.app.application.event_bus import EventBus
from backend.app.domain.interfaces.repository import SupplyChainRepository
from backend.app.domain.interfaces.ai_client import AIClient
from backend.app.domain.services.simulation_engine import TemporalSimulationEngine
from backend.app.domain.services.decision_engine import DecisionEngine
from backend.app.domain.models.event import RiskEvent, EventStatus
from backend.app.domain.models.network import Node, Edge
from backend.app.domain.models.simulation import SimulationRun
from backend.app.domain.models.decision import RecommendationBundle

class EventOrchestrator:
    """
    EventOrchestrator coordinates the workflows of NEXUS, handling API requests
    and managing the transactional lifecycle of RiskEvents over the EventBus.
    """

    def __init__(
        self,
        repository: SupplyChainRepository,
        ai_client: AIClient,
        simulation_engine: TemporalSimulationEngine,
        decision_engine: DecisionEngine,
        event_bus: EventBus
    ):
        self.repo = repository
        self.ai = ai_client
        self.sim = simulation_engine
        self.decision = decision_engine
        self.bus = event_bus
        
        # Wire EventBus subscriptions
        self.bus.subscribe("RiskEventCommitted", self._on_event_committed)
        self.bus.subscribe("SimulationCompleted", self._on_simulation_completed)

    def ingest_news_alert(self, news_text: str) -> RiskEvent:
        """
        Ingestion Port: Parses news using Gemini, maps target nodes,
        instantiates the Pydantic RiskEvent domain model, saves it,
        and triggers the downstream bus.
        """
        # Fetch active nodes to supply context to the LLM
        nodes = self.repo.get_nodes()
        nodes_dict_list = [
            {"id": n.id, "name": n.name, "type": n.type.value, "location": n.location}
            for n in nodes
        ]
        
        # 1. Extraction (Infrastructure)
        extracted = self.ai.extract_risk_event_from_text(news_text, nodes_dict_list)
        
        # 2. Domain Validation & Aggregate Instantiation
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        risk_event = RiskEvent(
            id=event_id,
            title=extracted["title"],
            description=extracted["description"],
            location=extracted["location"],
            affected_node_id=extracted["affected_node_id"],
            severity=extracted["severity"],
            duration_days=extracted["duration_days"],
            confidence_score=extracted["confidence_score"],
            status=EventStatus.COMMITTED,
            created_at=datetime.now(timezone.utc)
        )
        
        # 3. Commit to Event Store (Infrastructure)
        self.repo.create_risk_event(risk_event)
        logger.info(f"[EVENT] RiskEventCommitted id={risk_event.id} target={risk_event.affected_node_id} severity={risk_event.severity}")
        
        # 4. Dispatch Event (Synchronous)
        self.bus.publish("RiskEventCommitted", risk_event)
        
        return risk_event

    def run_manual_simulation(self, event_id: str, duration_days: int = 10) -> SimulationRun:
        """
        Runs a simulation for an existing event, updating stored states.
        """
        event = self.repo.get_risk_event(event_id)
        if not event:
            raise ValueError(f"Event with ID {event_id} not found.")
            
        nodes = self.repo.get_nodes()
        edges = self.repo.get_edges()
        
        logger.info(f"[SIMULATION] Started id={event_id} steps={duration_days}")
        start_time = time.perf_counter()
        
        # Run calculation
        run = self.sim.run_simulation(event, nodes, edges, duration_days=duration_days)
        
        runtime_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(f"[SIMULATION] Completed runtime={runtime_ms:.2f} ms ID={run.id}")
        
        # Persist results
        self.repo.create_simulation_run(run)
        return run

    def get_decision_recommendations(self, event_id: str) -> Optional[RecommendationBundle]:
        """
        Retrieves or generates the recommendation bundle for an event.
        """
        # Return existing recommendation if already populated
        existing_rec = self.repo.get_recommendation_by_event(event_id)
        if existing_rec:
            return existing_rec
            
        # Otherwise run optimization pipeline
        event = self.repo.get_risk_event(event_id)
        if not event:
            return None
            
        sim_run = self.repo.get_latest_simulation_run_by_event(event_id)
        if not sim_run:
            sim_run = self.run_manual_simulation(event_id)
            
        nodes = self.repo.get_nodes()
        
        # Calculate algebraic utilities
        recommendation = self.decision.evaluate_mitigation(event, sim_run, nodes)
        
        # Generate LLM trade-off briefing narrative
        briefing = self.ai.generate_executive_recommendation(
            event, 
            recommendation.do_nothing_impact, 
            recommendation.options
        )
        recommendation.gemini_explanation = briefing
        
        # Persist and return
        self.repo.create_recommendation(recommendation)
        logger.info(f"[DECISION] Ranked {len(recommendation.options)} mitigation options. Recommended: {recommendation.options[0].title}")
        return recommendation

    def apply_mitigation_action(self, event_id: str, option_id: str) -> None:
        """
        Executes a mitigation selection, modifying the active database Digital Twin topology
        to reflect rerouted paths or domestic sourcing swaps.
        """
        logger.info(f"[DECISION] Applying Mitigation Action '{option_id}' for Event '{event_id}'")
        
        nodes = self.repo.get_nodes()
        edges = self.repo.get_edges()
        
        nodes_map = {n.id: n for n in nodes}
        
        if option_id == "opt-reroute-rotterdam":
            # 1. Reroute logistics flow from Antwerp to Rotterdam
            # Disable Antwerp edges, enable Rotterdam edges
            updated_edges = []
            for edge in edges:
                if edge.source == "port-kaohsiung" and edge.target == "port-antwerp":
                    # Disable Kaohsiung -> Antwerp flow ratio
                    updated_edges.append(edge.model_copy(update={"dependency_ratio": 0.0}))
                elif edge.source == "port-kaohsiung" and edge.target == "port-rotterdam":
                    # Route 100% flow ratio to Rotterdam
                    updated_edges.append(edge.model_copy(update={"dependency_ratio": 1.0}))
                elif edge.source == "port-antwerp" and edge.target == "warehouse-munich":
                    updated_edges.append(edge.model_copy(update={"dependency_ratio": 0.0}))
                elif edge.source == "port-rotterdam" and edge.target == "warehouse-munich":
                    updated_edges.append(edge.model_copy(update={"dependency_ratio": 1.0}))
                else:
                    updated_edges.append(edge)
            
            # 2. Adjust node operational parameters
            # Port Rotterdam daily operations become active (consumption = 40.0)
            # Port Antwerp becomes idle (consumption = 0.0)
            if "port-rotterdam" in nodes_map:
                r_node = nodes_map["port-rotterdam"]
                self.repo.update_node(r_node.model_copy(update={"daily_consumption": 40.0, "replenishment_rate": 40.0}))
            if "port-antwerp" in nodes_map:
                a_node = nodes_map["port-antwerp"]
                self.repo.update_node(a_node.model_copy(update={"daily_consumption": 0.0, "replenishment_rate": 0.0}))
                
            # Write updated edges to DB
            for edge in updated_edges:
                # In SQLite adapter, inserting handles replaces
                # To modify edge ratios, we reseed or write custom updates.
                # Since SQLiteRepo.reset_network_to_baseline resets from memory SEED arrays,
                # we can issue direct updates or clear/rewrite.
                # To be clean, let's write a simple raw update script or update via repo (noting that update_node updates nodes).
                # We'll run custom SQLite updates directly in our repo or via orchestrator connection.
                pass
                
            # Let's save edges directly. Let's make sure we update edges in SQLite database.
            # I will run a direct query to update edge dependency ratios in the DB.
            conn = sqlite3_connection = self.repo._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE edges SET dependency_ratio = 0.0 WHERE source = 'port-kaohsiung' AND target = 'port-antwerp'")
            cursor.execute("UPDATE edges SET dependency_ratio = 1.0 WHERE source = 'port-kaohsiung' AND target = 'port-rotterdam'")
            cursor.execute("UPDATE edges SET dependency_ratio = 0.0 WHERE source = 'port-antwerp' AND target = 'warehouse-munich'")
            cursor.execute("UPDATE edges SET dependency_ratio = 1.0 WHERE source = 'port-rotterdam' AND target = 'warehouse-munich'")
            conn.commit()
            conn.close()

        elif option_id == "opt-backup-supplier":
            # 2. Switch to local European Silicon Supplier
            # Reroute Assembly factory to local sourcing
            # (In standard electronics twin, Hsinchu Silicon -> Wafer -> Kaohsiung is bypassed)
            # To simulate this, we can set wafer factory to receive directly from domestic supplier or similar.
            # For simplicity, we directly restore wafer/assembly health to 1.0 by injecting local inventory.
            if "warehouse-munich" in nodes_map:
                hub = nodes_map["warehouse-munich"]
                self.repo.update_node(hub.model_copy(update={"inventory": 200.0, "health": 1.0}))
            if "factory-assembly" in nodes_map:
                fac = nodes_map["factory-assembly"]
                self.repo.update_node(fac.model_copy(update={"inventory": 100.0, "health": 1.0}))

        # Update event status
        self.repo.update_risk_event_status(event_id, EventStatus.RESOLVED)
        logger.info(f"[EVENT] RiskEventResolved id={event_id} mitigation={option_id}")

    def reset_system(self) -> None:
        """
        Resets the entire Digital Twin graph configurations to seed baseline.
        """
        self.repo.reset_network_to_baseline()
        logger.info("[SYSTEM] Digital Twin reset to baseline healthy state.")

    # Subscriber Callbacks (Synchronous Event In-Memory Chain)
    def _on_event_committed(self, event: RiskEvent) -> None:
        """
        Triggered when a RiskEvent is saved. Executes simulation.
        """
        try:
            self.run_manual_simulation(event.id)
        except Exception as e:
            logger.error(f"[SYSTEM] Auto-simulation failed for event {event.id}: {str(e)}")

    def _on_simulation_completed(self, run: SimulationRun) -> None:
        """
        Triggered when simulation run compiles. Executes mitigation calculations.
        """
        try:
            self.get_decision_recommendations(run.event_id)
        except Exception as e:
            logger.error(f"[SYSTEM] Auto-decision failed for event {run.event_id}: {str(e)}")
