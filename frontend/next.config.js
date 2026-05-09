/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: [],
  },
  turbopack: {
    // Silence the "multiple lockfiles" warning — our workspace root is the frontend dir
    root: __dirname,
  },
};

module.exports = nextConfig;
