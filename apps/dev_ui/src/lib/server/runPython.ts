import { spawn } from "child_process";
import path from "path";

export function runExperiment(args: {
  base: string;
  scenario: string;
  sweep: string;
  overrides?: Record<string, string | number | boolean>;
}) {
  const repoRoot = path.resolve(process.cwd(), "..", ".."); // dev_ui 기준 repo 루트
  const cmd = "py"; // windows면 보통 py가 제일 안정적. 안 되면 "python"으로 바꾸기

  // NOTE: Python 모듈 실행 (src/runner.py 기준)
  const pyArgs = [
    "-m", "src.runner",
    "--base", args.base,
    "--scenario", args.scenario,
    "--sweep", args.sweep,
  ];

  return new Promise<{ expDir: string; stdout: string }>((resolve, reject) => {
    const p = spawn(cmd, pyArgs, {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: repoRoot, // 중요: src 패키지 인식
      },
      shell: false,
    });

    let out = "";
    let err = "";

    p.stdout.on("data", (d) => (out += d.toString()));
    p.stderr.on("data", (d) => (err += d.toString()));

    p.on("close", (code) => {
      if (code !== 0) return reject(new Error(`runner failed(code=${code})\n${err}\n${out}`));

      // runner가 찍는 "[DONE] <exp_dir>/leaderboard.csv 생성 완료"에서 exp_dir 추출
      const m = out.match(/\[DONE\]\s+(.*)\/leaderboard\.csv/);
      if (!m) return reject(new Error(`Cannot parse exp_dir from runner output.\n${out}`));

      resolve({ expDir: m[1], stdout: out });
    });
  });
}
