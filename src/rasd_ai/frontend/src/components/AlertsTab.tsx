import { useMemo } from "react";
import { PriorityRecord } from "../types";

interface AlertsTabProps {
  priorities: PriorityRecord[];
  t: (key: string) => string;
}

function tierDot(tier: string) {
  if (tier === "HIGH") return "bg-red-500";
  if (tier === "MEDIUM") return "bg-yellow-400";
  return "bg-green-500";
}

export default function AlertsTab({ priorities, t }: AlertsTabProps) {
  // Critical alerts
  const urgentAlerts = useMemo(() => {
    return priorities
      .filter((p) => p.tto_hours <= 12)
      .sort((a, b) => a.tto_hours - b.tto_hours);
  }, [priorities]);

  const warningAlerts = useMemo(() => {
    return priorities
      .filter((p) => p.tto_hours > 12 && p.tto_hours <= 24)
      .sort((a, b) => a.tto_hours - b.tto_hours);
  }, [priorities]);

  const highRiskAlerts = useMemo(() => {
    return priorities
      .filter((p) => p.tier === "HIGH" && p.tto_hours > 24)
      .sort((a, b) => b.priority - a.priority);
  }, [priorities]);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="panel p-5 border-red-500/30">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-red-500/20 rounded-full flex items-center justify-center">
              <span className="text-3xl">🚨</span>
            </div>
            <div>
              <div className="text-sm text-slate-400">{t("urgentAlerts")}</div>
              <div className="text-3xl font-bold text-red-400">{urgentAlerts.length}</div>
            </div>
          </div>
        </div>

        <div className="panel p-5 border-yellow-500/30">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-yellow-500/20 rounded-full flex items-center justify-center">
              <span className="text-3xl">⚠️</span>
            </div>
            <div>
              <div className="text-sm text-slate-400">{t("warningAlerts")}</div>
              <div className="text-3xl font-bold text-yellow-400">{warningAlerts.length}</div>
            </div>
          </div>
        </div>

        <div className="panel p-5 border-orange-500/30">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-orange-500/20 rounded-full flex items-center justify-center">
              <span className="text-3xl">📊</span>
            </div>
            <div>
              <div className="text-sm text-slate-400">{t("highServed")}</div>
              <div className="text-3xl font-bold text-orange-400">{highRiskAlerts.length}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="panel p-4">
        <h3 className="text-lg font-bold text-neon-cyan mb-4">{t("alertsTitle")}</h3>

        {urgentAlerts.length === 0 && warningAlerts.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-5xl mb-4">✅</div>
            <div className="text-slate-400 text-lg">{t("noAlerts")}</div>
          </div>
        ) : (
          <div className="space-y-3 max-h-[60vh] overflow-auto">
            {/* Urgent */}
            {urgentAlerts.map((alert) => (
              <div
                key={alert.tank_id}
                className="flex items-center justify-between p-4 rounded-lg bg-red-500/10 border border-red-500/30"
              >
                <div className="flex items-center gap-4">
                  <span className={`h-3 w-3 rounded-full ${tierDot(alert.tier)} animate-pulse`} />
                  <div>
                    <div className="font-bold">خزان #{alert.tank_id}</div>
                    <div className="text-xs text-slate-400">
                      {alert.level_pct}% ممتلئ
                    </div>
                  </div>
                </div>
                <div className="text-left">
                  <div className="text-2xl font-bold text-red-400">{alert.tto_hours} {t("hours")}</div>
                  <div className="text-xs text-slate-400">{t("timeToOverflow")}</div>
                </div>
              </div>
            ))}

            {/* Warning */}
            {warningAlerts.map((alert) => (
              <div
                key={alert.tank_id}
                className="flex items-center justify-between p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30"
              >
                <div className="flex items-center gap-4">
                  <span className={`h-3 w-3 rounded-full ${tierDot(alert.tier)}`} />
                  <div>
                    <div className="font-bold">خزان #{alert.tank_id}</div>
                    <div className="text-xs text-slate-400">
                      {alert.level_pct}% ممتلئ
                    </div>
                  </div>
                </div>
                <div className="text-left">
                  <div className="text-2xl font-bold text-yellow-400">{alert.tto_hours} {t("hours")}</div>
                  <div className="text-xs text-slate-400">{t("timeToOverflow")}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
