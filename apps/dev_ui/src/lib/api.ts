async function safeJson<T>(res: Response): Promise<T> {
  const txt = await res.text();
  try {
    return JSON.parse(txt) as T;
  } catch {
    return ({ _raw: txt } as unknown) as T;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  // 프록시 경유: /api-proxy/api/health → http://localhost:8001/api/health
  const url = `/api-proxy${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { cache: "no-store" });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}\n${body}`);
  }
  return safeJson<T>(res);
}
