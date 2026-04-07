import Link from 'next/link';

/**
 * Universal not-found page for unknown routes.
 * Displays PrepIQ branding with links to both desktop and mobile dashboards.
 */
export default function NotFound() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-surface">
      <div className="text-center px-4">
        <h1 className="text-4xl font-serif italic text-primary mb-8">PrepIQ</h1>
        <p className="text-6xl font-light tracking-tighter text-gray-900 mb-4">404</p>
        <p className="text-xl text-on-surface-variant mb-8">Page not found</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/desktop/dashboard"
            className="px-6 py-3 bg-primary text-on-primary rounded font-medium hover:bg-primary-dark transition-colors"
          >
            Go to Dashboard
          </Link>
          <Link
            href="/mobile/dashboard"
            className="px-6 py-3 bg-surface-variant text-on-surface-variant rounded font-medium hover:bg-surface-variant-dark transition-colors border border-outline"
          >
            Go to Mobile
          </Link>
        </div>
      </div>
    </main>
  );
}
