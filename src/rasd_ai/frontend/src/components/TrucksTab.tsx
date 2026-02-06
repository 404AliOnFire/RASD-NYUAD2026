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
    <div className="space-y-4 md:space-y-6">
      <div className="panel p-3 md:p-4">
        <h2 className="text-lg md:text-xl font-bold text-neon-cyan">{t("trucksList")}</h2>
        <p className="text-xs md:text-sm text-slate-400 mt-1">{t("optimizedPlan")}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 md:gap-6">
        {summaries.map((truck, idx) => {
          const route = routes.find((r) => r.truck_id === truck.truckId);
          const highCount = getHighCount(truck.pitIds);

          return (
            <div key={truck.truckId} className="panel p-3 md:p-5">
              {/* Header */}
              <div className="flex items-center justify-between mb-3 md:mb-4">
                <h3 className="text-base md:text-lg font-bold text-neon-cyan">
                  🚛 {truck.truckId.replace("truck_", "الشاحنة ")}
                </h3>
                <div className="text-right">
                  <div className="text-[10px] md:text-xs text-slate-400">{t("highPriorityCount")}</div>
                  <div className="text-xl md:text-2xl font-bold text-red-400">{highCount}</div>
                </div>
              </div>

              {/* Route Steps - Scrollable on mobile */}
              <div className="panel-soft p-3 md:p-4 rounded-lg mb-3 md:mb-4 max-h-40 md:max-h-60 overflow-y-auto">
                <h4 className="text-xs md:text-sm font-semibold mb-2 md:mb-3">{t("routeSteps")}</h4>
                <div className="space-y-1.5 md:space-y-2">
                  {route?.stops.map((stop, i) => {
                    const isDepot = stop === "depot";
                    const priority = !isDepot ? priorityMap.get(stop as number) : null;

                    return (
                      <div key={i} className="flex items-center gap-2 md:gap-3">
                        <span className={`w-5 h-5 md:w-7 md:h-7 rounded-full flex items-center justify-center text-[10px] md:text-xs font-bold flex-shrink-0 ${
                          isDepot ? "bg-purple-600 text-white" : "bg-neon-cyan/20 text-neon-cyan"
                        }`}>
                          {isDepot ? "📍" : i}
                        </span>
                        <div className="flex-1 min-w-0">
                          {isDepot ? (
                            <span className="font-medium text-xs md:text-sm">
                              {i === 0 ? t("startFromDepot") : t("returnToDepot")}
                            </span>
                          ) : (
                            <div className="flex items-center gap-1 md:gap-2 text-xs md:text-sm">
                              <span className={`h-1.5 w-1.5 md:h-2 md:w-2 rounded-full flex-shrink-0 ${tierDot(priority?.tier || "LOW")}`} />
                              <span className="truncate">{t("tank")} #{stop}</span>
                              {priority && (
                                <span className="text-[10px] md:text-xs text-slate-400 flex-shrink-0">
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

              {/* Metrics - 2x2 grid on mobile */}
              <div className="grid grid-cols-4 gap-1 md:gap-2 mb-3 md:mb-4">
                <div className="panel-soft p-1.5 md:p-2 text-center rounded">
                  <div className="text-[10px] md:text-xs text-slate-400">{t("distance")}</div>
                  <div className="font-bold text-sm md:text-base">{truck.distance_km.toFixed(1)}</div>
                  <div className="text-[10px] md:text-xs text-slate-500">{t("km")}</div>
                </div>
                <div className="panel-soft p-1.5 md:p-2 text-center rounded">
                  <div className="text-[10px] md:text-xs text-slate-400">{t("fuel")}</div>
                  <div className="font-bold text-sm md:text-base">{truck.fuel_l.toFixed(1)}</div>
                  <div className="text-[10px] md:text-xs text-slate-500">{t("liters")}</div>
                </div>
                <div className="panel-soft p-1.5 md:p-2 text-center rounded">
                  <div className="text-[10px] md:text-xs text-slate-400">{t("co2")}</div>
                  <div className="font-bold text-sm md:text-base">{truck.co2_kg.toFixed(1)}</div>
                  <div className="text-[10px] md:text-xs text-slate-500">kg</div>
                </div>
                <div className="panel-soft p-1.5 md:p-2 text-center rounded">
                  <div className="text-[10px] md:text-xs text-slate-400">{t("eta")}</div>
                  <div className="font-bold text-sm md:text-base">{Math.round(truck.eta_min)}</div>
                  <div className="text-[10px] md:text-xs text-slate-500">{t("minutes")}</div>
                </div>
              </div>

              {/* Operator Instructions */}
              <div className={`p-2 md:p-3 rounded-lg border ${
                idx === 0 ? "bg-red-500/10 border-red-500/30" : "bg-yellow-500/10 border-yellow-500/30"
              }`}>
                <div className="text-xs md:text-sm font-semibold mb-0.5 md:mb-1">📋 {t("operatorInstructions")}</div>
                <div className="text-xs md:text-sm">
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
        <div className="panel p-6 md:p-8 text-center">
          <div className="text-3xl md:text-4xl mb-3 md:mb-4">🚛</div>
          <div className="text-slate-400 text-sm md:text-base">لا توجد شاحنات نشطة</div>
        </div>
      )}
    </div>
  );
}
