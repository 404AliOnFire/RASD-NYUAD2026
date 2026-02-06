import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { MetricsRecord, RouteSummary } from "../types";

interface CompareTabProps {
  baselineMetrics: MetricsRecord;
  quantumMetrics: MetricsRecord;
  baselineSummaries: RouteSummary[];
  quantumSummaries: RouteSummary[];
  t: (key: string) => string;
}

export default function CompareTab({
  baselineMetrics,
  quantumMetrics,
  baselineSummaries,
  quantumSummaries,
  t
}: CompareTabProps) {
  const tierData = [
    {
      tier: "HIGH",
      baseline: baselineMetrics.high_served ?? 0,
      quantum: quantumMetrics.high_served ?? 0
    },
    {
      tier: "MEDIUM",
      baseline: baselineMetrics.medium_served ?? 0,
      quantum: quantumMetrics.medium_served ?? 0
    },
    {
      tier: "LOW",
      baseline: baselineMetrics.low_served ?? 0,
      quantum: quantumMetrics.low_served ?? 0
    }
  ];

  const distanceData = [
    {
      name: t("distance"),
      baseline: baselineMetrics.total_distance_km ?? 0,
      quantum: quantumMetrics.total_distance_km ?? 0
    }
  ];

  const workloadData = [
    {
      name: t("trendBaseline"),
      stops: baselineSummaries.reduce((acc, s) => acc + s.stops, 0)
    },
    {
      name: t("trendQuantum"),
      stops: quantumSummaries.reduce((acc, s) => acc + s.stops, 0)
    }
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase">{t("compare")}</h3>
        <div className="mt-2 text-sm">{t("trendBaseline")} {t("distance")}: {baselineMetrics.total_distance_km ?? "-"}</div>
        <div className="text-sm">{t("trendQuantum")} {t("distance")}: {quantumMetrics.total_distance_km ?? "-"}</div>
        <div className="mt-2 text-sm">{t("trendBaseline")} {t("fuel")}: {baselineMetrics.fuel_l_est ?? "-"}</div>
        <div className="text-sm">{t("trendQuantum")} {t("fuel")}: {quantumMetrics.fuel_l_est ?? "-"}</div>
        <div className="mt-2 text-sm">
          {t("solverUsed")}: {(quantumMetrics.solver_used as string) ?? "ocean_simulated_annealing (simulation)"}
        </div>
      </div>

      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase">{t("distanceCompare")}</h3>
        <div className="mt-4 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={distanceData}>
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="baseline" fill="#00f0ff" />
              <Bar dataKey="quantum" fill="#a855f7" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase">{t("tierCoverage")}</h3>
        <div className="mt-4 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={tierData}>
              <XAxis dataKey="tier" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="baseline" fill="#00f0ff" />
              <Bar dataKey="quantum" fill="#a855f7" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel p-4 lg:col-span-3">
        <h3 className="text-sm text-slate-300 uppercase">{t("workload")}</h3>
        <div className="mt-3 h-40">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={workloadData}>
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="stops" fill="#ff4fd8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
