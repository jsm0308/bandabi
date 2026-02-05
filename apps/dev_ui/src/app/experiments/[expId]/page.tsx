import Link from "next/link";
import { readLeaderboard, pickBestVariant } from "@/lib/runs";
import { KpiPills } from "@/components/KpiPills";

export const dynamic = "force-dynamic";

function getFirstParam(params: Record<string, any>): string | null {
  const raw =
    params?.expId ??
    params?.expid ??
    params?.id ??
    // fallback: 첫 value
    (params ? Object.values(params)[0] : null);

  if (typeof raw !== "string" || raw.length === 0) return null;
  return raw;
}

function hrefVariant(expId: string, variantId: string) {
  return `/experiments/${encodeURIComponent(expId)}/variants/${encodeURIComponent(
    variantId
  )}`;
}

export default async function ExperimentDetailPage({
  params,
}: {
  // Next 16 일부 런타임에서 params가 Promise로 들어올 수 있음
  params: Promise<Record<string, any>> | Record<string, any>;
}) {
  // ✅ unwrap (Promise면 await, 아니면 그대로)
  const p = (typeof (params as any)?.then === "function"
    ? await (params as Promise<Record<string, any>>)
    : (params as Record<string, any>)) as Record<string, any>;

  const raw = getFirstParam(p);

  if (!raw) {
    return (
      <div className="space-y-4">
        <div className="text-2xl font-black">Experiment</div>
        <div className="rounded-2xl border p-4">
          <div className="font-bold text-red-600">Invalid route params</div>
          <div className="mt-2 text-sm opacity-70">
            params에서 expId를 찾지 못했습니다.
          </div>
        </div>
        <Link href="/experiments" className="opacity-70 hover:underline">
          ← back
        </Link>
      </div>
    );
  }

  const expId = decodeURIComponent(raw);

  let lb: any[] = [];
  try {
    lb = readLeaderboard(expId);
  } catch (e: any) {
    return (
      <div className="space-y-4">
        <div className="text-2xl font-black">{expId}</div>
        <div className="rounded-2xl border p-4">
          <div className="font-bold text-red-600">Failed to read leaderboard</div>
          <pre className="mt-2 text-xs opacity-80 whitespace-pre-wrap">
{String(e?.message ?? e)}
          </pre>
        </div>
        <Link href="/experiments" className="opacity-70 hover:underline">
          ← back
        </Link>
      </div>
    );
  }

  const best = pickBestVariant(lb);

  return (
    <div className="space-y-6">
      <div>
        <div className="text-2xl font-black">{expId}</div>
        <div className="opacity-70">leaderboard.csv 기반</div>
      </div>

      {best && (
        <div className="rounded-2xl border p-4">
          <div className="font-bold">Best Variant</div>
          <div className="mt-1">
            <Link
              href={hrefVariant(expId, best)}
              className="font-semibold hover:underline"
            >
              {best}
            </Link>
          </div>
          <div className="mt-3">
            <KpiPills row={lb.find((r) => r.variant === best) ?? lb[0]} />
          </div>
        </div>
      )}

      <div className="rounded-2xl border p-4 overflow-auto">
        <table className="min-w-[1100px] w-full text-sm">
          <thead className="bg-black/5">
            <tr>
              {Object.keys(lb[0] ?? {}).map((k) => (
                <th key={k} className="px-3 py-2 text-left whitespace-nowrap">
                  {k}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {lb.map((r, i) => (
              <tr key={i} className="border-t">
                {Object.keys(lb[0] ?? {}).map((k) => {
                  const v = r[k];
                  if (k === "variant") {
                    return (
                      <td key={k} className="px-3 py-2 whitespace-nowrap">
                        <Link
                          href={hrefVariant(expId, v)}
                          className="font-semibold hover:underline"
                        >
                          {v}
                        </Link>
                      </td>
                    );
                  }
                  return (
                    <td key={k} className="px-3 py-2 whitespace-nowrap">
                      {v}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Link href="/experiments" className="opacity-70 hover:underline">
        ← back
      </Link>
    </div>
  );
}
