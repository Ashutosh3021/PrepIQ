import { useState, FormEvent } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import Link from "next/link";
import { useAuth } from "@/lib/context/AuthContext";
import { isStrongPassword } from "@/lib/auth";

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
      setError("Email and password are required.");
      return;
    }

    if (mode === "signup") {
      const check = isStrongPassword(password);
      if (!check.ok) {
        setError(check.message ?? "Weak password.");
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
      setError(
        err instanceof Error ? err.message : "Something went wrong. Try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Head>
        <title>
          {mode === "login" ? "Sign in" : "Create account"} · PrepIQ
        </title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div
        className="min-h-screen flex"
        style={{
          backgroundColor: "var(--color-background)",
          color: "var(--color-on-surface)",
          fontFamily: "var(--font-family-sans)",
        }}
      >
        {/* ── Left decorative panel (desktop only) ── */}
        <aside
          className="hidden lg:flex lg:w-1/2 xl:w-[55%] flex-col justify-between p-16 relative overflow-hidden"
          style={{ backgroundColor: "var(--color-surface-container-highest)" }}
        >
          {/* Top wordmark */}
          <div>
            <span
              className="text-xs font-bold uppercase tracking-[0.25em]"
              style={{ color: "var(--color-primary)" }}
            >
              PrepIQ
            </span>
          </div>

          {/* Centre copy */}
          <div className="max-w-sm">
            <p
              className="text-xs font-bold uppercase tracking-[0.2em] mb-8"
              style={{ color: "var(--color-primary)" }}
            >
              AI-Powered Exam Prep
            </p>
            <h2
              className="text-5xl xl:text-6xl leading-tight mb-8"
              style={{
                fontFamily: "var(--font-family-serif)",
                fontStyle: "italic",
                color: "var(--color-on-surface)",
                letterSpacing: "-0.02em",
              }}
            >
              Study smarter,
              <br />
              not harder.
            </h2>
            <p
              className="text-sm leading-relaxed"
              style={{
                color: "var(--color-on-surface)",
                opacity: 0.55,
              }}
            >
              Upload past papers, get AI-generated predictions, and track your
              progress — all in one focused environment built for B.Tech
              students.
            </p>
          </div>

          {/* Bottom stats */}
          <div
            className="flex gap-12 border-t pt-8"
            style={{ borderColor: "var(--color-outline-variant)" }}
          >
            {[
              { label: "Active Students", value: "2,400+" },
              { label: "Papers Processed", value: "18K+" },
              { label: "Avg. Score Lift", value: "34%" },
            ].map((stat) => (
              <div key={stat.label}>
                <p
                  className="text-2xl font-light tracking-tight mb-1"
                  style={{ color: "var(--color-on-surface)" }}
                >
                  {stat.value}
                </p>
                <p
                  className="text-xs font-medium uppercase tracking-wider"
                  style={{ color: "var(--color-on-surface)", opacity: 0.45 }}
                >
                  {stat.label}
                </p>
              </div>
            ))}
          </div>

          {/* Subtle radial accent */}
          <div
            className="absolute bottom-0 right-0 w-72 h-72 pointer-events-none"
            style={{
              background: `radial-gradient(circle at bottom right, var(--color-primary) 0%, transparent 70%)`,
              opacity: 0.08,
            }}
          />
        </aside>

        {/* ── Right form panel ── */}
        <main className="flex-1 flex flex-col justify-center items-center px-6 py-12 sm:px-12 lg:px-16 xl:px-24">
          {/* Mobile wordmark */}
          <div className="lg:hidden mb-10 text-center">
            <span
              className="text-xs font-bold uppercase tracking-[0.25em]"
              style={{ color: "var(--color-primary)" }}
            >
              PrepIQ
            </span>
          </div>

          <div className="w-full max-w-sm">
            {/* Heading */}
            <div className="mb-10">
              <p
                className="text-xs font-bold uppercase tracking-[0.2em] mb-3"
                style={{ color: "var(--color-primary)" }}
              >
                {mode === "login" ? "Welcome back" : "Get started"}
              </p>
              <h1
                className="text-4xl sm:text-5xl"
                style={{
                  fontFamily: "var(--font-family-serif)",
                  fontStyle: "italic",
                  color: "var(--color-on-surface)",
                  letterSpacing: "-0.02em",
                  lineHeight: 1.15,
                }}
              >
                {mode === "login"
                  ? "Sign in to your account."
                  : "Create your account."}
              </h1>
            </div>

            {/* Mode toggle */}
            <div
              className="flex gap-8 mb-10 border-b"
              style={{ borderColor: "var(--color-outline-variant)" }}
            >
              {(["login", "signup"] as Mode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => {
                    setMode(m);
                    setError(null);
                  }}
                  className="pb-3 text-xs font-bold uppercase tracking-[0.2em] transition-all duration-150"
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    borderBottom: `2px solid ${
                      mode === m
                        ? "var(--color-primary)"
                        : "transparent"
                    }`,
                    color:
                      mode === m
                        ? "var(--color-primary)"
                        : "var(--color-on-surface)",
                    opacity: mode === m ? 1 : 0.4,
                    marginBottom: "-1px",
                  }}
                >
                  {m === "login" ? "Sign in" : "Sign up"}
                </button>
              ))}
            </div>

            {/* Error */}
            {error && (
              <div
                className="mb-6 px-4 py-3 text-sm border-l-2"
                style={{
                  backgroundColor: "var(--color-error-container)",
                  borderColor: "var(--color-error)",
                  color: "var(--color-on-error-container)",
                }}
                role="alert"
              >
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} noValidate className="space-y-6">
              {mode === "signup" && (
                <div className="space-y-2">
                  <label
                    htmlFor="fullName"
                    className="block text-[10px] font-bold uppercase tracking-[0.2em]"
                    style={{ color: "var(--color-primary)" }}
                  >
                    Full Name
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    autoComplete="name"
                    placeholder="Your full name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full bg-transparent border-b-2 px-0 py-3 text-sm outline-none transition-all duration-150 placeholder:opacity-30"
                    style={{
                      borderColor: "var(--color-outline-variant)",
                      color: "var(--color-on-surface)",
                    }}
                    onFocus={(e) =>
                      (e.currentTarget.style.borderColor =
                        "var(--color-primary)")
                    }
                    onBlur={(e) =>
                      (e.currentTarget.style.borderColor =
                        "var(--color-outline-variant)")
                    }
                  />
                </div>
              )}

              <div className="space-y-2">
                <label
                  htmlFor="email"
                  className="block text-[10px] font-bold uppercase tracking-[0.2em]"
                  style={{ color: "var(--color-primary)" }}
                >
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-transparent border-b-2 px-0 py-3 text-sm outline-none transition-all duration-150 placeholder:opacity-30"
                  style={{
                    borderColor: "var(--color-outline-variant)",
                    color: "var(--color-on-surface)",
                  }}
                  onFocus={(e) =>
                    (e.currentTarget.style.borderColor = "var(--color-primary)")
                  }
                  onBlur={(e) =>
                    (e.currentTarget.style.borderColor =
                      "var(--color-outline-variant)")
                  }
                />
              </div>

              <div className="space-y-2">
                <label
                  htmlFor="password"
                  className="block text-[10px] font-bold uppercase tracking-[0.2em]"
                  style={{ color: "var(--color-primary)" }}
                >
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete={
                      mode === "login" ? "current-password" : "new-password"
                    }
                    placeholder={
                      mode === "signup" ? "Min. 8 chars, A-z, 0-9" : "••••••••"
                    }
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full bg-transparent border-b-2 px-0 py-3 pr-16 text-sm outline-none transition-all duration-150 placeholder:opacity-30"
                    style={{
                      borderColor: "var(--color-outline-variant)",
                      color: "var(--color-on-surface)",
                    }}
                    onFocus={(e) =>
                      (e.currentTarget.style.borderColor =
                        "var(--color-primary)")
                    }
                    onBlur={(e) =>
                      (e.currentTarget.style.borderColor =
                        "var(--color-outline-variant)")
                    }
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    className="absolute right-0 top-1/2 -translate-y-1/2 text-[10px] font-bold uppercase tracking-[0.15em] transition-opacity duration-150 hover:opacity-70"
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: "var(--color-primary)",
                    }}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                {mode === "signup" && (
                  <p
                    className="text-xs mt-1"
                    style={{
                      color: "var(--color-on-surface)",
                      opacity: 0.45,
                    }}
                  >
                    At least 8 characters · one uppercase · one lowercase · one
                    number
                  </p>
                )}
              </div>

              {/* Submit */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={submitting || authLoading}
                  className="w-full flex items-center justify-center gap-3 py-4 px-6 text-xs font-bold uppercase tracking-[0.2em] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{
                    backgroundColor: "var(--color-primary)",
                    color: "var(--color-on-primary)",
                    border: "none",
                    cursor: submitting || authLoading ? "not-allowed" : "pointer",
                  }}
                  onMouseEnter={(e) => {
                    if (!submitting && !authLoading)
                      e.currentTarget.style.opacity = "0.88";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = "1";
                  }}
                >
                  {submitting && (
                    <svg
                      className="animate-spin"
                      xmlns="http://www.w3.org/2000/svg"
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                  )}
                  {submitting
                    ? mode === "login"
                      ? "Signing in…"
                      : "Creating account…"
                    : mode === "login"
                    ? "Sign in"
                    : "Create account"}
                </button>
              </div>
            </form>

            {/* Footer toggle */}
            <p
              className="mt-8 text-xs"
              style={{ color: "var(--color-on-surface)", opacity: 0.5 }}
            >
              {mode === "login" ? (
                <>
                  New to PrepIQ?{" "}
                  <button
                    type="button"
                    onClick={() => setMode("signup")}
                    className="font-bold underline underline-offset-2 transition-opacity hover:opacity-70"
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: "var(--color-on-surface)",
                      opacity: 1,
                    }}
                  >
                    Create an account
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => setMode("login")}
                    className="font-bold underline underline-offset-2 transition-opacity hover:opacity-70"
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: "var(--color-on-surface)",
                      opacity: 1,
                    }}
                  >
                    Sign in
                  </button>
                </>
              )}
            </p>

            <p className="mt-4 text-xs">
              <Link
                href="/"
                className="transition-opacity hover:opacity-70"
                style={{ color: "var(--color-primary)", opacity: 0.6 }}
              >
                ← Back to home
              </Link>
            </p>
          </div>
        </main>
      </div>
    </>
  );
}
