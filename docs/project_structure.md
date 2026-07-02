# Repository Project Structure

This document outlines the organization of backend packages and frontend modules across the NEXUS workspace.

---

## 1. Directory Tree Summary

```text
.
├── backend/
│   ├── app/
│   │   ├── api/             # REST Endpoints, routing, dependencies
│   │   ├── application/     # Application use-case orchestrators & Event Bus
│   │   ├── core/            # App config (FastAPI settings, logging configurations)
│   │   ├── domain/          # Core math layers: simulation & decision engines
│   │   ├── infrastructure/  # External adapters: SQLite DB repositories & AI provider clients
│   │   ├── models/          # API serialization schemas (Pydantic DTOs)
│   │   └── main.py          # FastAPI application entry point
│   ├── scripts/             # Seeding and testing helper scripts
│   ├── requirements.txt
│   └── nexus.db             # Local SQLite database file (generated)
├── docs/                    # Public documentation markdown suite
├── frontend/
│   ├── src/
│   │   ├── components/      # React functional UI views & custom canvas nodes
│   │   ├── context/         # React Context state managers (API queries & UI selections)
│   │   ├── styles/          # Vanilla CSS sheets (theme variables, layouts)
│   │   ├── types/           # TypeScript interface structures matching backend DTOs
│   │   ├── App.tsx          # Main React layout assembly
│   │   └── main.tsx         # Vite frontend client entry point
│   ├── package.json
│   └── vite.config.ts       # Vite project bundler configs
└── README.md
```

---

## 2. Backend Modules Reference

### 2.1 `backend/app/domain/`
This directory houses the core business boundaries:
-   **`models/network.py`:** Entities defining `Node`, `Edge`, and `NodeType`.
-   **`models/event.py`:** Transactional aggregate definition of `RiskEvent` and the `AffectedNodeImpact` child schema.
-   **`models/simulation.py`:** Models describing simulation run metrics, daily snap states, and overall timeline loops.
-   **`models/decision.py`:** Specifications of mitigation alternatives, do-nothing costs, and overall optimization scores.
-   **`services/simulation_engine.py`:** Temporal discrete-day simulation runner that calculates flows and resource allocations.
-   **`services/decision_engine.py`:** Algebraic utility ranker scoring playbooks against costs, lead times, and viability.

### 2.2 `backend/app/infrastructure/`
Contains external gateway adapters:
-   **`db/sqlite_repo.py`:** Concrete SQLite connection provider, table mapper, and persistence engine.
-   **`external/ai/providers.py`:** Implements `AIClient` interfaces for cloud APIs (Google Gemini) and local models (Ollama Mistral). Includes self-correction JSON repair logic.
-   **`external/ai/orchestrator.py`:** AI Orchestrator router handling sequential fallbacks (Gemini -> Ollama -> Mock).

### 2.3 `backend/app/application/`
Use-case orchestrators:
-   **`event_orchestrator.py`:** Central coordinator. Ingests dispatches, commits events, runs simulations, ranks mitigations, and applies parameter modifications.
-   **`event_bus.py`:** In-memory publisher-subscriber instance connecting workflows synchronously.

---

## 3. Frontend Modules Reference

### 3.1 `frontend/src/components/`
-   **`GraphView/GraphCanvas.tsx`:** Coordinates React Flow layout. Includes dynamic layout computation (`computeDataDrivenLayout`) and selected node detail HUD panels.
-   **`GraphView/CustomNode.tsx`:** Custom HTML node template rendering stock level progress bars, threshold bounds, and alert state highlights.
-   **`NewsInput/NewsBox.tsx`:** Combined view comprising alert ingestion textareas, preset scenario selectors, and the natural language assistant query boxes.
-   **`HUD/ControlBar.tsx`:** Simulation controls (Play/Pause, Scrubbing slider, Speed, Reset system).

### 3.2 `frontend/src/context/`
-   **`NexusContext.tsx`:** Core global state manager. Polls API coordinates, maintains active selections, handles ingestion posts, triggers simulations, and manages the active timeline playback day indices.
