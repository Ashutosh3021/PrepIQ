/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable TypeScript errors during build (for production)
  typescript: {
    ignoreBuildErrors: false, // Set to true only if you have blocking type errors
  },
  
  // Image optimization (unoptimized for static export, remove if using Next.js Image Optimization)
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.supabase.co',
        pathname: '/**',
      },
    ],
  },
  
  // External packages that need server-side execution
  serverExternalPackages: ['sharp'],
  
  // Security headers for all routes
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' blob: data: https:",
              "font-src 'self'",
              "connect-src 'self' https://*.supabase.co https://*.onrender.com",
              "frame-ancestors 'none'",
              "form-action 'self'",
              "base-uri 'self'",
            ].join('; '),
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
        ],
      },
      {
        // Service Worker specific headers
        source: '/sw.js',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=0, must-revalidate',
          },
        ],
      },
    ];
  },
  
  // URL rewrites
  async rewrites() {
    return [
      // Development service worker
      {
        source: '/dev-sw.js',
        destination: '/sw.js',
      },
    ];
  },
  
  // Redirects
  async redirects() {
    return [
      // Force HTTPS in production
      {
        source: '/:path*',
        has: [
          {
            type: 'header',
            key: 'x-forwarded-proto',
            value: 'http',
          },
        ],
        destination: 'https://:path*',
        permanent: true,
      },
    ];
  },
  
  // Webpack configuration
  webpack: (config, { isServer }) => {
    // Suppress punycode deprecation warning
    config.ignoreWarnings = [
      { module: /node_modules\/punycode/ }
    ];
    return config;
  },
};

module.exports = nextConfig;
