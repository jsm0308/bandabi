// apps/dev_ui/src/app/api/download/route.ts
import { NextRequest } from "next/server";
import fs from "node:fs";
import path from "node:path";
import { resolveRunFilePath } from "../../../lib/runs-repo";

export const runtime = "nodejs";

function contentType(file: string) {
  if (file.endsWith(".csv")) return "text/csv; charset=utf-8";
  if (file.endsWith(".yaml") || file.endsWith(".yml")) return "text/yaml; charset=utf-8";
  if (file.endsWith(".json")) return "application/json; charset=utf-8";
  if (file.endsWith(".html")) return "text/html; charset=utf-8";
  return "application/octet-stream";
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);

  const expId = searchParams.get("expId");
  const variantId = searchParams.get("variant");
  const file = searchParams.get("file");

  if (!expId || !file) {
    return new Response("Missing expId/file", { status: 400 });
  }

  // 허용 파일만 (안전)
  const allowed = new Set([
    "leaderboard.csv",
    "metrics.csv",
    "routes.csv",
    "events.csv",
    "config_resolved.yaml",
    "map_data.json",
    "map.html",
  ]);
  if (!allowed.has(file)) return new Response("File not allowed", { status: 403 });

  let abs: string;
  try {
    abs = resolveRunFilePath(expId, variantId, file);
  } catch (e: any) {
    return new Response(`Bad path: ${e?.message ?? e}`, { status: 400 });
  }

  if (!fs.existsSync(abs)) return new Response("Not found", { status: 404 });

  const stat = fs.statSync(abs);
  const stream = fs.createReadStream(abs);

  const headers = new Headers();
  headers.set("Content-Type", contentType(file));
  headers.set("Content-Length", String(stat.size));
  const wantDownload = searchParams.get("download") === "1";
  const dispType = !wantDownload && file.endsWith(".html") ? "inline" : "attachment";
  headers.set("Content-Disposition", `${dispType}; filename="${path.basename(file)}"`);

  return new Response(stream as any, { headers });
}
