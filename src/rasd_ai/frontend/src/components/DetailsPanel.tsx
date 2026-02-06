import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PriorityRecord, RouteSummary } from "../types";

interface DetailsPanelProps {
  selectedPit: PriorityRecord | null;
  selectedTruck: RouteSummary | null;
  visualOverride?: { level_pct: number; tier: string; priority: number; tto_hours: number } | null;
  t: (key: string) => string;
}

function tierBg(tier: string) {
  if (tier === "HIGH") return "bg-red-500/20 border-red-500";
  if (tier === "MEDIUM") return "bg-yellow-500/20 border-yellow-500";
  return "bg-green-500/20 border-green-500";
}

export default function DetailsPanel({ selectedPit, selectedTruck, visualOverride, t }: DetailsPanelProps) {
  // Use visual override values if available (for serviced pits)
  const displayLevel = visualOverride?.level_pct ?? selectedPit?.level_pct ?? 0;
  const displayTier = visualOverride?.tier ?? selectedPit?.tier ?? "LOW";
  const displayPriority = visualOverride?.priority ?? selectedPit?.priority ?? 0;
  const displayTto = visualOverride?.tto_hours ?? selectedPit?.tto_hours ?? 0;
  const isServiced = visualOverride !== null && visualOverride !== undefined;

  return (
    <div className="panel p-3 md:p-4 h-full max-h-[85vh] md:max-h-[85vh] overflow-auto">
      <h3 className="text-xs md:text-sm text-slate-300 uppercase font-semibold hidden xl:block">{t("details")}</h3>

      {!selectedPit && !selectedTruck && (
        <div className="mt-4 md:mt-8 text-center py-4 md:py-8">
          <div className="text-3xl md:text-4xl mb-2 md:mb-4">📍</div>
          <div className="text-slate-400 text-xs md:text-sm">{t("selectHint")}</div>
        </div>
      )}

      {selectedPit && (
        <div className="mt-2 md:mt-4 space-y-3 md:space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between gap-2">
            <div className="text-lg md:text-xl font-bold">خزان #{selectedPit.tank_id}</div>
            <span className={`px-2 md:px-3 py-0.5 md:py-1 rounded border text-xs md:text-sm font-bold ${tierBg(displayTier)}`}>
              {displayTier === "HIGH" ? t("tierHigh") : displayTier === "MEDIUM" ? t("tierMedium") : t("tierLow")}
            </span>
          </div>

          {/* Serviced Badge */}
          {isServiced && (
            <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-2 md:p-3 text-center">
              <span className="text-green-400 font-bold text-sm md:text-base">✅ تم التفريغ</span>
            </div>
          )}

          {/* Fill Level */}
          <div className="panel-soft p-4 rounded-lg">
            <div className="text-xs text-slate-400 uppercase">{t("fillLevel")}</div>
            <div className="flex items-end gap-2 mt-1">
              <span className="text-4xl font-bold text-neon-cyan">{displayLevel}</span>
              <span className="text-xl text-slate-400 mb-1">%</span>
            </div>
            <div className="mt-3 h-3 bg-panel rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  displayLevel >= 80 ? 'bg-red-500' : displayLevel >= 50 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(displayLevel, 100)}%` }}
              />
            </div>
          </div>

          {/* TTO and Priority */}
          <div className="grid grid-cols-2 gap-3">
            <div className="panel-soft p-3 rounded-lg text-center">
              <div className="text-xs text-slate-400">{t("timeToOverflow")}</div>
              <div className={`text-2xl font-bold ${displayTto <= 24 ? 'text-red-400' : isServiced ? 'text-green-400' : 'text-slate-200'}`}>
                {Math.round(displayTto)} {t("hours")}
              </div>
              {isServiced && <div className="text-xs text-green-400">+{Math.round(displayTto - selectedPit.tto_hours)}h</div>}
            </div>
            <div className="panel-soft p-3 rounded-lg text-center">
              <div className="text-xs text-slate-400">{t("priority")}</div>
              <div className={`text-2xl font-bold ${isServiced ? 'text-green-400' : 'text-neon-cyan'}`}>{displayPriority.toFixed(2)}</div>
              {isServiced && <div className="text-xs text-green-400">↓ {((1 - displayPriority / selectedPit.priority) * 100).toFixed(0)}%</div>}
            </div>
          </div>

          {/* Sensor Readings */}
          <div className="panel-soft p-4 rounded-lg">
            <div className="text-xs text-slate-400 uppercase mb-3">{t("sensorReadings")}</div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-xs text-slate-500">{t("gasLevel")}</div>
                <div className="font-bold">{selectedPit.gas_now}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">{t("temperature")}</div>
                <div className="font-bold">{selectedPit.temp_c}°C</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">{t("humidity")}</div>
                <div className="font-bold">{selectedPit.hum_pct}%</div>
              </div>
            </div>
          </div>

          {/* Risk Chart */}
          <div className="panel-soft p-4 rounded-lg">
            <div className="text-xs text-slate-400 uppercase mb-2">{t("riskBreakdown")}</div>
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { name: "أساسي", value: selectedPit.base },
                  { name: "غاز", value: selectedPit.gas_anom },
                  { name: "بيئي", value: selectedPit.env_anom }
                ]}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip contentStyle={{ backgroundColor: "#0b1020", border: "1px solid #1b2342" }} />
                  <Bar dataKey="value" fill="#00f0ff" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {selectedTruck && (
        <div className="mt-4 space-y-4">
          <div className="text-xl font-bold">{selectedTruck.truckId.replace("truck_", "الشاحنة ")}</div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="panel-soft p-3 rounded-lg text-center">
              <div className="text-xs text-slate-400">{t("stops")}</div>
              <div className="text-2xl font-bold">{selectedTruck.stopsCount}</div>
            </div>
            <div className="panel-soft p-3 rounded-lg text-center">
              <div className="text-xs text-slate-400">{t("distance")}</div>
              <div className="text-2xl font-bold">{selectedTruck.distance_km.toFixed(1)} {t("km")}</div>
            </div>
            <div className="panel-soft p-3 rounded-lg text-center">
              <div className="text-xs text-slate-400">{t("fuel")}</div>
              <div className="text-2xl font-bold">{selectedTruck.fuel_l.toFixed(1)} {t("liters")}</div>
            </div>
            <div className="panel-soft p-3 rounded-lg text-center">
              <div className="text-xs text-slate-400">{t("eta")}</div>
              <div className="text-2xl font-bold">{Math.round(selectedTruck.eta_min)} {t("minutes")}</div>
            </div>
          </div>

          {/* Route */}
          <div className="panel-soft p-4 rounded-lg">
            <div className="text-xs text-slate-400 uppercase mb-2">{t("routeSteps")}</div>
            <div className="text-sm space-y-1">
              {selectedTruck.stops.map((stop, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-neon-cyan/20 text-neon-cyan text-xs flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <span>{stop === "depot" ? t("depot") : `${t("tank")} #${stop}`}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
