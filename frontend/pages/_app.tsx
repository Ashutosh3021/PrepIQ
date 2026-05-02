import { SWRConfig } from 'swr';
import type { AppProps } from 'next/app';
import { AuthProvider, useAuth } from '@/lib/context/AuthContext';
import { useRouter } from 'next/router';
import { useEffect, ReactNode } from 'react';
import '@/styles/globals.css';

// Protected route wrapper
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render children if not authenticated (will redirect)
  if (!user) {
    return null;
  }

  return <>{children}</>;
}

function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    // Skip auth check for login/signup pages
    if (router.pathname === '/login' || router.pathname === '/signup') {
      return;
    }

    if (!loading && !user) {
      router.push('/login');
    }
  }, [router, user, loading]);

  // Allow access to login/signup without protection
  if (router.pathname === '/login' || router.pathname === '/signup') {
    return <>{children}</>;
  }

  // Show loading for protected routes
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect if not authenticated
  if (!user) {
    return null;
  }

  return <>{children}</>;
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <SWRConfig
        value={{
          revalidateOnFocus: false,
          revalidateOnReconnect: true,
          dedupingInterval: 5000,
          errorRetryCount: 3,
        }}
      >
        <AuthGuard>
          <Component {...pageProps} />
        </AuthGuard>
      </SWRConfig>
    </AuthProvider>
  );
}
