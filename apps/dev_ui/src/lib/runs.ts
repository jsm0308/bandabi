// apps/dev_ui/src/lib/runs.ts
import "server-only";

import fs from "fs";
import path from "path";
import crypto from "crypto";

export type Row = Record<string, string>;

export type ExperimentInfo = {
  expId: string;
  expName: string;
  createdAt: string;
  createdAtMs: number;
  variants: string[];
  hasLeaderboard: boolean;
};

export type VariantSummary = {
  vehicles_used?: number;
  vehicles_used_by_gu?: Record<string, number>;
  total_travel_time_min_sum?: number;
  total_travel_time_min_mean?: number;
  total_travel_time_min_p95?: number;

  pickup_wait_time_min_sum?: number;
  service_time_min_sum?: number;

  notes?: string[];
  generated_at?: string;
};

export type VariantFiles = {
  metrics: Row | null;
  events: Row[]; // head preview
  routes: Row[]; // head preview
  summary: VariantSummary | null;

  meta: {
    expDir: string;
    variantDir: string;

    metricsPath: string;
    eventsPath: string;
    routesPath: string;
    summaryPath: string;
    configResolvedPath: string;

    eventsTruncated: boolean;
    routesTruncated: boolean;

    eventsBytes: number | null;
    routesBytes: number | null;

    configHash: string | null;
  };
};

function exists(p: string): boolean {
  try {
    fs.accessSync(p, fs.constants.R_OK);
    return true;
  } catch {
    return false;
  }
}

function getRunsRoot(): string {
  // 1) env first
  const env = process.env.BANDABI_RUNS_DIR;
  if (env && exists(env)) return env;

  // 2) dev_ui 기준: apps/dev_ui -> ../../runs
  const p1 = path.resolve(process.cwd(), "../../runs");
  if (exists(p1)) return p1;

  // 3) fallback
  const p2 = path.resolve(process.cwd(), "../../../runs");
  if (exists(p2)) return p2;

  // 4) local
  const p3 = path.resolve(process.cwd(), "runs");
  if (exists(p3)) return p3;

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

function sha256Text(s: string): string {
  return crypto.createHash("sha256").update(s, "utf8").digest("hex").slice(0, 12);
}

function safeReadText(p: string): string | null {
  try {
    if (!exists(p)) return null;
    return fs.readFileSync(p, "utf-8");
  } catch {
    return null;
  }
}

function readHeadText(p: string, maxBytes: number): { text: string; truncated: boolean; bytes: number | null } {
  try {
    if (!exists(p)) return { text: "", truncated: false, bytes: null };
    const st = fs.statSync(p);
    const bytes = st.size;

    const fd = fs.openSync(p, "r");
    const buf = Buffer.alloc(Math.min(maxBytes, bytes));
    const n = fs.readSync(fd, buf, 0, buf.length, 0);
    fs.closeSync(fd);

    let text = buf.slice(0, n).toString("utf-8");
    // 마지막 줄이 잘렸을 수 있으니 마지막 개행까지만
    const lastNl = Math.max(text.lastIndexOf("\n"), text.lastIndexOf("\r\n"));
    if (lastNl > 0) text = text.slice(0, lastNl);

    const truncated = bytes > n;
    return { text, truncated, bytes };
  } catch {
    return { text: "", truncated: false, bytes: null };
  }
}

function splitCsvLine(line: string): string[] {
  // 따옴표/콤마 기본 지원 (RFC 완벽 구현은 아님, but 훨씬 튼튼)
  const out: string[] = [];
  let cur = "";
  let inQ = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];

    if (ch === '"') {
      // escaped quote ("")
      if (inQ && line[i + 1] === '"') {
        cur += '"';
        i++;
        continue;
      }
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
  const lines = text
    .replace(/^\uFEFF/, "") // BOM 제거
    .split(/\r?\n/)
    .filter((l) => l.trim().length > 0);

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

export function listExperiments(): ExperimentInfo[] {
  const root = getRunsRoot();
  const names = fs.readdirSync(root, { withFileTypes: true });

  const exps: ExperimentInfo[] = [];
  for (const d of names) {
    if (!d.isDirectory()) continue;

    const expId = d.name;
    const expDir = path.join(root, expId);
    const lbPath = path.join(expDir, "leaderboard.csv");

    const hasLeaderboard = exists(lbPath);
    if (!hasLeaderboard) continue;

    try {
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
        createdAtMs: st.mtimeMs,
        variants,
        hasLeaderboard,
      });
    } catch {
      continue;
    }
  }

  // 최신순
  exps.sort((a, b) => b.createdAtMs - a.createdAtMs);
  return exps;
}

export function readLeaderboard(expId: string): Row[] {
  if (!expId) throw new Error(`readLeaderboard: expId is empty`);
  const root = getRunsRoot();
  const p = path.join(root, expId, "leaderboard.csv");
  if (!exists(p)) throw new Error(`leaderboard.csv not found: ${p}`);

  const text = fs.readFileSync(p, "utf-8");
  return parseCsv(text);
}

export function readVariantFiles(expId: string, variantId: string): VariantFiles {
  if (!expId) throw new Error(`readVariantFiles: expId is empty`);
  if (!variantId) throw new Error(`readVariantFiles: variantId is empty`);

  const root = getRunsRoot();
  const expDir = path.join(root, expId);
  const variantDir = path.join(expDir, variantId);

  const metricsPath = path.join(variantDir, "metrics.csv");
  const eventsPath = path.join(variantDir, "events.csv");
  const routesPath = path.join(variantDir, "routes.csv");
  const summaryPath = path.join(variantDir, "variant_summary.json");
  const configResolvedPath = path.join(variantDir, "config_resolved.yaml");

  const metricsText = safeReadText(metricsPath);
  const metrics = metricsText ? (parseCsv(metricsText)[0] ?? null) : null;

  // 대용량 방어: head만 읽기
  const ev = readHeadText(eventsPath, 2_000_000);  // 2MB
  const rt = readHeadText(routesPath, 2_000_000);  // 2MB

  const events = ev.text ? parseCsv(ev.text).slice(0, 2000) : [];
  const routes = rt.text ? parseCsv(rt.text).slice(0, 2000) : [];

  const summaryText = safeReadText(summaryPath);
  const summary = summaryText ? (JSON.parse(summaryText) as VariantSummary) : null;

  const cfgText = safeReadText(configResolvedPath);
  const configHash = cfgText ? sha256Text(cfgText) : null;

  return {
    metrics,
    events,
    routes,
    summary,
    meta: {
      expDir,
      variantDir,
      metricsPath,
      eventsPath,
      routesPath,
      summaryPath,
      configResolvedPath,
      eventsTruncated: ev.truncated,
      routesTruncated: rt.truncated,
      eventsBytes: ev.bytes,
      routesBytes: rt.bytes,
      configHash,
    },
  };
}

export function readResolvedConfig(expId: string, variantId: string): string | null {
  const root = getRunsRoot();
  const p = path.join(root, expId, variantId, "config_resolved.yaml");
  return safeReadText(p);
}

export function pickBestVariant(lb: Row[], rule?: { primary?: string; secondary?: string; tertiary?: string }): string | undefined {
  if (!lb || lb.length === 0) return undefined;

  const primary = rule?.primary ?? "center_late_p95";
  const secondary = rule?.secondary ?? "vehicles_used";
  const tertiary = rule?.tertiary ?? "ride_time_p95";

  const sorted = [...lb].sort((a, b) => {
    const c1 = toNum(a[primary]);
    const c2 = toNum(b[primary]);
    if (c1 !== c2) return c1 - c2;

    const v1 = toNum(a[secondary]);
    const v2 = toNum(b[secondary]);
    if (v1 !== v2) return v1 - v2;

    const r1 = toNum(a[tertiary]);
    const r2 = toNum(b[tertiary]);
    return r1 - r2;
  });

  return sorted[0]["variant"] ?? sorted[0]["variant_id"];
}
