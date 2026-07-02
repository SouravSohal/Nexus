# Hackathon Live Demo Walkthrough Script

This script outlines a structured, 3-to-5 minute live demonstration walkthrough of the NEXUS platform. It showcases the complete end-to-end event-to-mitigation decision intelligence pipeline.

---

## Part 1: Introduction & Problem Context (45 Seconds)
1.  **State the Problem:**
    "When a major disruption occurs—whether it is a natural disaster, a regional power grid failure, or a logistics blockade—operators of critical municipal infrastructure struggle to identify how local failures will cascade downstream. Information is locked in unstructured bulletins, and mitigation is often based on guesswork rather than quantitative modeling."
2.  **Introduce NEXUS:**
    "NEXUS is an AI-powered Decision Intelligence Platform for Critical Infrastructure & Community Resilience. It translates raw intelligence dispatches into active simulations, maps cascading supply-chain failures, and ranks optimal mitigation plans."
3.  **Show the Baseline:**
    Point to the dashboard. "Here is our Digital Twin network. It consists of 33 nodes and 30 connectivity channels representing raw material partners, international gateways, regional logistics hubs, operations centers, and community recipients in Munich—such as hospitals, transit, and water treatment grids. The system is currently healthy, showing a 100% resilience score."

---

## Part 2: Disruption Ingestion & AI Parsing (60 Seconds)
1.  **Select a Preset:**
    In the **Resource Telemetry Ingest** panel, select the preset: **Total Gateway Shutdown: Antwerp & Rotterdam (5d)**. 
    Explain: "A severe storm surge has shut down container handling at both the Port of Antwerp and Port of Rotterdam simultaneously for 5 days."
2.  **Process Ingestion:**
    Click **Ingest & Process Alert**.
    Explain: "Behind the scenes, the AI client extracts the structured parameters. If our primary cloud engine is unreachable, the system automatically falls back to local models or mock processors, ensuring zero downtime. Here, both ports have been extracted as active target locations with 100% severity."
3.  **Observe Visual Highlights:**
    Point to the map: "Notice that both the Port of Antwerp and Port of Rotterdam have immediately highlighted in red warning borders, indicating active shutdowns."

---

## Part 3: Simulation & Cascading Failure Tracking (60 Seconds)
1.  **Run Timeline Scrubbing:**
    Set the timeline slider to **Day 0** and play the simulation.
    Explain: "Initially, the system remains operational because regional storage centers have safety stock buffers. But watch what happens as we scrub forward to Day 3."
2.  **Demonstrate Cascade:**
    Scrub the timeline to **Day 3** and then **Day 6**.
    Explain: "On Day 3, the Munich Regional Logistics Hub safety stock depletes, dropping its health. By Day 6, the Munich Essential Operations Center runs out of inputs, causing a total shutdown. This cascade propagates downstream, starving the Munich Regional Hospital Network, Clean Water Treatment Authority, and Energy Grid Operations. Overall system resilience drops, and financial loss metrics update in real time."

---

## Part 4: Decision Support & Ask AI (60 Seconds)
1.  **Explain Playbook Rankings:**
    Scroll down to the **Mitigation Options** section.
    Explain: "Instead of operators guessing the best response, the NEXUS Decision Engine scores playbooks using costs, lead times, and viability. It recommends the Switch to Backup European Supplier because it bypasses international shipping routes entirely, restoring inflows within 24 hours."
2.  **Ask AI:**
    In the **Ask AI** console, type: *"What assets are currently affected?"*
    Explain: "Operators can query the network in plain English. The assistant reads the database state, noting that Antwerp and Rotterdam are closed, and safety stocks are depleting."

---

## Part 5: Mitigation Application & Resolution (45 Seconds)
1.  **Authorize Mitigation:**
    Click **Authorize** on the recommended playbook.
    Explain: "When we apply the mitigation, NEXUS modifies the active database parameters in real time, routing traffic away from the blocked ports to our alternative corridors."
2.  **Verify Restoration:**
    Run the simulation again. Note that the safety stock recovery begins immediately, health scores return to 100%, and the system is restored to a safe state.
3.  **Conclusion:**
    "NEXUS provides operators with the foresight needed to intercept cascading infrastructure failures, protecting communities and municipal services before the impact is felt on the ground. Thank you."
