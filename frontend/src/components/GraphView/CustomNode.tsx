import React, { memo } from "react";
import { Handle, Position } from "reactflow";
import { Server, Anchor, Warehouse, Factory, Package, AlertOctagon, ShieldAlert } from "lucide-react";
import type { NodeType } from "../../types";

export interface CustomNodeProps {
  id: string;
  data: {
    name: string;
    type: NodeType;
    health: number;
    inventory: number;
    capacity: number;
    safety_stock: number;
    isTarget: boolean;
    isStandby: boolean;
    selectedState: "active" | "upstream" | "downstream" | "dimmed" | "none";
  };
}

export const getDescriptiveLabel = (id: string): string => {
  switch (id) {
    case "supplier-silicon": return "Silicon Supplier";
    case "factory-wafer": return "Taichung Wafer Fab";
    case "port-kaohsiung": return "Port of Kaohsiung";
    case "port-antwerp": return "Port of Antwerp";
    case "port-rotterdam": return "Port of Rotterdam";
    case "warehouse-munich": return "Munich Warehouse";
    case "factory-assembly": return "Munich Factory";
    case "distributor-europe": return "Euro Distribution Center";
    case "product-nexus-ecu": return "Nexus ECU";
    default: return id;
  }
};

const CustomNode: React.FC<CustomNodeProps> = ({ id, data }) => {
  const { type, health, inventory, capacity, safety_stock, isTarget, isStandby, selectedState } = data;
  
  const label = getDescriptiveLabel(id);

  const getNodeIcon = () => {
    const isDisrupted = health === 0;
    const iconClass = `w-4.5 h-4.5 ${isDisrupted ? "animate-pulse" : ""}`;
    switch (type) {
      case "SUPPLIER":
        return <Server className={iconClass} />;
      case "PORT":
        return <Anchor className={iconClass} />;
      case "WAREHOUSE":
        return <Warehouse className={iconClass} />;
      case "FACTORY":
        return <Factory className={iconClass} />;
      default:
        return <Package className={iconClass} />;
    }
  };

  // Node background/border styling based on health and alternative routes
  const getNodeColorClass = () => {
    if (isStandby && health === 1.0) {
      return "border-status-standby text-status-standby bg-status-standby/5 shadow-[0_0_12px_rgba(59,130,246,0.15)]";
    }
    if (health >= 1.0) {
      // Check if inventory is running below safety stock (Starvation Warning)
      if (type !== "PRODUCT" && inventory < safety_stock) {
        return "border-status-warning text-status-warning bg-status-warning/[0.02] shadow-[0_0_12px_rgba(245,158,11,0.15)] animate-pulse";
      }
      return "border-status-healthy text-status-healthy bg-status-healthy/[0.02] shadow-[0_0_12px_rgba(34,197,94,0.1)]";
    }
    if (health > 0.0) {
      return "border-status-warning text-status-warning bg-status-warning/5 shadow-[0_0_15px_rgba(245,158,11,0.3)] animate-pulse";
    }
    return "border-status-alert text-status-alert bg-status-alert/10 shadow-[0_0_20px_rgba(239,68,68,0.4)] animate-pulse border-2";
  };

  // Selection highlighting overrides
  const getSelectionBorderClass = () => {
    switch (selectedState) {
      case "active":
        return "ring-2 ring-brand-primary !border-brand-primary !shadow-glass-glow scale-105 z-40";
      case "upstream":
        return "!border-status-standby ring-1 ring-status-standby/35 scale-102";
      case "downstream":
        return "!border-status-healthy ring-1 ring-status-healthy/35 scale-102";
      case "dimmed":
        return "opacity-25 scale-95 hover:opacity-40 transition-all";
      default:
        return "opacity-100";
    }
  };

  const isStarved = type !== "PRODUCT" && !isStandby && inventory < safety_stock;

  return (
    <div className={`relative font-mono select-none transition-all duration-300 ${getSelectionBorderClass()}`}>
      
      {/* Handles for Flow Routing */}
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-border" />
      
      {/* Node Card Shell */}
      <div 
        className={`px-3 py-2 border-2 rounded-lg bg-card/95 flex flex-col gap-1 w-44 glass-panel ${getNodeColorClass()}`}
      >
        {/* Header (Icon + Label) */}
        <div className="flex items-center gap-2 border-b border-border/40 pb-1.5 mb-1.5">
          <div className="p-1 rounded bg-background/55">
            {getNodeIcon()}
          </div>
          <span className="text-xxs font-bold text-textDefault leading-tight truncate">
            {label}
          </span>
        </div>

        {/* Info Rows */}
        <div className="flex flex-col gap-1 text-[9px] text-textMuted">
          
          {/* Health Status read-out */}
          <div className="flex justify-between items-center">
            <span>Health:</span>
            {health < 1.0 ? (
              <span className={`font-bold animate-pulse ${health > 0 ? "text-status-warning" : "text-status-alert"}`}>
                {(health * 100).toFixed(0)}%
              </span>
            ) : (
              <span className="text-status-healthy font-semibold">100%</span>
            )}
          </div>

          {/* Starvation warning pill */}
          {isStarved && health > 0 && (
            <div className="flex items-center gap-1 text-status-warning font-bold text-[8px] uppercase mt-0.5 border border-status-warning/20 bg-status-warning/5 px-1 py-0.5 rounded">
              <ShieldAlert className="w-2.5 h-2.5 animate-pulse" />
              <span>Safety Stock Alert</span>
            </div>
          )}

          {type !== "PRODUCT" && !isStandby && (
            <div className="flex flex-col gap-0.5 mt-0.5">
              <div className="flex justify-between">
                <span>Inventory:</span>
                <span className="text-textDefault font-semibold">{inventory.toFixed(0)} / {capacity.toFixed(0)}</span>
              </div>
              
              {/* Inventory Meter */}
              <div className="w-full bg-background h-1.5 rounded-full overflow-hidden mt-1 border border-border/20">
                <div 
                  style={{ width: `${Math.min(100, (inventory / capacity) * 100)}%` }}
                  className={`h-full transition-all duration-500 ${
                    inventory < safety_stock ? "bg-status-warning" : "bg-status-healthy"
                  }`}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Target Disruption Flag Overlay */}
      {isTarget && health < 1.0 && (
        <div className="absolute -top-4.5 left-1/2 -translate-x-1/2 flex items-center gap-0.5 text-status-alert text-[8px] font-bold uppercase animate-bounce bg-background border border-status-alert/30 px-1.5 py-0.5 rounded shadow z-25">
          <AlertOctagon className="w-3.5 h-3.5 fill-status-alert text-white" />
          <span>BLOCKED</span>
        </div>
      )}

      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-border" />
    </div>
  );
};

export default memo(CustomNode);
