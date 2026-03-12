import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    formats: ["image/webp"],
    deviceSizes: [640, 750, 828, 1080],
    imageSizes: [32, 48, 64, 128],
  },
};

export default nextConfig;
