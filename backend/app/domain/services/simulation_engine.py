import uuid
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Any
from backend.app.domain.interfaces.graph_engine import GraphEngine
from backend.app.domain.models.event import RiskEvent
from backend.app.domain.models.network import Node, Edge, NodeType
from backend.app.domain.models.simulation import SimulationRun, TemporalStep, StepMetrics, NodeState

class TemporalSimulationEngine:
    """
    TemporalSimulationEngine executes a discrete-day simulation of the supply chain network,
    propagating disruptions downstream via inventory depletion and transit lead times.
    """

    def __init__(self, graph_engine: GraphEngine):
        self.graph_engine = graph_engine

    def run_simulation(
        self,
        event: RiskEvent,
        nodes: List[Node],
        edges: List[Edge],
        duration_days: int = 10
    ) -> SimulationRun:
        """
        Executes a temporal simulation for a RiskEvent. Returns a SimulationRun
        containing day-by-day node states and aggregated KPIs.
        """
        # 1. Build the graph representation
        self.graph_engine.build_graph(nodes, edges)
        
        # Build a mapping of affected nodes from the event
        affected_nodes_map = {n.node_id: n for n in event.affected_nodes}
        
        # 2. Setup simulation variables
        current_nodes = {node.id: node.model_copy() for node in nodes}
        adjacency_in: Dict[str, List[Tuple[str, float, int]]] = {node.id: [] for node in nodes}
        
        # Build inbound edge mapping: target -> list of (source, dependency_ratio, lead_time)
        for edge in edges:
            if edge.target in adjacency_in:
                adjacency_in[edge.target].append((edge.source, edge.dependency_ratio, edge.lead_time_days))
        
        # Track historical daily outflows for all nodes: node_id -> dict of {day: quantity}
        # Pre-populate day t < 0 with baseline consumption (steady state operation)
        max_lead_time = max([e.lead_time_days for e in edges]) if edges else 1
        outflow_history: Dict[str, Dict[int, float]] = {node.id: {} for node in nodes}
        for node in nodes:
            for day in range(-max_lead_time - 1, 0):
                outflow_history[node.id][day] = node.daily_consumption

        timeline: List[TemporalStep] = []
        cumulative_financial_loss = 0.0
        cumulative_delayed_products = 0.0

        # 3. Execute the day-by-day loop
        for day in range(duration_days):
            day_node_states: Dict[str, NodeState] = {}
            
            # Step 3.1: Calculate health cap for the directly disrupted node
            event_active = (day < event.duration_days)
            
            # Step 3.2: Calculate inflows for each node on this day
            inflows: Dict[str, float] = {}
            for node_id, node in current_nodes.items():
                inbound_links = adjacency_in[node_id]
                
                if not inbound_links:
                    # Raw material supplier node with no inputs: replenishment is constant
                    # but affected by its own health (if it is disrupted)
                    node_health = node.health
                    if node_id in affected_nodes_map and event_active:
                        impact = affected_nodes_map[node_id]
                        node_health = min(node_health, 1.0 - impact.severity)
                    inflows[node_id] = node.replenishment_rate * node_health
                else:
                    # Inflow is the sum of shipments that departed suppliers (lead_time_days) ago,
                    # weighted by the dependency ratio.
                    total_inflow = 0.0
                    for source_id, dep_ratio, lead_time in inbound_links:
                        departed_day = day - lead_time
                        departed_qty = outflow_history[source_id].get(departed_day, current_nodes[source_id].daily_consumption)
                        total_inflow += departed_qty * dep_ratio
                    inflows[node_id] = total_inflow

            # Step 3.3: Update inventory balances and compute new health / risk states
            for node_id, node in current_nodes.items():
                inflow = inflows[node_id]
                
                # Inventory depletion formula
                # Inv(t) = Max(0, Inv(t-1) + Inflow(t) - Consumption)
                prev_inventory = node.inventory
                new_inventory = max(0.0, prev_inventory + inflow - node.daily_consumption)
                node.inventory = new_inventory
                
                # Determine health and risk based on safety stock levels
                if new_inventory >= node.safety_stock:
                    node_health = 1.0
                    node_risk = 0.0
                elif new_inventory > 0.0:
                    # Partial health drop if below safety stock
                    node_health = 0.5 + 0.5 * (new_inventory / node.safety_stock)
                    node_risk = 1.0 - node_health
                else:
                    # Inventory is empty: node is starved of material
                    node_health = 0.0
                    node_risk = 1.0

                # Cap health if this is the directly disrupted event target
                if node_id in affected_nodes_map and event_active:
                    impact = affected_nodes_map[node_id]
                    node_health = min(node_health, 1.0 - impact.severity)
                    node_risk = max(node_risk, impact.severity)
                
                node.health = node_health
                node.risk_score = node_risk
                
                # Calculate active outflow capacity on this day
                # Unhealthy nodes produce less
                effective_outflow = node.daily_consumption * node_health
                outflow_history[node_id][day] = effective_outflow
                
                # Store node state snapshot
                day_node_states[node_id] = NodeState(
                    health=node.health,
                    inventory=node.inventory,
                    risk_score=node.risk_score,
                    replenishment_rate=inflow
                )

            # Step 3.4: Compute Global Metrics for this day
            total_nodes = len(current_nodes)
            avg_health = sum(node.health for node in current_nodes.values()) / total_nodes
            resilience = avg_health * 100.0
            
            disrupted_count = sum(1 for node in current_nodes.values() if node.health < 1.0)
            
            # Identify delayed end products (nodes of type PRODUCT)
            day_delayed_products = 0.0
            day_operating_loss = 0.0
            
            for node_id, node in current_nodes.items():
                # Downtime base operational loss
                day_operating_loss += node.base_cost * (1.0 - node.health)
                
                if node.type == NodeType.PRODUCT:
                    # Delayed product units = daily consumption - actual shipped output
                    delayed_qty = max(0.0, node.daily_consumption - outflow_history[node_id][day])
                    day_delayed_products += delayed_qty
                    
                    # Add financial sales loss (unit price of product)
                    unit_price = node.metadata.get("unit_sale_price", 100.0)
                    day_operating_loss += delayed_qty * unit_price
            
            cumulative_financial_loss += day_operating_loss
            cumulative_delayed_products += day_delayed_products

            timeline.append(TemporalStep(
                day=day,
                metrics=StepMetrics(
                    resilience_score=round(resilience, 2),
                    financial_loss=round(cumulative_financial_loss, 2),
                    delayed_products=int(cumulative_delayed_products),
                    disrupted_nodes_count=disrupted_count
                ),
                node_states=day_node_states
            ))

        # 4. Compile and return full simulation run
        sim_run_id = f"sim-{uuid.uuid4().hex[:8]}"
        return SimulationRun(
            id=sim_run_id,
            event_id=event.id,
            timeline=timeline,
            created_at=datetime.now(timezone.utc)
        )

