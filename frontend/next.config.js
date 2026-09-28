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
      // Auth aliases
      { source: "/login", destination: "/auth", permanent: true },
      { source: "/signup", destination: "/auth", permanent: true },
      { source: "/signin", destination: "/auth", permanent: true },
      { source: "/register", destination: "/auth", permanent: true },
      { source: "/auth/login", destination: "/auth", permanent: true },
      { source: "/auth/signup", destination: "/auth", permanent: true },
      { source: "/desktop/login", destination: "/auth", permanent: true },
      { source: "/desktop/signup", destination: "/auth", permanent: true },
      { source: "/mobile/login", destination: "/auth", permanent: true },
      { source: "/mobile/signup", destination: "/auth", permanent: true },

      // The old post-login target — /dashboard has no page and 404'd.
      // Canonical surface for a wide screen is the desktop dashboard.
      { source: "/dashboard", destination: "/desktop/dashboard", permanent: true },
      { source: "/dashboard/:path*", destination: "/desktop/dashboard", permanent: true },

      // Device-less wizard deep link (the wizard lives under each variant)
      { source: "/wizard", destination: "/desktop/wizard", permanent: true },
    ];
  },
};

module.exports = nextConfig;
