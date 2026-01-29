// apps/dev_ui/src/app/experiments/[expId]/variants/[variantId]/page.tsx
import Link from "next/link";
import { readVariantFiles } from "../../../../../lib/runsRepo";
import { KpiCards } from "../../../../../components/KpiCards";
import { DataTable } from "../../../../../components/DataTable";
import type { ColumnDef } from "@tanstack/react-table";

export const dynamic = "force-dynamic";

type Row = Record<string, any>;

function inferColumns(rows: Row[], limit = 12): ColumnDef<Row>[] {
  const keys = Array.from(new Set(rows.flatMap((r) => Object.keys(r ?? {})))).slice(0, limit);
  return keys.map((k) => ({
    accessorKey: k,
    header: k,
    cell: ({ row }) => {
      const v = row.original[k];
      if (v == null) return "";
      return typeof v === "number" ? (Number.isFinite(v) ? v.toString() : "") : String(v);
    },
  }));
}

export default async function Page({
  params,
}: {
  params: Promise<{ expId: string; variantId: string }>;
}) {
  const { expId: rawE, variantId: rawV } = await params;
  const expId = decodeURIComponent(rawE);
  const variantId = decodeURIComponent(rawV);

  const data = await readVariantFiles(expId, variantId);

  const routesCols = inferColumns(data.routesPreview);
  const eventsCols = inferColumns(data.eventsPreview);

  const dl = (file: string) =>
    `/api/download?expId=${encodeURIComponent(expId)}&variant=${encodeURIComponent(variantId)}&file=${encodeURIComponent(file)}`;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs text-neutral-400">Variant</div>
          <h1 className="text-2xl font-bold font-mono">{expId} / {variantId}</h1>
        </div>
        <div className="flex gap-3 items-center">
          <Link className="text-sm text-neutral-300 hover:underline" href={`/experiments/${encodeURIComponent(expId)}`}>
            ← back
          </Link>
          <a className="text-sm text-neutral-300 hover:underline" href={dl("config_resolved.yaml")}>
            config 다운로드
          </a>
        </div>
      </div>

      <section className="border border-neutral-800 rounded-xl p-4 bg-neutral-950 space-y-3">
        <div className="flex items-center justify-between">
          <div className="font-semibold">KPIs (metrics.csv)</div>
          <a className="text-sm text-neutral-300 hover:underline" href={dl("metrics.csv")}>
            Download metrics.csv
          </a>
        </div>
        <KpiCards metrics={data.metrics} />
      </section>

      <section className="border border-neutral-800 rounded-xl p-4 bg-neutral-950 space-y-3">
        <div className="flex items-center justify-between">
          <div className="font-semibold">config_resolved.yaml</div>
          <a className="text-sm text-neutral-300 hover:underline" href={dl("config_resolved.yaml")}>Download</a>
        </div>
        <pre className="text-xs overflow-auto max-h-[520px] whitespace-pre-wrap border border-neutral-900 rounded-lg p-3 bg-neutral-950 text-neutral-100">
{data.configYaml || "(missing config_resolved.yaml)"}
        </pre>
      </section>

      <section className="border border-neutral-800 rounded-xl p-4 bg-neutral-950 space-y-3">
        <div className="flex items-center justify-between">
          <div className="font-semibold">routes.csv (preview)</div>
          <a className="text-sm text-neutral-300 hover:underline" href={dl("routes.csv")}>
            Download routes.csv
          </a>
        </div>
        {data.routesPreview.length === 0 ? (
          <div className="text-sm text-neutral-400">(no routes preview)</div>
        ) : (
          <DataTable data={data.routesPreview} columns={routesCols} globalFilterPlaceholder="routes 검색..." />
        )}
      </section>

      <section className="border border-neutral-800 rounded-xl p-4 bg-neutral-950 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-semibold">events.csv (head preview)</div>
            <div className="text-xs text-neutral-400">대용량 안전: head만 파싱, 전체는 다운로드</div>
          </div>
          <a className="text-sm text-neutral-300 hover:underline" href={dl("events.csv")}>
            Download events.csv
          </a>
        </div>
        {data.eventsPreview.length === 0 ? (
          <div className="text-sm text-neutral-400">(no events preview)</div>
        ) : (
          <DataTable data={data.eventsPreview} columns={eventsCols} globalFilterPlaceholder="events 검색..." />
        )}
      </section>
    </div>
  );
}
