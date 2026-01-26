import fs from "node:fs";
import path from "node:path";

const RUNS_DIR = path.join(process.cwd(), "runs");

export function listRunIds(): string[] {
  if (!fs.existsSync(RUNS_DIR)) return [];
  return fs
    .readdirSync(RUNS_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort((a, b) => {
      const ta = fs.statSync(path.join(RUNS_DIR, a)).mtimeMs;
      const tb = fs.statSync(path.join(RUNS_DIR, b)).mtimeMs;
      return tb - ta;
    });
}

export function readLeaderboard(runId: string): { columns: string[]; rows: Record<string, any>[] } {
  const p = path.join(RUNS_DIR, runId, "leaderboard.csv");
  if (!fs.existsSync(p)) return { columns: [], rows: [] };

  const txt = fs.readFileSync(p, "utf-8");
  const lines = txt.split(/\r?\n/).filter(Boolean);
  if (lines.length === 0) return { columns: [], rows: [] };

  const columns = lines[0].split(",").map((s) => s.trim());
  const rows = lines.slice(1).map((line) => {
    const vals = line.split(",");
    const obj: Record<string, any> = {};
    columns.forEach((c, i) => {
      const v = (vals[i] ?? "").trim();
      // 숫자면 숫자로
      const num = Number(v);
      obj[c] = v !== "" && !Number.isNaN(num) ? num : v;
    });
    return obj;
  });

  return { columns, rows };
}
