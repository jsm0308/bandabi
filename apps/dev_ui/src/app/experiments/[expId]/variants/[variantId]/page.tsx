import Link from "next/link";

import { KpiPills } from "@/components/KpiPills";
import { readLeaderboard, readResolvedConfig, readVariantFiles } from "@/lib/runs";

export const dynamic = "force-dynamic";

function firstKeys(rows: Record<string, any>[], limit: number = 10): string[] {
  const keys = new Set<string>();
  for (const r of rows) {
    for (const k of Object.keys(r)) keys.add(k);
    if (keys.size >= limit) break;
  }
  return Array.from(keys).slice(0, limit);
}

function DataPreview({ title, rows }: { title: string; rows: Record<string, any>[] }) {
  if (!rows || rows.length === 0) {
    return (
      <section className="rounded-lg border p-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-sm text-gray-500">(no rows)</p>
      </section>
    );
  }

  const cols = firstKeys(rows, 12);

  return (
    <section className="rounded-lg border p-4">
      <h2 className="text-lg font-semibold mb-3">{title}</h2>
      <div className="overflow-x-auto">
        <table className="min-w-[900px] text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              {cols.map((c) => (
                <th key={c} className="text-left px-2 py-2 font-medium text-gray-700">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 50).map((r, i) => (
              <tr key={i} className="border-b">
                {cols.map((c) => (
                  <td key={c} className="px-2 py-2 whitespace-nowrap">
                    {String(r[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-gray-500">Showing first {Math.min(50, rows.length)} rows</p>
    </section>
  );
}

export default function VariantDetailPage({
  params,
}: {
  params: { expId: string; variantId: string };
}) {
  const { expId, variantId } = params;

  const files = readVariantFiles(expId, variantId);
  const config = readResolvedConfig(expId, variantId);
  const lb = readLeaderboard(expId);

  const lbRow = lb.find((r) => String(r.variant ?? r.variant_id ?? r.id ?? "") === variantId) ?? null;
  const kpiRow = files.metrics ?? lbRow ?? null;

  const d = (file: string, extra?: Record<string, string>) => {
    const qs = new URLSearchParams({ expId, variant: variantId, file, ...{ download: "1" }, ...extra });
    return `/api/download?${qs.toString()}`;
  };

  const mapSrc = (() => {
    const qs = new URLSearchParams({ expId, variant: variantId, file: "map.html" });
    return `/api/download?${qs.toString()}`;
  })();

  return (
    <main className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/experiments/${expId}`} className="text-sm text-gray-600 hover:underline">
            ← Back
          </Link>
          <h1 className="text-2xl font-bold mt-2">
            {expId} / {variantId}
          </h1>
          <p className="text-sm text-gray-500">variant outputs → CSV/YAML/HTML</p>
        </div>
      </div>

      {kpiRow ? (
        <section className="rounded-lg border p-4">
          <h2 className="text-lg font-semibold mb-3">KPIs</h2>
          <KpiPills row={kpiRow} />
        </section>
      ) : null}

      <section className="rounded-lg border p-4 space-y-2">
        <h2 className="text-lg font-semibold">Artifacts</h2>
        <div className="flex flex-wrap gap-2 text-sm">
          <a className="px-3 py-1 rounded border hover:bg-gray-50" href={d("config_resolved.yaml")}>Config (resolved)</a>
          <a className="px-3 py-1 rounded border hover:bg-gray-50" href={d("metrics.csv")}>metrics.csv</a>
          <a className="px-3 py-1 rounded border hover:bg-gray-50" href={d("events.csv")}>events.csv</a>
          <a className="px-3 py-1 rounded border hover:bg-gray-50" href={d("routes.csv")}>routes.csv</a>
          {files.meta.hasMapData ? (
            <a className="px-3 py-1 rounded border hover:bg-gray-50" href={d("map_data.json")}>map_data.json</a>
          ) : null}
          {files.meta.hasMapHtml ? (
            <a className="px-3 py-1 rounded border hover:bg-gray-50" href={d("map.html")}>map.html</a>
          ) : null}
        </div>
        <p className="text-xs text-gray-500">
          events/routes previews are truncated in UI for speed. Full files are downloadable.
        </p>
      </section>

      <section className="rounded-lg border p-4">
        <h2 className="text-lg font-semibold mb-3">Route map</h2>
        {files.meta.hasMapHtml ? (
          <div className="rounded overflow-hidden border">
            <iframe title="route-map" src={mapSrc} className="w-full h-[640px]" />
          </div>
        ) : (
          <div className="text-sm text-gray-600">
            <p className="mb-2">map.html not found in this variant folder.</p>
            <p>
              • 새 코드로 실험을 다시 실행하면 variant 폴더에 <code>map.html</code> / <code>map_data.json</code>이 생성됩니다.
              (또는 <code>python scripts/render_route_map.py</code>로 생성)
            </p>
          </div>
        )}
      </section>

      <DataPreview title="routes.csv (preview)" rows={files.routes} />
      <DataPreview title="events.csv (preview)" rows={files.events} />

      <section className="rounded-lg border p-4">
        <h2 className="text-lg font-semibold mb-3">config_resolved.yaml (preview)</h2>
        <pre className="text-xs whitespace-pre-wrap bg-gray-50 p-3 rounded border overflow-x-auto">
          {config ?? "(missing config_resolved.yaml)"}
        </pre>
      </section>
    </main>
  );
}
