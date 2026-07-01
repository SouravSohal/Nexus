import React, { useState } from "react";
import { useNexus } from "../../context/NexusContext";
import { Send, FileText, Clock, AlertCircle } from "lucide-react";

export const NewsBox: React.FC = () => {
  const { ingestNewsAlert, events, activeEvent, selectEvent, loading } = useNexus();
  const [newsText, setNewsText] = useState<string>("");

  const PRESETS = [
    {
      label: "Antwerp Port Strike (5d)",
      text: "BREAKING: Dockworkers at the Port of Antwerp-Bruges have launched a sudden five-day strike protesting terminal shifts. Operations at Europa Terminal are halted, blocking shipping container processing completely. Logistics managers warn of severe disruptions to regional warehouse flows."
    },
    {
      label: "Kaohsiung Typhoon (3d)",
      text: "Logistics Alert: A Category 3 typhoon is making landfall near Kaohsiung. Port authorities have closed all container berths at the Port of Kaohsiung for at least 3 days to secure equipment and protect workers, stopping all shipping vessel loading."
    },
    {
      label: "Munich Hub Fire (7d)",
      text: "Emergency Update: A major fire broke out at the Munich Logistics Hub early this morning. The main warehouse suffered significant structure damage, halting all incoming parts receiving and outbound distribution. Operations will remain offline for the next 7 days while safety teams inspect the site."
    }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newsText.trim() || loading) return;
    ingestNewsAlert(newsText);
    setNewsText("");
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

  return (
    <div className="flex flex-col h-full gap-4">
      {/* News Ingestion Input Card */}
      <div className="glass-panel p-4 flex flex-col">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-textDefault mb-3 flex items-center gap-2">
          <FileText className="w-4 h-4 text-brand-primary" />
          Risk Event Ingestion
        </h2>
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <textarea
            value={newsText}
            onChange={(e) => setNewsText(e.target.value)}
            placeholder="Paste raw breaking news, transport bulletins, or weather alerts here..."
            className="w-full h-28 bg-background border border-border rounded-lg p-2.5 text-sm text-textDefault placeholder:text-textMuted/50 focus:outline-none focus:border-brand-primary/50 focus:ring-1 focus:ring-brand-primary/30 transition-all resize-none font-sans"
          />
          
          <button
            type="submit"
            disabled={!newsText.trim() || loading}
            className="w-full flex items-center justify-center gap-2 py-2 bg-brand-primary text-white font-semibold text-sm rounded-lg hover:bg-brand-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-glass"
          >
            {loading ? "Extracting Risk Elements..." : "Ingest & Analyze"}
            {!loading && <Send className="w-4 h-4" />}
          </button>
        </form>

        {/* Quick Presets */}
        <div className="mt-4">
          <span className="text-textMuted text-xxs font-semibold uppercase tracking-wider block mb-2">Preset Scenarios</span>
          <div className="flex flex-col gap-1.5">
            {PRESETS.map((p, idx) => (
              <button
                key={idx}
                disabled={loading}
                onClick={() => ingestNewsAlert(p.text)}
                className="w-full text-left py-1.5 px-2 bg-background border border-border/60 rounded text-xxs font-mono text-textMuted hover:text-textDefault hover:border-brand-primary/30 hover:bg-cardHover transition-all truncate disabled:opacity-50 disabled:cursor-not-allowed"
              >
                &gt; {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Historical Disruption Log */}
      <div className="glass-panel p-4 flex-1 flex flex-col min-h-0">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-textDefault mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand-primary" />
          Active Incident Log
        </h2>
        
        <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1">
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-28 border border-dashed border-border rounded-lg text-textMuted text-xs p-4 text-center">
              <AlertCircle className="w-5 h-5 text-textMuted/40 mb-1" />
              No incidents registered. Ingest a news alert above to simulate.
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
                    <span className={`px-1.5 py-0.5 text-xxs border rounded font-mono ${getStatusBadgeClass(evt.status)}`}>
                      {evt.status}
                    </span>
                  </div>
                  <span className="text-textMuted font-mono text-xxs truncate">{evt.location}</span>
                  <div className="flex justify-between items-center text-xxs text-textMuted font-mono">
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
  );
};
