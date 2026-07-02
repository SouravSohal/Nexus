import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.app.domain.interfaces.repository import SupplyChainRepository
from backend.app.domain.models.event import RiskEvent, EventStatus
from backend.app.domain.models.network import Node, Edge, NodeType, EdgeType
from backend.app.domain.models.simulation import SimulationRun, TemporalStep
from backend.app.domain.models.decision import RecommendationBundle, MitigationOption, CompositeConfidence, DoNothingImpact

class SQLiteRepository(SupplyChainRepository):
    """
    SQLiteRepository implements data persistence using SQLite.
    It automatically boots the schema if the tables are missing.
    """

    def __init__(self, db_path: str):
        import os
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            raise FileNotFoundError(
                f"SQLite database file not found or empty at expected path: '{db_path}'. "
                "Please seed the database first by running: python scripts/seed_db.py"
            )
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Create Nodes Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    base_cost REAL NOT NULL,
                    capacity REAL NOT NULL,
                    health REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    inventory REAL NOT NULL,
                    safety_stock REAL NOT NULL,
                    daily_consumption REAL NOT NULL,
                    replenishment_rate REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)

            # Create Edges Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    type TEXT NOT NULL,
                    dependency_ratio REAL NOT NULL,
                    lead_time_days INTEGER NOT NULL,
                    transport_mode TEXT NOT NULL,
                    PRIMARY KEY (source, target)
                )
            """)

            # Create Risk Events Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    location TEXT NOT NULL,
                    affected_node_id TEXT NOT NULL,
                    severity REAL NOT NULL,
                    duration_days INTEGER NOT NULL,
                    confidence_score REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    affected_nodes_json TEXT
                )
            """)
            
            # Check and add column if it was created previously without this column
            cursor.execute("PRAGMA table_info(risk_events)")
            columns = [info[1] for info in cursor.fetchall()]
            if "affected_nodes_json" not in columns:
                cursor.execute("ALTER TABLE risk_events ADD COLUMN affected_nodes_json TEXT")

            # Create Simulation Runs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    timeline_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES risk_events(id)
                )
            """)

            # Create Recommendations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    do_nothing_json TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    confidence_json TEXT NOT NULL,
                    gemini_explanation TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES risk_events(id)
                )
            """)
            conn.commit()

    def get_nodes(self) -> List[Node]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM nodes")
            rows = cursor.fetchall()
            nodes = []
            for row in rows:
                nodes.append(Node(
                    id=row["id"],
                    name=row["name"],
                    type=NodeType(row["type"]),
                    location=row["location"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    base_cost=row["base_cost"],
                    capacity=row["capacity"],
                    health=row["health"],
                    risk_score=row["risk_score"],
                    inventory=row["inventory"],
                    safety_stock=row["safety_stock"],
                    daily_consumption=row["daily_consumption"],
                    replenishment_rate=row["replenishment_rate"],
                    metadata=json.loads(row["metadata"])
                ))
            return nodes

    def get_node(self, node_id: str) -> Optional[Node]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Node(
                id=row["id"],
                name=row["name"],
                type=NodeType(row["type"]),
                location=row["location"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                base_cost=row["base_cost"],
                capacity=row["capacity"],
                health=row["health"],
                risk_score=row["risk_score"],
                inventory=row["inventory"],
                safety_stock=row["safety_stock"],
                daily_consumption=row["daily_consumption"],
                replenishment_rate=row["replenishment_rate"],
                metadata=json.loads(row["metadata"])
            )

    def get_edges(self) -> List[Edge]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM edges")
            rows = cursor.fetchall()
            edges = []
            for row in rows:
                edges.append(Edge(
                    source=row["source"],
                    target=row["target"],
                    type=EdgeType(row["type"]),
                    dependency_ratio=row["dependency_ratio"],
                    lead_time_days=row["lead_time_days"],
                    transport_mode=row["transport_mode"]
                ))
            return edges

    def update_node(self, node: Node) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE nodes SET
                    name = ?, type = ?, location = ?, latitude = ?, longitude = ?,
                    base_cost = ?, capacity = ?, health = ?, risk_score = ?,
                    inventory = ?, safety_stock = ?, daily_consumption = ?,
                    replenishment_rate = ?, metadata = ?
                WHERE id = ?
            """, (
                node.name, node.type.value, node.location, node.latitude, node.longitude,
                node.base_cost, node.capacity, node.health, node.risk_score,
                node.inventory, node.safety_stock, node.daily_consumption,
                node.replenishment_rate, json.dumps(node.metadata), node.id
            ))
            conn.commit()

    def reset_network_to_baseline(self) -> None:
        from backend.app.infrastructure.db.seed_data import SEED_NODES, SEED_EDGES
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Clear Tables
            cursor.execute("DELETE FROM nodes")
            cursor.execute("DELETE FROM edges")
            
            # Seed Nodes
            for node in SEED_NODES:
                cursor.execute("""
                    INSERT OR REPLACE INTO nodes (
                        id, name, type, location, latitude, longitude, base_cost, capacity,
                        health, risk_score, inventory, safety_stock, daily_consumption,
                        replenishment_rate, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    node.id, node.name, node.type.value, node.location, node.latitude, node.longitude,
                    node.base_cost, node.capacity, node.health, node.risk_score,
                    node.inventory, node.safety_stock, node.daily_consumption,
                    node.replenishment_rate, json.dumps(node.metadata)
                ))
            
            # Seed Edges
            for edge in SEED_EDGES:
                cursor.execute("""
                    INSERT OR REPLACE INTO edges (
                        source, target, type, dependency_ratio, lead_time_days, transport_mode
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    edge.source, edge.target, edge.type.value, edge.dependency_ratio,
                    edge.lead_time_days, edge.transport_mode
                ))
            conn.commit()

    def create_risk_event(self, event: RiskEvent) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            affected_nodes_json = json.dumps([n.model_dump() for n in event.affected_nodes])
            cursor.execute("""
                INSERT OR REPLACE INTO risk_events (
                    id, title, description, location, affected_node_id,
                    severity, duration_days, confidence_score, status, created_at, affected_nodes_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id, event.title, event.description, event.location, event.affected_node_id,
                event.severity, event.duration_days, event.confidence_score, event.status.value,
                event.created_at.isoformat(), affected_nodes_json
            ))
            conn.commit()

    def get_risk_event(self, event_id: str) -> Optional[RiskEvent]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM risk_events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            if not row:
                return None
            row_dict = dict(row)
            affected_nodes = []
            if row_dict.get("affected_nodes_json"):
                try:
                    affected_nodes = json.loads(row_dict["affected_nodes_json"])
                except Exception:
                    pass
            return RiskEvent(
                id=row_dict["id"],
                title=row_dict["title"],
                description=row_dict["description"],
                location=row_dict["location"],
                affected_node_id=row_dict["affected_node_id"],
                severity=row_dict["severity"],
                duration_days=row_dict["duration_days"],
                confidence_score=row_dict["confidence_score"],
                status=EventStatus(row_dict["status"]),
                created_at=datetime.fromisoformat(row_dict["created_at"]),
                affected_nodes=affected_nodes
            )

    def get_risk_events(self) -> List[RiskEvent]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM risk_events ORDER BY created_at DESC")
            rows = cursor.fetchall()
            events = []
            for row in rows:
                row_dict = dict(row)
                affected_nodes = []
                if row_dict.get("affected_nodes_json"):
                    try:
                        affected_nodes = json.loads(row_dict["affected_nodes_json"])
                    except Exception:
                        pass
                events.append(RiskEvent(
                    id=row_dict["id"],
                    title=row_dict["title"],
                    description=row_dict["description"],
                    location=row_dict["location"],
                    affected_node_id=row_dict["affected_node_id"],
                    severity=row_dict["severity"],
                    duration_days=row_dict["duration_days"],
                    confidence_score=row_dict["confidence_score"],
                    status=EventStatus(row_dict["status"]),
                    created_at=datetime.fromisoformat(row_dict["created_at"]),
                    affected_nodes=affected_nodes
                ))
            return events

    def update_risk_event_status(self, event_id: str, status: EventStatus) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE risk_events SET status = ? WHERE id = ?
            """, (status.value, event_id))
            conn.commit()

    def create_simulation_run(self, run: SimulationRun) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timeline_list = [step.model_dump() for step in run.timeline]
            cursor.execute("""
                INSERT OR REPLACE INTO simulation_runs (
                    id, event_id, timeline_json, created_at
                ) VALUES (?, ?, ?, ?)
            """, (
                run.id, run.event_id, json.dumps(timeline_list), run.created_at.isoformat()
            ))
            conn.commit()

    def get_simulation_run(self, run_id: str) -> Optional[SimulationRun]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM simulation_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            timeline_data = json.loads(row["timeline_json"])
            timeline = [TemporalStep(**step) for step in timeline_data]
            
            return SimulationRun(
                id=row["id"],
                event_id=row["event_id"],
                timeline=timeline,
                created_at=datetime.fromisoformat(row["created_at"])
            )

    def get_latest_simulation_run_by_event(self, event_id: str) -> Optional[SimulationRun]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM simulation_runs 
                WHERE event_id = ? 
                ORDER BY created_at DESC LIMIT 1
            """, (event_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            timeline_data = json.loads(row["timeline_json"])
            timeline = [TemporalStep(**step) for step in timeline_data]
            
            return SimulationRun(
                id=row["id"],
                event_id=row["event_id"],
                timeline=timeline,
                created_at=datetime.fromisoformat(row["created_at"])
            )

    def create_recommendation(self, recommendation: RecommendationBundle) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO recommendations (
                    id, event_id, do_nothing_json, options_json, confidence_json,
                    gemini_explanation, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                recommendation.id,
                recommendation.event_id,
                recommendation.do_nothing_impact.model_dump_json(),
                json.dumps([opt.model_dump() for opt in recommendation.options]),
                recommendation.composite_confidence.model_dump_json(),
                recommendation.gemini_explanation,
                recommendation.created_at.isoformat()
            ))
            conn.commit()

    def get_recommendation_by_event(self, event_id: str) -> Optional[RecommendationBundle]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM recommendations 
                WHERE event_id = ? 
                ORDER BY created_at DESC LIMIT 1
            """, (event_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            do_nothing = DoNothingImpact(**json.loads(row["do_nothing_json"]))
            options = [MitigationOption(**opt) for opt in json.loads(row["options_json"])]
            confidence = CompositeConfidence(**json.loads(row["confidence_json"]))
            
            return RecommendationBundle(
                id=row["id"],
                event_id=row["event_id"],
                do_nothing_impact=do_nothing,
                options=options,
                composite_confidence=confidence,
                gemini_explanation=row["gemini_explanation"],
                created_at=datetime.fromisoformat(row["created_at"])
            )
