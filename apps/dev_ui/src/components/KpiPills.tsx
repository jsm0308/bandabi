"use client";

export function KpiPills({ row }: { row: Record<string, any> }) {
  const pick = (k: string) => row?.[k] ?? "";

  const pills = [
    ["pickup_late_p95", pick("pickup_late_p95")],
    ["center_late_p95", pick("center_late_p95")],
    ["ride_time_p95", pick("ride_time_p95")],
    ["vehicles_used", pick("vehicles_used")],
    ["total_travel_time_min", pick("total_travel_time_min")],
    ["runtime_total_sec", pick("runtime_total_sec")],
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {pills.map(([k, v]) => (
        <div
          key={k}
          className="rounded-full border px-3 py-1 text-xs font-semibold"
        >
          <span className="opacity-70">{k}</span> <span>{String(v)}</span>
        </div>
      ))}
    </div>
  );
}
