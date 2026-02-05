import fs from "fs";
import path from "path";

export type Row = Record<string, string>;

export type ExperimentInfo = {
  expId: string;
  expName: string;
  createdAt: string;
  variants: string[];
};

export type VariantArtifacts = {
  metrics: Row | null;
  events: Row[];
  routes: Row[];
  summary: any | null; // variant_summary.json
  fixedParams: any | null; // fixed_params.json
  mapData: any | null; // map_data.json
};

function getRunsRoot(): string {
  const env = process.env.BANDABI_RUNS_DIR;
  if (env && fs.existsSync(env)) return env;

  // dev_ui 기준: apps/dev_ui -> ../../runs = repo_root/runs
  const p1 = path.resolve(process.cwd(), "../../runs");
  if (fs.existsSync(p1)) return p1;

  const p2 = path.resolve(process.cwd(), "../../../runs");
  if (fs.existsSync(p2)) return p2;

  const p3 = path.resolve(process.cwd(), "runs");
  if (fs.existsSync(p3)) return p3;

  throw new Error(
    `runs 폴더를 찾지 못했습니다. BANDABI_RUNS_DIR을 설정하세요. cwd=${process.cwd()}`
  );
}

function extractExpName(expId: string): string {
  // phase1_time_mult_20260130_051733 -> phase1_time_mult
  const parts = expId.split("_");
  if (parts.length >= 3) return parts.slice(0, -2).join("_");
  return expId;
}

function fmtTime(ms: number): string {
  const d = new Date(ms);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}`;
}

function splitCsvLine(line: string): string[] {
  // 단순 파서(현재 생성 csv 전제). 따옴표 섞여도 최대한 버팀.
  const out: string[] = [];
  let cur = "";
  let inQ = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      inQ = !inQ;
      continue;
    }
    if (ch === "," && !inQ) {
      out.push(cur);
      cur = "";
      continue;
    }
    cur += ch;
  }
  out.push(cur);
  return out.map((s) => s.trim());
}

function parseCsv(text: string): Row[] {
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length === 0) return [];
  const header = splitCsvLine(lines[0]);
  const rows: Row[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = splitCsvLine(lines[i]);
    const r: Row = {};
    for (let j = 0; j < header.length; j++) {
      r[header[j]] = cols[j] ?? "";
    }
    rows.push(r);
  }
  return rows;
}

function toNum(v: any): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : Number.POSITIVE_INFINITY;
}

function readJsonIfExists(p: string): any | null {
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, "utf-8"));
  } catch {
    return null;
  }
}

export function listExperiments(): ExperimentInfo[] {
  const root = getRunsRoot();
  const names = fs.readdirSync(root, { withFileTypes: true });
  const exps: ExperimentInfo[] = [];

  for (const d of names) {
    if (!d.isDirectory()) continue;
    const expId = d.name;
    const expDir = path.join(root, expId);

    try {
      const lbPath = path.join(expDir, "leaderboard.csv");
      if (!fs.existsSync(lbPath)) continue;

      const variants = fs
        .readdirSync(expDir, { withFileTypes: true })
        .filter((x) => x.isDirectory() && x.name.startsWith("v_"))
        .map((x) => x.name)
        .sort();

      const st = fs.statSync(lbPath);
      exps.push({
        expId,
        expName: extractExpName(expId),
        createdAt: fmtTime(st.mtimeMs),
        variants,
      });
    } catch {
      continue;
    }
  }

  exps.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
  return exps;
}

export function readLeaderboard(expId: string): Row[] {
  if (!expId) throw new Error(`readLeaderboard: expId is empty`);
  const root = getRunsRoot();
  const p = path.join(root, expId, "leaderboard.csv");
  if (!fs.existsSync(p)) throw new Error(`leaderboard.csv not found: ${p}`);
  return parseCsv(fs.readFileSync(p, "utf-8"));
}

export function readVariantArtifacts(expId: string, variantId: string): VariantArtifacts {
  if (!expId || !variantId) {
    throw new Error(`readVariantArtifacts: expId/variantId missing (${expId}, ${variantId})`);
  }

  const root = getRunsRoot();
  const vDir = path.join(root, expId, variantId);

  const metricsPath = path.join(vDir, "metrics.csv");
  const eventsPath = path.join(vDir, "events.csv");
  const routesPath = path.join(vDir, "routes.csv");

  const summaryPath = path.join(vDir, "variant_summary.json");
  const fixedParamsPath = path.join(vDir, "fixed_params.json");
  const mapDataPath = path.join(vDir, "map_data.json");

  const metrics = fs.existsSync(metricsPath)
    ? (parseCsv(fs.readFileSync(metricsPath, "utf-8"))[0] ?? null)
    : null;

  const events = fs.existsSync(eventsPath) ? parseCsv(fs.readFileSync(eventsPath, "utf-8")) : [];
  const routes = fs.existsSync(routesPath) ? parseCsv(fs.readFileSync(routesPath, "utf-8")) : [];

  return {
    metrics,
    events,
    routes,
    summary: readJsonIfExists(summaryPath),
    fixedParams: readJsonIfExists(fixedParamsPath),
    mapData: readJsonIfExists(mapDataPath),
  };
}

export function pickBestVariant(lb: Row[]): string | undefined {
  if (!lb || lb.length === 0) return undefined;

  // 기본 Best 규칙(지금 당장 면접용으로 “납득되는” 순서)
  // center_late_p95 asc -> pickup_late_p95 asc -> vehicles_used asc -> ride_time_p95 asc
  const sorted = [...lb].sort((a, b) => {
    const c1 = toNum(a["center_late_p95"]);
    const c2 = toNum(b["center_late_p95"]);
    if (c1 !== c2) return c1 - c2;

    const p1 = toNum(a["pickup_late_p95"]);
    const p2 = toNum(b["pickup_late_p95"]);
    if (p1 !== p2) return p1 - p2;

    const v1 = toNum(a["vehicles_used"]);
    const v2 = toNum(b["vehicles_used"]);
    if (v1 !== v2) return v1 - v2;

    const r1 = toNum(a["ride_time_p95"]);
    const r2 = toNum(b["ride_time_p95"]);
    return r1 - r2;
  });

  return sorted[0]["variant"];
}
