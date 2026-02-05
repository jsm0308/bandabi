import fs from "fs";
import path from "path";

function exists(p: string): boolean {
  try {
    fs.accessSync(p, fs.constants.R_OK);
    return true;
  } catch {
    return false;
  }
}

export function resolveRepoRoot(cwd: string = process.cwd()): string {
  // dev_ui 기준: apps/dev_ui -> ../.. (repo root)
  const c1 = path.resolve(cwd, "../..");
  if (exists(path.join(c1, "runs")) || exists(path.join(c1, "configs"))) return c1;

  // repo root에서 실행되는 케이스
  const c2 = cwd;
  if (exists(path.join(c2, "runs")) || exists(path.join(c2, "configs"))) return c2;

  // fallback: 상위로 더 올라가보기
  const c3 = path.resolve(cwd, "../../..");
  if (exists(path.join(c3, "runs")) || exists(path.join(c3, "configs"))) return c3;

  return c1;
}

export function resolveRunsRoot(): string {
  const env = process.env.BANDABI_RUNS_DIR;
  if (env && exists(env)) return env;

  const root = resolveRepoRoot();
  const p = path.join(root, "runs");
  if (!exists(p)) {
    throw new Error(`runs 폴더를 찾지 못했습니다. BANDABI_RUNS_DIR을 설정하세요. cwd=${process.cwd()}`);
  }
  return p;
}

function assertSafeSegment(seg: string, name: string): void {
  if (!seg) throw new Error(`${name} is empty`);
  if (seg.includes("..") || seg.includes("/") || seg.includes("\\")) {
    throw new Error(`${name} contains an invalid path segment`);
  }
}

export function resolveRunFilePath(expId: string, variantId: string | null, filename: string): string {
  assertSafeSegment(expId, "expId");
  if (variantId) assertSafeSegment(variantId, "variantId");
  assertSafeSegment(filename, "filename");

  const runsRoot = resolveRunsRoot();
  const target = variantId
    ? path.join(runsRoot, expId, variantId, filename)
    : path.join(runsRoot, expId, filename);

  const normalized = path.normalize(target);
  if (!normalized.startsWith(path.normalize(path.join(runsRoot, expId)))) {
    throw new Error("path traversal detected");
  }
  return normalized;
}
