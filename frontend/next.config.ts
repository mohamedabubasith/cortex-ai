import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://backend:8000/api/:path*", // Proxy to Backend
      },
      {
        source: "/docs",
        destination: "http://backend:8000/docs", // Proxy to Docs
      },
      {
        source: "/openapi.json",
        destination: "http://backend:8000/openapi.json", // Proxy to OpenAPI
      },
    ];
  },
};

export default nextConfig;
