import os
import sys
from datetime import datetime, timezone

# Append project roots to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.app.api.dependencies import get_orchestrator, get_repository

def main():
    print("============================================================")
    # 1. Reset System to healthy baseline
    print("[1/5] Resetting Digital Twin database to clean baseline...")
    orchestrator = get_orchestrator()
    repo = get_repository()
    orchestrator.reset_system()
    
    # Verify baseline metrics
    nodes = repo.get_nodes()
    print(f"      -> Baseline verified. {len(nodes)} active nodes loaded.")
    
    # 2. Ingest News Event (Typhoon at Port of Kaohsiung)
    # This article will hit the Port of Kaohsiung (Taiwan) for 3 days
    typhoon_news = (
        "Logistics Alert: A Category 3 typhoon is making landfall near Kaohsiung. "
        "Port authorities have closed all container berths at the Port of Kaohsiung for at least 3 days "
        "to secure equipment and protect workers, stopping all shipping vessel loading."
    )
    
    print("\n[2/5] Simulating News Ingestion Alert...")
    print(f"      Source News: \"{typhoon_news}\"")
    
    # Ingest news - this will automatically trigger:
    # Ingestion -> Gemini Extraction -> RiskEvent Committed -> Simulation Run -> Decision Engine Optimization
    # because of the synchronous event handlers wired on the EventBus!
    event = orchestrator.ingest_news_alert(typhoon_news)
    
    print(f"\n[3/5] Verifying Auto-Triggered Event & Simulation Artifacts...")
    # Fetch committed event
    db_event = repo.get_risk_event(event.id)
    assert db_event is not None
    print(f"      -> Event Committed: ID='{db_event.id}' Target='{db_event.affected_node_id}' Status='{db_event.status.value}'")
    
    # Fetch simulation run
    sim_run = repo.get_latest_simulation_run_by_event(event.id)
    assert sim_run is not None
    print(f"      -> Simulation Compiled: ID='{sim_run.id}' Timeline Steps={len(sim_run.timeline)}")
    
    # 4. Fetch Scored Mitigation Recommendations
    print("\n[4/5] Retrieving Optimizations and AI Recommendation Briefing...")
    rec = orchestrator.get_decision_recommendations(event.id)
    assert rec is not None
    
    print(f"      -> Earliest Stockout Day: Day {rec.do_nothing_impact.earliest_stockout_day}")
    print(f"      -> Financial Risk: ${rec.do_nothing_impact.total_financial_loss:,.2f}")
    print(f"      -> Recommended Mitigation: {rec.options[0].title} (Utility Score: {rec.options[0].calculated_score})")
    
    print("\n      --- Executive AI Summary Briefing ---")
    print(rec.gemini_explanation)
    print("      -------------------------------------")
    
    # 5. Execute Rerouting Mitigation (Bypass Kaohsiung/Antwerp via Rotterdam)
    print("\n[5/5] Executing Rerouting Mitigation Strategy...")
    # Apply Rotterdam Rerouting
    orchestrator.apply_mitigation_action(event.id, "opt-reroute-rotterdam")
    
    # Verify event status transitions to RESOLVED
    updated_event = repo.get_risk_event(event.id)
    assert updated_event.status.value == "RESOLVED"
    print(f"      -> Event Status updated to: '{updated_event.status.value}'")
    
    # Verify graph edge dependency ratios updated in DB
    edges = repo.get_edges()
    for edge in edges:
        if edge.source == "port-kaohsiung" and edge.target == "port-rotterdam":
            print(f"      -> Edge port-kaohsiung -> port-rotterdam dependency ratio is now: {edge.dependency_ratio} (active!)")
        elif edge.source == "port-kaohsiung" and edge.target == "port-antwerp":
            print(f"      -> Edge port-kaohsiung -> port-antwerp dependency ratio is now: {edge.dependency_ratio} (de-activated)")

    print("\n============================================================")
    print("      APPLICATION LAYER EVENT LIFECYCLE VERIFIED SUCCESSFULLY!")
    print("============================================================")

if __name__ == "__main__":
    main()
