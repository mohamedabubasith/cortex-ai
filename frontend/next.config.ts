import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    console.log("Debug: Next.js Rewrite Backend URL:", backendUrl);
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`, // Proxy to Backend
      },
      {
        source: "/docs",
        destination: `${backendUrl}/docs`, // Proxy to Docs
      },
      {
        source: "/openapi.json",
        destination: `${backendUrl}/openapi.json`, // Proxy to OpenAPI
      },
    ];
  },
};

export default nextConfig;
