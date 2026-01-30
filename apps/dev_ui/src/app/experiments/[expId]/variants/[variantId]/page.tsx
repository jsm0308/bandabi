import Link from "next/link";
import { readVariantFiles } from "@/lib/runs";
import { Histogram } from "@/components/Histogram";
import { ECDF } from "@/components/ECDF";
import { EdgeCasesTable } from "@/components/EdgeCasesTable";

export const dynamic = "force-dynamic";

function toNum(x: any): number {
  const n = Number(x);
  return Number.isFinite(n) ? n : NaN;
}

export default function VariantDetailPage({
  params,
}: {
  params: { expId: string; variantId: string };
}) {
  const expId = decodeURIComponent(params.expId);
  const variantId = decodeURIComponent(params.variantId);

  const { metrics, events, routes } = readVariantFiles(expId, variantId);

  // late = actual - promise
  const pickupLate = events
    .map((r) => toNum(r["pickup_actual_min"]) - toNum(r["pickup_promise_min"]))
    .filter((v) => Number.isFinite(v))
    .map((v) => String(v));

  const centerLate = events
    .map((r) => toNum(r["center_actual_min"]) - toNum(r["center_promise_min"]))
    .filter((v) => Number.isFinite(v))
    .map((v) => String(v));

  const rideTime = events
    .map((r) => toNum(r["ride_time_min"]))
    .filter((v) => Number.isFinite(v))
    .map((v) => String(v));

  // edge cases: pickup late top 30
  const edge = events
    .map((r) => {
      const pl = toNum(r["pickup_actual_min"]) - toNum(r["pickup_promise_min"]);
      const cl = toNum(r["center_actual_min"]) - toNum(r["center_promise_min"]);
      return {
        ...r,
        pickup_late_min: String(pl),
        center_late_min: String(cl),
      };
    })
    .filter((r) => Number.isFinite(Number(r.pickup_late_min)))
    .sort((a, b) => Number(b.pickup_late_min) - Number(a.pickup_late_min))
    .slice(0, 30);

  return (
    <div className="space-y-8">
      <div>
        <div className="text-2xl font-black">
          {expId} / {variantId}
        </div>
        <div className="opacity-70">
          metrics.csv / events.csv / routes.csv 기반
        </div>
      </div>

      {metrics && (
        <div className="rounded-2xl border p-4">
          <div className="font-bold mb-2">Metrics</div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
            {Object.entries(metrics).map(([k, v]) => (
              <div key={k} className="rounded-xl border px-3 py-2">
                <div className="text-xs opacity-60">{k}</div>
                <div className="font-semibold">{String(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        <Histogram title="Pickup Late (min)" values={pickupLate} bins={24} />
        <ECDF title="Pickup Late ECDF" values={pickupLate} />
        <Histogram title="Center Late (min)" values={centerLate} bins={24} />
        <ECDF title="Center Late ECDF" values={centerLate} />
        <Histogram title="Ride Time (min)" values={rideTime} bins={24} />
        <ECDF title="Ride Time ECDF" values={rideTime} />
      </div>

      <EdgeCasesTable title="Edge Cases: Pickup Late Top 30" rows={edge} />

      <Link
        href={`/experiments/${encodeURIComponent(expId)}`}
        className="opacity-70 hover:underline"
      >
        ← back
      </Link>
    </div>
  );
}
