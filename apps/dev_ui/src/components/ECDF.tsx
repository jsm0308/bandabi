"use client";

import React from "react";

function toNum(x: any): number | null {
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

export function ECDF({
  title,
  values,
  height = 200,
}: {
  title: string;
  values: Array<string | number>;
  height?: number;
}) {
  const xs = values.map(toNum).filter((v): v is number => v !== null).sort((a, b) => a - b);
  const n = xs.length;

  if (n === 0) {
    return (
      <div className="rounded-2xl border p-4">
        <div className="font-bold">{title}</div>
        <div className="text-sm opacity-70 mt-1">No data</div>
      </div>
    );
  }

  const min = xs[0];
  const max = xs[n - 1];
  const span = Math.max(1e-9, max - min);

  const w = 900;
  const h = height;
  const pad = 24;
  const innerW = w - pad * 2;
  const innerH = h - pad * 2;

  // build path
  const pts: Array<[number, number]> = [];
  for (let i = 0; i < n; i++) {
    const x = xs[i];
    const p = (i + 1) / n;
    const px = pad + ((x - min) / span) * innerW;
    const py = pad + (1 - p) * innerH;
    pts.push([px, py]);
  }

  const d = pts
    .map(([x, y], i) => (i === 0 ? `M ${x.toFixed(2)} ${y.toFixed(2)}` : `L ${x.toFixed(2)} ${y.toFixed(2)}`))
    .join(" ");

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
          {/* border */}
          <rect x={pad} y={pad} width={innerW} height={innerH} fill="none" stroke="currentColor" opacity={0.15} />
          {/* line */}
          <path d={d} fill="none" stroke="currentColor" strokeWidth={2} opacity={0.7} />
        </svg>
      </div>
    </div>
  );
}
