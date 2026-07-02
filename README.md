# NEXUS: Decision Intelligence Platform for Critical Infrastructure & Community Resilience

NEXUS is a domain-agnostic Decision Intelligence Platform designed to monitor, simulate, and mitigate cascading disruptions across complex critical infrastructure networks. By combining a graph-driven Digital Twin, a discrete-day temporal simulation engine, and an AI Provider resilience layer with automatic local failover, NEXUS translates unstructured intelligence reports (e.g., weather dispatches, logistics logs, citizen reports) into actionable mitigation playbooks.

---

## 1. Executive Summary
Critical infrastructure networks (smart cities, power grids, healthcare logistics, emergency services) are highly interdependent. A single local failure can propagate downstream, starving dependent community services of resources. NEXUS ingests unstructured dispatches, extracts multi-asset impact scopes, runs high-fidelity simulations to forecast safety stock depletion timelines, and ranks optimal mitigation strategies (e.g., rerouting cargo, switching to backup regional operation centers) using an algebraic utility model.

---

## 2. Problem Statement
Critical infrastructure management relies on fragmented, legacy monitoring tools that operate in silos. When a crisis occurs (e.g., weather disaster, grid failure):
1.  **Delayed Ingestion:** Information is trapped in unstructured text formats (news alerts, agency reports).
2.  **Invisible Cascades:** Operators cannot trace how local failures cascade downstream over time.
3.  **Ad-Hoc Decision Making:** Mitigation plans are selected based on intuition rather than quantitative trade-off analysis.

---

## 3. Solution Overview
NEXUS solves this by integrating:
-   **Unstructured Ingest:** Natural language processing parses reports into structured multi-node risk events.
-   **Digital Twin & Simulation:** A discrete-day temporal engine propagates resource outflows, tracking safety stocks and daily operations.
-   **Decision & Optimization:** Evaluates candidate playbooks against costs, lead times, and feasibility using a multi-criteria utility score.
-   **Resilient AI Layer:** Employs a provider-agnostic client that falls back from Google Gemini to a local Ollama Mistral node or a local mock fail-safe during cloud outages.

---

## 4. Key Features
-   **Multi-Node Disruption Extraction:** Ingests and maps news reports that affect multiple infrastructure assets simultaneously.
-   **33-Node Demonstration Network:** Represents an international gateway pipeline feeding municipal services in Munich (Hospitals, Clean Water, Energy Grid, Metro Transit, and Emergency Disaster Relief).
-   **Interactive Timeline Playback:** Visualizes step-by-step downstream stockout depletion on the React Flow topology canvas.
-   **Natural Language Assistant:** Allows operators to query current network metrics and receive localized mitigation summaries.
-   **Automatic Local AI Fallback:** Guarantees platform availability in disconnected or denied environments.

---

## 5. Technology Stack
-   **Backend:** FastAPI, Python, SQLite, NetworkX, Pydantic.
-   **Frontend:** React, TypeScript, React Flow, Vite, Vanilla CSS.
-   **AI Engines:** Google Gemini SDK, Ollama API, Local Mock Parser.

---

## 6. Architecture Overview
NEXUS is built using Clean Architecture principles, separating domain logic from external infrastructures:

```text
                  +-----------------------------------+
                  |            API Layer              |
                  |     (FastAPI, REST Endpoints)     |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |         Application Layer         |
                  |     (Orchestrator, Event Bus)     |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |            Domain Layer           |
                  |   (Simulation, Decision Engines)  |
                  +-----------------+-----------------+
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v                                                     v
+--------+--------+                                   +--------+--------+
|  Infrastructure |                                   |  Infrastructure |
|  AI Provider    |                                   |  SQLite Repo    |
|  (Orchestrator) |                                   |  (Event Store)  |
+-----------------+                                   +-----------------+
```

---

## 7. Screenshots
*(Refer to docs/screenshots/ for interface visuals)*
-   **Digital Twin Canvas:** Dynamic high-density topology indicating node health and live capacity.
-   **Ingestion Panel:** Multi-source input log console.
-   **Decision Console:** Utility score tables ranking playbooks.

---

## 8. Installation Guide

### Prerequisites
-   Python 3.11+
-   Node.js 18+
-   Ollama (optional, for local fallback)

### Step 1: Environment Variables
Create a `.env` file inside the `backend` directory:
```bash
# backend/.env
PRIMARY_AI_PROVIDER=gemini
FALLBACK_AI_PROVIDER=ollama
GEMINI_API_KEY=your_gemini_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
DB_PATH=backend/nexus.db
```

### Step 2: Backend Setup
```bash
# Navigate to workspace
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed the SQLite database with the 33-node network
python scripts/seed_db.py
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install
```

### Step 4: Ollama Setup (Local Fallback)
1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull the Mistral model:
   ```bash
   ollama pull mistral
   ```

---

## 9. Running the Application

### Start Backend Dev Server
```bash
cd backend
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```

### Start Frontend Dev Server
```bash
cd frontend
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 10. Running Tests
Run backend integration and unit tests:
```bash
# Execute local AI resilience failover unit tests
python scripts/test_ai_failover.py

# Execute API lifecycle integration tests
python scripts/test_api_flow.py

# Execute multi-node extraction and simulation tests
python scripts/test_multi_node.py
```

---

## 11. Folder Structure
```text
.
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI controllers & dependencies
│   │   ├── application/     # Application workflow & Event Bus
│   │   ├── domain/          # Core model boundaries & simulation engines
│   │   ├── infrastructure/  # DB SQLite repository & AI providers
│   │   └── models/          # API DTO schemas
│   ├── scripts/             # Seeding and validation scripts
│   └── requirements.txt
├── docs/                    # Public documentation suite
├── frontend/
│   ├── src/
│   │   ├── components/      # React Flow custom nodes & HUD widgets
│   │   ├── context/         # Global state managers
│   │   └── types/           # TypeScript interface models
│   └── package.json
└── README.md
```

---

## 12. Future Roadmap
-   **Prototype (Current):** 33-node network, multi-node storm/typhoon/grid disruption extraction, temporal simulation, fallback AI, React Flow HUD.
-   **Version 1:** Live REST sensor telemetry integrations, confidence-score propagation across edges, interactive node positioning save states.
-   **Version 2:** Streaming data integrations via Apache Kafka, probabilistic Monte Carlo disruption simulation modeling.
-   **Enterprise Edition:** Distributed graph scaling via cuGraph/RAPIDS, multi-tenant RBAC profiles, integration with BigQuery.

---

## 13. License
This project is licensed under the MIT License.
