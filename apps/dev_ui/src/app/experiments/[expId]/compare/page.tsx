import Link from "next/link";
import { readLeaderboard } from "@/lib/runsRepo";
import { CompareChart } from "@/components/CompareChart";

export const dynamic = "force-dynamic";

function bestVariant(rows: any[]) {
  // Best 규칙(예시): center_late_p95 최소 우선, 동률이면 vehicles_used 최소
  const scored = rows
    .map((r) => ({
      variant: r.variant,
      a: Number(r.center_late_p95),
      b: Number(r.vehicles_used),
    }))
    .filter((x) => Number.isFinite(x.a) && Number.isFinite(x.b))
    .sort((x, y) => x.a - y.a || x.b - y.b);
  return scored[0]?.variant ?? null;
}

export default async function Page({ params }: { params: { expId: string } }) {
  const expId = decodeURIComponent(params.expId);
  const rows = await readLeaderboard(expId).catch(() => []);
  const best = bestVariant(rows);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs text-neutral-400">Experiment Compare</div>
          <h1 className="text-2xl font-bold font-mono">{expId}</h1>
        </div>
        <div className="flex gap-3">
          <Link className="text-sm text-neutral-300 hover:underline" href={`/experiments/${encodeURIComponent(expId)}`}>
            ← back
          </Link>
          {best && (
            <Link
              className="text-sm text-neutral-300 hover:underline"
              href={`/experiments/${encodeURIComponent(expId)}/variants/${encodeURIComponent(best)}`}
            >
              Best → {best}
            </Link>
          )}
        </div>
      </div>

      <CompareChart rows={rows} />
    </div>
  );
}
