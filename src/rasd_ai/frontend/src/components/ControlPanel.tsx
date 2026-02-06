import { useMemo } from "react";
import { MetricsRecord, PriorityRecord, RouteSummary } from "../types";

interface ControlPanelProps {
  metrics: MetricsRecord;
  toggles: {
    pits: boolean;
    routes: boolean;
    closures: boolean;
    heatmap: boolean;
  };
  setToggles: (t: ControlPanelProps["toggles"]) => void;
  speed: number;
  setSpeed: (s: number) => void;
  priorities: PriorityRecord[];
  summaries: RouteSummary[];
  focusTruckId: string | null;
  setFocusTruckId: (id: string | null) => void;
  servicedPitsCount?: number;
  t: (key: string) => string;
}

function tierDot(tier: string) {
  if (tier === "HIGH") return "bg-red-500";
  if (tier === "MEDIUM") return "bg-yellow-400";
  return "bg-green-500";
}

export default function ControlPanel({
  metrics,
  toggles,
  setToggles,
  speed,
  setSpeed,
  priorities,
  summaries,
  focusTruckId,
  setFocusTruckId,
  servicedPitsCount = 0,
  t
}: ControlPanelProps) {
  // KPI tiles - include serviced count
  const tiles = [
    { label: t("totalDistance"), value: `${(metrics.total_distance_km ?? 0).toFixed(1)} ${t("km")}` },
    { label: t("servedTotal"), value: `${servicedPitsCount}/${metrics.served_total ?? 0}`, highlight: servicedPitsCount > 0 },
    { label: t("highServed"), value: `${metrics.high_served ?? 0}/${metrics.high_total ?? 0}` },
    { label: t("fuelEstimate"), value: `${(metrics.fuel_l_est ?? 0).toFixed(1)} ${t("liters")}` },
    { label: t("co2Estimate"), value: `${(metrics.co2_kg_est ?? 0).toFixed(1)} kg` }
  ];

  // Critical alerts
  const criticalCount = priorities.filter((p) => p.tier === "HIGH" && p.tto_hours <= 24).length;
  const totalAlerts = priorities.filter((p) => p.tier === "HIGH" || p.tier === "MEDIUM").length;

  // Top tanks by priority
  const topTanks = useMemo(
    () => [...priorities].sort((a, b) => b.priority - a.priority).slice(0, 8),
    [priorities]
  );

  return (
    <div className="flex flex-col gap-4 max-h-[85vh] overflow-auto">
      {/* Status Cards */}
      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase font-semibold mb-3">{t("optimizedPlan")}</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="panel-soft p-3 text-center">
            <div className="text-xs text-slate-400">{t("activeTrucks")}</div>
            <div className="text-2xl font-bold text-neon-cyan">{summaries.length}</div>
          </div>
          <div className="panel-soft p-3 text-center">
            <div className="text-xs text-slate-400">{t("tanksMonitored")}</div>
            <div className="text-2xl font-bold text-neon-cyan">{priorities.length}</div>
          </div>
          <div className="panel-soft p-3 text-center">
            <div className="text-xs text-slate-400">{t("criticalAlerts")}</div>
            <div className="text-2xl font-bold text-red-400">{criticalCount}</div>
          </div>
          <div className={`panel-soft p-3 text-center ${servicedPitsCount > 0 ? 'border border-green-500/50 bg-green-500/10' : ''}`}>
            <div className="text-xs text-slate-400">{t("servicedTanks")}</div>
            <div className={`text-2xl font-bold ${servicedPitsCount > 0 ? 'text-green-400' : 'text-slate-400'}`}>{servicedPitsCount}</div>
          </div>
        </div>
      </div>

      {/* KPI Summary */}
      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase font-semibold mb-3">{t("kpiSummary")}</h3>
        <div className="space-y-2">
          {tiles.map((tile) => (
            <div key={tile.label} className={`flex justify-between items-center panel-soft p-2 rounded ${(tile as any).highlight ? 'border border-green-500/50' : ''}`}>
              <span className="text-xs text-slate-400">{tile.label}</span>
              <span className={`font-semibold ${(tile as any).highlight ? 'text-green-400' : 'text-neon-cyan'}`}>{tile.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Map Controls */}
      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase font-semibold mb-3">{t("mapLayers")}</h3>
        <div className="space-y-2">
          {([
            ["pits", t("showTanks")],
            ["routes", t("showRoutes")],
            ["heatmap", t("showHeatmap")]
          ] as const).map(([key, label]) => (
            <label key={key} className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={toggles[key]}
                onChange={(e) => setToggles({ ...toggles, [key]: e.target.checked })}
                className="accent-neon-cyan w-4 h-4"
              />
              <span className="text-sm">{label}</span>
            </label>
          ))}
        </div>
        <div className="mt-4">
          <div className="text-xs text-slate-400 mb-1">{t("animationSpeed")}</div>
          <input
            type="range"
            min={0.25}
            max={2}
            step={0.25}
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
            className="w-full accent-neon-cyan"
          />
          <div className="text-xs text-slate-400 text-center">{speed.toFixed(2)}x</div>
        </div>
      </div>

      {/* Priority Tanks */}
      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase font-semibold mb-3">{t("tanksList")}</h3>
        <div className="space-y-2 max-h-48 overflow-auto">
          {topTanks.map((tank) => (
            <div key={tank.tank_id} className="flex items-center justify-between panel-soft p-2 rounded text-sm">
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${tierDot(tank.tier)}`} />
                <span>#{tank.tank_id}</span>
              </div>
              <span className="text-slate-400">{tank.level_pct}%</span>
              <span className="text-slate-400">{tank.tto_hours}{t("hours")}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Trucks List */}
      <div className="panel p-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm text-slate-300 uppercase font-semibold">{t("trucksList")}</h3>
          {focusTruckId && (
            <button
              type="button"
              className="text-xs text-neon-cyan hover:underline"
              onClick={() => setFocusTruckId(null)}
            >
              {t("clearFocus")}
            </button>
          )}
        </div>
        <div className="space-y-2">
          {summaries.map((truck) => (
            <button
              key={truck.truckId}
              type="button"
              onClick={() => setFocusTruckId(truck.truckId === focusTruckId ? null : truck.truckId)}
              className={`w-full text-right panel-soft p-2 rounded transition ${
                focusTruckId === truck.truckId ? "border-neon-cyan text-neon-cyan" : ""
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-medium">{truck.truckId.replace("_", " ")}</span>
                <span className="text-xs text-slate-400">{truck.stopsCount} {t("stops")}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>{truck.distance_km.toFixed(1)} {t("km")}</span>
                <span>{truck.fuel_l.toFixed(1)} {t("liters")}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
