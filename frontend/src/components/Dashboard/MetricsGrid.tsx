import React from "react";
import { useNexus } from "../../context/NexusContext";
import { Shield, DollarSign, Package, AlertTriangle } from "lucide-react";

export const MetricsGrid: React.FC = () => {
  const { metrics } = useNexus();

  // Helper to color the resilience score based on thresholds
  const getResilienceColor = (score: number) => {
    if (score >= 95) return "text-status-healthy";
    if (score >= 75) return "text-status-warning";
    return "text-status-alert";
  };

  const getResilienceGlow = (score: number) => {
    if (score >= 95) return "shadow-[0_0_15px_rgba(34,197,94,0.1)]";
    if (score >= 75) return "shadow-[0_0_15px_rgba(245,158,11,0.1)]";
    return "shadow-[0_0_15px_rgba(239,68,68,0.15)]";
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 w-full mb-6">
      {/* 1. Global Resilience */}
      <div className={`glass-panel p-4 flex items-center justify-between ${getResilienceGlow(metrics.overall_resilience)}`}>
        <div className="flex flex-col">
          <span className="text-textMuted text-xs uppercase tracking-wider font-semibold">Global Resilience</span>
          <span className={`text-3xl font-bold font-sans mt-1 ${getResilienceColor(metrics.overall_resilience)}`}>
            {metrics.overall_resilience.toFixed(1)}%
          </span>
        </div>
        <div className={`p-2.5 rounded-lg bg-card ${getResilienceColor(metrics.overall_resilience)}`}>
          <Shield className="w-6 h-6" />
        </div>
      </div>

      {/* 2. Cumulative Financial Risk */}
      <div className={`glass-panel p-4 flex items-center justify-between ${metrics.total_financial_loss > 0 ? "shadow-[0_0_15px_rgba(239,68,68,0.1)] border-status-alert/20" : ""}`}>
        <div className="flex flex-col">
          <span className="text-textMuted text-xs uppercase tracking-wider font-semibold">Financial Exposure</span>
          <span className={`text-3xl font-bold font-sans mt-1 ${metrics.total_financial_loss > 0 ? "text-status-alert" : "text-textDefault"}`}>
            {formatCurrency(metrics.total_financial_loss)}
          </span>
        </div>
        <div className={`p-2.5 rounded-lg bg-card ${metrics.total_financial_loss > 0 ? "text-status-alert" : "text-textMuted"}`}>
          <DollarSign className="w-6 h-6" />
        </div>
      </div>

      {/* 3. Delayed Products */}
      <div className={`glass-panel p-4 flex items-center justify-between ${metrics.delayed_products_count > 0 ? "shadow-[0_0_15px_rgba(245,158,11,0.1)] border-status-warning/20" : ""}`}>
        <div className="flex flex-col">
          <span className="text-textMuted text-xs uppercase tracking-wider font-semibold">Delayed Shipment Vol</span>
          <span className={`text-3xl font-bold font-sans mt-1 ${metrics.delayed_products_count > 0 ? "text-status-warning" : "text-textDefault"}`}>
            {metrics.delayed_products_count.toLocaleString()} <span className="text-xs text-textMuted">units</span>
          </span>
        </div>
        <div className={`p-2.5 rounded-lg bg-card ${metrics.delayed_products_count > 0 ? "text-status-warning" : "text-textMuted"}`}>
          <Package className="w-6 h-6" />
        </div>
      </div>

      {/* 4. Active Disrupted Nodes */}
      <div className={`glass-panel p-4 flex items-center justify-between ${metrics.disrupted_nodes_count > 0 ? "shadow-[0_0_15px_rgba(239,68,68,0.15)] border-status-alert/30" : ""}`}>
        <div className="flex flex-col">
          <span className="text-textMuted text-xs uppercase tracking-wider font-semibold">Disrupted Twin Nodes</span>
          <span className={`text-3xl font-bold font-sans mt-1 ${metrics.disrupted_nodes_count > 0 ? "text-status-alert" : "text-textDefault"}`}>
            {metrics.disrupted_nodes_count} <span className="text-xs text-textMuted">/ {metrics.disrupted_nodes_count > 0 ? "9" : "Healthy"}</span>
          </span>
        </div>
        <div className={`p-2.5 rounded-lg bg-card ${metrics.disrupted_nodes_count > 0 ? "text-status-alert animate-pulse" : "text-textMuted"}`}>
          <AlertTriangle className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};
