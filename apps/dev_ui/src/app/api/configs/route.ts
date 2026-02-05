import fs from "node:fs/promises";
import path from "node:path";
import { resolveRepoRoot } from "../../../lib/runs-repo";

export const runtime = "nodejs";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const type = searchParams.get("type"); // base|scenarios|sweeps

  const repo = resolveRepoRoot();

  let dir: string;
  if (type === "base") dir = path.join(repo, "configs");
  else if (type === "scenarios") dir = path.join(repo, "configs", "scenarios");
  else if (type === "sweeps") dir = path.join(repo, "configs", "sweeps");
  else return new Response(JSON.stringify({ error: "type must be base|scenarios|sweeps" }), { status: 400 });

  const ents = await fs.readdir(dir, { withFileTypes: true }).catch(() => []);
  const files = ents
    .filter((e) => e.isFile() && (e.name.endsWith(".yaml") || e.name.endsWith(".yml")))
    .map((e) => {
      if (type === "base") return path.join("configs", e.name);
      return path.join("configs", type, e.name);
    })
    .map((p) => p.replace(/\\/g, "/"));

  return Response.json({ files });
}
