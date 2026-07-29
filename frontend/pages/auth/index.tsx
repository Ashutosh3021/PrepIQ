import { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/lib/context/AuthContext';
import { passwordStrengthHint } from '@/lib/auth';
import { getDashboardPath, getWizardPath } from '@/lib/utils/device';
import { apiFetch } from '@/lib/services/base.service';

type Mode = 'signin' | 'signup';

interface WizardStatus {
  completed: boolean;
}

export default function AuthPage() {
  const router = useRouter();
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<Mode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const strength = mode === 'signup' ? passwordStrengthHint(password) : null;

  const afterAuth = async () => {
    try {
      const status = await apiFetch<WizardStatus>('/wizard/status', { completed: false });
      router.replace(status.completed ? getDashboardPath() : getWizardPath());
    } catch {
      router.replace(getWizardPath());
    }
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setInfo('');
    setLoading(true);
    try {
      if (mode === 'signin') {
        await signIn(email, password);
        await afterAuth();
      } else {
        if (strength) {
          setError(strength);
          setLoading(false);
          return;
        }
        const { needsConfirmation } = await signUp(email, password, fullName);
        if (needsConfirmation) {
          setInfo('Account created. Please sign in with your email and password.');
          setMode('signin');
          setPassword('');
        } else {
          await afterAuth();
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    backgroundColor: 'var(--color-surface-container-lowest)',
    border: '1px solid var(--color-outline-variant)',
    color: 'var(--color-on-surface)',
    padding: '0.875rem 1rem',
    fontSize: '0.875rem',
    outline: 'none',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: '0.65rem',
    fontWeight: 700,
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    marginBottom: '0.5rem',
    color: 'var(--color-on-surface)',
    opacity: 0.55,
  };

  return (
    <div
      className="min-h-screen flex"
      style={{ backgroundColor: 'var(--color-background)', color: 'var(--color-on-surface)' }}
    >
      {/* Left decorative panel — desktop */}
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
          <p className="text-sm leading-relaxed" style={{ color: 'var(--color-on-surface)', opacity: 0.55 }}>
            Upload past papers, get AI-generated predictions, and track your progress — all in one
            focused environment built for B.Tech students.
          </p>
        </div>

        <div className="flex gap-12 border-t pt-8" style={{ borderColor: 'var(--color-outline-variant)' }}>
          {[
            { label: 'Active Students', value: '2,400+' },
            { label: 'Papers Processed', value: '18K+' },
            { label: 'Avg. Score Lift', value: '34%' },
          ].map((stat) => (
            <div key={stat.label}>
              <p className="text-2xl font-light tracking-tight mb-1" style={{ color: 'var(--color-on-surface)' }}>
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

      {/* Form panel */}
      <main className="flex-1 flex flex-col justify-center items-center px-6 py-12 sm:px-12 lg:px-16 xl:px-24">
        <div className="lg:hidden mb-10 text-center">
          <span
            className="text-xs font-bold uppercase tracking-[0.25em]"
            style={{ color: 'var(--color-primary)' }}
          >
            PrepIQ
          </span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-10">
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
              {mode === 'signin' ? 'Sign in to continue.' : 'Create your account.'}
            </h1>
          </div>

          {/* Tabs */}
          <div
            className="flex gap-6 mb-8 border-b"
            style={{ borderColor: 'var(--color-outline-variant)' }}
          >
            {(['signin', 'signup'] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m);
                  setError('');
                  setInfo('');
                }}
                className="pb-3 text-xs font-bold uppercase tracking-[0.15em] transition-opacity"
                style={{
                  color: 'var(--color-on-surface)',
                  opacity: mode === m ? 1 : 0.4,
                  borderBottom: mode === m ? '2px solid var(--color-primary)' : '2px solid transparent',
                  background: 'transparent',
                }}
              >
                {m === 'signin' ? 'Sign in' : 'Sign up'}
              </button>
            ))}
          </div>

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

          {info && (
            <div
              className="mb-6 px-4 py-3 text-sm font-medium border-l-2"
              style={{
                backgroundColor: 'var(--color-surface-container)',
                borderColor: 'var(--color-primary)',
                color: 'var(--color-on-surface)',
              }}
            >
              {info}
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-5">
            {mode === 'signup' && (
              <div>
                <label htmlFor="fullName" style={labelStyle}>
                  Full name
                </label>
                <input
                  id="fullName"
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={inputStyle}
                  placeholder="Optional"
                />
              </div>
            )}

            <div>
              <label htmlFor="email" style={labelStyle}>
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={inputStyle}
                placeholder="you@college.edu"
              />
            </div>

            <div>
              <label htmlFor="password" style={labelStyle}>
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ ...inputStyle, paddingRight: '3rem' }}
                  placeholder={mode === 'signup' ? 'Min 8 chars, mixed case, digit, symbol' : '••••••••'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold uppercase tracking-wider"
                  style={{ color: 'var(--color-primary)', background: 'transparent', border: 'none' }}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {mode === 'signup' && strength && password.length > 0 && (
                <p className="mt-2 text-xs" style={{ color: 'var(--color-error)', opacity: 0.9 }}>
                  {strength}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 py-4 mt-2 text-sm font-bold uppercase tracking-[0.15em] transition-opacity disabled:opacity-40"
              style={{
                backgroundColor: 'var(--color-primary)',
                color: 'var(--color-on-primary)',
                border: 'none',
              }}
            >
              {loading ? (
                <>
                  <SpinnerIcon />
                  Please wait…
                </>
              ) : mode === 'signin' ? (
                'Sign in'
              ) : (
                'Create account'
              )}
            </button>
          </form>

          <p className="mt-8 text-xs leading-relaxed" style={{ color: 'var(--color-on-surface)', opacity: 0.4 }}>
            By continuing, you agree to PrepIQ&apos;s terms of service. Passwords must be at least 8
            characters with upper, lower, digit, and special character.
          </p>
        </div>
      </main>
    </div>
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
      style={{ color: 'var(--color-on-primary)' }}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
