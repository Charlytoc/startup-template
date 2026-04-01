import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  distDir: ".next",
  outputFileTracingRoot: "/app",
};

export default nextConfig;
