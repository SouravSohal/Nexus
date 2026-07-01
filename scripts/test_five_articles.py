import os
import sys
import json
from datetime import datetime, timezone

# Append project roots to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.app.infrastructure.db.sqlite_repo import SQLiteRepository
from backend.app.infrastructure.external.gemini_client import GeminiClient

def main():
    db_path = os.path.join(project_root, "backend", "nexus.db")
    repo = SQLiteRepository(db_path)
    nodes = repo.get_nodes()
    
    # Format nodes context to pass to Gemini
    nodes_list = [
        {
            "id": node.id,
            "name": node.name,
            "type": node.type.value,
            "location": node.location
        }
        for node in nodes
    ]
    
    # Instantiate live Gemini client
    print("Initializing live Gemini Client...")
    client = GeminiClient()
    
    if client.mock_active:
        print("ERROR: Gemini API key is missing. Set GEMINI_API_KEY to test the live API.")
        return

    # Five sample news articles representing different tiers of the supply chain
    articles = [
        {
            "num": 1,
            "tier": "Port Disruption (Europe)",
            "text": "BREAKING: Dockworkers at the Port of Antwerp-Bruges have launched a sudden five-day strike protesting terminal shifts. Operations at Europa Terminal are halted, blocking shipping container processing completely. Logistics managers warn of severe disruptions to regional warehouse flows."
        },
        {
            "num": 2,
            "tier": "Port Disruption (Asia)",
            "text": "Logistics Alert: A Category 3 typhoon is making landfall near Kaohsiung. Port authorities have closed all container berths at the Port of Kaohsiung for at least 3 days to secure equipment and protect workers, stopping all shipping vessel loading."
        },
        {
            "num": 3,
            "tier": "Warehousing Disruption",
            "text": "A major fire broke out at the Munich Logistics Hub early this morning. The main warehouse suffered significant structure damage, halting all incoming parts receiving and outbound distribution. Operations will remain offline for the next 7 days while safety teams inspect the site."
        },
        {
            "num": 4,
            "tier": "Supplier Tier-2 Disruption",
            "text": "Industrial Incident: A regional power grid failure has blacked out key parks in Hsinchu. Silicon production at Silicon Valley Taiwan Ltd is completely halted. Engineers estimate operations will be offline for at least 2 days to repair substations."
        },
        {
            "num": 5,
            "tier": "Distribution Center Disruption",
            "text": "Cyber Security Alert: Euro-DC Frankfurt, the major regional distribution center, has taken all cargo-tracking systems offline following a ransomware attack. Shipping dispatch and container loading are frozen for 4 days during system recovery."
        }
    ]
    
    print("\n--- Starting Extraction Test for 5 Distinct Articles ---")
    
    for article in articles:
        print(f"\n============================================================")
        print(f"ARTICLE #{article['num']} | Tier: {article['tier']}")
        print(f"============================================================")
        print(f"News Source: \"{article['text']}\"\n")
        
        try:
            extracted = client.extract_risk_event_from_text(article['text'], nodes_list)
            print("Gemini Structured Output JSON:")
            print(json.dumps(extracted, indent=2))
        except Exception as e:
            print(f"Extraction failed for article {article['num']}: {str(e)}")

if __name__ == "__main__":
    main()
