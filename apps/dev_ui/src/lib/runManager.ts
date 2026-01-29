import { spawn } from "node:child_process";

type RunState = {
  id: string;
  createdAt: number;
  lines: string[];
  done: boolean;
  exitCode: number | null;
  error?: string;
  expId?: string;
};

const g = globalThis as any;
if (!g.__bandabiRuns) g.__bandabiRuns = new Map<string, RunState>();
const runs: Map<string, RunState> = g.__bandabiRuns;

export function startRun(args: { base: string; scenario: string; sweep: string }) {
  const id = `run_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  const st: RunState = { id, createdAt: Date.now(), lines: [], done: false, exitCode: null };
  runs.set(id, st);

  const py = process.env.BANDABI_PYTHON ?? "python";
  const mod = process.env.BANDABI_PY_MODULE ?? "bandabi.runner";
  const cwd = process.env.BANDABI_REPO_ROOT;

  const p = spawn(py, ["-m", mod, "--base", args.base, "--scenario", args.scenario, "--sweep", args.sweep], {
    cwd,
    env: process.env,
  });

  const onChunk = (chunk: Buffer) => {
    const s = chunk.toString("utf-8");
    s.split(/\r?\n/).forEach((line) => {
      if (!line) return;
      st.lines.push(line);

      // runner가 exp_dir 로그 찍는다고 가정: [RUNNER] exp_dir: .../runs/<expId>
      const m = line.match(/\[RUNNER\]\s+exp_dir:\s+(.+)$/);
      if (m?.[1]) {
        const p = m[1].trim().replace(/\\/g, "/");
        const parts = p.split("/");
        st.expId = parts[parts.length - 1];
      }
    });

    if (st.lines.length > 5000) st.lines = st.lines.slice(-5000);
  };

  p.stdout.on("data", onChunk);
  p.stderr.on("data", onChunk);

  p.on("close", (code) => {
    st.done = true;
    st.exitCode = code ?? 0;
    st.lines.push(`[UI] process closed: ${st.exitCode}`);
  });

  p.on("error", (err) => {
    st.done = true;
    st.exitCode = -1;
    st.error = String(err);
    st.lines.push(`[UI] process error: ${st.error}`);
  });

  return { runId: id };
}

export function getRun(runId: string) {
  return runs.get(runId);
}
