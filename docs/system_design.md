# System Design & Lifecycle Specifications

This document outlines the lifecycles, event flows, and sequence diagrams of the NEXUS platform.

---

## 1. End-to-End Request Lifecycle

The diagram below traces a news bulletin from user submission to database update:

```mermaid
sequenceDiagram
    autonumber
    actor User as Operator Console
    participant API as FastAPI REST Controllers
    participant Orch as EventOrchestrator
    participant AI as AIOrchestrator
    participant DB as SQLiteRepository
    participant Bus as EventBus
    participant Sim as TemporalSimulationEngine
    participant Dec as DecisionEngine

    User->>API: POST /api/events (Ingest Raw News Text)
    API->>Orch: ingest_news_alert(news_text)
    Orch->>DB: get_nodes() (Fetch network list for context)
    DB-->>Orch: Return Nodes
    Orch->>AI: extract_risk_event_from_text(news_text, nodes)
    
    Note over AI: Falls back from Gemini to Ollama<br/>to Mock if auth/network errors occur
    
    AI-->>Orch: Return structured JSON (affected_nodes, severity, duration)
    Orch->>DB: create_risk_event(RiskEvent)
    Orch->>Bus: publish("RiskEventCommitted", RiskEvent)
    
    activate Bus
    Bus->>Orch: _on_event_committed(RiskEvent)
    Orch->>Sim: run_simulation(RiskEvent, nodes, edges)
    Sim-->>Orch: Return SimulationRun (10-day step timeline)
    Orch->>DB: create_simulation_run(SimulationRun)
    Orch->>Bus: publish("SimulationCompleted", SimulationRun)
    deactivate Bus

    activate Bus
    Bus->>Orch: _on_simulation_completed(SimulationRun)
    Orch->>Dec: evaluate_mitigation(RiskEvent, SimulationRun, nodes)
    Dec-->>Orch: Return RecommendationBundle (Ranked Playbooks)
    Orch->>AI: generate_executive_recommendation(RiskEvent, metrics, options)
    AI-->>Orch: Return markdown briefing
    Orch->>DB: create_recommendation(RecommendationBundle)
    deactivate Bus

    Orch-->>API: Return RiskEvent DTO
    API-->>User: Ingest Success response
```

---

## 2. Ingestion to Execution Data Flow

```mermaid
flowchart TD
    A[Unstructured News Ingestion] -->|AI Extraction| B(RiskEvent committed to DB)
    B -->|Event Bus Trigger| C[Discrete Day Simulation]
    C -->|Timeline Snapshots| D(Safety Stock & Stockout KPI Analysis)
    D -->|Algebraic Optimization| E[Playbooks Ranked & Scored]
    E -->|UI Display| F[Action Authorize Panel]
    F -->|Operator Approval| G[Mitigation Playbook Applied]
    G -->|Alter SQL Network State| H[Database Edge/Node Modification]
    H -->|System Reset / Re-run| I[Digital Twin Restored to Operational]
```

---

## 3. Detailed Component Lifecycles

### 3.1 AI Provider Failover Loop
The AI client utilizes a sequential try-catch retry sequence:
1.  **Stage 1: Google Gemini.** Attempts structured extraction using `gemini-2.5-flash` with response schema enforcement.
2.  **Stage 2: Local Ollama (Fallback).** If cloud keys are missing or rate limits occur, calls `localhost:11434/api/generate` with a Mistral model. If JSON output fails validation, launches an LLM repair prompt.
3.  **Stage 3: Mock Provider (Valve).** If Ollama is offline, matches key phrases inside the news text to return deterministic, high-fidelity mock extraction payloads.

### 3.2 Simulation Lifecycle
The temporal engine evaluates daily steps sequentially:
-   **Day 0:** Reads active baseline nodes and applies health reductions for directly disrupted targets listed in the active event's `affected_nodes`.
-   **Days 1–10:** Loops through each node, processing inflows from inbound paths based on lead times and updating local inventories. Downstream nodes with depleted safety stock see health drops, which automatically scale down their daily production outflows to downstream dependents on subsequent days.
-   **KPI Compile:** Aggregates overall system resilience, delayed unit numbers, and operating costs.
