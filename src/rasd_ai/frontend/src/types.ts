export type NodeId = number | "depot";

export interface NodeRecord {
  node_id: NodeId;
  lat: number;
  lon: number;
  zone: string;
}

export interface PriorityRecord {
  tank_id: number;
  tier: "HIGH" | "MEDIUM" | "LOW" | string;
  priority: number;
  tto_hours: number;
  level_pct: number;
  gas_now: number;
  temp_c: number;
  hum_pct: number;
  base: number;
  gas_anom: number;
  env_anom: number;
  profile: string;
}

export interface MetricsRecord {
  total_distance_km?: number;
  served_total?: number;
  high_served?: number;
  high_total?: number;
  medium_served?: number;
  medium_total?: number;
  low_served?: number;
  low_total?: number;
  fuel_l_est?: number;
  co2_kg_est?: number;
  solver_used?: string;
  [key: string]: unknown;
}

// Route from routes_for_frontend.json
export interface RouteData {
  truck_id: string;
  stops: (string | number)[];
  polyline: [number, number][];
}

// Full routes_for_frontend.json structure
export interface RoutesForFrontend {
  depot: { id: string; lat: number; lon: number };
  pits: Array<{ id: number; lat: number; lon: number; tier: string; priority: number }>;

  routes: {
    baseline: RouteData[];
    quantum: RouteData[];
  };
}

export interface RouteSummary {
  truckId: string;
  stops: (string | number)[];
  polyline: [number, number][];
  pitIds: number[];
  stopsCount: number;
  distance_km: number;
  fuel_l: number;
  co2_kg: number;
  fuel_cost_usd: number;
  eta_min: number;
}

export interface ClosureRecord {
  from: number;
  to: number;
}

export interface LoadedData {
  nodes: NodeRecord[];
  priorities: PriorityRecord[];
  routesForFrontend: RoutesForFrontend | null;
  quantumMetrics: MetricsRecord;
  closures: ClosureRecord[];
  toastMessages: string[];
}
