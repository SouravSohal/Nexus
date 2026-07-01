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
    
    # Ensure it's not in mock mode for this test
    if client.mock_active:
        print("ERROR: Gemini API key is missing. Set GEMINI_API_KEY to test the live API.")
        return
        
    sample_news = (
        "BREAKING: Dockworkers at the Port of Antwerp-Bruges have launched a sudden five-day strike "
        "protesting terminal shifts. Operations at Europa Terminal are halted, blocking shipping container processing "
        "completely. Logistics managers warn of severe disruptions to regional warehouse flows."
    )
    
    print("\n--- Sending Article to Gemini 2.5 (Structured Schema Mode) ---")
    print(f"Article: \"{sample_news}\"")
    
    try:
        # We invoke the extraction method
        extracted_dict = client.extract_risk_event_from_text(sample_news, nodes_list)
        
        print("\nStructured JSON Returned by Gemini:")
        print("=" * 60)
        print(json.dumps(extracted_dict, indent=2))
        print("=" * 60)
        
    except Exception as e:
        print(f"Extraction failed: {str(e)}")

if __name__ == "__main__":
    main()
