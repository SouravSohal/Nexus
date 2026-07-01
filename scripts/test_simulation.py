import os
import sys
from datetime import datetime, timezone

# Append project roots to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.app.infrastructure.db.sqlite_repo import SQLiteRepository
from backend.app.infrastructure.graph.networkx_engine import NetworkXGraphEngine
from backend.app.domain.services.simulation_engine import TemporalSimulationEngine
from backend.app.domain.models.event import RiskEvent, EventStatus

def main():
    db_path = os.path.join(project_root, "backend", "nexus.db")
    print(f"Reading database at: {db_path}")
    repo = SQLiteRepository(db_path)
    
    nodes = repo.get_nodes()
    edges = repo.get_edges()
    
    print(f"Loaded {len(nodes)} nodes and {len(edges)} edges.")
    
    # Initialize engines
    graph_engine = NetworkXGraphEngine()
    sim_engine = TemporalSimulationEngine(graph_engine)
    
    # Define Antwerp Port Worker Strike Event
    strike_event = RiskEvent(
        id="evt-antwerp-strike-2026",
        title="Port of Antwerp Worker Strike",
        description="Workers at Antwerp announce a 5-day walkout halting container shipments.",
        location="Antwerp, Belgium",
        affected_node_id="port-antwerp",
        severity=0.85,
        duration_days=5,
        confidence_score=0.95,
        status=EventStatus.COMMITTED,
        created_at=datetime.now(timezone.utc)
    )
    
    print("\n--- Starting Temporal Simulation (10 Days) ---")
    print(f"Disrupting Node: {strike_event.affected_node_id} (Severity: {strike_event.severity}, Duration: {strike_event.duration_days} days)")
    
    run = sim_engine.run_simulation(strike_event, nodes, edges, duration_days=10)
    
    print(f"Simulation execution successful. Simulation ID: {run.id}")
    print("\nTimeline Progress Summary:")
    print(f"{'Day':<4} | {'Resilience':<10} | {'Loss ($)':<12} | {'Delayed Pds':<12} | {'Antwerp Hlt':<12} | {'Munich Fac Hlt':<14} | {'Munich Inv':<10}")
    print("-" * 88)
    
    for step in run.timeline:
        day = step.day
        metrics = step.metrics
        antwerp_state = step.node_states["port-antwerp"]
        munich_state = step.node_states["factory-assembly"]
        munich_inv = step.node_states["warehouse-munich"]  # Inventory hub feeding Munich assembly
        
        print(f"Day {day:<2} | {metrics.resilience_score:<10.1f}% | ${metrics.financial_loss:<11,.2f} | {metrics.delayed_products:<12} | {antwerp_state.health:<12.2f} | {munich_state.health:<14.2f} | {munich_inv.inventory:<10.1f}")
        
    print("\n--- Simulation Analysis ---")
    first_stockout_day = next((step.day for step in run.timeline if step.node_states["warehouse-munich"].inventory == 0), None)
    if first_stockout_day is not None:
        print(f"[Starvation Alert] Munich Hub ran completely out of inventory on Day {first_stockout_day}.")
        
    first_shutdown_day = next((step.day for step in run.timeline if step.node_states["factory-assembly"].health == 0), None)
    if first_shutdown_day is not None:
        print(f"[Shutdown Alert] Munich Cognitive Electronics Factory shut down (health = 0.0) on Day {first_shutdown_day}.")

if __name__ == "__main__":
    main()
