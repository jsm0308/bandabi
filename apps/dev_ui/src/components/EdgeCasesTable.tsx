"use client";

import React from "react";

export function EdgeCasesTable({
  title,
  rows,
  maxRows = 30,
}: {
  title: string;
  rows: Array<Record<string, any>>;
  maxRows?: number;
}) {
  const data = rows.slice(0, maxRows);
  describeColumns(data);

  if (data.length === 0) {
    return (
      <div className="rounded-2xl border p-4">
        <div className="font-bold">{title}</div>
        <div className="text-sm opacity-70 mt-1">No rows</div>
      </div>
    );
  }

  const cols = describeColumns(data);

  return (
    <div className="rounded-2xl border p-4">
      <div className="flex items-end justify-between gap-4">
        <div className="font-bold">{title}</div>
        <div className="text-xs opacity-70">rows={data.length}</div>
      </div>

      <div className="mt-3 overflow-auto">
        <table className="min-w-[1100px] w-full text-sm">
          <thead className="bg-black/5">
            <tr>
              {cols.map((c) => (
                <th key={c} className="px-3 py-2 text-left whitespace-nowrap">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((r, i) => (
              <tr key={i} className="border-t">
                {cols.map((c) => (
                  <td key={c} className="px-3 py-2 whitespace-nowrap">
                    {String(r?.[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function describeColumns(rows: Array<Record<string, any>>): string[] {
  const keys = new Set<string>();
  for (const r of rows) Object.keys(r || {}).forEach((k) => keys.add(k));

  // 실무적으로 자주 보는 컬럼을 앞으로
  const preferred = [
    "request_id",
    "center_id",
    "timeslot",
    "vehicle_id",
    "pickup_late_min",
    "center_late_min",
    "ride_time_min",
    "pickup_promise_min",
    "pickup_actual_min",
    "center_promise_min",
    "center_actual_min",
  ];

  const all = Array.from(keys);
  const pref = preferred.filter((k) => keys.has(k));
  const rest = all.filter((k) => !pref.includes(k)).sort();
  return [...pref, ...rest];
}
