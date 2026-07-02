import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import type { 
  Node, 
  Edge, 
  MetricsResponse, 
  RiskEvent, 
  SimulationRun, 
  RecommendationBundle 
} from "../types";
import { useNexusApi } from "../hooks/useNexusApi";

interface NexusContextType {
  nodes: Node[];
  edges: Edge[];
  metrics: MetricsResponse;
  events: RiskEvent[];
  activeEvent: RiskEvent | null;
  activeSimulation: SimulationRun | null;
  activeRecommendation: RecommendationBundle | null;
  selectedDay: number;
  timelinePlaying: boolean;
  loading: boolean;
  error: string | null;
  aiStatus: string;
  
  // Actions
  fetchSystemState: () => Promise<void>;
  ingestNewsAlert: (text: string) => Promise<void>;
  selectEvent: (eventId: string) => Promise<void>;
  setSelectedDay: (day: number) => void;
  setTimelinePlaying: (play: boolean) => void;
  applyMitigationAction: (optionId: string) => Promise<void>;
  resetDigitalTwin: () => Promise<void>;
}

const NexusContext = createContext<NexusContextType | undefined>(undefined);

export const NexusProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const api = useNexusApi();
  
  // Core Graph & Dashboard State
  const [rawNodes, setRawNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [metrics, setMetrics] = useState<MetricsResponse>({
    overall_resilience: 100.0,
    total_financial_loss: 0.0,
    delayed_products_count: 0,
    disrupted_nodes_count: 0
  });
  const [events, setEvents] = useState<RiskEvent[]>([]);
  
  // Active Simulation Workflow
  const [activeEvent, setActiveEvent] = useState<RiskEvent | null>(null);
  const [activeSimulation, setActiveSimulation] = useState<SimulationRun | null>(null);
  const [activeRecommendation, setActiveRecommendation] = useState<RecommendationBundle | null>(null);
  
  // Scrubber & Player Controls
  const [selectedDay, setSelectedDay] = useState<number>(0);
  const [timelinePlaying, setTimelinePlaying] = useState<boolean>(false);
  const playIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Loading & Global Errors
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<string>("gemini");

  // Fetch baseline network data
  const fetchSystemState = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const graph = await api.getGraphTopology();
      const dbMetrics = await api.getDashboardMetrics();
      const dbEvents = await api.listEvents();
      
      setRawNodes(graph.nodes);
      setEdges(graph.edges);
      setMetrics(dbMetrics);
      setEvents(dbEvents);

      try {
        const aiStatusData = await api.getAiStatus();
        setAiStatus(aiStatusData.provider);
      } catch {
        setAiStatus("offline");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load Digital Twin state.");
    } finally {
      setLoading(false);
    }
  }, [api]);

  // Bootstrapping
  useEffect(() => {
    fetchSystemState();
  }, [fetchSystemState]);

  // Handle news ingestion
  const ingestNewsAlert = async (text: string) => {
    setLoading(true);
    setError(null);
    setTimelinePlaying(false);
    setSelectedDay(0);
    try {
      const newEvent = await api.ingestNews(text);
      setActiveEvent(newEvent);
      
      // Fetch auto-triggered simulation run & recommendations
      const run = await api.getImpactTimeline(newEvent.id);
      setActiveSimulation(run);
      
      const rec = await api.getRecommendations(newEvent.id);
      setActiveRecommendation(rec);
      
      // Update global events listing
      const dbEvents = await api.listEvents();
      setEvents(dbEvents);
      
      // Update metrics
      const dbMetrics = await api.getDashboardMetrics();
      setMetrics(dbMetrics);
      
    } catch (err: any) {
      setError(err.message || "Failed to process risk ingestion.");
    } finally {
      setLoading(false);
    }
  };

  // Inspect a specific past event
  const selectEvent = async (eventId: string) => {
    setLoading(true);
    setError(null);
    setTimelinePlaying(false);
    setSelectedDay(0);
    try {
      const selected = events.find(e => e.id === eventId) || await api.getEvent(eventId);
      setActiveEvent(selected);
      
      const run = await api.getImpactTimeline(eventId);
      setActiveSimulation(run);
      
      const rec = await api.getRecommendations(eventId);
      setActiveRecommendation(rec);
    } catch (err: any) {
      setError(err.message || `Failed to load event details for '${eventId}'.`);
    } finally {
      setLoading(false);
    }
  };

  // Execute mitigation selection
  const applyMitigationAction = async (optionId: string) => {
    if (!activeEvent) return;
    setLoading(true);
    setError(null);
    try {
      await api.applyMitigation(activeEvent.id, optionId);
      
      // Reload current state (edges/nodes updated in database)
      await fetchSystemState();
      
      // Reset active simulation selection to clear disruption
      setActiveEvent(null);
      setActiveSimulation(null);
      setActiveRecommendation(null);
      setSelectedDay(0);
      setTimelinePlaying(false);
    } catch (err: any) {
      setError(err.message || "Failed to execute mitigation playbook.");
    } finally {
      setLoading(false);
    }
  };

  // Reset the system back to baseline healthy
  const resetDigitalTwin = async () => {
    setLoading(true);
    setError(null);
    setTimelinePlaying(false);
    setSelectedDay(0);
    try {
      await api.resetSystem();
      setActiveEvent(null);
      setActiveSimulation(null);
      setActiveRecommendation(null);
      await fetchSystemState();
    } catch (err: any) {
      setError(err.message || "Failed to reset Digital Twin.");
    } finally {
      setLoading(false);
    }
  };

  // Autoplay handler for timeline player
  useEffect(() => {
    if (timelinePlaying && activeSimulation) {
      playIntervalRef.current = setInterval(() => {
        setSelectedDay(prev => {
          const maxDays = activeSimulation.timeline.length;
          if (prev >= maxDays - 1) {
            setTimelinePlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500); // Step time step every 1.5s
    } else {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    }
    
    return () => {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    };
  }, [timelinePlaying, activeSimulation]);

  // Compute dynamic nodes reflecting current timeline playback state
  const getDynamicNodes = (): Node[] => {
    if (!activeSimulation || selectedDay >= activeSimulation.timeline.length) {
      return rawNodes;
    }
    
    const daySnapshot = activeSimulation.timeline[selectedDay];
    return rawNodes.map(node => {
      const stateSnapshot = daySnapshot.node_states[node.id];
      if (stateSnapshot) {
        return {
          ...node,
          health: stateSnapshot.health,
          inventory: stateSnapshot.inventory,
          risk_score: stateSnapshot.risk_score,
          replenishment_rate: stateSnapshot.replenishment_rate
        };
      }
      return node;
    });
  };

  // Compute dynamic KPIs reflecting current timeline playback state
  const getDynamicMetrics = (): MetricsResponse => {
    if (!activeSimulation || selectedDay >= activeSimulation.timeline.length) {
      return metrics;
    }
    const dayMetrics = activeSimulation.timeline[selectedDay].metrics;
    return {
      overall_resilience: dayMetrics.resilience_score,
      total_financial_loss: dayMetrics.financial_loss,
      delayed_products_count: dayMetrics.delayed_products,
      disrupted_nodes_count: dayMetrics.disrupted_nodes_count
    };
  };

  return (
    <NexusContext.Provider value={{
      nodes: getDynamicNodes(),
      edges,
      metrics: getDynamicMetrics(),
      events,
      activeEvent,
      activeSimulation,
      activeRecommendation,
      selectedDay,
      timelinePlaying,
      loading,
      error,
      aiStatus,
      
      fetchSystemState,
      ingestNewsAlert,
      selectEvent,
      setSelectedDay,
      setTimelinePlaying,
      applyMitigationAction,
      resetDigitalTwin
    }}>
      {children}
    </NexusContext.Provider>
  );
};

export const useNexus = () => {
  const context = useContext(NexusContext);
  if (context === undefined) {
    throw new Error("useNexus must be used within a NexusProvider");
  }
  return context;
};
