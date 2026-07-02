import React, { useState, useMemo } from "react";
import { useNexus } from "../../context/NexusContext";
import { 
  Send, 
  FileText, 
  Clock, 
  AlertCircle, 
  MessageSquare, 
  Activity, 
  Sparkles, 
  HelpCircle,
  ShieldAlert,
  ArrowRight
} from "lucide-react";
import { getDescriptiveLabel } from "../GraphView/CustomNode";

export const NewsBox: React.FC = () => {
  const { 
    ingestNewsAlert, 
    events, 
    activeEvent, 
    selectEvent, 
    activeSimulation, 
    loading, 
    askQuestion 
  } = useNexus();

  // Tab State
  const [activeTab, setActiveTab] = useState<"ingest" | "ask" | "anomalies">("ingest");

  // Ingestion form state
  const [newsText, setNewsText] = useState<string>("");
  const [sourceType, setSourceType] = useState<string>("news");

  // AI Assistant state
  const [questionText, setQuestionText] = useState<string>("");
  const [assistantReply, setAssistantReply] = useState<string>("");
  const [assistantLoading, setAssistantLoading] = useState<boolean>(false);

  // Critical infrastructure-oriented presets
  const PRESETS = [
    {
      label: "Total Gateway Shutdown: Antwerp & Rotterdam (5d)",
      text: "DISASTER BULLETIN: A severe storm surge closes both the ports of Antwerp and Rotterdam, halting container handling and cutting off maritime shipping lines into Central Europe entirely for 5 days."
    },
    {
      label: "Dual Port Incident: Kaohsiung & Singapore (3d)",
      text: "ALERT: Typhoon storm warnings halt maritime container berths at Port of Kaohsiung and Pasir Panjang Terminal at the Port of Singapore simultaneously for 3 days. Strategic material transfers and emergency kit loading are suspended."
    },
    {
      label: "Port & Logistics Hub Outage: Antwerp & Munich (4d)",
      text: "DISASTER REPORT: Industrial security actions suspend shipping container processing at Port of Antwerp and trigger power supply failures at Munich Regional Logistics Hub for 4 days."
    },
    {
      label: "Multi-Hub Regional Storage: Munich & Stuttgart (5d)",
      text: "SYSTEM EMERGENCY: Severe cloud outages take inventory telemetry offline at Munich Regional Logistics Hub and Stuttgart Regional Logistics Hub for 5 days, halting distribution scheduling."
    },
    {
      label: "Transit & Sourcing Outage: Kaohsiung & Dresden (3d)",
      text: "CRITICAL WARNING: Power grid fluctuations disrupt container movement at Port of Kaohsiung and halt precision fabrication at Dresden Advanced Operations Center for 3 days."
    }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newsText.trim() || loading) return;
    ingestNewsAlert(newsText);
    setNewsText("");
  };

  const handleAsk = async (textToAsk: string) => {
    if (!textToAsk.trim() || assistantLoading) return;
    setAssistantLoading(true);
    setAssistantReply("");
    const reply = await askQuestion(textToAsk);
    setAssistantReply(reply);
    setAssistantLoading(false);
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "RESOLVED":
        return "bg-status-healthy/10 text-status-healthy border-status-healthy/20";
      case "COMMITTED":
        return "bg-brand-primary/10 text-brand-primary border-brand-primary/20";
      default:
        return "bg-status-gray/10 text-textMuted border-border";
    }
  };

  // Rule-based anomaly detection scanner over active simulation steps
  const anomalies = useMemo(() => {
    if (!activeSimulation || !activeSimulation.timeline) return [];

    const list: Array<{ day: number; type: "critical" | "warning"; text: string }> = [];
    
    // Scan timeline day-by-day
    activeSimulation.timeline.forEach((step, idx) => {
      Object.entries(step.node_states).forEach(([nodeId, state]) => {
        const nodeLabel = getDescriptiveLabel(nodeId);
        
        // 1. Health drop anomaly
        if (state.health === 0.0) {
          list.push({
            day: idx,
            type: "critical",
            text: `[D${idx}] [CRITICAL] Facility Shutdown: ${nodeLabel} health drops to 0% (berth/grid offline)`
          });
        } else if (state.health < 1.0) {
          list.push({
            day: idx,
            type: "warning",
            text: `[D${idx}] [WARNING] Infrastructure degradation: ${nodeLabel} degraded to ${(state.health * 100).toFixed(0)}%`
          });
        }

        // 2. Inventory starvation anomaly
        // Using safety stock thresholds (we hardcode typical limits based on seed data)
        const safetyLimit = nodeId.includes("warehouse") ? 80 : 40;
        if (state.inventory === 0 && !nodeId.includes("port") && !nodeId.includes("supplier")) {
          list.push({
            day: idx,
            type: "critical",
            text: `[D${idx}] [CRITICAL] Stockpile Depleted: ${nodeLabel} inventory completely depleted to 0.`
          });
        } else if (state.inventory < safetyLimit && !nodeId.includes("port") && !nodeId.includes("supplier")) {
          list.push({
            day: idx,
            type: "warning",
            text: `[D${idx}] [WARNING] Low Stockpile Alert: ${nodeLabel} stock drops below safety limit (${state.inventory.toFixed(0)} units).`
          });
        }
      });
    });

    // Sort anomalies chronologically
    return list.slice(0, 12);
  }, [activeSimulation]);

  return (
    <div className="flex flex-col h-full gap-4 font-mono select-none">
      
      {/* Sidebar Navigation Tabs */}
      <div className="flex border-b border-border/50 text-[10px] uppercase font-bold text-textMuted bg-card/25 rounded-t-lg p-0.5 select-none">
        <button
          onClick={() => setActiveTab("ingest")}
          className={`flex-1 py-1.5 rounded transition-all text-center flex items-center justify-center gap-1 ${
            activeTab === "ingest" 
              ? "bg-brand-primary/10 text-brand-primary border border-brand-primary/30 font-semibold" 
              : "hover:text-textDefault hover:bg-cardHover"
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Ingest</span>
        </button>
        <button
          onClick={() => setActiveTab("ask")}
          className={`flex-1 py-1.5 rounded transition-all text-center flex items-center justify-center gap-1 ${
            activeTab === "ask" 
              ? "bg-brand-primary/10 text-brand-primary border border-brand-primary/30 font-semibold" 
              : "hover:text-textDefault hover:bg-cardHover"
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Ask AI</span>
        </button>
        <button
          onClick={() => setActiveTab("anomalies")}
          className={`flex-1 py-1.5 rounded transition-all text-center flex items-center justify-center gap-1 ${
            activeTab === "anomalies" 
              ? "bg-brand-primary/10 text-brand-primary border border-brand-primary/30 font-semibold" 
              : "hover:text-textDefault hover:bg-cardHover"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Anomalies</span>
        </button>
      </div>

      {/* --- TAB 1: INGESTION CONSOLE --- */}
      {activeTab === "ingest" && (
        <div className="flex-1 flex flex-col gap-4 overflow-y-auto min-h-0 pr-1">
          <div className="glass-panel p-4 flex flex-col gap-2">
            <h2 className="text-xxs font-bold uppercase tracking-wider text-textDefault mb-1 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-brand-primary" />
              Resource Telemetry Ingest
            </h2>
            
            <form onSubmit={handleSubmit} className="flex flex-col gap-2.5">
              {/* Telemetry Source Dropdown */}
              <div className="flex flex-col gap-1">
                <span className="text-[9px] text-textMuted uppercase">Intelligence Feed Source</span>
                <select 
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="bg-background border border-border rounded p-1.5 text-xxs text-textDefault focus:outline-none focus:border-brand-primary/50 cursor-pointer"
                >
                  <option value="news">News Media Reports</option>
                  <option value="weather">Weather Warning Services</option>
                  <option value="gov">Emergency Agency Bulletins</option>
                  <option value="iot">IoT Telemetry Feed</option>
                  <option value="citizen">Citizen Dispatch Reports</option>
                  <option value="transit">Transit Operations Data</option>
                </select>
              </div>

              <textarea
                value={newsText}
                onChange={(e) => setNewsText(e.target.value)}
                placeholder="Paste emergency alerts, transport bulletins, or weather warning dispatches..."
                className="w-full h-24 bg-background border border-border rounded-lg p-2 text-xxs text-textDefault placeholder:text-textMuted/45 focus:outline-none focus:border-brand-primary/50 focus:ring-1 focus:ring-brand-primary/30 transition-all resize-none font-sans"
              />
              
              <button
                type="submit"
                disabled={!newsText.trim() || loading}
                className="w-full flex items-center justify-center gap-2 py-2 bg-brand-primary text-white font-semibold text-xs rounded-lg hover:bg-brand-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-glass"
              >
                {loading ? "Analyzing Ingest Data..." : "Ingest & Process Alert"}
                {!loading && <Send className="w-4 h-4" />}
              </button>
            </form>

            {/* Quick Presets */}
            <div className="mt-2.5 border-t border-border/30 pt-2.5">
              <span className="text-textMuted text-xxs font-semibold uppercase tracking-wider block mb-2">Simulate Critical Presets</span>
              <div className="flex flex-col gap-1.5">
                {PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    disabled={loading}
                    onClick={() => ingestNewsAlert(p.text)}
                    className="w-full text-left py-1.5 px-2 bg-background border border-border/60 rounded text-[9.5px] text-textMuted hover:text-textDefault hover:border-brand-primary/30 hover:bg-cardHover transition-all truncate disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    &gt; {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Active Incident Log */}
          <div className="glass-panel p-4 flex-1 flex flex-col min-h-0">
            <h2 className="text-xxs font-bold uppercase tracking-wider text-textDefault mb-3 flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-brand-primary" />
              Active Critical Incident Log
            </h2>
            
            <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1">
              {events.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-28 border border-dashed border-border rounded-lg text-textMuted text-xs p-4 text-center">
                  <AlertCircle className="w-5 h-5 text-textMuted/40 mb-1" />
                  No events active. Ingest an alert above to simulate.
                </div>
              ) : (
                events.map((evt) => {
                  const isActive = activeEvent?.id === evt.id;
                  return (
                    <div
                      key={evt.id}
                      onClick={() => selectEvent(evt.id)}
                      className={`border p-2.5 rounded-lg text-xs cursor-pointer flex flex-col gap-1.5 transition-all ${
                        isActive 
                          ? "bg-cardHover border-brand-primary shadow-[0_0_10px_rgba(59,130,246,0.1)]" 
                          : "bg-card/40 border-border hover:border-brand-primary/30 hover:bg-cardHover/60"
                      }`}
                    >
                      <div className="flex justify-between items-start gap-1">
                        <span className="font-semibold text-textDefault truncate">{evt.title}</span>
                        <span className={`px-1.5 py-0.5 text-xxs border rounded ${getStatusBadgeClass(evt.status)}`}>
                          {evt.status}
                        </span>
                      </div>
                      <span className="text-textMuted text-xxs truncate">{evt.location}</span>
                      <div className="flex justify-between items-center text-xxs text-textMuted">
                        <span>Severity: {(evt.severity * 100).toFixed(0)}%</span>
                        <span>Dur: {evt.duration_days} days</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 2: AI COGNITIVE ASSISTANT --- */}
      {activeTab === "ask" && (
        <div className="flex-1 flex flex-col gap-4 overflow-y-auto min-h-0 pr-1">
          <div className="glass-panel p-4 flex flex-col gap-3 flex-1 min-h-0">
            <h2 className="text-xxs font-bold uppercase tracking-wider text-textDefault flex items-center gap-1.5 select-none">
              <Sparkles className="w-4 h-4 text-brand-primary" />
              Ask NEXUS: Decision Assistant
            </h2>

            {/* Quick Queries */}
            <div className="flex flex-col gap-1 mt-1 select-none">
              <span className="text-[9px] text-textMuted uppercase mb-1">Quick Queries</span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  "Which facilities are currently most at risk?",
                  "Summarize the current situation.",
                  "What happens if this lasts another 5 days?",
                  "Which mitigation minimizes impact?"
                ].map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuestionText(q);
                      handleAsk(q);
                    }}
                    className="text-[9px] text-textMuted hover:text-textDefault bg-background border border-border/80 px-2 py-1 rounded-full hover:border-brand-primary/40 hover:bg-cardHover transition-all flex items-center gap-1 select-none text-left"
                  >
                    <ArrowRight className="w-2.5 h-2.5 text-brand-primary shrink-0" />
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Assistant Query Console Input */}
            <div className="flex flex-col gap-2 mt-2">
              <textarea
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                placeholder="Ask NEXUS a question (e.g., 'What is the stockpile status at Munich distribution center?')..."
                className="w-full h-16 bg-background border border-border rounded p-2 text-xxs text-textDefault placeholder:text-textMuted/45 focus:outline-none focus:border-brand-primary/50"
              />
              <button
                onClick={() => handleAsk(questionText)}
                disabled={!questionText.trim() || assistantLoading}
                className="w-full flex items-center justify-center gap-2 py-1.5 bg-brand-primary text-white font-semibold text-xxs rounded hover:bg-brand-primary/90 disabled:opacity-50 transition-all select-none"
              >
                {assistantLoading ? "Consulting AI Engine..." : "Submit Question"}
                {!assistantLoading && <Send className="w-3 h-3" />}
              </button>
            </div>

            {/* Assistant Response Box */}
            <div className="flex-1 flex flex-col border border-border/60 bg-background/50 rounded-lg p-3 overflow-y-auto select-none mt-2 relative">
              <span className="text-[9px] text-textMuted uppercase font-mono block mb-1 border-b border-border/30 pb-1">Response Output</span>
              {assistantLoading ? (
                <div className="flex items-center gap-2 text-textMuted text-xxs font-mono mt-2 select-none">
                  <span className="w-2 h-2 rounded-full bg-brand-primary animate-ping" />
                  <span>NEXUS Assistant is generating response...</span>
                </div>
              ) : assistantReply ? (
                <div className="text-xxs font-mono text-textDefault leading-relaxed select-text mt-1 whitespace-pre-wrap">
                  {assistantReply}
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center text-textMuted/55 text-xxs font-mono p-4 select-none">
                  <HelpCircle className="w-7 h-7 text-textMuted/30 mb-1.5" />
                  <span>Enter a question or select a preset query to consult the Decision Engine.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 3: COGNITIVE ANOMALY SCANNERS --- */}
      {activeTab === "anomalies" && (
        <div className="flex-1 flex flex-col gap-4 overflow-y-auto min-h-0 pr-1 select-none">
          <div className="glass-panel p-4 flex-1 flex flex-col min-h-0">
            <h2 className="text-xxs font-bold uppercase tracking-wider text-textDefault mb-3 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-brand-primary" />
              Cognitive Anomaly Scan
            </h2>

            <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1 font-mono text-xxs">
              {anomalies.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 border border-dashed border-border rounded-lg text-textMuted text-center p-4">
                  <ShieldAlert className="w-6 h-6 text-status-healthy/40 mb-1.5" />
                  <span className="text-status-healthy font-semibold">Corridor Integrity Clear</span>
                  <span className="text-[10px] mt-1 text-textMuted/70">
                    No facility health drops or stock depletion anomalies detected in the current active simulation timeline.
                  </span>
                </div>
              ) : (
                <div className="flex flex-col gap-2.5">
                  <div className="text-[9px] uppercase text-textMuted font-bold border-b border-border/30 pb-1.5">
                    Detected Telemetry Deviations:
                  </div>
                  {anomalies.map((anom, idx) => (
                    <div 
                      key={idx}
                      className={`p-2 rounded border border-border bg-card/25 flex flex-col gap-1 ${
                        anom.type === "critical" 
                          ? "border-status-alert/30 text-status-alert bg-status-alert/[0.01]" 
                          : "border-status-warning/30 text-status-warning bg-status-warning/[0.01]"
                      }`}
                    >
                      <span className="font-semibold leading-tight">{anom.text}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
