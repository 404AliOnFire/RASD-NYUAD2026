import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";
import { PriorityRecord, RouteSummary, MetricsRecord } from "../types";

interface StatsTabProps {
  priorities: PriorityRecord[];
  summaries: RouteSummary[];
  metrics: MetricsRecord;
  t: (key: string) => string;
}

const COLORS = {
  high: "#ef4444",
  medium: "#facc15",
  low: "#22c55e",
  primary: "#00f0ff",
  secondary: "#a855f7",
  accent: "#ff4fd8",
};

export default function StatsTab({ priorities, summaries, metrics, t }: StatsTabProps) {
  // Tier distribution data
  const tierData = useMemo(() => {
    const high = priorities.filter((p) => p.tier === "HIGH").length;
    const medium = priorities.filter((p) => p.tier === "MEDIUM").length;
    const low = priorities.filter((p) => p.tier === "LOW").length;
    return [
      { name: t("tierHigh"), value: high, color: COLORS.high },
      { name: t("tierMedium"), value: medium, color: COLORS.medium },
      { name: t("tierLow"), value: low, color: COLORS.low },
    ];
  }, [priorities, t]);

  // Level distribution data
  const levelDistribution = useMemo(() => {
    const ranges = [
      { range: "0-20%", min: 0, max: 20, count: 0 },
      { range: "20-40%", min: 20, max: 40, count: 0 },
      { range: "40-60%", min: 40, max: 60, count: 0 },
      { range: "60-80%", min: 60, max: 80, count: 0 },
      { range: "80-100%", min: 80, max: 100, count: 0 },
    ];
    priorities.forEach((p) => {
      const range = ranges.find((r) => p.level_pct >= r.min && p.level_pct < r.max);
      if (range) range.count++;
      else if (p.level_pct >= 100) ranges[4].count++;
    });
    return ranges;
  }, [priorities]);

  // TTO distribution
  const ttoDistribution = useMemo(() => {
    const critical = priorities.filter((p) => p.tto_hours <= 24).length;
    const warning = priorities.filter((p) => p.tto_hours > 24 && p.tto_hours <= 72).length;
    const safe = priorities.filter((p) => p.tto_hours > 72).length;
    return [
      { name: "حرج (≤24h)", value: critical, color: COLORS.high },
      { name: "تحذير (24-72h)", value: warning, color: COLORS.medium },
      { name: "آمن (>72h)", value: safe, color: COLORS.low },
    ];
  }, [priorities]);

  // Truck workload data
  const truckWorkload = useMemo(() => {
    return summaries.map((s) => ({
      name: s.truckId.replace("truck_", "شاحنة "),
      stops: s.stopsCount,
      distance: Number(s.distance_km.toFixed(1)),
      fuel: Number(s.fuel_l.toFixed(1)),
      co2: Number(s.co2_kg.toFixed(1)),
    }));
  }, [summaries]);

  // Priority scores
  const priorityScores = useMemo(() => {
    return priorities
      .slice()
      .sort((a, b) => b.priority - a.priority)
      .slice(0, 10)
      .map((p) => ({
        name: `#${p.tank_id}`,
        priority: Number(p.priority.toFixed(2)),
        level: p.level_pct,
        tto: p.tto_hours,
      }));
  }, [priorities]);

  // Weekly trend (mock data for demo)
  const weeklyTrend = useMemo(() => {
    const days = ["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"];
    return days.map((day) => ({
      day,
      served: Math.floor(8 + Math.random() * 6),
      alerts: Math.floor(2 + Math.random() * 4),
      efficiency: Math.floor(75 + Math.random() * 20),
    }));
  }, []);

  const renderPieLabel = ({ name, value, x, y, cx }: { name: string; value: number; x: number; y: number; cx: number }) => (
    <text
      x={x}
      y={y}
      fill="#e2e8f0"
      textAnchor={x > cx ? "start" : "end"}
      dominantBaseline="central"
      style={{ fontSize: "12px", fontWeight: 700, paintOrder: "stroke" }}
      stroke="rgba(0,0,0,0.7)"
      strokeWidth={3}
    >
      {`${name}: ${value}`}
    </text>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="panel p-4">
        <h2 className="text-2xl font-bold text-neon-cyan">{t("statsTitle")}</h2>
        <p className="text-sm text-slate-400 mt-1">{t("statsSubtitle")}</p>
      </div>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="panel p-4 text-center">
          <div className="text-3xl font-bold text-neon-cyan">{priorities.length}</div>
          <div className="text-sm text-slate-400">{t("tanksMonitored")}</div>
        </div>
        <div className="panel p-4 text-center">
          <div className="text-3xl font-bold text-red-400">
            {priorities.filter((p) => p.tier === "HIGH").length}
          </div>
          <div className="text-sm text-slate-400">{t("highPriorityCount")}</div>
        </div>
        <div className="panel p-4 text-center">
          <div className="text-3xl font-bold text-green-400">
            {(metrics.total_distance_km ?? 0).toFixed(1)} km
          </div>
          <div className="text-sm text-slate-400">{t("totalDistance")}</div>
        </div>
        <div className="panel p-4 text-center">
          <div className="text-3xl font-bold text-purple-400">{summaries.length}</div>
          <div className="text-sm text-slate-400">{t("activeTrucks")}</div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tier Distribution Pie */}
        <div className="panel p-4">
          <h3 className="text-lg font-semibold mb-4">{t("tierDistribution")}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={tierData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
                label={renderPieLabel}
                labelLine={{ stroke: "#cbd5f5", strokeWidth: 1 }}
              >
                {tierData.map((entry) => (
                  <Cell key={`tier-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#0b1020", border: "1px solid #1b2342", color: "#e2e8f0" }}
                itemStyle={{ color: "#e2e8f0" }}
              />
              <Legend wrapperStyle={{ color: "#e2e8f0" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Level Distribution Bar */}
        <div className="panel p-4">
          <h3 className="text-lg font-semibold mb-4">{t("levelDistribution")}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={levelDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1b2342" />
              <XAxis dataKey="range" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ background: "#0b1020", border: "1px solid #1b2342", color: "#e2e8f0" }}
                itemStyle={{ color: "#00f0ff" }}
                labelStyle={{ color: "#e2e8f0" }}
                cursor={{ fill: "rgba(0,0,0,0)" }}
              />
              <Bar dataKey="count" fill={COLORS.primary} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* TTO Distribution */}
        <div className="panel p-4">
          <h3 className="text-lg font-semibold mb-4">{t("ttoDistribution")}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={ttoDistribution}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={renderPieLabel}
                labelLine={{ stroke: "#cbd5f5", strokeWidth: 1 }}
              >
                {ttoDistribution.map((entry) => (
                  <Cell key={`tto-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#0b1020", border: "1px solid #1b2342", color: "#e2e8f0" }}
                itemStyle={{ color: "#e2e8f0" }}
              />
              <Legend wrapperStyle={{ color: "#e2e8f0" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Truck Workload */}
        <div className="panel p-4">
          <h3 className="text-lg font-semibold mb-4">{t("truckWorkload")}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={truckWorkload}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1b2342" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ background: "#0b1020", border: "1px solid #1b2342", color: "#e2e8f0" }}
                itemStyle={{ color: "#00f0ff" }}
                labelStyle={{ color: "#e2e8f0" }}
                cursor={{ fill: "rgba(0,0,0,0)" }}
              />
              <Legend wrapperStyle={{ color: "#e2e8f0" }} />
              <Bar dataKey="stops" name={t("stops")} fill={COLORS.primary} />
              <Bar dataKey="distance" name={t("distance")} fill={COLORS.secondary} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 3 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Priority Tanks */}
        <div className="panel p-4">
          <h3 className="text-lg font-semibold mb-4">{t("topPriorityTanks")}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={priorityScores} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1b2342" />
              <XAxis type="number" stroke="#94a3b8" />
              <YAxis dataKey="name" type="category" stroke="#94a3b8" width={50} />
              <Tooltip
                contentStyle={{ background: "#0b1020", border: "1px solid #1b2342", color: "#e2e8f0" }}
                itemStyle={{ color: "#00f0ff" }}
                labelStyle={{ color: "#e2e8f0" }}
                cursor={{ fill: "rgba(0,0,0,0)" }}
                formatter={(value, name) => {
                  if (name === "priority") return [value, t("priority")];
                  if (name === "level") return [`${value}%`, t("fillLevel")];
                  return [value, String(name)];
                }}
              />
              <Bar dataKey="priority" fill={COLORS.high} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Weekly Trend */}
        <div className="panel p-4">
          <h3 className="text-lg font-semibold mb-4">{t("weeklyTrend")}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={weeklyTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1b2342" />
              <XAxis dataKey="day" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ background: "#0b1020", border: "1px solid #1b2342", color: "#e2e8f0" }}
                itemStyle={{ color: "#00f0ff" }}
                labelStyle={{ color: "#e2e8f0" }}
                cursor={{ fill: "rgba(0,0,0,0)" }}
              />
              <Legend wrapperStyle={{ color: "#e2e8f0" }} />
              <Area
                type="monotone"
                dataKey="served"
                name={t("servedTotal")}
                stroke={COLORS.primary}
                fill={COLORS.primary}
                fillOpacity={0.3}
              />
              <Area
                type="monotone"
                dataKey="efficiency"
                name={t("efficiency")}
                stroke={COLORS.low}
                fill={COLORS.low}
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Fuel & CO2 Summary */}
      <div className="panel p-4">
        <h3 className="text-lg font-semibold mb-4">{t("environmentalImpact")}</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="panel-soft p-4 text-center">
            <div className="text-4xl mb-2">⛽</div>
            <div className="text-3xl font-bold text-yellow-400">
              {(metrics.fuel_l_est ?? 0).toFixed(1)} L
            </div>
            <div className="text-sm text-slate-400">{t("fuelEstimate")}</div>
          </div>
          <div className="panel-soft p-4 text-center">
            <div className="text-4xl mb-2">🌍</div>
            <div className="text-3xl font-bold text-green-400">
              {(metrics.co2_kg_est ?? 0).toFixed(1)} kg
            </div>
            <div className="text-sm text-slate-400">{t("co2Estimate")}</div>
          </div>
          <div className="panel-soft p-4 text-center">
            <div className="text-4xl mb-2">💰</div>
            <div className="text-3xl font-bold text-neon-cyan">
              ${((metrics.fuel_l_est ?? 0) * 1.8).toFixed(2)}
            </div>
            <div className="text-sm text-slate-400">{t("fuelCost")}</div>
          </div>
        </div>
      </div>

      {/* Generated Charts Images */}
      <div className="panel p-4">
        <h3 className="text-lg font-semibold mb-4">{t("generatedCharts")}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { src: "/data/fig_kpi_summary.png", title: t("kpiSummary") },
            { src: "/data/fig_tier_coverage.png", title: t("tierCoverage") },
            { src: "/data/fig_workload_balance.png", title: t("workloadBalance") },
            { src: "/data/fig_distance_and_served.png", title: t("distanceServed") },
            { src: "/data/fig_efficiency_vs_safety.png", title: t("efficiencySafety") },
            { src: "/data/fig_routes_compare.png", title: t("routesCompare") },
          ].map((chart) => (
            <div key={chart.src} className="panel-soft p-3 rounded-lg">
              <h4 className="text-sm font-medium mb-2 text-center">{chart.title}</h4>
              <img
                src={chart.src}
                alt={chart.title}
                className="w-full h-auto rounded-lg border border-grid"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Visualization Images */}
      <div className="panel p-4">
        <h3 className="text-lg font-semibold mb-4">{t("visualizations")}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { src: "/data/viz_1_forecast.png", title: t("forecastViz") },
            { src: "/data/viz_2_priority_wow.png", title: t("priorityWow") },
            { src: "/data/viz_3_priority_breakdown.png", title: t("priorityBreakdown") }
          ].map((viz) => (
            <div key={viz.src} className="panel-soft p-3 rounded-lg">
              <h4 className="text-sm font-medium mb-2 text-center">{viz.title}</h4>
              <img
                src={viz.src}
                alt={viz.title}
                className="w-full h-auto rounded-lg border border-grid"
                onError={(e) => {
                  (e.target as HTMLImageElement).parentElement!.style.display = "none";
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
