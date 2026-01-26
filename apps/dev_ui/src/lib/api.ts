async function safeJson<T>(res: Response): Promise<T> {
  const txt = await res.text();
  try { return JSON.parse(txt) as T; } catch { return ({ _raw: txt } as unknown) as T; }
}

export async function apiGet<T>(path: string): Promise<T> {
  const url = `/api-proxy${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  return safeJson<T>(res);
}
