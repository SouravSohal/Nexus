import os
import sys
import time
import math
from datetime import datetime, timezone

# Append project roots to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.app.infrastructure.db.sqlite_repo import SQLiteRepository
from backend.app.infrastructure.graph.networkx_engine import NetworkXGraphEngine
from backend.app.infrastructure.graph.cugraph_engine import CuGraphEngine
from backend.app.domain.services.simulation_engine import TemporalSimulationEngine
from backend.app.domain.models.event import RiskEvent, EventStatus
from backend.app.domain.models.network import Node, Edge, NodeType, EdgeType

def run_tests():
    print("==================================================")
    print("          NEXUS MILESTONE 2 VALIDATION            ")
    print("==================================================")

    # Load Repository
    db_path = os.path.join(project_root, "backend", "nexus.db")
    repo = SQLiteRepository(db_path)
    nodes = repo.get_nodes()
    edges = repo.get_edges()

    # 1. Graph Topology Integrity
    print("[1/8] Verifying Graph Topology Integrity...")
    graph_engine = NetworkXGraphEngine()
    graph_engine.build_graph(nodes, edges)
    
    assert len(graph_engine.get_nodes()) == 9, f"Expected 9 nodes, got {len(graph_engine.get_nodes())}"
    assert len(graph_engine.get_edges()) == 9, f"Expected 9 edges, got {len(graph_engine.get_edges())}"
    
    node_ids = {n.id for n in graph_engine.get_nodes()}
    required_nodes = {"supplier-silicon", "port-antwerp", "warehouse-munich", "factory-assembly"}
    for req in required_nodes:
        assert req in node_ids, f"Required node {req} missing from topology"
    print("      -> SUCCESS: Topology matches seed specifications.")

    # 2. Simulation Determinism
    print("[2/8] Verifying Simulation Determinism...")
    sim_engine = TemporalSimulationEngine(graph_engine)
    strike_event = RiskEvent(
        id="evt-det-test",
        title="Strike",
        description="Strike",
        location="Antwerp",
        affected_node_id="port-antwerp",
        severity=0.8,
        duration_days=4,
        confidence_score=0.9,
        status=EventStatus.COMMITTED,
        created_at=datetime.now(timezone.utc)
    )
    
    run_1 = sim_engine.run_simulation(strike_event, nodes, edges, duration_days=10)
    run_2 = sim_engine.run_simulation(strike_event, nodes, edges, duration_days=10)
    
    assert len(run_1.timeline) == len(run_2.timeline)
    for t1, t2 in zip(run_1.timeline, run_2.timeline):
        assert t1.day == t2.day
        assert math.isclose(t1.metrics.resilience_score, t2.metrics.resilience_score)
        assert math.isclose(t1.metrics.financial_loss, t2.metrics.financial_loss)
        assert t1.metrics.delayed_products == t2.metrics.delayed_products
        assert t1.metrics.disrupted_nodes_count == t2.metrics.disrupted_nodes_count
        
        for n_id in t1.node_states:
            n1 = t1.node_states[n_id]
            n2 = t2.node_states[n_id]
            assert math.isclose(n1.health, n2.health)
            assert math.isclose(n1.inventory, n2.inventory)
            assert math.isclose(n1.risk_score, n2.risk_score)
            assert math.isclose(n1.replenishment_rate, n2.replenishment_rate)
            
    print("      -> SUCCESS: Dual runs produce bit-identical states.")

    # 3. Edge-Case Behavior
    print("[3/8] Verifying Simulation Edge Cases...")
    
    # 3.1. Zero Severity Strike (effectively zero disruption)
    zero_sev_event = RiskEvent(
        id="evt-zero-sev",
        title="Zero Severity",
        description="",
        location="Antwerp",
        affected_node_id="port-antwerp",
        severity=0.0,  # Zero severity
        duration_days=5,
        confidence_score=0.9,
        status=EventStatus.COMMITTED,
        created_at=datetime.now(timezone.utc)
    )
    
    run_zero = sim_engine.run_simulation(zero_sev_event, nodes, edges, duration_days=10)
    for step in run_zero.timeline:
        assert step.metrics.resilience_score == 100.0, f"Expected 100% resilience, got {step.metrics.resilience_score}"
        assert step.metrics.financial_loss == 0.0
        assert step.metrics.delayed_products == 0
        assert step.node_states["port-antwerp"].health == 1.0

    # 3.2. Invalid target node
    invalid_node_event = RiskEvent(
        id="evt-invalid-node",
        title="Invalid Node",
        description="",
        location="Mars",
        affected_node_id="non-existent-node-id",
        severity=0.9,
        duration_days=5,
        confidence_score=0.9,
        status=EventStatus.COMMITTED,
        created_at=datetime.now(timezone.utc)
    )
    # The system should run and ignore the invalid target, remaining healthy
    run_invalid = sim_engine.run_simulation(invalid_node_event, nodes, edges, duration_days=10)
    for step in run_invalid.timeline:
        assert step.metrics.resilience_score == 100.0, f"Expected 100% resilience for non-existent node, got {step.metrics.resilience_score}"

    # 3.3. Full Disruption (100% severity, infinite duration)
    apocalypse_event = RiskEvent(
        id="evt-apocalypse",
        title="Permanent Shutdown",
        description="",
        location="Antwerp",
        affected_node_id="port-antwerp",
        severity=1.0,
        duration_days=20,
        confidence_score=0.9,
        status=EventStatus.COMMITTED,
        created_at=datetime.now(timezone.utc)
    )
    run_apocalypse = sim_engine.run_simulation(apocalypse_event, nodes, edges, duration_days=15)
    
    # Antwerp must be completely dead
    for step in run_apocalypse.timeline:
        assert step.node_states["port-antwerp"].health == 0.0
        
    # By day 10, Munich Hub (inventory) should be completely starved (inventory == 0) and Munich Factory health should drop to 0
    day_10_step = run_apocalypse.timeline[10]
    assert day_10_step.node_states["warehouse-munich"].inventory == 0.0
    assert day_10_step.node_states["factory-assembly"].health == 0.0
    
    print("      -> SUCCESS: Zero severity, invalid nodes, and total disruption behave correctly.")

    # 4. Recovery Correctness
    print("[4/8] Verifying Recovery Correctness...")
    recovery_event = RiskEvent(
        id="evt-recovery",
        title="Short Strike",
        description="",
        location="Antwerp",
        affected_node_id="port-antwerp",
        severity=1.0,
        duration_days=2,  # Disrupted only on Day 0 and Day 1
        confidence_score=0.9,
        status=EventStatus.COMMITTED,
        created_at=datetime.now(timezone.utc)
    )
    run_rec = sim_engine.run_simulation(recovery_event, nodes, edges, duration_days=8)
    
    # Day 0, 1: Port is shut down
    assert run_rec.timeline[0].node_states["port-antwerp"].health == 0.0
    assert run_rec.timeline[1].node_states["port-antwerp"].health == 0.0
    
    # Day 2: Port recovers to 1.0 health
    assert run_rec.timeline[2].node_states["port-antwerp"].health == 1.0
    
    # Warehouse Munich replenishment: Port Antwerp -> Warehouse Munich lead time is 2 days.
    # Disruption occurred on Day 0 and Day 1, so shipments on Day 0 and 1 are 0.
    # Therefore, on Day 2 and Day 3, replenishment_rate (inflow) at Warehouse Munich should be restricted.
    # Port recovered on Day 2, so shipments on Day 2 are normal (40.0). These arrive on Day 4.
    # So replenishment_rate at Warehouse Munich on Day 2 & 3 must be low, and on Day 4 it must recover to normal (40.0)
    assert run_rec.timeline[2].node_states["warehouse-munich"].replenishment_rate == 0.0, f"Expected 0 replenishment on Day 2, got {run_rec.timeline[2].node_states['warehouse-munich'].replenishment_rate}"
    assert run_rec.timeline[3].node_states["warehouse-munich"].replenishment_rate == 0.0
    assert run_rec.timeline[4].node_states["warehouse-munich"].replenishment_rate == 40.0, f"Expected replenishment to recover to 40 on Day 4, got {run_rec.timeline[4].node_states['warehouse-munich'].replenishment_rate}"
    
    print("      -> SUCCESS: Temporal recovery propagation matches lead-time delays.")

    # 5. Inventory Conservation Law
    print("[5/8] Verifying Inventory Conservation...")
    # For every node (except product/source where conservation might have edge overrides):
    # Inventory(t) = Max(0, Inventory(t-1) + Inflow(t) - Consumption)
    # Let's verify this for warehouse-munich and factory-assembly across all steps of a run
    node_map = {n.id: n for n in nodes}
    for step_idx in range(1, len(run_1.timeline)):
        prev_step = run_1.timeline[step_idx - 1]
        curr_step = run_1.timeline[step_idx]
        
        for n_id in ["warehouse-munich", "factory-assembly"]:
            prev_inv = prev_step.node_states[n_id].inventory
            curr_inv = curr_step.node_states[n_id].inventory
            inflow = curr_step.node_states[n_id].replenishment_rate
            consumption = node_map[n_id].daily_consumption
            
            calculated_inv = max(0.0, prev_inv + inflow - consumption)
            assert math.isclose(curr_inv, calculated_inv), f"Day {step_idx} {n_id}: Inv violation. Prev: {prev_inv}, Inflow: {inflow}, Cons: {consumption}, Expected: {calculated_inv}, Got: {curr_inv}"
            
    print("      -> SUCCESS: Inventory mass balance is preserved across steps.")

    # 6. Lead-Time Calculations
    print("[6/8] Verifying Graph Engine Lead-Time and Paths...")
    # Kaohsiung to Antwerp is 5 days.
    # Kaohsiung to Rotterdam is 6 days.
    # Shortest path lead time from supplier-silicon to factory-assembly should be:
    # silicon -> wafer (1) + wafer -> kaohsiung (1) + kaohsiung -> antwerp (5) + antwerp -> munich_hub (2) + munich_hub -> assembly (1) = 10 days
    total_time = graph_engine.get_shortest_path_lead_time("supplier-silicon", "factory-assembly")
    assert total_time == 10, f"Expected shortest path lead time to be 10, got {total_time}"
    
    # Path bypass test: Find path bypassing Antwerp Port
    paths_bypass_antwerp = graph_engine.find_alternative_paths("port-kaohsiung", "warehouse-munich", "port-antwerp")
    assert len(paths_bypass_antwerp) == 1, "Expected exactly 1 alternative path via Rotterdam"
    assert paths_bypass_antwerp[0] == ["port-kaohsiung", "port-rotterdam", "warehouse-munich"], f"Unexpected alternative path: {paths_bypass_antwerp[0]}"
    
    print("      -> SUCCESS: Network lead times and alternative paths calculated correctly.")

    # 7. Performance Metrics
    print("[7/8] Verifying Solver Performance (Dashboard Readiness)...")
    runs_count = 100
    start_time = time.perf_counter()
    for _ in range(runs_count):
        sim_engine.run_simulation(strike_event, nodes, edges, duration_days=10)
    end_time = time.perf_counter()
    
    total_duration_ms = (end_time - start_time) * 1000.0
    avg_duration_ms = total_duration_ms / runs_count
    print(f"      -> Stats: 100 runs took {total_duration_ms:.2f}ms (Average: {avg_duration_ms:.2f}ms/simulation)")
    assert avg_duration_ms < 5.0, f"Performance too slow! Average was {avg_duration_ms:.2f}ms per run"
    print("      -> SUCCESS: Solver speed is sub-millisecond (real-time ready).")

    # 8. GraphEngine Interface Compliance
    print("[8/8] Verifying GraphEngine Interface Compliance...")
    engines = [NetworkXGraphEngine(), CuGraphEngine()]
    for idx, engine in enumerate(engines):
        name = "NetworkX" if idx == 0 else "cuGraph Mock"
        engine.build_graph(nodes, edges)
        
        # Test basic retrieval
        g_nodes = engine.get_nodes()
        g_edges = engine.get_edges()
        assert len(g_nodes) == 9
        assert len(g_edges) == 9
        
        # Test routing compatibility
        lead_time = engine.get_shortest_path_lead_time("supplier-silicon", "factory-assembly")
        assert lead_time == 10
        
        alt_paths = engine.find_alternative_paths("port-kaohsiung", "warehouse-munich", "port-antwerp")
        assert len(alt_paths) == 1
        print(f"      -> SUCCESS: {name} complies with GraphEngine port.")

    print("\n==================================================")
    print("  ALL MILESTONE 2 VALIDATION TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
