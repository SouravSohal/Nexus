import { useMemo } from "react";
import type {
  GraphResponse,
  MetricsResponse,
  RiskEvent,
  SimulationRun,
  RecommendationBundle
} from "../types";

const API_BASE = (
  import.meta.env.VITE_API_URL ||
  "https://nexus-api-357869022312.asia-south1.run.app"
).replace(/\/$/, "");

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
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return response.json() as Promise<T>;
    };

    return {
      /** Digital Twin Graph */
      getGraphTopology: () =>
        fetchJson<GraphResponse>("/api/graph/"),

      /** Dashboard KPIs */
      getDashboardMetrics: () =>
        fetchJson<MetricsResponse>("/api/metrics/"),

      /** All Risk Events */
      listEvents: () =>
        fetchJson<RiskEvent[]>("/api/events/"),

      /** Single Event */
      getEvent: (eventId: string) =>
        fetchJson<RiskEvent>(`/api/events/${eventId}`),

      /** Ingest News */
      ingestNews: (newsText: string) =>
        fetchJson<RiskEvent>("/api/events/", {
          method: "POST",
          body: JSON.stringify({
            news_text: newsText,
          }),
        }),

      /** Simulation Timeline */
      getImpactTimeline: (eventId: string) =>
        fetchJson<SimulationRun>(`/api/events/${eventId}/impact`),

      /** Recommendations */
      getRecommendations: (eventId: string) =>
        fetchJson<RecommendationBundle>(`/api/events/${eventId}/decision`),

      /** Apply Mitigation */
      applyMitigation: (eventId: string, optionId: string) =>
        fetchJson<{ status: string; message: string }>(
          `/api/events/${eventId}/decision/mitigate`,
          {
            method: "POST",
            body: JSON.stringify({
              option_id: optionId,
            }),
          }
        ),

      /** Reset System */
      resetSystem: () =>
        fetchJson<{ status: string; message: string }>(
          "/api/events/system/reset",
          {
            method: "POST",
          }
        ),

      /** AI Provider Status */
      getAiStatus: () =>
        fetchJson<{ provider: string }>(
          "/api/events/system/ai-status"
        ),

      /** Ask NEXUS */
      askQuestion: (question: string) =>
        fetchJson<{ answer: string }>(
          "/api/events/system/ask",
          {
            method: "POST",
            body: JSON.stringify({
              question,
            }),
          }
        ),
    };
  }, []);
};