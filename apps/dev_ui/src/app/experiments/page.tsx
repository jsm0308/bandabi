import Link from "next/link";
import { listExperiments } from "../../lib/runsRepo";

export const dynamic = "force-dynamic";

export default async function Page() {
  const exps = await listExperiments();

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Experiments</h1>

      <div className="border border-neutral-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-12 bg-neutral-900/40 text-xs text-neutral-300 px-4 py-2">
          <div className="col-span-7">expId</div>
          <div className="col-span-2">variants</div>
          <div className="col-span-3">leaderboard</div>
        </div>

        {exps.map((e) => (
          <Link
            key={e.expId}
            href={`/experiments/${encodeURIComponent(e.expId)}`}
            className="grid grid-cols-12 px-4 py-3 border-t border-neutral-900 hover:bg-neutral-900/30"
          >
            <div className="col-span-7 font-mono text-sm">{e.expId}</div>
            <div className="col-span-2 text-sm">{e.variants}</div>
            <div className="col-span-3 text-sm">{e.hasLeaderboard ? "yes" : "no"}</div>
          </Link>
        ))}

        {exps.length === 0 && (
          <div className="px-4 py-6 text-sm text-neutral-400">
            runs/ 폴더를 못 찾았거나 비어있음
          </div>
        )}
      </div>
    </div>
  );
}
