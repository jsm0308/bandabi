"use client";
import { useMemo, useState } from "react";
import { KPI, formatValue } from "@/lib/kpiRegistry";

export function LeaderboardTable({ rows }: { rows: Record<string, string>[] }) {
  const cols = useMemo(() => {
    const fixed = ["variant", "param_value"];
    const kpiCols = KPI.map((k) => k.key);
    const rest = Object.keys(rows[0] ?? {}).filter((c) => !fixed.includes(c) && !kpiCols.includes(c));
    return [...fixed, ...kpiCols, ...rest];
  }, [rows]);

  const [sortKey, setSortKey] = useState<string>("center_late_p95");
  const [asc, setAsc] = useState(true);

  const sorted = useMemo(() => {
    const cp = rows.slice();
    cp.sort((a, b) => {
      const ax = Number(a[sortKey]); const bx = Number(b[sortKey]);
      if (!Number.isFinite(ax) || !Number.isFinite(bx)) return (a[sortKey] ?? "").localeCompare(b[sortKey] ?? "");
      return asc ? ax - bx : bx - ax;
    });
    return cp;
  }, [rows, sortKey, asc]);

  return (
    <div className="overflow-auto rounded-xl border">
      <table className="min-w-[1200px] w-full text-sm">
        <thead className="sticky top-0 bg-black/5">
          <tr>
            {cols.map((c) => (
              <th
                key={c}
                className="cursor-pointer whitespace-nowrap px-3 py-2 text-left"
                onClick={() => {
                  if (sortKey === c) setAsc(!asc);
                  else { setSortKey(c); setAsc(true); }
                }}
              >
                {c}{sortKey === c ? (asc ? " ↑" : " ↓") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, idx) => (
            <tr key={idx} className="border-t hover:bg-black/5">
              {cols.map((c) => (
                <td key={c} className="whitespace-nowrap px-3 py-2">
                  {KPI.find((k) => k.key === c) ? formatValue(c, r[c] ?? "") : (r[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
