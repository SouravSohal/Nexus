import React from "react";
import { useNexus } from "../../context/NexusContext";
import { BrainCircuit, Play, ShieldAlert, Sparkles, CheckCircle2 } from "lucide-react";

export const DecisionPanel: React.FC = () => {
  const { activeEvent, activeRecommendation, applyMitigationAction, loading } = useNexus();

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0
    }).format(val);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return "text-status-healthy";
    if (score >= 0.75) return "text-status-warning";
    return "text-status-alert";
  };

  if (!activeEvent) {
    return (
      <div className="glass-panel p-4 flex flex-col h-full items-center justify-center text-center text-textMuted/60">
        <BrainCircuit className="w-8 h-8 text-textMuted/30 mb-2 animate-pulse" />
        <span className="text-xs font-semibold uppercase tracking-wider mb-1">Decision Intelligence Pane</span>
        <span className="text-xxs font-mono max-w-[200px] leading-relaxed">
          No incident selected. Submit a news article or select an active alert to generate mitigation trade-offs.
        </span>
      </div>
    );
  }

  if (!activeRecommendation) {
    return (
      <div className="glass-panel p-4 flex flex-col h-full items-center justify-center text-center text-textMuted/60">
        <Sparkles className="w-6 h-6 text-brand-primary mb-2 animate-spin" />
        <span className="text-xs font-semibold uppercase tracking-wider mb-1">Evaluating Playbooks</span>
        <span className="text-xxs font-mono">
          Algebraic scoring & Gemini narrative compilation in progress...
        </span>
      </div>
    );
  }

  const { do_nothing_impact, options, composite_confidence, gemini_explanation } = activeRecommendation;

  return (
    <div className="flex flex-col h-full gap-4 overflow-y-auto pr-1">
      {/* 1. Do Nothing Impact Card */}
      <div className="border border-status-alert/30 bg-status-alert/5 p-3 rounded-lg flex flex-col gap-2 shadow-[0_0_10px_rgba(239,68,68,0.03)]">
        <h3 className="text-xxs font-bold uppercase tracking-wider text-status-alert flex items-center gap-1.5">
          <ShieldAlert className="w-4.5 h-4.5" />
          Do Nothing Risk Forecast
        </h3>
        <div className="grid grid-cols-2 gap-2 text-xxs font-mono text-textMuted mt-1">
          <div className="flex flex-col border-r border-border/40">
            <span>Earliest Stockout:</span>
            <span className="text-sm font-bold text-textDefault mt-0.5">Day {do_nothing_impact.earliest_stockout_day}</span>
          </div>
          <div className="flex flex-col pl-2">
            <span>Downtime Penalty:</span>
            <span className="text-sm font-bold text-status-alert mt-0.5">{formatCurrency(do_nothing_impact.total_financial_loss)}</span>
          </div>
        </div>
      </div>

      {/* 2. Confidence Indicator Gauge */}
      {(() => {
        const getAsciiProgress = (val: number): string => {
          const totalBlocks = 10;
          const filled = Math.round(val * totalBlocks);
          const empty = totalBlocks - filled;
          return "█".repeat(filled) + "░".repeat(empty);
        };

        return (
          <div className="glass-panel p-3.5 flex flex-col gap-2 font-mono text-xxs select-none">
            <span className="font-bold uppercase tracking-wider text-textMuted select-none">Decision Confidence Matrix</span>
            
            <div className="flex flex-col gap-1.5 mt-1 border-t border-border/30 pt-2.5">
              <div className="flex justify-between items-center">
                <span className="text-textMuted font-sans">Extraction</span>
                <span className="text-textDefault font-bold">
                  <span className="text-brand-primary/80 mr-2">{getAsciiProgress(composite_confidence.extraction)}</span>
                  {(composite_confidence.extraction * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-textMuted font-sans">Telemetry</span>
                <span className="text-textDefault font-bold">
                  <span className="text-brand-primary/80 mr-2">{getAsciiProgress(composite_confidence.simulation)}</span>
                  {(composite_confidence.simulation * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-textMuted font-sans">Feasibility</span>
                <span className="text-textDefault font-bold">
                  <span className="text-brand-primary/80 mr-2">{getAsciiProgress(composite_confidence.optimization)}</span>
                  {(composite_confidence.optimization * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between items-center border-t border-border/30 pt-2 mt-1 text-brand-primary">
                <span className="font-sans">Overall Index</span>
                <span className="font-bold">
                  <span className="mr-2">{getAsciiProgress(composite_confidence.overall)}</span>
                  {(composite_confidence.overall * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        );
      })()}

      {/* 3. Scored Options List */}
      <div className="flex flex-col gap-2.5">
        <span className="text-xxs font-bold uppercase tracking-wider text-textMuted">Evaluated Mitigation Options</span>
        
        <div className="flex flex-col gap-2">
          {options.map((opt) => (
            <div
              key={opt.option_id}
              className={`border p-2.5 rounded-lg flex flex-col gap-2 bg-card/40 transition-all ${
                opt.is_recommended 
                  ? "border-status-healthy/30 shadow-[0_0_8px_rgba(34,197,94,0.05)] bg-status-healthy/[0.01]" 
                  : "border-border hover:border-border/80"
              }`}
            >
              <div className="flex justify-between items-start gap-1">
                <div className="flex flex-col">
                  <span className="text-xxs font-bold text-textDefault flex items-center gap-1">
                    {opt.is_recommended && <CheckCircle2 className="w-3.5 h-3.5 text-status-healthy" />}
                    {opt.title}
                  </span>
                  <span className="text-xxs text-textMuted/80 mt-0.5 leading-relaxed">{opt.description}</span>
                </div>
                
                {/* Score */}
                <div className="flex flex-col text-right">
                  <span className="text-xxs text-textMuted scale-90">Score</span>
                  <span className={`text-xs font-bold font-mono ${getScoreColor(opt.calculated_score)}`}>
                    {opt.calculated_score.toFixed(3)}
                  </span>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-2 border-t border-border/30 pt-2 text-xxs font-mono text-textMuted">
                <div>
                  <span className="block text-xxs scale-90 origin-left">Mitigation Cost</span>
                  <span className="font-semibold text-textDefault">{formatCurrency(opt.cost_impact)}</span>
                </div>
                <div>
                  <span className="block text-xxs scale-90 origin-left">Transit Shift</span>
                  <span className="font-semibold text-textDefault">
                    {opt.lead_time_surcharge_days > 0 ? `+${opt.lead_time_surcharge_days}` : opt.lead_time_surcharge_days}d
                  </span>
                </div>
                <div className="text-right">
                  <span className="block text-xxs scale-90 origin-right">Feasibility</span>
                  <span className="font-semibold text-textDefault">{(opt.feasibility_score * 100).toFixed(0)}%</span>
                </div>
              </div>

              {/* Implement Button */}
              <button
                disabled={loading}
                onClick={() => applyMitigationAction(opt.option_id)}
                className={`w-full py-1 px-3 mt-1 rounded flex items-center justify-center gap-1.5 font-semibold text-xxs transition-all border ${
                  opt.is_recommended
                    ? "bg-status-healthy border-status-healthy text-white hover:bg-status-healthy/90"
                    : "bg-transparent border-border text-textMuted hover:text-textDefault hover:border-brand-primary/40 hover:bg-cardHover"
                }`}
              >
                <Play className="w-3 h-3 fill-current" />
                {opt.is_recommended ? "Authorize Recommendation" : "Execute Plan"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 4. AI Narration summary */}
      {gemini_explanation && (
        <div className="glass-panel p-3.5 rounded-lg border-brand-primary/20 bg-brand-primary/[0.01] flex flex-col gap-2.5">
          <h4 className="text-xxs font-bold uppercase tracking-wider text-brand-primary flex items-center gap-1">
            <Sparkles className="w-4 h-4 text-brand-primary animate-pulse" />
            Gemini Executive Analysis
          </h4>
          <div className="text-xxs leading-relaxed font-sans text-textDefault/90 border-t border-brand-primary/10 pt-2 prose prose-invert font-light max-w-none">
            {/* Split lines to render basic paragraphs cleanly in HTML */}
            {gemini_explanation.split("\n\n").map((para, pIdx) => {
              if (para.startsWith("###") || para.startsWith("**")) {
                return (
                  <p key={pIdx} className="font-semibold text-brand-primary mb-2 mt-1">
                    {para.replace(/###|\*\*/g, "")}
                  </p>
                );
              }
              return (
                <p key={pIdx} className="mb-2">
                  {para.replace(/\*\*/g, "")}
                </p>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
