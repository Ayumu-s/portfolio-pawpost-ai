import type { NextConfig } from "next";

const additionalDevOrigin = process.env.NEXT_PUBLIC_DEV_ORIGIN_HOST?.trim();

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Set NEXT_PUBLIC_DEV_ORIGIN_HOST when testing from another device on a LAN.
  allowedDevOrigins: [
    "localhost",
    "127.0.0.1",
    ...(additionalDevOrigin ? [additionalDevOrigin] : []),
  ],
};

export default nextConfig;
