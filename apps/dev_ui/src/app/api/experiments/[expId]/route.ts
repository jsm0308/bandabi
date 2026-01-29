export const runtime = "nodejs";

import { NextResponse } from "next/server";
import { spawnSync } from "child_process";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..", "..");
}
function dbPath() {
  return path.join(repoRoot(), "db", "devui.sqlite");
}

export async function GET(_: Request, ctx: { params: { expId: string } }) {
  const root = repoRoot();
  const expId = ctx.params.expId;

  const result = spawnSync("py", ["-m", "src.expdb", "get", "--db", dbPath(), "--exp_id", expId], {
    cwd: root,
    env: { ...process.env, PYTHONPATH: root },
    encoding: "utf-8",
  });

  if (result.status !== 0) {
    return NextResponse.json({ ok: false, error: result.stderr }, { status: 500 });
  }

  return NextResponse.json(JSON.parse(result.stdout));
}
