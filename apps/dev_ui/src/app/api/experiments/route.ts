import { NextResponse } from "next/server";
import { listExperiments } from "@/lib/runs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const experiments = listExperiments();
    return NextResponse.json({ ok: true, experiments });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message ?? String(e) }, { status: 500 });
  }
}
