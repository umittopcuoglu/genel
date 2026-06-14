/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "export",
  images: { unoptimized: true },
  basePath: process.env.PAGES_BASE_PATH || "",
  trailingSlash: true,
};
module.exports = nextConfig;
