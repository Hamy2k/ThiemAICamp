/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Security headers
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
  // Image optimization disabled for static export simplicity
  images: { unoptimized: true },
  // Keep bundle lean
  experimental: {
    optimizePackageImports: ["react-hook-form", "zod"],
  },
};

module.exports = nextConfig;
