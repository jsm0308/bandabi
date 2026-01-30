import Link from "next/link";
import { listExperiments, readLeaderboard, pickBestVariant } from "@/lib/runs";
import { KpiPills } from "@/components/KpiPills";

export const dynamic = "force-dynamic";

export default function ExperimentsPage() {
  const exps = listExperiments();

  // expName 기준으로 묶기
  const grouped = new Map<string, typeof exps>();
  for (const e of exps) {
    const expName = e.expName ?? e.expId;
    if (!grouped.has(expName)) grouped.set(expName, []);
    grouped.get(expName)!.push(e);
  }

  return (
    <div className="space-y-8">
      <div>
        <div className="text-2xl font-black">Experiments Lab</div>
        <div className="opacity-70">
          runs 폴더를 스캔해서 실험 블록(실험 단위)로 표시합니다.
        </div>
      </div>

      {[...grouped.entries()].map(([expName, items]) => (
        <section key={expName} className="space-y-3">
          <div className="text-xl font-bold">{expName}</div>

          <div className="grid grid-cols-1 gap-3">
            {items.map((e) => {
              let best: string | undefined;
              let bestRow: any = null;

              try {
                const lb = readLeaderboard(e.expId);
                best = pickBestVariant(lb);
                bestRow = lb.find((r) => r.variant === best) ?? lb[0];
              } catch {
                // leaderboard가 없거나 파싱 실패해도 UI는 살아있게
              }

              return (
                <div key={e.expId} className="rounded-2xl border p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <Link
                        href={`/experiments/${e.expId}`}
                        className="text-lg font-bold hover:underline"
                      >
                        {e.expId}
                      </Link>

                      <div className="text-sm opacity-70">
                        {e.createdAt} · variants {e.variants.length}
                      </div>

                      {best && (
                        <div className="mt-1 text-sm">
                          <span className="opacity-70">Best:</span>{" "}
                          <span className="font-semibold">{best}</span>
                        </div>
                      )}
                    </div>

                    <div className="text-xs opacity-60 text-right">
                      Best Rule<br />
                      center_late_p95 → vehicles_used → ride_time_p95
                    </div>
                  </div>

                  {bestRow && (
                    <div className="mt-3">
                      <KpiPills row={bestRow} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
