"use client";
import { useState, FormEvent } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import Link from "next/link";
import { useAuth } from "../../lib/context/AuthContext";
import { isStrongPassword } from "../../lib/auth";

type Mode = "login" | "signup";

export default function AuthPage() {
  const router = useRouter();
  const { login, signup, isAuthenticated, loading: authLoading } = useAuth();

  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Redirect if already logged in
  if (!authLoading && isAuthenticated) {
    if (typeof window !== "undefined") router.replace("/dashboard");
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError("Email and password are required");
      return;
    }

    if (mode === "signup") {
      const check = isStrongPassword(password);
      if (!check.ok) {
        setError(check.message || "Weak password");
        return;
      }
    }

    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await signup(email, password, fullName || undefined);
      }
      router.replace("/dashboard");
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Something went wrong. Try again.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Head>
        <title>{mode === "login" ? "Sign in" : "Create account"} · PrepIQ</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="auth-page">
        <div className="auth-card">
          {/* Brand */}
          <div className="brand">
            <div className="logo">P</div>
            <h1>PrepIQ</h1>
            <p className="tagline">Smart exam prep, powered by AI</p>
          </div>

          {/* Tabs */}
          <div className="tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={mode === "login"}
              className={mode === "login" ? "tab active" : "tab"}
              onClick={() => {
                setMode("login");
                setError(null);
              }}
            >
              Sign in
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === "signup"}
              className={mode === "signup" ? "tab active" : "tab"}
              onClick={() => {
                setMode("signup");
                setError(null);
              }}
            >
              Sign up
            </button>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            {mode === "signup" && (
              <div className="field">
                <label htmlFor="fullName">Full name</label>
                <input
                  id="fullName"
                  type="text"
                  autoComplete="name"
                  placeholder="Your name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
            )}

            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <div className="password-wrap">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                  placeholder={
                    mode === "signup"
                      ? "Min. 8 chars, upper, lower, number"
                      : "••••••••"
                  }
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="toggle-pw"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
              {mode === "signup" && (
                <p className="hint">
                  At least 8 characters, one uppercase, one lowercase, one
                  number.
                </p>
              )}
            </div>

            {error && (
              <div className="error" role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="submit"
              disabled={submitting || authLoading}
            >
              {submitting
                ? mode === "login"
                  ? "Signing in…"
                  : "Creating account…"
                : mode === "login"
                ? "Sign in"
                : "Create account"}
            </button>
          </form>

          <p className="footer-note">
            {mode === "login" ? (
              <>
                New to PrepIQ?{" "}
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => setMode("signup")}
                >
                  Create an account
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => setMode("login")}
                >
                  Sign in
                </button>
              </>
            )}
          </p>

          <p className="back">
            <Link href="/">← Back to home</Link>
          </p>
        </div>
      </div>

      <style jsx>{`
        .auth-page {
          min-height: 100vh;
          min-height: 100dvh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1.25rem;
          background: linear-gradient(
            160deg,
            #0f172a 0%,
            #1e1b4b 45%,
            #312e81 100%
          );
          font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
        }
        .auth-card {
          width: 100%;
          max-width: 420px;
          background: #ffffff;
          border-radius: 16px;
          padding: 1.75rem 1.5rem 1.5rem;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
        }
        .brand {
          text-align: center;
          margin-bottom: 1.5rem;
        }
        .logo {
          width: 48px;
          height: 48px;
          margin: 0 auto 0.75rem;
          border-radius: 12px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: #fff;
          font-weight: 700;
          font-size: 1.35rem;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .brand h1 {
          margin: 0;
          font-size: 1.5rem;
          font-weight: 700;
          color: #0f172a;
          letter-spacing: -0.02em;
        }
        .tagline {
          margin: 0.35rem 0 0;
          font-size: 0.875rem;
          color: #64748b;
        }
        .tabs {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.35rem;
          background: #f1f5f9;
          padding: 0.3rem;
          border-radius: 10px;
          margin-bottom: 1.35rem;
        }
        .tab {
          border: none;
          background: transparent;
          padding: 0.55rem 0.75rem;
          border-radius: 8px;
          font-size: 0.9rem;
          font-weight: 600;
          color: #64748b;
          cursor: pointer;
          transition: background 0.15s, color 0.15s;
        }
        .tab.active {
          background: #fff;
          color: #4f46e5;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        }
        .field {
          margin-bottom: 1rem;
        }
        .field label {
          display: block;
          font-size: 0.8rem;
          font-weight: 600;
          color: #334155;
          margin-bottom: 0.35rem;
        }
        .field input {
          width: 100%;
          box-sizing: border-box;
          padding: 0.7rem 0.85rem;
          border: 1.5px solid #e2e8f0;
          border-radius: 10px;
          font-size: 0.95rem;
          color: #0f172a;
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }
        .field input:focus {
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
        }
        .password-wrap {
          position: relative;
        }
        .password-wrap input {
          padding-right: 3.5rem;
        }
        .toggle-pw {
          position: absolute;
          right: 0.5rem;
          top: 50%;
          transform: translateY(-50%);
          border: none;
          background: transparent;
          color: #6366f1;
          font-size: 0.8rem;
          font-weight: 600;
          cursor: pointer;
          padding: 0.25rem 0.4rem;
        }
        .hint {
          margin: 0.35rem 0 0;
          font-size: 0.75rem;
          color: #94a3b8;
        }
        .error {
          background: #fef2f2;
          color: #b91c1c;
          border: 1px solid #fecaca;
          border-radius: 8px;
          padding: 0.65rem 0.85rem;
          font-size: 0.85rem;
          margin-bottom: 1rem;
        }
        .submit {
          width: 100%;
          border: none;
          border-radius: 10px;
          padding: 0.8rem 1rem;
          font-size: 0.95rem;
          font-weight: 600;
          color: #fff;
          background: linear-gradient(135deg, #4f46e5, #7c3aed);
          cursor: pointer;
          transition: opacity 0.15s, transform 0.1s;
          margin-top: 0.25rem;
        }
        .submit:hover:not(:disabled) {
          opacity: 0.95;
        }
        .submit:active:not(:disabled) {
          transform: scale(0.99);
        }
        .submit:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }
        .footer-note {
          text-align: center;
          margin: 1.25rem 0 0;
          font-size: 0.875rem;
          color: #64748b;
        }
        .link-btn {
          border: none;
          background: none;
          color: #4f46e5;
          font-weight: 600;
          font-size: inherit;
          cursor: pointer;
          padding: 0;
        }
        .back {
          text-align: center;
          margin: 1rem 0 0;
          font-size: 0.8rem;
        }
        .back a {
          color: #94a3b8;
          text-decoration: none;
        }
        .back a:hover {
          color: #64748b;
        }
        /* Desktop */
        @media (min-width: 640px) {
          .auth-card {
            padding: 2rem 2rem 1.75rem;
          }
        }
      `}</style>
    </>
  );
}
