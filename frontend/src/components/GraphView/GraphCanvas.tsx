import React, { useState, useMemo } from "react";
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  BackgroundVariant 
} from "reactflow";
import "reactflow/dist/style.css";
import { useNexus } from "../../context/NexusContext";
import CustomNode, { getDescriptiveLabel } from "./CustomNode";
import type { Node as ModelNode, Edge as ModelEdge } from "../../types";
import { Activity, X, Server, Anchor, Warehouse, Factory, Package, ArrowUpRight, ArrowDownRight } from "lucide-react";

const nodeTypes = {
  customNode: CustomNode
};

/**
 * BFS/DFS helper to calculate upstream and downstream subgraphs for a selected node.
 */
const getPathDependencies = (
  selectedId: string,
  edges: ModelEdge[]
): { upstream: Set<string>; downstream: Set<string> } => {
  const upstream = new Set<string>();
  const downstream = new Set<string>();

  const traverseUp = (id: string) => {
    edges.forEach(e => {
      if (e.target === id && !upstream.has(e.source)) {
        upstream.add(e.source);
        traverseUp(e.source);
      }
    });
  };

  const traverseDown = (id: string) => {
    edges.forEach(e => {
      if (e.source === id && !downstream.has(e.target)) {
        downstream.add(e.target);
        traverseDown(e.target);
      }
    });
  };

  traverseUp(selectedId);
  traverseDown(selectedId);

  return { upstream, downstream };
};

/**
 * 100% Data-Driven rank-based layered layout generator for Directed Acyclic Graphs (DAGs).
 */
const computeDataDrivenLayout = (
  nodes: ModelNode[],
  edges: ModelEdge[]
): Record<string, { x: number; y: number }> => {
  const adj: Record<string, string[]> = {};
  const inDegree: Record<string, number> = {};

  nodes.forEach(n => {
    adj[n.id] = [];
    inDegree[n.id] = 0;
  });

  edges.forEach(e => {
    if (adj[e.source]) {
      adj[e.source].push(e.target);
    }
    inDegree[e.target] = (inDegree[e.target] || 0) + 1;
  });

  // Roots occupy Level 0
  const levels: Record<string, number> = {};
  const queue: string[] = [];

  nodes.forEach(n => {
    if (inDegree[n.id] === 0) {
      levels[n.id] = 0;
      queue.push(n.id);
    }
  });

  while (queue.length > 0) {
    const current = queue.shift()!;
    const currentLevel = levels[current] || 0;

    adj[current].forEach(target => {
      levels[target] = Math.max(levels[target] || 0, currentLevel + 1);
      queue.push(target);
    });
  }

  nodes.forEach(n => {
    if (levels[n.id] === undefined) {
      levels[n.id] = 0;
    }
  });

  const nodesByLevel: Record<number, string[]> = {};
  nodes.forEach(n => {
    const lvl = levels[n.id];
    if (!nodesByLevel[lvl]) {
      nodesByLevel[lvl] = [];
    }
    nodesByLevel[lvl].push(n.id);
  });

  const positions: Record<string, { x: number; y: number }> = {};
  const xSpacing = 240;
  const ySpacing = 150;

  Object.keys(nodesByLevel).forEach(lvlStr => {
    const lvl = parseInt(lvlStr, 10);
    const nodeIds = nodesByLevel[lvl];
    const totalHeight = (nodeIds.length - 1) * ySpacing;
    const yOffset = -totalHeight / 2;

    nodeIds.forEach((id, index) => {
      positions[id] = {
        x: lvl * xSpacing + 50,
        y: yOffset + (index * ySpacing) + 200
      };
    });
  });

  return positions;
};

export const GraphCanvas: React.FC = () => {
  const { nodes, edges, activeEvent } = useNexus();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Compute selected node details for Inspector
  const selectedNode = useMemo(() => {
    return nodes.find(n => n.id === selectedNodeId);
  }, [nodes, selectedNodeId]);

  // Compute upstream/downstream nodes for highlights
  const { upstream, downstream } = useMemo(() => {
    if (!selectedNodeId) {
      return { upstream: new Set<string>(), downstream: new Set<string>() };
    }
    return getPathDependencies(selectedNodeId, edges);
  }, [selectedNodeId, edges]);

  // Compute topological positions dynamically
  const nodePositions = useMemo(() => {
    return computeDataDrivenLayout(nodes, edges);
  }, [nodes, edges]);

  // Convert context nodes to React Flow Node objects
  const flowNodes = useMemo(() => {
    return nodes.map(node => {
      const isTarget = activeEvent?.affected_node_id === node.id;
      const isStandby = node.id === "port-rotterdam";
      const pos = nodePositions[node.id] || { x: 300, y: 250 };
      
      let selectedState: "active" | "upstream" | "downstream" | "dimmed" | "none" = "none";
      if (selectedNodeId) {
        if (selectedNodeId === node.id) {
          selectedState = "active";
        } else if (upstream.has(node.id)) {
          selectedState = "upstream";
        } else if (downstream.has(node.id)) {
          selectedState = "downstream";
        } else {
          selectedState = "dimmed";
        }
      }

      return {
        id: node.id,
        type: "customNode",
        position: pos,
        data: {
          name: node.name,
          type: node.type,
          health: node.health,
          inventory: node.inventory,
          capacity: node.capacity,
          safety_stock: node.safety_stock,
          isTarget,
          isStandby,
          selectedState
        }
      };
    });
  }, [nodes, activeEvent, selectedNodeId, upstream, downstream, nodePositions]);

  // Convert context edges to React Flow Edge objects
  const flowEdges = useMemo(() => {
    return edges.map((edge, idx) => {
      const startNode = nodes.find(n => n.id === edge.source);
      const startHealth = startNode ? startNode.health : 1.0;
      
      const isStandby = edge.dependency_ratio === 0;
      const isBlocked = startHealth === 0.0;
      const isAtRisk = startHealth < 1.0;

      // Color and dash config based on state
      let strokeColor = "rgba(59, 130, 246, 0.45)";  // Default active blue
      let strokeDash = undefined;
      let strokeWidth = 2.5;
      
      if (isStandby) {
        strokeColor = "#374151";                     // Gray bypassed path
        strokeDash = "5,5";
        strokeWidth = 1.5;
      } else if (isBlocked) {
        strokeColor = "hsl(346, 80%, 50%)";          // Disrupted red path
        strokeDash = "4,4";
      } else if (isAtRisk) {
        strokeColor = "hsl(45, 93%, 47%)";           // Warning amber path
        strokeDash = "3,3";
      }

      // Handle path highlights
      let opacity = "1.0";
      if (selectedNodeId) {
        const isPartOfSelection = 
          (selectedNodeId === edge.source && downstream.has(edge.target)) ||
          (selectedNodeId === edge.target && upstream.has(edge.source)) ||
          (upstream.has(edge.source) && upstream.has(edge.target) && (edge.target === selectedNodeId || upstream.has(edge.target))) ||
          (downstream.has(edge.source) && downstream.has(edge.target) && (edge.source === selectedNodeId || downstream.has(edge.source)));

        if (isPartOfSelection) {
          strokeWidth += 1.0;
        } else {
          opacity = "0.08";
        }
      }

      return {
        id: `edge-${edge.source}-${edge.target}-${idx}`,
        source: edge.source,
        target: edge.target,
        animated: !isStandby && !isBlocked,
        style: {
          stroke: strokeColor,
          strokeWidth: strokeWidth,
          strokeDasharray: strokeDash,
          opacity: opacity
        }
      };
    });
  }, [edges, nodes, selectedNodeId, upstream, downstream]);

  const getNodeIcon = (type: string) => {
    const iconClass = "w-4 h-4 text-brand-primary";
    switch (type) {
      case "SUPPLIER": return <Server className={iconClass} />;
      case "PORT": return <Anchor className={iconClass} />;
      case "WAREHOUSE": return <Warehouse className={iconClass} />;
      case "FACTORY": return <Factory className={iconClass} />;
      default: return <Package className={iconClass} />;
    }
  };

  return (
    <div className="glass-panel w-full flex-1 flex flex-col min-h-[460px] relative overflow-hidden bg-card/45">
      
      {/* 1. Topology Header Metadata Info */}
      <div className="absolute top-3 left-3 z-15 flex items-center gap-2 font-mono text-[9px] text-textMuted bg-background/85 border border-border py-1.5 px-3 rounded-md backdrop-blur-sm shadow-sm select-none">
        <Activity className="w-3.5 h-3.5 text-brand-primary animate-pulse" />
        <span>COGNITIVE DIGITAL TWIN ENGINE: RUNNING</span>
      </div>

      {/* 2. React Flow Canvas Node Map */}
      <div className="flex-1 w-full h-full select-none">
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => setSelectedNodeId(node.id)}
          onPaneClick={() => setSelectedNodeId(null)}
          fitView
          fitViewOptions={{ padding: 0.1 }} // visual scale prominence increase
          minZoom={0.3}
          maxZoom={1.8}
          proOptions={{ hideAttribution: true }}
          className="w-full h-full"
        >
          <Background 
            variant={BackgroundVariant.Dots} 
            gap={18} 
            size={1} 
            color="rgba(255, 255, 255, 0.05)" 
          />
          <Controls className="!bg-card/90 !border-border" />
          <MiniMap 
            nodeColor="#030712"
            maskColor="rgba(3, 7, 18, 0.6)"
            className="!bg-card/90 !border-border" 
          />
        </ReactFlow>
      </div>

      {/* 3. Floating Selected Node Inspector Panel */}
      {selectedNode && (
        <div className="absolute top-3 right-3 z-15 w-64 bg-background/90 border border-border p-3.5 rounded-lg shadow-glass backdrop-blur-md font-mono text-xxs flex flex-col gap-2.5 select-none animate-fade-in border-brand-primary/20">
          <div className="flex justify-between items-center border-b border-border/40 pb-2">
            <div className="flex items-center gap-1.5">
              {getNodeIcon(selectedNode.type)}
              <span className="text-textDefault font-bold font-sans text-xs">{getDescriptiveLabel(selectedNode.id)}</span>
            </div>
            <button 
              onClick={() => setSelectedNodeId(null)}
              className="text-textMuted hover:text-textDefault p-0.5 rounded bg-cardHover border border-border/60"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          
          <div className="flex justify-between">
            <span className="text-textMuted">Location:</span>
            <span className="text-textDefault font-semibold">{selectedNode.location}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-textMuted">Health Status:</span>
            <span className={selectedNode.health === 1.0 ? "text-status-healthy font-semibold" : selectedNode.health > 0 ? "text-status-warning font-bold animate-pulse" : "text-status-alert font-bold"}>
              {selectedNode.health === 1.0 ? "Operational (100%)" : selectedNode.health > 0 ? `Degraded (${(selectedNode.health * 100).toFixed(0)}%)` : "SHUTDOWN (0%)"}
            </span>
          </div>
          
          {selectedNode.type !== "PRODUCT" && (
            <div className="flex flex-col gap-1 border-t border-border/30 pt-2">
              <div className="flex justify-between">
                <span className="text-textMuted">Inventory Level:</span>
                <span className="text-textDefault font-semibold">
                  {selectedNode.inventory.toFixed(0)} / {selectedNode.capacity.toFixed(0)}
                </span>
              </div>
              <div className="w-full bg-background/50 h-1.5 rounded-full overflow-hidden mt-0.5 border border-border/20">
                <div 
                  style={{ width: `${(selectedNode.inventory / selectedNode.capacity) * 100}%` }}
                  className={`h-full transition-all duration-500 ${
                    selectedNode.inventory < selectedNode.safety_stock ? "bg-status-warning" : "bg-status-healthy"
                  }`}
                />
              </div>
              <div className="flex justify-between text-[9px] text-textMuted/80">
                <span>Safety Stock Limit:</span>
                <span className="text-status-warning font-semibold">{selectedNode.safety_stock.toFixed(0)} units</span>
              </div>
            </div>
          )}
          
          <div className="border-t border-border/30 pt-2 flex flex-col gap-1 text-[9.5px]">
            <div className="flex justify-between">
              <span className="text-textMuted">Daily Operating Cost:</span>
              <span className="text-textDefault">${selectedNode.base_cost.toLocaleString()}</span>
            </div>
            {selectedNode.type !== "PRODUCT" && (
              <>
                <div className="flex justify-between">
                  <span className="text-textMuted">Daily Inflow:</span>
                  <span className="text-status-healthy font-semibold flex items-center">
                    <ArrowUpRight className="w-3.5 h-3.5" />
                    +{selectedNode.replenishment_rate.toFixed(0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-textMuted">Daily Outflow:</span>
                  <span className="text-status-warning font-semibold flex items-center">
                    <ArrowDownRight className="w-3.5 h-3.5" />
                    -{selectedNode.daily_consumption.toFixed(0)}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* 4. Floating Node Legends */}
      <div className="absolute bottom-3 left-3 z-15 flex items-center gap-3.5 font-mono text-[9px] text-textMuted bg-background/85 border border-border p-2 rounded-md backdrop-blur-sm shadow-sm select-none">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-status-healthy glow-green" />
          <span className="text-textDefault font-medium">Operational</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-status-warning glow-yellow" />
          <span className="text-textDefault font-medium">At Risk</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-status-alert glow-red" />
          <span className="text-textDefault font-medium">Disrupted</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-status-standby" />
          <span className="text-textDefault font-medium">Alternative Path</span>
        </div>
      </div>

    </div>
  );
};
