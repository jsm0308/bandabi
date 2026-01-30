// apps/dev_ui/src/app/insights/page.tsx
import Link from "next/link";
import { listExperiments, readLeaderboard, pickBestVariant, readVariantFiles } from "@/lib/runs";

function n(v: any): number {
  const x = Number(v);
  return Number.isFinite(x) ? x : NaN;
}

function fmt(v: any, digits = 2): string {
  const x = n(v);
  if (!Number.isFinite(x)) return "-";
  return x.toFixed(digits);
}

function deriveTextInsights(lb: Record<string, string>[], bestKey = "center_late_p95"): string[] {
  if (!lb.length) return ["리더보드가 비어있음"];

  // 대충 “변수 3개”로 트레이드오프 메시지 생성 (면접용 감성)
  const rows = lb
    .map((r) => ({
      variant: r.variant ?? r.variant_id ?? "?",
      centerP95: n(r.center_late_p95),
      pickupP95: n(r.pickup_late_p95),
      rideP95: n(r.ride_time_p95),
      veh: n(r.vehicles_used),
      tSum: n(r.total_travel_time_min ?? r.total_travel_time),
    }))
    .filter((x) => Number.isFinite(x.centerP95) && Number.isFinite(x.veh));

  if (!rows.length) return ["수치형 KPI 파싱 실패: 컬럼명 확인 필요"];

  rows.sort((a, b) => a.centerP95 - b.centerP95);
  const best = rows[0];

  const mostEff = [...rows]
    .filter((x) => Number.isFinite(x.tSum))
    .sort((a, b) => a.tSum - b.tSum)[0];

  const minVeh = [...rows].sort((a, b) => a.veh - b.veh)[0];

  const out: string[] = [];
  out.push(`Best(센터 p95 최소) = ${best.variant}: center_late_p95=${best.centerP95.toFixed(2)}min, vehicles=${best.veh}`);
  if (mostEff?.variant && mostEff.variant !== best.variant) {
    out.push(`총 주행시간 합 최소 = ${mostEff.variant}: total_travel_time_min≈${mostEff.tSum.toFixed(1)}min`);
  }
  if (minVeh?.variant && minVeh.variant !== best.variant) {
    out.push(`차량 수 최소 = ${minVeh.variant}: vehicles_used=${minVeh.veh} (단, 지연/승차시간 악화 가능)`);
  }
  out.push("해석 포인트: 지연(p95) vs 차량수 vs 총비용(총 주행시간)의 Pareto trade-off를 보고 의사결정해야 함.");
  return out;
}

export default async function InsightsPage({
  searchParams,
}: {
  searchParams?: { expId?: string };
}) {
  const exps = listExperiments();
  const selectedExpId = searchParams?.expId ?? exps[0]?.expId;

  if (!selectedExpId) {
    return (
      <div className="p-6">
        <h1 className="text-xl font-semibold">Insights</h1>
        <p className="mt-2 text-neutral-300">runs/ 아래에 leaderboard.csv가 있는 실험이 없습니다.</p>
      </div>
    );
  }

  const lb = readLeaderboard(selectedExpId);
  const bestVariant = pickBestVariant(lb);
  const bestRow = lb.find((r) => (r.variant ?? r.variant_id) === bestVariant) ?? lb[0];
  const bestVariantId = (bestRow?.variant ?? bestRow?.variant_id) as string;

  const vf = readVariantFiles(selectedExpId, bestVariantId);

  const insights = deriveTextInsights(lb);

  return (
    <div className="min-h-screen p-6 text-neutral-100">
      <div className="flex gap-6">
        {/* Left: experiment list */}
        <aside className="w-[340px] shrink-0 rounded-2xl border border-neutral-800 bg-neutral-950/40 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Experiments</h2>
            <Link className="text-sm text-neutral-300 hover:text-white" href="/experiments">
              /experiments →
            </Link>
          </div>
          <div className="mt-3 space-y-2">
            {exps.slice(0, 30).map((e) => {
              const active = e.expId === selectedExpId;
              return (
                <Link
                  key={e.expId}
                  href={`/insights?expId=${encodeURIComponent(e.expId)}`}
                  className={[
                    "block rounded-xl border px-3 py-2",
                    active
                      ? "border-neutral-600 bg-neutral-900"
                      : "border-neutral-800 bg-neutral-950/40 hover:bg-neutral-900/40",
                  ].join(" ")}
                >
                  <div className="text-sm font-medium">{e.expId}</div>
                  <div className="mt-1 text-xs text-neutral-400">
                    {e.createdAt} · variants {e.variants.length}
                  </div>
                </Link>
              );
            })}
          </div>
        </aside>

        {/* Right: selected exp insights */}
        <main className="flex-1 space-y-6">
          <header className="rounded-2xl border border-neutral-800 bg-neutral-950/40 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-semibold">Insights</h1>
                <div className="mt-1 text-sm text-neutral-300">
                  exp: <span className="font-mono">{selectedExpId}</span>
                </div>
                <div className="mt-1 text-sm text-neutral-300">
                  best: <span className="font-mono">{bestVariantId}</span> · configHash{" "}
                  <span className="font-mono">{vf.meta.configHash ?? "-"}</span>
                </div>
              </div>
              <Link
                href={`/experiments/${encodeURIComponent(selectedExpId)}`}
                className="rounded-xl border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm hover:bg-neutral-800"
              >
                상세 페이지 →
              </Link>
            </div>

            <div className="mt-4 rounded-xl border border-neutral-800 bg-neutral-950/30 p-4">
              <div className="text-sm font-semibold">Auto Insights (면접용 한 줄 해석)</div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-neutral-300">
                {insights.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>
          </header>

          {/* KPI cards */}
          <section className="grid grid-cols-2 gap-4">
            <div className="rounded-2xl border border-neutral-800 bg-neutral-950/40 p-4">
              <div className="text-sm text-neutral-400">center_late_p95 (min)</div>
              <div className="mt-1 text-2xl font-semibold">{fmt(bestRow?.center_late_p95)}</div>
              <div className="mt-1 text-xs text-neutral-500">
                actual - promise, 음수면 조기 도착
              </div>
            </div>

            <div className="rounded-2xl border border-neutral-800 bg-neutral-950/40 p-4">
              <div className="text-sm text-neutral-400">vehicles_used</div>
              <div className="mt-1 text-2xl font-semibold">{fmt(bestRow?.vehicles_used, 0)}</div>
              <div className="mt-1 text-xs text-neutral-500">
                차량 수는 비용/운영 리소스의 1차 proxy
              </div>
            </div>

            <div className="rounded-2xl border border-neutral-800 bg-neutral-950/40 p-4">
              <div className="text-sm text-neutral-400">total_travel_time_min (sum)</div>
              <div className="mt-1 text-2xl font-semibold">{fmt(bestRow?.total_travel_time_min)}</div>
              <div className="mt-1 text-xs text-neutral-500">
                합은 “총비용”, 평균/p95는 “QoS”
              </div>
            </div>

            <div className="rounded-2xl border border-neutral-800 bg-neutral-950/40 p-4">
              <div className="text-sm text-neutral-400">runtime_total_sec</div>
              <div className="mt-1 text-2xl font-semibold">{fmt(bestRow?.runtime_total_sec)}</div>
              <div className="mt-1 text-xs text-neutral-500">파이프라인 계산 런타임(초)</div>
            </div>
          </section>

          {/* vehicles_used_by_gu */}
          <section className="rounded-2xl border border-neutral-800 bg-neutral-950/40 p-5">
            <h3 className="text-lg font-semibold">vehicles_used_by_gu</h3>
            <p className="mt-1 text-sm text-neutral-400">
              variant_summary.json이 있으면 그걸 사용, 없으면 “표시 불가”
            </p>

            {!vf.summary?.vehicles_used_by_gu ? (
              <div className="mt-3 rounded-xl border border-neutral-800 bg-neutral-950/30 p-4 text-sm text-neutral-300">
                variant_summary.json이 없습니다. (파이프라인에서 생성하도록 아래 Python 코드 반영)
              </div>
            ) : (
              <div className="mt-3 overflow-hidden rounded-xl border border-neutral-800">
                <table className="w-full text-sm">
                  <thead className="bg-neutral-900/60 text-neutral-300">
                    <tr>
                      <th className="px-3 py-2 text-left">gu</th>
                      <th className="px-3 py-2 text-right">vehicles</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(vf.summary.vehicles_used_by_gu)
                      .sort((a, b) => b[1] - a[1])
                      .map(([gu, cnt]) => (
                        <tr key={gu} className="border-t border-neutral-800">
                          <td className="px-3 py-2">{gu}</td>
                          <td className="px-3 py-2 text-right">{cnt}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Leaderboard preview */}
          <section className="rounded-2xl border border-neutral-800 bg-neutral-950/40 p-5">
            <h3 className="text-lg font-semibold">Leaderboard (preview)</h3>
            <div className="mt-3 overflow-auto rounded-xl border border-neutral-800">
              <table className="min-w-[900px] text-sm">
                <thead className="bg-neutral-900/60 text-neutral-300">
                  <tr>
                    {Object.keys(lb[0] ?? {}).slice(0, 10).map((k) => (
                      <th key={k} className="px-3 py-2 text-left">{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {lb.slice(0, 15).map((r, i) => (
                    <tr key={i} className="border-t border-neutral-800">
                      {Object.keys(lb[0] ?? {}).slice(0, 10).map((k) => (
                        <td key={k} className="px-3 py-2 font-mono text-neutral-200">
                          {String(r[k] ?? "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-2 text-xs text-neutral-500">
              더 디테일한 분포/ECDF/EdgeCases는 variant 상세 페이지에서 계속 확장.
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
