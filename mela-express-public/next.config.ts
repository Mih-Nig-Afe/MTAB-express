import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Public tracking page — no auth, minimal config
  // API base URL injected at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  },
};

export default nextConfig;
