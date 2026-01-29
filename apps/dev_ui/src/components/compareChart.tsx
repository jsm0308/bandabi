"use client";

import * as React from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
  ScatterChart, Scatter
} from "recharts";

type Row = Record<string, any>;

const KPI_CANDIDATES = [
  "center_late_p95",
  "pickup_late_p95",
  "ride_time_mean",
  "vehicles_used",
  "total_travel_time_min",
  "center_on_time_rate",
  "pickup_on_time_rate",
];

export function CompareChart({ rows }: { rows: Row[] }) {
  const [kpi, setKpi] = React.useState<string>("center_late_p95");
  const [mode, setMode] = React.useState<"line" | "scatter">("line");

  const data = React.useMemo(() => {
    return rows
      .map((r) => {
        const param = Number(r.param_value);
        const raw = Number(r[kpi]);
        const y = kpi.includes("on_time_rate") ? raw * 100 : raw;
        return { param_value: param, y, variant: String(r.variant ?? "") };
      })
      .filter((d) => Number.isFinite(d.param_value) && Number.isFinite(d.y))
      .sort((a, b) => a.param_value - b.param_value);
  }, [rows, kpi]);

  return (
    <div className="border border-neutral-800 rounded-xl p-4 bg-neutral-950 space-y-4">
      <div className="flex flex-wrap gap-2 items-center justify-between">
        <div className="font-semibold">Compare</div>
        <div className="flex gap-2 items-center">
          <select value={kpi} onChange={(e) => setKpi(e.target.value)} className="bg-neutral-950 border border-neutral-800 rounded-lg px-2 py-1 text-sm">
            {KPI_CANDIDATES.map((k) => <option key={k} value={k}>{k}</option>)}
          </select>

          <select value={mode} onChange={(e) => setMode(e.target.value as any)} className="bg-neutral-950 border border-neutral-800 rounded-lg px-2 py-1 text-sm">
            <option value="line">line</option>
            <option value="scatter">scatter</option>
          </select>
        </div>
      </div>

      <div className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          {mode === "line" ? (
            <LineChart data={data}>
              <CartesianGrid />
              <XAxis dataKey="param_value" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="y" dot />
            </LineChart>
          ) : (
            <ScatterChart>
              <CartesianGrid />
              <XAxis dataKey="param_value" />
              <YAxis dataKey="y" />
              <Tooltip />
              <Scatter data={data} />
            </ScatterChart>
          )}
        </ResponsiveContainer>
      </div>

      <div className="text-xs text-neutral-400">
        * on_time_rate 계열은 0~1 저장값을 %로 변환해 표시
      </div>
    </div>
  );
}
