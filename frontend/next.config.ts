import type { NextConfig } from "next";

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig: NextConfig = {
  // Required for Docker standalone build
  output: 'standalone',

  // Image optimization - simplified for production
  images: {
    unoptimized: true, // Disable Next.js image optimization for Docker
  },
};

export default nextConfig;
