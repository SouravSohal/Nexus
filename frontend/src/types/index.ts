export type NodeType = "SUPPLIER" | "PORT" | "WAREHOUSE" | "FACTORY" | "DISTRIBUTION_CENTER" | "PRODUCT";
export type EdgeType = "SUPPLIES" | "SHIPS_TO" | "DEPENDS_ON" | "MANUFACTURES";
export type EventStatus = "DRAFTED" | "COMMITTED" | "ACTIVE" | "RESOLVED";

export interface Node {
  id: string;
  name: string;
  type: NodeType;
  location: string;
  latitude: number;
  longitude: number;
  base_cost: number;
  capacity: number;
  health: number;
  risk_score: number;
  inventory: number;
  safety_stock: number;
  daily_consumption: number;
  replenishment_rate: number;
  metadata: Record<string, any>;
}

export interface Edge {
  source: string;
  target: string;
  type: EdgeType;
  dependency_ratio: number;
  lead_time_days: number;
  transport_mode: string;
}

export interface RiskEvent {
  id: string;
  title: string;
  description: string;
  location: string;
  affected_node_id: string;
  severity: number;
  duration_days: number;
  confidence_score: number;
  status: EventStatus;
  created_at: string;
}

export interface NodeState {
  health: number;
  inventory: number;
  risk_score: number;
  replenishment_rate: number;
}

export interface StepMetrics {
  resilience_score: number;
  financial_loss: number;
  delayed_products: number;
  disrupted_nodes_count: number;
}

export interface TemporalStep {
  day: number;
  metrics: StepMetrics;
  node_states: Record<string, NodeState>;
}

export interface SimulationRun {
  id: string;
  event_id: string;
  timeline: TemporalStep[];
  created_at: string;
}

export interface MitigationOption {
  option_id: string;
  title: string;
  description: string;
  cost_impact: number;
  lead_time_surcharge_days: number;
  feasibility_score: number;
  calculated_score: number;
  is_recommended: boolean;
}

export interface CompositeConfidence {
  extraction: number;
  simulation: number;
  optimization: number;
  overall: number;
}

export interface DoNothingImpact {
  earliest_stockout_day: number;
  total_financial_loss: number;
  delayed_products_count: number;
}

export interface RecommendationBundle {
  id: string;
  event_id: string;
  do_nothing_impact: DoNothingImpact;
  options: MitigationOption[];
  composite_confidence: CompositeConfidence;
  gemini_explanation: string;
  created_at: string;
}

export interface GraphResponse {
  nodes: Node[];
  edges: Edge[];
}

export interface MetricsResponse {
  overall_resilience: number;
  total_financial_loss: number;
  delayed_products_count: number;
  disrupted_nodes_count: number;
}

export interface SystemStatusResponse {
  status: string;
  service: string;
  time: number;
}
