import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    externalDir: true,
    typedRoutes: false,
  },
};

export default nextConfig;
