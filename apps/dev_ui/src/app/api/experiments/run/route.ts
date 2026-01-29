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

function runCmd(args: string[]) {
  const root = repoRoot();
  const r = spawnSync("py", args, {
    cwd: root,
    env: { ...process.env, PYTHONPATH: root },
    encoding: "utf-8",
  });
  return r;
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));

  const base = body.base ?? "configs/base.yaml";
  const scenario = body.scenario ?? "configs/scenarios/seoul_allgu_v1.yaml";
  const sweep = body.sweep ?? "configs/sweeps/phase1_time_mult.yaml";
  const notes = body.notes ?? "";

  // 1) 실험 실행
  const r1 = runCmd(["-m", "src.runner", "--base", base, "--scenario", scenario, "--sweep", sweep]);
  if (r1.status !== 0) {
    return NextResponse.json({ ok: false, stage: "runner", error: r1.stderr, stdout: r1.stdout }, { status: 500 });
  }

  // runner stdout에서 exp_dir 추출: "[DONE] <exp_dir>/leaderboard.csv" 패턴
  const m = r1.stdout.match(/\[DONE\]\s+(.*)\/leaderboard\.csv/);
  if (!m) {
    return NextResponse.json({ ok: false, stage: "parse_exp_dir", stdout: r1.stdout }, { status: 500 });
  }
  const expDir = m[1];
  const expId = path.basename(expDir);

  // 2) DB ingest
  const r2 = runCmd(["-m", "src.expdb", "ingest", "--db", dbPath(), "--exp_id", expId, "--exp_dir", expDir,
                    "--scenario_name", path.basename(scenario), "--sweep_param_path", "auto", "--notes", notes]);
  if (r2.status !== 0) {
    return NextResponse.json({ ok: false, stage: "ingest", error: r2.stderr }, { status: 500 });
  }

  // 3) experiment-level insights 생성
  const r3 = runCmd(["-m", "src.expdb", "insights", "--db", dbPath(), "--exp_id", expId, "--primary_metric", "center_late_p95"]);
  if (r3.status !== 0) {
    return NextResponse.json({ ok: false, stage: "insights", error: r3.stderr }, { status: 500 });
  }

  return NextResponse.json({ ok: true, expId, expDir, runner_stdout: r1.stdout });
}
