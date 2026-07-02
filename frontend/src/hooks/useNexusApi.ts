import { useMemo } from "react";
import type { 
  GraphResponse, 
  MetricsResponse, 
  RiskEvent, 
  SimulationRun, 
  RecommendationBundle 
} from "../types";

const API_BASE = "http://localhost:8000/api";

export const useNexusApi = () => {
  return useMemo(() => {
    const fetchJson = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
        ...options,
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
      }
      
      return response.json() as Promise<T>;
    };

    return {
      /** Fetch Digital Twin Nodes and Edges */
      getGraphTopology: () => fetchJson<GraphResponse>("/graph/"),

      /** Fetch live dashboard metrics */
      getDashboardMetrics: () => fetchJson<MetricsResponse>("/metrics/"),

      /** List all historical/active events */
      listEvents: () => fetchJson<RiskEvent[]>("/events/"),

      /** Fetch a single event metadata */
      getEvent: (eventId: string) => fetchJson<RiskEvent>(`/events/${eventId}`),

      /** Ingest news to extract and trigger full simulation flow */
      ingestNews: (newsText: string) => 
        fetchJson<RiskEvent>("/events/", {
          method: "POST",
          body: JSON.stringify({ news_text: newsText })
        }),

      /** Get simulation timeline steps for an event */
      getImpactTimeline: (eventId: string) => 
        fetchJson<SimulationRun>(`/events/${eventId}/impact`),

      /** Get optimization scoring and Gemini briefings for an event */
      getRecommendations: (eventId: string) => 
        fetchJson<RecommendationBundle>(`/events/${eventId}/decision`),

      /** Execute a mitigation playbook rerouting action */
      applyMitigation: (eventId: string, optionId: string) => 
        fetchJson<{ status: string; message: string }>(`/events/${eventId}/decision/mitigate`, {
          method: "POST",
          body: JSON.stringify({ option_id: optionId })
        }),

      /** Reset the entire Digital Twin graph back to default baseline */
      resetSystem: () => 
        fetchJson<{ status: string; message: string }>("/events/system/reset", {
          method: "POST"
        }),

      /** Get active AI engine provider state */
      getAiStatus: () => 
        fetchJson<{ provider: string }>("/events/system/ai-status"),

      /** Ask natural language questions about active digital twin state */
      askQuestion: (question: string) => 
        fetchJson<{ answer: string }>("/events/system/ask", {
          method: "POST",
          body: JSON.stringify({ question })
        })
    };
  }, []);
};
