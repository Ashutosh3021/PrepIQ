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
  async redirects() {
    return [
      { source: "/login", destination: "/auth", permanent: true },
      { source: "/signup", destination: "/auth", permanent: true },
      { source: "/desktop/login", destination: "/auth", permanent: true },
      { source: "/desktop/signup", destination: "/auth", permanent: true },
    ];
  },
};

module.exports = nextConfig;
