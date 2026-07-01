import React from "react";
import { useNexus } from "../../context/NexusContext";
import { Play, Pause, RotateCcw, Calendar } from "lucide-react";

export const TimelineScrubber: React.FC = () => {
  const { 
    activeSimulation, 
    activeRecommendation,
    selectedDay, 
    setSelectedDay, 
    timelinePlaying, 
    setTimelinePlaying, 
    resetDigitalTwin 
  } = useNexus();

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedDay(parseInt(e.target.value, 10));
  };

  const togglePlay = () => {
    if (!activeSimulation) return;
    setTimelinePlaying(!timelinePlaying);
  };

  const handleReset = () => {
    resetDigitalTwin();
  };

  if (!activeSimulation) {
    return (
      <div className="glass-panel p-3 flex items-center justify-between w-full">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-textMuted" />
          <span className="text-xs font-mono text-textMuted">Timeline Monitor: Standby baseline mode.</span>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-1.5 py-1 px-3 bg-card border border-border hover:bg-cardHover hover:border-brand-primary/30 rounded text-xxs font-semibold font-mono text-textMuted hover:text-textDefault transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Force Recalibrate
        </button>
      </div>
    );
  }

  const stepsCount = activeSimulation.timeline.length;
  const stockoutDay = activeRecommendation?.do_nothing_impact.earliest_stockout_day ?? -1;

  return (
    <div className="glass-panel p-3.5 flex flex-col gap-3 w-full border-brand-primary/20 shadow-[0_0_15px_rgba(59,130,246,0.05)]">
      <div className="flex items-center justify-between">
        
        {/* Play/Pause controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={togglePlay}
            className={`p-2 rounded-full border transition-all ${
              timelinePlaying
                ? "bg-brand-primary/20 border-brand-primary text-brand-primary shadow-glass-glow"
                : "bg-card border-border text-textDefault hover:border-brand-primary/50"
            }`}
          >
            {timelinePlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
          </button>
          
          <div className="flex flex-col">
            <span className="text-xxs font-bold uppercase tracking-wider text-textMuted font-sans">Simulation Playback</span>
            <span className="text-xs font-mono text-brand-primary font-bold">
              Day {selectedDay} <span className="text-textMuted font-normal">/ {stepsCount - 1}</span>
            </span>
          </div>
        </div>

        {/* Dynamic status readout */}
        <div className="hidden md:flex items-center gap-4 text-xxs font-mono text-textMuted">
          {stockoutDay !== -1 && (
            <div className="flex items-center gap-1.5 border border-status-alert/20 bg-status-alert/5 px-2 py-0.5 rounded">
              <span className="w-1.5 h-1.5 rounded-full bg-status-alert animate-ping" />
              <span>Forecasted stockout: Day {stockoutDay}</span>
            </div>
          )}
          <span>Resilience at Day {selectedDay}: {activeSimulation.timeline[selectedDay].metrics.resilience_score.toFixed(1)}%</span>
        </div>

        {/* Recalibrate button */}
        <button
          onClick={handleReset}
          className="flex items-center gap-1.5 py-1.5 px-3.5 bg-card border border-border hover:bg-cardHover hover:border-brand-primary/30 rounded-lg text-xxs font-semibold text-textMuted hover:text-textDefault transition-all shadow-glass"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Baseline
        </button>
      </div>

      {/* Progress Track Slider */}
      <div className="relative w-full flex items-center h-4 mt-1">
        {/* Stockout indicator flag on track */}
        {stockoutDay !== -1 && stockoutDay < stepsCount && (
          <div 
            style={{ left: `${(stockoutDay / (stepsCount - 1)) * 100}%` }}
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-20 flex flex-col items-center group cursor-pointer"
          >
            <div className="w-1 h-3.5 bg-status-alert shadow-red" />
            <div className="absolute -top-7 bg-status-alert text-white text-xxs px-1.5 py-0.5 rounded shadow font-semibold opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
              Stockout Day {stockoutDay}
            </div>
          </div>
        )}
        
        <input
          type="range"
          min="0"
          max={stepsCount - 1}
          value={selectedDay}
          onChange={handleSliderChange}
          className="w-full h-1 bg-border rounded-lg appearance-none cursor-pointer accent-brand-primary focus:outline-none relative z-10"
          style={{
            background: `linear-gradient(to right, hsl(217, 91%, 60%) 0%, hsl(217, 91%, 60%) ${(selectedDay / (stepsCount - 1)) * 100}%, hsl(222, 30%, 15%) ${(selectedDay / (stepsCount - 1)) * 100}%, hsl(222, 30%, 15%) 100%)`
          }}
        />
      </div>
      
      {/* Day label markers */}
      <div className="flex justify-between px-1 text-xxs font-mono text-textMuted/60">
        {Array.from({ length: stepsCount }).map((_, idx) => (
          <span 
            key={idx} 
            onClick={() => setSelectedDay(idx)}
            className={`cursor-pointer transition-colors hover:text-textDefault ${selectedDay === idx ? "text-brand-primary font-bold" : ""}`}
          >
            D{idx}
          </span>
        ))}
      </div>
    </div>
  );
};
