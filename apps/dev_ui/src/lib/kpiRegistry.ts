// apps/dev_ui/src/lib/kpiRegistry.ts
export type MetricSpec = {
  key: string;
  label: string;
  unit?: "min" | "sec" | "count" | "pct";
  better: "lower" | "higher";
  group: "ETA" | "Ops" | "Runtime";
};

export const KPI: MetricSpec[] = [
  { key: "center_late_p95", label: "센터 도착 지연 P95", unit: "min", better: "lower", group: "ETA" },
  { key: "vehicles_used", label: "차량 수", unit: "count", better: "lower", group: "Ops" },
  { key: "ride_time_p95", label: "탑승시간 P95", unit: "min", better: "lower", group: "ETA" },

  { key: "pickup_late_p95", label: "픽업 지연 P95", unit: "min", better: "lower", group: "ETA" },
  { key: "pickup_on_time_rate", label: "픽업 정시율", unit: "pct", better: "higher", group: "ETA" },
  { key: "center_on_time_rate", label: "센터 정시율", unit: "pct", better: "higher", group: "ETA" },

  { key: "total_travel_time_min", label: "총 운행시간", unit: "min", better: "lower", group: "Ops" },
  { key: "runtime_total_sec", label: "런타임", unit: "sec", better: "lower", group: "Runtime" },
];

export const BEST_RULE = {
  primary: { key: "center_late_p95", order: "asc" as const },
  tie1: { key: "vehicles_used", order: "asc" as const },
  tie2: { key: "ride_time_p95", order: "asc" as const },
};

export function formatValue(key: string, raw: string): string {
  const v = Number(raw);
  if (!Number.isFinite(v)) return raw ?? "";
  const spec = KPI.find((k) => k.key === key);

  if (!spec) return raw;

  if (spec.unit === "pct") return `${(v * 100).toFixed(1)}%`;
  if (spec.unit === "min") return `${v.toFixed(2)} min`;
  if (spec.unit === "sec") return `${v.toFixed(2)} s`;
  if (spec.unit === "count") return `${Math.round(v)}`;
  return raw;
}
