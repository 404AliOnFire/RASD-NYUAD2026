import { useMemo, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PriorityRecord } from "../types";

interface AiTabProps {
  priorities: PriorityRecord[];
  t: (key: string) => string;
}

export default function AiTab({ priorities, t }: AiTabProps) {
  const [selectedId, setSelectedId] = useState<number | "">(priorities[0]?.tank_id ?? "");

  const selected = useMemo(
    () => priorities.find((p) => p.tank_id === selectedId) ?? priorities[0],
    [priorities, selectedId]
  );

  const top15 = useMemo(
    () => [...priorities].sort((a, b) => b.priority - a.priority).slice(0, 15),
    [priorities]
  );

  if (!selected) {
    return <div className="panel p-4">No priority data loaded.</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase">{t("selectTank")}</h3>
        <select
          className="mt-2 w-full bg-panel-soft border border-grid rounded-lg p-2"
          value={selectedId}
          onChange={(e) => setSelectedId(Number(e.target.value))}
        >
          {priorities.map((p) => (
            <option key={p.tank_id} value={p.tank_id}>
              {p.tank_id}
            </option>
          ))}
        </select>
        <div className="mt-4 text-sm text-slate-300">Tier: {selected.tier}</div>
        <div className="mt-1 text-sm text-slate-300">{t("priority")}: {selected.priority}</div>
        <div className="mt-1 text-sm text-slate-300">{t("ttoHours")}: {selected.tto_hours}</div>
        <div className="mt-1 text-sm text-slate-300">{t("levelPct")}: {selected.level_pct}</div>
      </div>

      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase">{t("sensorFusion")}</h3>
        <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
          <div>Gas: {selected.gas_now}</div>
          <div>Temp: {selected.temp_c}</div>
          <div>Humidity: {selected.hum_pct}</div>
        </div>
        <div className="mt-4 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={[
                { name: "Base", value: selected.base },
                { name: "Gas", value: selected.gas_anom },
                { name: "Env", value: selected.env_anom }
              ]}
            >
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="value" fill="#a855f7" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel p-4">
        <h3 className="text-sm text-slate-300 uppercase">{t("topByPriority")}</h3>
        <div className="mt-3 max-h-64 overflow-auto text-sm">
          <table className="w-full">
            <thead>
              <tr className="text-slate-400">
                <th className="text-left">{t("tanks")}</th>
                <th className="text-left">Tier</th>
                <th className="text-left">{t("priority")}</th>
              </tr>
            </thead>
            <tbody>
              {top15.map((row) => (
                <tr key={row.tank_id} className="border-t border-grid">
                  <td>{row.tank_id}</td>
                  <td>{row.tier}</td>
                  <td>{row.priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
