import sys
import os
import traceback

# Append project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.api.dependencies import get_orchestrator, get_repository
from backend.app.core.config import settings

def run_multi_node_tests():
    print("============================================================")
    print("STARTING MULTI-NODE DISRUPTION PIPELINE VERIFICATION")
    print("============================================================")

    # 1. Retrieve the pre-wired singletons
    repo = get_repository()
    orchestrator = get_orchestrator()
    
    # Reset to baseline 33 nodes
    print("[1] Resetting network to baseline...")
    orchestrator.reset_system()
    
    # 2. Test Articles
    scenarios = [
        {
            "name": "Total Gateway Shutdown",
            "text": "DISASTER BULLETIN: A severe storm surge closes both the ports of Antwerp and Rotterdam, halting container handling and cutting off maritime shipping lines into Central Europe entirely for 5 days.",
            "expected_nodes": ["port-antwerp", "port-rotterdam"]
        },
        {
            "name": "Two Ports Outage",
            "text": "ALERT: Typhoon storm warnings halt maritime container berths at Port of Kaohsiung and Port of Singapore simultaneously for 3 days.",
            "expected_nodes": ["port-kaohsiung", "port-singapore"]
        },
        {
            "name": "Port & Warehouse Outage",
            "text": "DISASTER REPORT: Industrial security actions suspend shipping container processing at Port of Antwerp and trigger power supply failures at Munich Regional Logistics Hub for 4 days.",
            "expected_nodes": ["port-antwerp", "warehouse-munich"]
        },
        {
            "name": "Multiple Logistics Hubs Outage",
            "text": "SYSTEM EMERGENCY: Severe cloud outages take inventory telemetry offline at Munich Regional Logistics Hub and Stuttgart Regional Logistics Hub for 5 days.",
            "expected_nodes": ["warehouse-munich", "warehouse-stuttgart"]
        },
        {
            "name": "Mixed Infrastructure Outage",
            "text": "CRITICAL WARNING: Power grid fluctuations disrupt container movement at Port of Kaohsiung and halt precision fabrication at Dresden Advanced Operations Center for 3 days.",
            "expected_nodes": ["port-kaohsiung", "factory-wafer-de"]
        }
    ]
    
    for idx, sc in enumerate(scenarios):
        print(f"\n--- Testing Scenario {idx+1}: {sc['name']} ---")
        print(f"Ingesting text: '{sc['text']}'")
        
        # Ingest
        event = orchestrator.ingest_news_alert(sc["text"])
        print(f"Successfully created RiskEvent: '{event.title}' (ID: {event.id})")
        print("Extracted affected nodes:")
        for node_impact in event.affected_nodes:
            print(f"  - Node ID: {node_impact.node_id}, Severity: {node_impact.severity}, Disruption: {node_impact.disruption_type}")
            
        # Verify nodes matches
        extracted_ids = [n.node_id for n in event.affected_nodes]
        for expected in sc["expected_nodes"]:
            assert expected in extracted_ids, f"Expected {expected} to be in extracted nodes list: {extracted_ids}"
            
        # Retrieve simulation run (triggered automatically by synchronous event bus)
        sim_run = repo.get_latest_simulation_run_by_event(event.id)
        assert sim_run is not None, "SimulationRun should be compiled and saved automatically"
        print(f"SimulationRun: {sim_run.id} compiled successfully with {len(sim_run.timeline)} daily steps.")
        
        # Verify both target nodes health are degraded on Day 0
        day_0_states = sim_run.timeline[0].node_states
        for expected in sc["expected_nodes"]:
            node_state = day_0_states.get(expected)
            assert node_state is not None, f"Node state for {expected} should exist in Day 0 timeline step"
            print(f"  * Target Node [{expected}] Day 0 Health: {node_state.health * 100:.0f}%, Risk Score: {node_state.risk_score * 100:.0f}%")
            assert node_state.health < 1.0, f"Expected target node {expected} health to be degraded on Day 0"
            
        # Retrieve or compute decision recommendation manually to see if any exception is raised
        try:
            rec_bundle = orchestrator.get_decision_recommendations(event.id)
            assert rec_bundle is not None, "Mitigation recommendations should be compiled"
            print(f"Decision recommendations compiled: {len(rec_bundle.options)} playbooks ranked.")
            print(f"  * Recommended Playbook: {rec_bundle.options[0].title} (Utility: {rec_bundle.options[0].calculated_score})")
            print(f"  * Earliest stockout forecast day: Day {rec_bundle.do_nothing_impact.earliest_stockout_day}")
        except Exception as e:
            print("ERROR generating recommendations:")
            traceback.print_exc()
            sys.exit(1)
        
    print("\n============================================================")
    print("ALL MULTI-NODE DISRUPTION PIPELINE TESTS PASSED SUCCESSFULLY!")
    print("============================================================")

if __name__ == "__main__":
    run_multi_node_tests()
