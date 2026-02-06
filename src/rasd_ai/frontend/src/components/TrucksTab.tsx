import { useMemo } from "react";
import { RouteData, RouteSummary, PriorityRecord } from "../types";

interface TrucksTabProps {
  routes: RouteData[];
  summaries: RouteSummary[];
  priorities: PriorityRecord[];
  t: (key: string) => string;
}

function tierDot(tier: string) {
  if (tier === "HIGH") return "bg-red-500";
  if (tier === "MEDIUM") return "bg-yellow-400";
  return "bg-green-500";
}

export default function TrucksTab({ routes, summaries, priorities, t }: TrucksTabProps) {
  const priorityMap = useMemo(() => {
    const map = new Map<number, PriorityRecord>();
    priorities.forEach((p) => map.set(p.tank_id, p));
    return map;
  }, [priorities]);

  const getHighCount = (pitIds: number[]) => {
    return pitIds.filter((id) => priorityMap.get(id)?.tier === "HIGH").length;
  };

  return (
    <div className="space-y-6">
      <div className="panel p-4">
        <h2 className="text-xl font-bold text-neon-cyan">{t("trucksList")}</h2>
        <p className="text-sm text-slate-400 mt-1">{t("optimizedPlan")}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {summaries.map((truck, idx) => {
          const route = routes.find((r) => r.truck_id === truck.truckId);
          const highCount = getHighCount(truck.pitIds);

          return (
            <div key={truck.truckId} className="panel p-5">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-neon-cyan">
                  🚛 {truck.truckId.replace("truck_", "الشاحنة ")}
                </h3>
                <div className="text-right">
                  <div className="text-xs text-slate-400">{t("highPriorityCount")}</div>
                  <div className="text-2xl font-bold text-red-400">{highCount}</div>
                </div>
              </div>

              {/* Route Steps */}
              <div className="panel-soft p-4 rounded-lg mb-4">
                <h4 className="text-sm font-semibold mb-3">{t("routeSteps")}</h4>
                <div className="space-y-2">
                  {route?.stops.map((stop, i) => {
                    const isDepot = stop === "depot";
                    const priority = !isDepot ? priorityMap.get(stop as number) : null;

                    return (
                      <div key={i} className="flex items-center gap-3">
                        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                          isDepot ? "bg-purple-600 text-white" : "bg-neon-cyan/20 text-neon-cyan"
                        }`}>
                          {isDepot ? "📍" : i}
                        </span>
                        <div className="flex-1">
                          {isDepot ? (
                            <span className="font-medium">
                              {i === 0 ? t("startFromDepot") : t("returnToDepot")}
                            </span>
                          ) : (
                            <div className="flex items-center gap-2">
                              <span className={`h-2 w-2 rounded-full ${tierDot(priority?.tier || "LOW")}`} />
                              <span>{t("tank")} #{stop}</span>
                              {priority && (
                                <span className="text-xs text-slate-400">
                                  ({priority.level_pct}%)
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-4 gap-2 mb-4">
                <div className="panel-soft p-2 text-center rounded">
                  <div className="text-xs text-slate-400">{t("distance")}</div>
                  <div className="font-bold">{truck.distance_km.toFixed(1)}</div>
                  <div className="text-xs text-slate-500">{t("km")}</div>
                </div>
                <div className="panel-soft p-2 text-center rounded">
                  <div className="text-xs text-slate-400">{t("fuel")}</div>
                  <div className="font-bold">{truck.fuel_l.toFixed(1)}</div>
                  <div className="text-xs text-slate-500">{t("liters")}</div>
                </div>
                <div className="panel-soft p-2 text-center rounded">
                  <div className="text-xs text-slate-400">{t("co2")}</div>
                  <div className="font-bold">{truck.co2_kg.toFixed(1)}</div>
                  <div className="text-xs text-slate-500">kg</div>
                </div>
                <div className="panel-soft p-2 text-center rounded">
                  <div className="text-xs text-slate-400">{t("eta")}</div>
                  <div className="font-bold">{Math.round(truck.eta_min)}</div>
                  <div className="text-xs text-slate-500">{t("minutes")}</div>
                </div>
              </div>

              {/* Operator Instructions */}
              <div className={`p-3 rounded-lg border ${
                idx === 0 ? "bg-red-500/10 border-red-500/30" : "bg-yellow-500/10 border-yellow-500/30"
              }`}>
                <div className="text-sm font-semibold mb-1">📋 {t("operatorInstructions")}</div>
                <div className="text-sm">
                  {idx === 0 ? (
                    <span className="text-red-400">{t("startImmediately")}</span>
                  ) : (
                    <span className="text-yellow-400">{t("afterTruck")}</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {summaries.length === 0 && (
        <div className="panel p-8 text-center">
          <div className="text-4xl mb-4">🚛</div>
          <div className="text-slate-400">لا توجد شاحنات نشطة</div>
        </div>
      )}
    </div>
  );
}
