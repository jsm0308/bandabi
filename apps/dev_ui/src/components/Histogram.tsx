"use client";

import React from "react";

function toNum(x: any): number | null {
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

export function Histogram({
  title,
  values,
  bins = 24,
  height = 180,
}: {
  title: string;
  values: Array<string | number>;
  bins?: number;
  height?: number;
}) {
  const nums = values.map(toNum).filter((v): v is number => v !== null);
  const n = nums.length;

  if (n === 0) {
    return (
      <div className="rounded-2xl border p-4">
        <div className="font-bold">{title}</div>
        <div className="text-sm opacity-70 mt-1">No data</div>
      </div>
    );
  }

  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const span = Math.max(1e-9, max - min);
  const binW = span / bins;

  const counts = new Array(bins).fill(0);
  for (const x of nums) {
    let idx = Math.floor((x - min) / binW);
    if (idx < 0) idx = 0;
    if (idx >= bins) idx = bins - 1;
    counts[idx]++;
  }

  const maxC = Math.max(...counts);
  const w = 900;
  const h = height;
  const pad = 24;
  const innerW = w - pad * 2;
  const innerH = h - pad * 2;

  return (
    <div className="rounded-2xl border p-4">
      <div className="flex items-end justify-between gap-4">
        <div className="font-bold">{title}</div>
        <div className="text-xs opacity-70">
          n={n} · min={min.toFixed(2)} · max={max.toFixed(2)}
        </div>
      </div>

      <div className="mt-3 overflow-x-auto">
        <svg width={w} height={h} className="block">
          {/* axis baseline */}
          <line
            x1={pad}
            y1={h - pad}
            x2={w - pad}
            y2={h - pad}
            stroke="currentColor"
            opacity={0.2}
          />

          {counts.map((c, i) => {
            const bw = innerW / bins;
            const x = pad + i * bw + 1;
            const barH = (c / Math.max(1, maxC)) * (innerH - 6);
            const y = h - pad - barH;

            return (
              <rect
                key={i}
                x={x}
                y={y}
                width={bw - 2}
                height={barH}
                rx={4}
                fill="currentColor"
                opacity={0.25}
              />
            );
          })}
        </svg>
      </div>
    </div>
  );
}
