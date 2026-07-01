import os
import sys

# Append project roots to sys.path to allow execution from the repository root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.app.infrastructure.db.sqlite_repo import SQLiteRepository

def main():
    db_dir = os.path.join(project_root, "backend")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "nexus.db")
    
    print(f"Initializing SQLite database at: {db_path}")
    repo = SQLiteRepository(db_path)
    
    print("Seeding database with baseline high-tech supply chain network...")
    repo.reset_network_to_baseline()
    
    # Verification
    nodes = repo.get_nodes()
    edges = repo.get_edges()
    
    print("Database seeding completed successfully.")
    print(f"Nodes loaded: {len(nodes)}")
    for node in nodes:
        print(f"  - [{node.type.value}] {node.id}: {node.name} (Inventory: {node.inventory})")
        
    print(f"Edges loaded: {len(edges)}")
    for edge in edges:
        print(f"  - {edge.source} --({edge.transport_mode}, lead: {edge.lead_time_days}d)--> {edge.target}")

if __name__ == "__main__":
    main()
