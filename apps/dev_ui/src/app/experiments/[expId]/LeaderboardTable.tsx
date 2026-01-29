"use client";

import Link from "next/link";
import { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "../../../components/DataTable";

type Row = Record<string, any>;

function fmtNum(x: any, digits = 3) {
  const v = Number(x);
  if (!Number.isFinite(v)) return "-";
  return v.toFixed(digits);
}

function fmtPct01(x: any) {
  const v = Number(x);
  if (!Number.isFinite(v)) return "-";
  return `${(v * 100).toFixed(1)}%`;
}

export default function LeaderboardTable({ expId, rows }: { expId: string; rows: Row[] }) {
  const columns: ColumnDef<Row>[] = [
    {
      accessorKey: "variant",
      header: "variant",
      cell: ({ row }) => {
        const v = String(row.original.variant ?? "");
        return (
          <Link
            className="font-mono hover:underline"
            href={`/experiments/${encodeURIComponent(expId)}/variants/${encodeURIComponent(v)}`}
          >
            {v}
          </Link>
        );
      },
    },
    { accessorKey: "param_path", header: "param_path", cell: ({ row }) => <span className="text-xs font-mono">{String(row.original.param_path ?? "-")}</span> },
    { accessorKey: "param_value", header: "param_value", cell: ({ row }) => fmtNum(row.original.param_value, 3) },

    { accessorKey: "pickup_late_p95", header: "pickup_late_p95", cell: ({ row }) => fmtNum(row.original.pickup_late_p95, 3) },
    { accessorKey: "center_late_p95", header: "center_late_p95", cell: ({ row }) => fmtNum(row.original.center_late_p95, 3) },

    { accessorKey: "pickup_on_time_rate", header: "pickup_on_time_rate", cell: ({ row }) => fmtPct01(row.original.pickup_on_time_rate) },
    { accessorKey: "center_on_time_rate", header: "center_on_time_rate", cell: ({ row }) => fmtPct01(row.original.center_on_time_rate) },

    { accessorKey: "vehicles_used", header: "vehicles_used", cell: ({ row }) => String(row.original.vehicles_used ?? "-") },
    { accessorKey: "total_travel_time_min", header: "total_travel_time_min", cell: ({ row }) => fmtNum(row.original.total_travel_time_min, 2) },
    { accessorKey: "runtime_total_sec", header: "runtime_total_sec", cell: ({ row }) => fmtNum(row.original.runtime_total_sec, 3) },
  ];

  return (
    <div className="space-y-2">
      <div className="text-xs text-neutral-400">
        * on_time_rate는 0~1 저장값 → UI에서 %로 변환 표시
      </div>
      <DataTable data={rows} columns={columns} globalFilterPlaceholder="leaderboard 전체 검색..." />
    </div>
  );
}
