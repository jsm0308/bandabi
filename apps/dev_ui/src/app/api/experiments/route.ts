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

export async function GET() {
  const root = repoRoot();
  const result = spawnSync("py", ["-m", "src.expdb", "list", "--db", dbPath()], {
    cwd: root,
    env: { ...process.env, PYTHONPATH: root },
    encoding: "utf-8",
  });

  if (result.status !== 0) {
    return NextResponse.json({ ok: false, error: result.stderr }, { status: 500 });
  }

  return NextResponse.json(JSON.parse(result.stdout));
}
