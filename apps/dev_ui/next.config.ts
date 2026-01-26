// apps/dev_ui/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";
    return [{ source: "/api-proxy/:path*", destination: `${base}/:path*` }];
  },
};
export default nextConfig;
