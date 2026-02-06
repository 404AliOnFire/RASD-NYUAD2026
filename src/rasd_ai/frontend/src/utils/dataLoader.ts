import Papa from "papaparse";
import {
  ClosureRecord,
  LoadedData,
  MetricsRecord,
  NodeRecord,
  PriorityRecord,
  RoutesForFrontend
} from "../types";

const DATA_ROOT = "/data";

// Mock data for fallback
const mockNodes: NodeRecord[] = [
  { node_id: "depot", lat: 31.53, lon: 35.095, zone: "center" },
  { node_id: 2, lat: 31.5375, lon: 35.0736, zone: "center" }
];

const mockPriorities: PriorityRecord[] = [
  {
    tank_id: 2,
    tier: "HIGH",
    priority: 0.92,
    tto_hours: 6,
    level_pct: 78,
    gas_now: 48,
    temp_c: 27,
    hum_pct: 40,
    base: 0.4,
    gas_anom: 0.4,
    env_anom: 0.12,
    profile: "baseline"
  }
];

const mockMetrics: MetricsRecord = {
  total_distance_km: 45.2,
  served_total: 10,
  high_served: 6,
  high_total: 8,
  medium_served: 2,
  medium_total: 2,
  low_served: 2,
  low_total: 10,
  fuel_l_est: 15.8,
  co2_kg_est: 42.4
};

const mockClosures: ClosureRecord[] = [
  { from: 6, to: 10 },
  { from: 1, to: 4 }
];

async function fetchJson<T>(path: string, toast: string[]): Promise<T | null> {
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    console.log(`[RASD] ✓ Loaded ${path}`);
    return data as T;
  } catch (err) {
    console.warn(`[RASD] ✗ Failed to load ${path}:`, err);
    toast.push(`تعذر تحميل ${path}`);
    return null;
  }
}

async function fetchCsv<T>(path: string, toast: string[]): Promise<T[] | null> {
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const text = await res.text();
    return new Promise<T[]>((resolve) => {
      Papa.parse<T>(text, {
        header: true,
        dynamicTyping: true,
        complete: (results) => {
          const data = results.data.filter((row) => row && Object.keys(row).length > 1);
          console.log(`[RASD] ✓ Loaded ${path}: ${data.length} rows`);
          resolve(data);
        }
      });
    });
  } catch (err) {
    console.warn(`[RASD] ✗ Failed to load ${path}:`, err);
    toast.push(`تعذر تحميل ${path}`);
    return null;
  }
}

export async function loadAllData(): Promise<LoadedData> {
  const toastMessages: string[] = [];

  console.log("[RASD] === بدء تحميل البيانات ===");

  const [nodes, priorities, routesForFrontend, quantumMetrics, closures] = await Promise.all([
    fetchJson<NodeRecord[]>(`${DATA_ROOT}/nodes.json`, toastMessages),
    fetchCsv<PriorityRecord>(`${DATA_ROOT}/priorities.csv`, toastMessages),
    fetchJson<RoutesForFrontend>(`${DATA_ROOT}/routes_for_frontend.json`, toastMessages),
    fetchJson<MetricsRecord>(`${DATA_ROOT}/quantum_metrics_enriched.json`, toastMessages),
    fetchJson<ClosureRecord[]>(`${DATA_ROOT}/closures.json`, toastMessages)
  ]);

  // Log loading status
  console.log("[RASD] === ملخص التحميل ===");
  console.log(`  - العقد (nodes): ${nodes?.length ?? 0}`);
  console.log(`  - الأولويات (priorities): ${priorities?.length ?? 0}`);
  console.log(`  - المسارات: ${routesForFrontend?.routes?.quantum?.length ?? 0} شاحنات`);
  console.log(`  - الإغلاقات: ${closures?.length ?? 0}`);

  // Validate routes data
  if (routesForFrontend?.routes?.quantum) {
    routesForFrontend.routes.quantum.forEach((route) => {
      console.log(`  - ${route.truck_id}: ${route.stops.length} محطات, ${route.polyline.length} نقاط`);
    });
  }

  return {
    nodes: nodes ?? mockNodes,
    priorities: priorities ?? mockPriorities,
    routesForFrontend: routesForFrontend ?? null,
    quantumMetrics: quantumMetrics ?? mockMetrics,
    closures: closures ?? mockClosures,
    toastMessages
  };
}
