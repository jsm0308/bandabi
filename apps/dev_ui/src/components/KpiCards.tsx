import React from "react";

function isRateKey(k: string) {
  return k.includes("on_time_rate") || k.endsWith("_rate");
}

function fmt(k: string, v: any) {
  const n = Number(v);
  if (!Number.isFinite(n)) return String(v ?? "-");
  if (isRateKey(k)) return `${(n * 100).toFixed(1)}%`;
  // 시간/분/초 등은 저장 단위가 섞일 수 있으니 일단 숫자 3자리
  return n.toFixed(3);
}

export function KpiCards({ metrics }: { metrics: Record<string, any> }) {
  const entries = Object.entries(metrics ?? {})
    .filter(([k, v]) => k && v != null)
    .sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {entries.map(([k, v]) => (
        <div key={k} className="border border-neutral-800 rounded-xl p-3 bg-neutral-950">
          <div className="text-xs text-neutral-400">{k}</div>
          <div className="mt-1 font-mono text-sm">{fmt(k, v)}</div>
        </div>
      ))}
      {entries.length === 0 && (
        <div className="text-sm text-neutral-400">metrics.csv 없음 또는 비어있음</div>
      )}
    </div>
  );
}
