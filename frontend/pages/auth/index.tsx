import { useState } from 'react';
import { supabase } from '@/lib/supabase';

type Provider = 'google' | 'github';

export default function AuthPage() {
  const [loadingProvider, setLoadingProvider] = useState<Provider | null>(null);
  const [error, setError] = useState('');

  const handleOAuth = async (provider: Provider) => {
    setLoadingProvider(provider);
    setError('');

    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        // Supabase will redirect here after OAuth completes
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (error) {
      setError(error.message);
      setLoadingProvider(null);
    }
    // On success, browser navigates away — no need to reset state
  };

  return (
    <div
      className="min-h-screen flex"
      style={{ backgroundColor: 'var(--color-background)', color: 'var(--color-on-surface)' }}
    >
      {/* ── Left decorative panel ── */}
      <aside
        className="hidden lg:flex lg:w-1/2 xl:w-[55%] flex-col justify-between p-16 relative overflow-hidden"
        style={{ backgroundColor: 'var(--color-surface-container-highest)' }}
      >
        <div>
          <span
            className="text-xs font-bold uppercase tracking-[0.25em]"
            style={{ color: 'var(--color-primary)' }}
          >
            PrepIQ
          </span>
        </div>

        <div className="max-w-sm">
          <p
            className="text-xs font-bold uppercase tracking-[0.2em] mb-8"
            style={{ color: 'var(--color-primary)' }}
          >
            AI-Powered Exam Prep
          </p>
          <h2
            className="text-5xl xl:text-6xl leading-tight mb-8"
            style={{
              fontFamily: 'var(--font-family-serif)',
              fontStyle: 'italic',
              color: 'var(--color-on-surface)',
              letterSpacing: '-0.02em',
            }}
          >
            Study smarter, not harder.
          </h2>
          <p
            className="text-sm leading-relaxed"
            style={{ color: 'var(--color-on-surface)', opacity: 0.55 }}
          >
            Upload past papers, get AI-generated predictions, and track your
            progress — all in one focused environment built for B.Tech students.
          </p>
        </div>

        <div
          className="flex gap-12 border-t pt-8"
          style={{ borderColor: 'var(--color-outline-variant)' }}
        >
          {[
            { label: 'Active Students', value: '2,400+' },
            { label: 'Papers Processed', value: '18K+' },
            { label: 'Avg. Score Lift', value: '34%' },
          ].map((stat) => (
            <div key={stat.label}>
              <p
                className="text-2xl font-light tracking-tight mb-1"
                style={{ color: 'var(--color-on-surface)' }}
              >
                {stat.value}
              </p>
              <p
                className="text-xs font-medium uppercase tracking-wider"
                style={{ color: 'var(--color-on-surface)', opacity: 0.45 }}
              >
                {stat.label}
              </p>
            </div>
          ))}
        </div>

        <div
          className="absolute bottom-0 right-0 w-64 h-64 opacity-10 pointer-events-none"
          style={{
            background: `radial-gradient(circle at bottom right, var(--color-primary) 0%, transparent 70%)`,
          }}
        />
      </aside>

      {/* ── Right form panel ── */}
      <main className="flex-1 flex flex-col justify-center items-center px-6 py-12 sm:px-12 lg:px-16 xl:px-24">
        {/* Mobile brand */}
        <div className="lg:hidden mb-10 text-center">
          <span
            className="text-xs font-bold uppercase tracking-[0.25em]"
            style={{ color: 'var(--color-primary)' }}
          >
            PrepIQ
          </span>
        </div>

        <div className="w-full max-w-sm">
          {/* Heading */}
          <div className="mb-12">
            <p
              className="text-xs font-bold uppercase tracking-[0.2em] mb-3"
              style={{ color: 'var(--color-primary)' }}
            >
              Welcome
            </p>
            <h1
              className="text-4xl sm:text-5xl"
              style={{
                fontFamily: 'var(--font-family-serif)',
                fontStyle: 'italic',
                color: 'var(--color-on-surface)',
                letterSpacing: '-0.02em',
                lineHeight: 1.15,
              }}
            >
              Sign in or create an account.
            </h1>
          </div>

          {/* Error */}
          {error && (
            <div
              className="mb-6 px-4 py-3 text-sm font-medium border-l-2"
              style={{
                backgroundColor: 'var(--color-error-container)',
                borderColor: 'var(--color-error)',
                color: 'var(--color-on-error-container)',
              }}
            >
              {error}
            </div>
          )}

          {/* OAuth buttons */}
          <div
            className="border-t"
            style={{ borderColor: 'var(--color-outline-variant)' }}
          >
            {/* Google */}
            <button
              onClick={() => handleOAuth('google')}
              disabled={loadingProvider !== null}
              className="w-full flex items-center gap-4 py-5 px-0 border-b transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed group"
              style={{
                borderColor: 'var(--color-outline-variant)',
                backgroundColor: 'transparent',
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor = 'var(--color-surface-container-low)')
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor = 'transparent')
              }
            >
              {loadingProvider === 'google' ? (
                <SpinnerIcon />
              ) : (
                <GoogleIcon />
              )}
              <span
                className="text-sm font-bold uppercase tracking-[0.15em]"
                style={{ color: 'var(--color-on-surface)' }}
              >
                Continue with Google
              </span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="ml-auto group-hover:translate-x-1 transition-transform duration-150"
                style={{ color: 'var(--color-primary)' }}
              >
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </button>

            {/* GitHub */}
            <button
              onClick={() => handleOAuth('github')}
              disabled={loadingProvider !== null}
              className="w-full flex items-center gap-4 py-5 px-0 border-b transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed group"
              style={{
                borderColor: 'var(--color-outline-variant)',
                backgroundColor: 'transparent',
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor = 'var(--color-surface-container-low)')
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor = 'transparent')
              }
            >
              {loadingProvider === 'github' ? (
                <SpinnerIcon />
              ) : (
                <GitHubIcon />
              )}
              <span
                className="text-sm font-bold uppercase tracking-[0.15em]"
                style={{ color: 'var(--color-on-surface)' }}
              >
                Continue with GitHub
              </span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="ml-auto group-hover:translate-x-1 transition-transform duration-150"
                style={{ color: 'var(--color-primary)' }}
              >
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </button>
          </div>

          {/* Fine print */}
          <p
            className="mt-8 text-xs leading-relaxed"
            style={{ color: 'var(--color-on-surface)', opacity: 0.4 }}
          >
            By continuing, you agree to PrepIQ's terms of service. New accounts
            are created automatically on first sign-in.
          </p>
        </div>
      </main>
    </div>
  );
}

// ── Icon helpers ─────────────────────────────────────────────────────────────

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
        fill="#4285F4"
      />
      <path
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
        fill="#34A853"
      />
      <path
        d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
        fill="#FBBC05"
      />
      <path
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
        fill="#EA4335"
      />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      style={{ color: 'var(--color-on-surface)' }}
    >
      <path d="M12 0C5.37 0 0 5.373 0 12c0 5.303 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.757-1.333-1.757-1.089-.745.083-.729.083-.729 1.205.084 1.84 1.237 1.84 1.237 1.07 1.834 2.807 1.304 3.492.997.108-.775.418-1.305.762-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.468-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.3 1.23A11.52 11.52 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.29-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222 0 1.606-.015 2.898-.015 3.293 0 .322.216.694.825.576C20.565 21.796 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
    </svg>
  );
}

function SpinnerIcon() {
  return (
    <svg
      className="animate-spin"
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      style={{ color: 'var(--color-primary)' }}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}