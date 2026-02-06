import { useMemo, useState } from "react";
import { PriorityRecord, NodeRecord } from "../types";

interface TanksTabProps {
  priorities: PriorityRecord[];
  nodes: NodeRecord[];
  onSelectTank: (tank: PriorityRecord) => void;
  t: (key: string) => string;
}

function tierDot(tier: string) {
  if (tier === "HIGH") return "bg-red-500";
  if (tier === "MEDIUM") return "bg-yellow-400";
  return "bg-green-500";
}

function tierBg(tier: string) {
  if (tier === "HIGH") return "border-red-500/30 bg-red-500/10";
  if (tier === "MEDIUM") return "border-yellow-500/30 bg-yellow-500/10";
  return "border-green-500/30 bg-green-500/10";
}

export default function TanksTab({ priorities, nodes, onSelectTank, t }: TanksTabProps) {
  const [filter, setFilter] = useState<"all" | "HIGH" | "MEDIUM" | "LOW">("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"priority" | "tto" | "level">("priority");

  const filteredTanks = useMemo(() => {
    let result = [...priorities];

    // Filter by tier
    if (filter !== "all") {
      result = result.filter((p) => p.tier === filter);
    }

    // Search by ID
    if (search) {
      result = result.filter((p) => String(p.tank_id).includes(search));
    }

    // Sort
    switch (sortBy) {
      case "priority":
        result.sort((a, b) => b.priority - a.priority);
        break;
      case "tto":
        result.sort((a, b) => a.tto_hours - b.tto_hours);
        break;
      case "level":
        result.sort((a, b) => b.level_pct - a.level_pct);
        break;
    }

    return result;
  }, [priorities, filter, search, sortBy]);

  const counts = useMemo(() => ({
    all: priorities.length,
    HIGH: priorities.filter((p) => p.tier === "HIGH").length,
    MEDIUM: priorities.filter((p) => p.tier === "MEDIUM").length,
    LOW: priorities.filter((p) => p.tier === "LOW").length
  }), [priorities]);

  return (
    <div className="space-y-3 md:space-y-4">
      {/* Header */}
      <div className="panel p-3 md:p-4">
        <h2 className="text-lg md:text-xl font-bold text-neon-cyan">{t("tanksList")}</h2>
      </div>

      {/* Filters */}
      <div className="panel p-3 md:p-4">
        <div className="flex flex-col md:flex-row md:flex-wrap md:items-center gap-3 md:gap-4">
          {/* Tier Filter Buttons */}
          <div className="flex gap-1 md:gap-2 overflow-x-auto hide-scrollbar">
            {(["all", "HIGH", "MEDIUM", "LOW"] as const).map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`px-3 md:px-4 py-1.5 md:py-2 rounded-full text-xs md:text-sm font-medium transition whitespace-nowrap ${
                  filter === f
                    ? f === "HIGH" ? "bg-red-500 text-white" 
                      : f === "MEDIUM" ? "bg-yellow-500 text-black"
                      : f === "LOW" ? "bg-green-500 text-white"
                      : "bg-neon-cyan text-black"
                    : "bg-panel-soft text-slate-300 border border-grid hover:border-neon-cyan"
                }`}
              >
                {f === "all" ? t("filterAll") : f === "HIGH" ? t("filterHigh") : f === "MEDIUM" ? t("filterMedium") : t("filterLow")} ({counts[f]})
              </button>
            ))}
          </div>

          {/* Search */}
          <input
            type="text"
            placeholder={t("search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-panel-soft border border-grid rounded-lg px-3 py-2 text-xs md:text-sm w-full md:w-32"
          />

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-panel-soft border border-grid rounded-lg px-3 py-2 text-xs md:text-sm w-full md:w-auto"
          >
            <option value="priority">{t("priority")}</option>
            <option value="tto">{t("timeToOverflow")}</option>
            <option value="level">{t("fillLevel")}</option>
          </select>
        </div>
      </div>

      {/* Tanks Grid - Responsive */}
      <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 md:gap-4">
        {filteredTanks.map((tank) => (
          <button
            key={tank.tank_id}
            type="button"
            onClick={() => onSelectTank(tank)}
            className={`panel p-2 md:p-4 text-right transition hover:scale-[1.02] border ${tierBg(tank.tier)}`}
          >
            <div className="flex items-center justify-between mb-2 md:mb-3">
              <span className={`h-2 w-2 md:h-3 md:w-3 rounded-full ${tierDot(tank.tier)}`} />
              <span className="text-sm md:text-lg font-bold">#{tank.tank_id}</span>
            </div>

            {/* Fill Level Bar */}
            <div className="mb-2 md:mb-3">
              <div className="flex justify-between text-[10px] md:text-xs mb-1">
                <span className="text-slate-400">{t("fillLevel")}</span>
                <span className="font-bold">{tank.level_pct}%</span>
              </div>
              <div className="h-1.5 md:h-2 bg-panel-soft rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    tank.level_pct >= 80 ? 'bg-red-500' : tank.level_pct >= 50 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(tank.level_pct, 100)}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-1 md:gap-2 text-[10px] md:text-sm">
              <div>
                <div className="text-[10px] md:text-xs text-slate-400 truncate">{t("timeToOverflow")}</div>
                <div className={`font-bold ${tank.tto_hours <= 24 ? 'text-red-400' : ''}`}>
                  {tank.tto_hours}h
                </div>
              </div>
              <div>
                <div className="text-[10px] md:text-xs text-slate-400">{t("priority")}</div>
                <div className="font-bold text-neon-cyan">{tank.priority.toFixed(1)}</div>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Empty state */}
      {filteredTanks.length === 0 && (
        <div className="panel p-6 md:p-8 text-center">
          <div className="text-3xl md:text-4xl mb-3 md:mb-4">🔍</div>
          <div className="text-slate-400 text-sm md:text-base">لا توجد خزانات مطابقة</div>
        </div>
      )}
    </div>
  );
}
