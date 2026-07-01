# BUSINESS CONTEXT – NEXUS

## 1. Product Vision
NEXUS is a cognitive supply-chain twin designed to bridge the gap between real-world events and business operations. By converting unstructured news (e.g., strikes, extreme weather, geopolitics) into structured digital twin simulations, NEXUS calculates how disruption propagates across multi-tier supplier networks. It then executes algebraic optimizations to rank mitigation strategies, using Google Gemini to explain the trade-offs to executives in plain language.

---

## 2. Business Objectives
- **Reduce Mean Time to Identify (MTTI):** Shrink the window between a public event and understanding its supply chain impact from days to seconds.
- **Minimize Financial Loss:** Provide optimal rerouting and alternative supplier choices to prevent manufacturing assembly shutdowns.
- **Improve Decision Confidence:** Establish clear, quantifiable confidence metrics that combine LLM parser trust, graph simulation variance, and optimization feasibility.
- **Enable Multi-Scenario Playbook Replay:** Allow risk managers to store, retrieve, and compare "what-if" options.

---

## 3. User Personas & Journeys

### Persona A: Sarah – Global Risk & Resilience Manager
- **Needs:** Immediate awareness of global events affecting suppliers; clear visual indicator of which plants and products are in the blast radius.
- **Frustrations:** Receives thousands of news alerts daily but manually maps them to spreadsheets. Cannot easily prove the ROI of preemptive rerouting.
- **Journey:**
  1. Sarah logs into the NEXUS dashboard; sees a healthy green network.
  2. She receives an alert about an impending worker strike at the Port of Antwerp.
  3. She pastes the news article into NEXUS.
  4. The Event Processor parses the location (Antwerp), severity (85%), and duration (5 days).
  5. NEXUS highlights the Port node in red and propagates the disruption downstream.
  6. Sarah views the timeline to see that by **Day 5**, Factory Munich will run out of microchips, stopping assembly.
  7. The Decision Engine presents ranked alternatives.
  8. Sarah selects "Option A: Reroute to Port of Rotterdam," downloads the generated report, and triggers the ERP update.

### Persona B: Marcus – Chief Operations Officer (COO)
- **Needs:** High-level executive KPIs (financial risk, delayed product counts, supply chain resilience score).
- **Frustrations:** Technical risk analyses are too granular. Needs to see the cost-benefit trade-offs of mitigation plans immediately.
- **Journey:**
  1. Marcus receives a high-level briefing notification from NEXUS detailing the Antwerp strike.
  2. He opens the executive dashboard, viewing the visual summary of the $1.25M financial risk and the recommended Rotterdam redirection.
  3. He reviews the Gemini-generated explanation outlining the trade-offs: *Rotterdam adds $45,000 in logistics costs but prevents a $1.2M plant shutdown.*
  4. He signs off on the decision.

---

## 4. Key Performance Indicators (KPIs)

- **Supply Chain Resilience Score (0-100%):** A composite score reflecting graph connectivity, inventory levels relative to safety stocks, and supplier health.
- **Total Financial Risk ($):** Cumulative potential loss based on assembly line downtime, delayed product sales, and contract penalties.
- **Delayed Products Count:** Number of final products whose assembly is delayed due to component stockouts.
- **Time-to-Impact (Days):** The number of days before a disruption propagates and causes an active stockout at the assembly plant.
- **Decision Confidence Score (%):** Combined metric representing parser accuracy, simulation variance, and mitigation feasibility.

---

## 5. Demo Narrative (The Antwerp Strike)
To win the hackathon, the live demonstration follows this storyline:
1. **The Calm (Day 0):** The map shows the baseline state. All supply chain nodes (Suppliers, Ports, Warehouses, Factories) are green (100% health). Inventory charts show healthy safety stocks.
2. **The Disruption (The Port Strike):** The user pastes a real-world news excerpt: *"Port of Antwerp workers launch a five-day strike halting all shipping container processing."*
3. **The Cognitive Extraction:** The system processes the event. Gemini extracts the target (`Port of Antwerp`), severity (`0.85`), and duration (`5 days`). It stores the `RiskEvent` in the Event Store.
4. **The Propagation (Temporal Simulation):**
   - **Day 1:** Port health drops to 15%.
   - **Day 3:** Warehouse Antwerp runs low on inventory.
   - **Day 5:** Munich Assembly Plant experiences a critical stockout of electronic chips. Factory health drops to 20%. The UI map highlights Munich in red.
5. **The Decision Engine Optimization:** The Decision Engine evaluates alternative actions:
   - *Option 1: Reroute via Port of Rotterdam* (adds $45k, delays shipments by 2 days, preserves Munich assembly).
   - *Option 2: Air freight components* (adds $250k, 0 days delay, preserves Munich assembly).
   - *Option 3: Do nothing* (costs $1.25M in delayed orders, assembly down for 5 days).
6. **The LLM Recommendation:** Gemini synthesizes the optimization results, generating a text briefing comparing the options, highlighting Rotterdam as the most cost-effective solution with 92% confidence.
7. **Resolution:** The user selects "Apply Rotterdam Mitigation". The simulation state updates, the Munich Plant turns back to green, and the financial risk drops.

---

## 6. Competitive Positioning & Hackathon Judging Alignment
NEXUS stands out by moving beyond "AI wrappers" and "static dashboards":
- **Technical Complexity:** Merges NLP (Gemini structured extraction) with Graph Theory (downstream network propagation) and operations research (optimization algorithms).
- **GPU-Ready:** Demonstrates a path to handle millions of supply nodes using RAPIDS cuGraph.
- **Actionable Output:** Instead of just showing *why* something is broken, it calculates *exactly what to do* and *how much it will cost*.
- **Executive-Ready UI:** Framer Motion transitions, interactive timeline controls, and React Flow maps deliver high-end visual appeal.
