import Link from "next/link";
import { listVariants, readLeaderboard } from "../../../lib/runsRepo";
import LeaderboardTable from "./LeaderboardTable";

export const dynamic = "force-dynamic";

function pickBestVariant(rows: any[]) {
  const scored = rows
    .map((r) => ({
      variant: String(r.variant ?? ""),
      a: Number(r.center_late_p95),
      b: Number(r.vehicles_used),
    }))
    .filter((x) => x.variant && Number.isFinite(x.a) && Number.isFinite(x.b))
    .sort((x, y) => x.a - y.a || x.b - y.b);
  return scored[0]?.variant ?? null;
}

export default async function Page({ params }: { params: Promise<{ expId: string }> }) {
  const { expId: raw } = await params;
  const expId = decodeURIComponent(raw);

  const [variants, leaderboard] = await Promise.all([
    listVariants(expId).catch(() => []),
    readLeaderboard(expId).catch(() => []),
  ]);

  const best = pickBestVariant(leaderboard);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs text-neutral-400">Experiment</div>
          <h1 className="text-2xl font-bold font-mono">{expId}</h1>
        </div>

        <div className="flex gap-3 items-center">
          <Link className="text-sm text-neutral-300 hover:underline" href="/experiments">
            ← back
          </Link>
          <Link className="text-sm text-neutral-300 hover:underline" href={`/experiments/${encodeURIComponent(expId)}/compare`}>
            Compare →
          </Link>
          <Link className="text-sm text-neutral-300 hover:underline" href="/new-run">
            New Run →
          </Link>
        </div>
      </div>

      {best && (
        <div className="border border-neutral-800 rounded-xl p-4 bg-neutral-950 flex items-center justify-between">
          <div>
            <div className="text-xs text-neutral-400">Best (rule: center_late_p95 min → vehicles_used min)</div>
            <div className="font-mono text-sm mt-1">{best}</div>
          </div>
          <Link
            className="text-sm text-neutral-300 hover:underline"
            href={`/experiments/${encodeURIComponent(expId)}/variants/${encodeURIComponent(best)}`}
          >
            Open →
          </Link>
        </div>
      )}

      <section className="border border-neutral-800 rounded-xl p-4 bg-neutral-950">
        <div className="flex items-center justify-between">
          <div className="font-semibold">Variants</div>
          <div className="text-xs text-neutral-400">count: {variants.length}</div>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {variants.map((v) => (
            <Link
              key={v}
              href={`/experiments/${encodeURIComponent(expId)}/variants/${encodeURIComponent(v)}`}
              className="text-xs font-mono px-3 py-1 rounded-lg border border-neutral-800 hover:border-neutral-600 hover:bg-neutral-900"
            >
              {v}
            </Link>
          ))}
          {variants.length === 0 && <div className="text-sm text-neutral-400">no variants</div>}
        </div>
      </section>

      <section className="border border-neutral-800 rounded-xl p-4 bg-neutral-950 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-semibold">Leaderboard</div>
            <div className="text-xs text-neutral-400">정렬/필터는 테이블에서 바로 가능</div>
          </div>

          <a
            className="text-sm text-neutral-300 hover:underline"
            href={`/api/download?expId=${encodeURIComponent(expId)}&file=leaderboard.csv`}
          >
            Download CSV
          </a>
        </div>

        <LeaderboardTable expId={expId} rows={leaderboard} />
      </section>
    </div>
  );
}
