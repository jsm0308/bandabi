// apps/dev_ui/src/lib/runsRepo.ts
import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import Papa from "papaparse";
import YAML from "yaml";

export type ExperimentSummary = {
  expId: string;
  mtimeMs: number;
  hasLeaderboard: boolean;
  variants: number;
};

function parseCsv<T extends Record<string, any>>(text: string): T[] {
  const out = Papa.parse<T>(text, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
  });
  return (out.data ?? []).filter(Boolean);
}

export function resolveRepoRoot(): string {
  const envRoot = process.env.BANDABI_REPO_ROOT;

  const candidates = [
    envRoot,
    path.resolve(process.cwd(), "../.."), // apps/dev_ui -> repo root 추정
    process.cwd(),
  ].filter(Boolean) as string[];

  for (const c of candidates) {
    if (fsSync.existsSync(path.join(c, "runs"))) return c;
  }
  return candidates[0] ?? process.cwd();
}

export function resolveRunsDir(): string {
  return path.join(resolveRepoRoot(), "runs");
}

async function exists(p: string) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

function safeJoin(root: string, ...parts: string[]): string {
  const resolvedRoot = path.resolve(root);
  const p = path.resolve(resolvedRoot, ...parts);
  if (!p.startsWith(resolvedRoot + path.sep)) {
    throw new Error("Invalid path (path traversal blocked)");
  }
  return p;
}

async function readTextHead(absPath: string, maxBytes: number) {
  const fh = await fs.open(absPath, "r");
  try {
    const buf = Buffer.alloc(maxBytes);
    const { bytesRead } = await fh.read(buf, 0, maxBytes, 0);
    let text = buf.slice(0, bytesRead).toString("utf-8");
    // 마지막 줄 깨짐 방지: 마지막 개행까지만
    const lastNL = text.lastIndexOf("\n");
    if (lastNL > 0) text = text.slice(0, lastNL);
    return text;
  } finally {
    await fh.close();
  }
}

export async function listExperiments(): Promise<ExperimentSummary[]> {
  const root = resolveRunsDir();
  let ents: any[] = [];
  try {
    ents = await fs.readdir(root, { withFileTypes: true });
  } catch {
    return [];
  }

  const out: ExperimentSummary[] = [];
  for (const e of ents) {
    if (!e.isDirectory()) continue;
    const expId = e.name;
    const expPath = safeJoin(root, expId);

    const st = await fs.stat(expPath);
    const lbPath = path.join(expPath, "leaderboard.csv");
    const hasLeaderboard = await exists(lbPath);

    const subs = await fs.readdir(expPath, { withFileTypes: true });
    const variants = subs.filter((x) => x.isDirectory()).length;

    out.push({ expId, mtimeMs: st.mtimeMs, hasLeaderboard, variants });
  }

  out.sort((a, b) => b.mtimeMs - a.mtimeMs);
  return out;
}

export async function listVariants(expId: string): Promise<string[]> {
  const root = resolveRunsDir();
  const expPath = safeJoin(root, expId);
  const ents = await fs.readdir(expPath, { withFileTypes: true });
  return ents.filter((e) => e.isDirectory()).map((e) => e.name).sort();
}

export async function readLeaderboard(expId: string): Promise<Record<string, any>[]> {
  const p = safeJoin(resolveRunsDir(), expId, "leaderboard.csv");
  const txt = await fs.readFile(p, "utf-8");
  return parseCsv<Record<string, any>>(txt);
}

export async function readVariantFiles(expId: string, variantId: string) {
  const base = safeJoin(resolveRunsDir(), expId, variantId);

  const metricsPath = path.join(base, "metrics.csv");
  const configPath = path.join(base, "config_resolved.yaml");
  const routesPath = path.join(base, "routes.csv");
  const eventsPath = path.join(base, "events.csv");

  const metricsCsv = (await exists(metricsPath)) ? await fs.readFile(metricsPath, "utf-8") : "";
  const routesCsv = (await exists(routesPath)) ? await fs.readFile(routesPath, "utf-8") : "";
  const configYaml = (await exists(configPath)) ? await fs.readFile(configPath, "utf-8") : "";
  const eventsHead = (await exists(eventsPath)) ? await readTextHead(eventsPath, 512 * 1024) : "";

  const metrics = metricsCsv ? (parseCsv<Record<string, any>>(metricsCsv)[0] ?? {}) : {};
  const routesPreview = routesCsv ? parseCsv<Record<string, any>>(routesCsv).slice(0, 200) : [];
  const eventsPreview = eventsHead ? parseCsv<Record<string, any>>(eventsHead).slice(0, 300) : [];

  const configObj = configYaml ? YAML.parse(configYaml) : null;

  return {
    metrics,
    routesPreview,
    eventsPreview,
    configYaml,
    configObj,
    fileExists: {
      metrics: await exists(metricsPath),
      routes: await exists(routesPath),
      events: await exists(eventsPath),
      config: await exists(configPath),
    },
  };
}

export function resolveRunFilePath(expId: string, variantId: string | null, file: string) {
  const root = resolveRunsDir();
  if (variantId) return safeJoin(root, expId, variantId, file);
  return safeJoin(root, expId, file);
}
