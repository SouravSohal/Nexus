import React from "react";
import { NexusProvider, useNexus } from "./context/NexusContext";
import { MetricsGrid } from "./components/Dashboard/MetricsGrid";
import { NewsBox } from "./components/NewsInput/NewsBox";
import { GraphCanvas } from "./components/GraphView/GraphCanvas";
import { DecisionPanel } from "./components/Recommendation/DecisionPanel";
import { TimelineScrubber } from "./components/Dashboard/TimelineScrubber";
import { Cpu, Wifi, AlertTriangle } from "lucide-react";

const DashboardContent: React.FC = () => {
  const { loading, error, aiStatus } = useNexus();

  return (
    <div className="flex flex-col h-screen w-screen p-4 md:p-6 bg-background relative overflow-hidden">
      
      {/* Global Error Overlay */}
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 bg-status-alert/15 border border-status-alert/30 text-status-alert text-xs py-2 px-4 rounded-lg shadow-glass backdrop-blur-md">
          <AlertTriangle className="w-4.5 h-4.5 animate-pulse" />
          <span>{error}</span>
        </div>
      )}

      {/* 1. Header Control Panel */}
      <header className="flex items-center justify-between border-b border-border/60 pb-3 mb-4 select-none">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-brand-primary/10 border border-brand-primary/20 rounded-lg text-brand-primary">
            <Cpu className="w-5 h-5 animate-pulse" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-lg font-bold tracking-wider font-sans text-textDefault">
              NEXUS <span className="text-textMuted font-mono text-xxs font-normal">v2.0.0</span>
            </h1>
            <span className="text-xxs font-mono uppercase tracking-wider text-textMuted/80">
              Cognitive Digital Twin Control Plane
            </span>
          </div>
        </div>

        {/* Global telemetry status dot */}
        <div className="flex items-center gap-4">
          <div className="hidden md:flex flex-col text-right font-mono text-xxs text-textMuted">
            <span>OPERATOR: SECURE_DEMO_PLANE</span>
            <span className="text-textMuted/60">SYS_TIME: 2026-07-01 UTC</span>
          </div>
          
          {/* AI Engine Provider Status */}
          <div className="flex items-center gap-2 border border-border bg-card/45 px-3 py-1.5 rounded-lg text-xxs font-mono text-textMuted shadow-sm">
            <span className="text-textMuted/60">AI:</span>
            {aiStatus === "gemini" && (
              <>
                <span className="font-semibold text-textDefault">Gemini</span>
                <span className="w-1.5 h-1.5 rounded-full bg-status-healthy glow-green" />
              </>
            )}
            {aiStatus === "ollama" && (
              <>
                <span className="font-semibold text-textDefault">Local AI</span>
                <span className="w-1.5 h-1.5 rounded-full bg-status-warning glow-yellow animate-pulse" />
              </>
            )}
            {aiStatus === "offline" && (
              <>
                <span className="font-semibold text-textDefault">Offline</span>
                <span className="w-1.5 h-1.5 rounded-full bg-status-alert glow-red animate-pulse" />
              </>
            )}
          </div>

          <div className="flex items-center gap-2 border border-border bg-card/45 px-3 py-1.5 rounded-lg text-xxs font-mono text-textMuted shadow-sm">
            <Wifi className="w-3.5 h-3.5 text-status-healthy animate-pulse" />
            <span className="font-semibold text-textDefault">TELEMETRY: ONLINE</span>
            <span className="w-1.5 h-1.5 rounded-full bg-status-healthy glow-green ml-1" />
          </div>
        </div>
      </header>

      {/* 2. Primary KPI Counter Grid */}
      <MetricsGrid />

      {/* 3. Main Dashboard Workspace Layout */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 min-h-0 mb-4 relative">
        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-background/50 backdrop-blur-xs z-40 flex items-center justify-center pointer-events-auto rounded-lg">
            <div className="flex flex-col items-center gap-2.5">
              <div className="w-10 h-10 border-4 border-brand-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-mono text-brand-primary uppercase tracking-widest font-semibold animate-pulse">Syncing Twin State...</span>
            </div>
          </div>
        )}

        {/* Left column: News input & Alert log */}
        <section className="lg:col-span-1 min-h-0">
          <NewsBox />
        </section>

        {/* Center columns: 2D coordinates map */}
        <section className="lg:col-span-2 flex flex-col min-h-0">
          <GraphCanvas />
        </section>

        {/* Right column: Decisions optimization & Gemini narration */}
        <section className="lg:col-span-1 min-h-0">
          <DecisionPanel />
        </section>
      </main>

      {/* 4. Bottom timeline player playback scrubber */}
      <footer className="w-full select-none mt-auto">
        <TimelineScrubber />
      </footer>
    </div>
  );
};

export default function App() {
  return (
    <NexusProvider>
      <DashboardContent />
    </NexusProvider>
  );
}
