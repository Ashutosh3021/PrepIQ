import { SWRConfig } from 'swr';
import type { AppProps } from 'next/app';
import { AuthProvider, useAuth } from '@/lib/context/AuthContext';
import { useRouter } from 'next/router';
import { useEffect, useRef, ReactNode } from 'react';
import '@/styles/globals.css';

// Routes that don't require authentication
const PUBLIC_ROUTES = ['/auth', '/auth/callback'];

// Wizard routes — authenticated but allowed before wizard completion
const WIZARD_ROUTES = ['/desktop/wizard', '/mobile/wizard'];

function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();

  const isPublic = PUBLIC_ROUTES.some(
    (route) => router.pathname === route || router.pathname.startsWith(route + '/')
  );
  const isWizard = WIZARD_ROUTES.includes(router.pathname);

  // Keep isPublic/isWizard in refs so the auth effect reads current values
  // without listing them as deps (they change every render as computed values).
  const isPublicRef = useRef(isPublic);
  const isWizardRef = useRef(isWizard);
  useEffect(() => {
    isPublicRef.current = isPublic;
    isWizardRef.current = isWizard;
  });

  useEffect(() => {
    if (loading) return;
    if (!isAuthenticated && !isPublicRef.current && !isWizardRef.current) {
      router.replace('/auth');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, loading]);

  // Allow public and wizard routes through immediately
  if (isPublic || isWizard) {
    return <>{children}</>;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <svg
          className="animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          style={{ color: 'var(--color-primary, #4f46e5)' }}
        >
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return <>{children}</>;
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <SWRConfig
        value={{
          revalidateOnFocus: false,
          revalidateOnReconnect: false,
          dedupingInterval: 10000,
          errorRetryCount: 0,
        }}
      >
        <AuthGuard>
          <Component {...pageProps} />
        </AuthGuard>
      </SWRConfig>
    </AuthProvider>
  );
}
