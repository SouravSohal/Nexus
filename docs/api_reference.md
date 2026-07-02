# REST API Reference

NEXUS exposes a clean REST API interface built on FastAPI. 

---

## 1. Network Core Endpoints

### 1.1 Get Active Network Graph
-   **Endpoint:** `GET /api/network/`
-   **Purpose:** Retrieves the current state of all nodes and edges in the active Digital Twin topology.
-   **Request Payload:** None
-   **Response (200 OK):**
    ```json
    {
      "nodes": [
        {
          "id": "port-antwerp",
          "name": "Port of Antwerp Emergency Gateway",
          "type": "PORT",
          "location": "Antwerp, Belgium",
          "latitude": 51.2204,
          "longitude": 4.4003,
          "base_cost": 50000.0,
          "capacity": 1000.0,
          "health": 1.0,
          "risk_score": 0.0,
          "inventory": 300.0,
          "safety_stock": 200.0,
          "daily_consumption": 100.0,
          "replenishment_rate": 100.0,
          "metadata": {}
        }
      ],
      "edges": [
        {
          "source": "port-kaohsiung",
          "target": "port-antwerp",
          "type": "TRANSPORT",
          "dependency_ratio": 0.6,
          "lead_time_days": 5,
          "transport_mode": "ocean"
        }
      ]
    }
    ```
-   **Errors:**
    -   `500 Internal Server Error`: Database query failure.

### 1.2 Reset System Topology
-   **Endpoint:** `POST /api/network/reset`
-   **Purpose:** Re-seeds the active database to the baseline healthy 33-node grid.
-   **Request Payload:** None
-   **Response (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Digital Twin reset to baseline healthy state."
    }
    ```

---

## 2. Risk Event Endpoints

### 2.1 Ingest Unstructured News Alert
-   **Endpoint:** `POST /api/events/`
-   **Purpose:** Submits an unstructured intelligence bulletin to the AI extraction orchestrator.
-   **Request Body:**
    ```json
    {
      "news_text": "ALERT: Typhoon storm warnings halt container berths at Port of Kaohsiung and Port of Singapore for 3 days."
    }
    ```
-   **Response (201 Created):**
    ```json
    {
      "id": "evt-7f9a2b1c",
      "title": "Dual East-Asia Maritime Disruptions",
      "description": "Severe weather alerts disrupt logistics berths at Port of Kaohsiung and Port of Singapore.",
      "location": "East Asia",
      "affected_node_id": "port-kaohsiung",
      "severity": 0.9,
      "duration_days": 3,
      "confidence_score": 0.95,
      "status": "COMMITTED",
      "created_at": "2026-07-02T09:14:00Z",
      "affected_nodes": [
        {
          "node_id": "port-kaohsiung",
          "severity": 0.9,
          "confidence": 0.95,
          "disruption_type": "weather_shutdown"
        },
        {
          "node_id": "port-singapore",
          "severity": 0.85,
          "confidence": 0.92,
          "disruption_type": "congestion"
        }
      ]
    }
    ```
-   **Errors:**
    -   `422 Unprocessable Entity`: Input validation error (e.g., missing text).
    -   `500 Internal Server Error`: AI client extraction failure.

### 2.2 Get Active Risk Events
-   **Endpoint:** `GET /api/events/`
-   **Purpose:** Lists all active and historically committed risk events.
-   **Response (200 OK):** List of `EventResponse` objects.

### 2.3 Manually Trigger Simulation Run
-   **Endpoint:** `POST /api/events/{event_id}/simulate`
-   **Purpose:** Executes a 10-day simulation run for a committed event.
-   **Response (200 OK):**
    ```json
    {
      "id": "sim-a2f9b8c0",
      "event_id": "evt-7f9a2b1c",
      "timeline": [
        {
          "day": 0,
          "metrics": {
            "resilience_score": 95.0,
            "financial_loss": 50000.0,
            "delayed_products": 0,
            "disrupted_nodes_count": 2
          },
          "node_states": {
            "port-kaohsiung": {
              "health": 0.1,
              "inventory": 400.0,
              "risk_score": 0.9,
              "replenishment_rate": 100.0
            }
          }
        }
      ],
      "created_at": "2026-07-02T09:14:05Z"
    }
    ```
-   **Errors:**
    -   `404 Not Found`: Event ID does not exist.

### 2.4 Get Simulation Impact Timeline
-   **Endpoint:** `GET /api/events/{event_id}/impact`
-   **Purpose:** Retrieves the pre-calculated daily metrics for timeline scrubbing.
-   **Response (200 OK):** `SimulationRunResponse` structure.

---

## 3. Decision & Mitigation Endpoints

### 3.1 Get Mitigation Recommendations
-   **Endpoint:** `GET /api/events/{event_id}/recommendations`
-   **Purpose:** Retrieves the ranked mitigation alternatives and LLM trade-off executive briefing.
-   **Response (200 OK):**
    ```json
    {
      "id": "rec-f9b8c0a2",
      "event_id": "evt-7f9a2b1c",
      "do_nothing_impact": {
        "earliest_stockout_day": 10,
        "total_financial_loss": 67500.0,
        "delayed_products_count": 0
      },
      "options": [
        {
          "option_id": "opt-backup-supplier",
          "title": "Switch to Backup European Supplier",
          "description": "Source raw parts from backup France supplier.",
          "cost_impact": 95000.0,
          "lead_time_surcharge_days": -5,
          "feasibility_score": 0.8,
          "calculated_score": 0.69,
          "is_recommended": true
        }
      ],
      "composite_confidence": {
        "extraction": 0.95,
        "simulation": 0.9,
        "optimization": 0.8,
        "overall": 0.68
      },
      "gemini_explanation": "### Executive Recommendation...",
      "created_at": "2026-07-02T09:14:10Z"
    }
    ```

### 3.2 Apply Mitigation Action
-   **Endpoint:** `POST /api/events/{event_id}/mitigate`
-   **Purpose:** Authorizes a playbook, executing network edge/node parameter shifts directly in the DB.
-   **Request Body:**
    ```json
    {
      "option_id": "opt-reroute-rotterdam"
    }
    ```
-   **Response (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Mitigation opt-reroute-rotterdam applied successfully."
    }
    ```

---

## 4. Ask NEXUS Assistant

### 4.1 Query Network Assistant
-   **Endpoint:** `POST /api/events/system/ask`
-   **Purpose:** Submits a natural language resilience query.
-   **Request Body:**
    ```json
    {
      "question": "What is the overall stock status of the Munich hub?"
    }
    ```
-   **Response (200 OK):**
    ```json
    {
      "answer": "The Munich Regional Logistics Hub has a stock level of 160 units, which is above safety stock limits. Overall resilience is stable at 100%."
    }
    ```
