// Classic email/password auth helpers (no OAuth)
// Email verification is disabled at the app layer for now.
const API_BASE = (
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000"
).replace(/\/$/, "");

export type AuthUser = {
  id: string;
  email: string;
  full_name?: string | null;
};

export type AuthSession = {
  access_token: string;
  user: AuthUser;
};

const TOKEN_KEY = "prepiq_access_token";
const USER_KEY = "prepiq_user";

function authApiBase(): string {
  if (API_BASE.endsWith("/api/v1")) return API_BASE;
  return `${API_BASE}/api/v1`;
}

function mapAuthResponse(
  data: Record<string, any>,
  fallbackEmail: string,
  fullName?: string | null
): AuthSession {
  const access_token = data.access_token || data.token;
  if (!access_token) {
    throw new Error(
      data.detail ||
        "Authentication succeeded but no access token was returned. " +
          "If email confirmation is enabled on the auth provider, disable it."
    );
  }

  const nested = data.user && typeof data.user === "object" ? data.user : null;
  const id =
    data.id || nested?.id || data.user_id || nested?.user_id || "";
  const email =
    data.email || nested?.email || fallbackEmail;
  const full_name =
    data.full_name ?? nested?.full_name ?? fullName ?? null;

  if (!id) {
    throw new Error("Auth response missing user id");
  }

  return {
    access_token: String(access_token),
    user: {
      id: String(id),
      email: String(email).trim().toLowerCase(),
      full_name: full_name != null ? String(full_name) : null,
    },
  };
}

function formatApiError(data: any, fallback: string): string {
  const detail = data?.detail ?? data?.message;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "string" ? d : d?.msg || JSON.stringify(d)))
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    return detail.message || detail.msg || JSON.stringify(detail);
  }
  return fallback;
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function persistSession(session: AuthSession) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, session.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(session.user));
}

export function clearSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function loginWithEmail(
  email: string,
  password: string
): Promise<AuthSession> {
  const res = await fetch(`${authApiBase()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(formatApiError(data, "Login failed"));
  }
  const session = mapAuthResponse(data, email);
  persistSession(session);
  return session;
}

export async function signupWithEmail(
  email: string,
  password: string,
  fullName?: string
): Promise<AuthSession> {
  const res = await fetch(`${authApiBase()}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password,
      full_name: fullName?.trim() || null,
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(formatApiError(data, "Signup failed"));
  }
  const session = mapAuthResponse(data, email, fullName);
  persistSession(session);
  return session;
}

export function isStrongPassword(password: string): {
  ok: boolean;
  message?: string;
} {
  if (password.length < 8) {
    return { ok: false, message: "Password must be at least 8 characters" };
  }
  if (!/[A-Z]/.test(password)) {
    return { ok: false, message: "Include at least one uppercase letter" };
  }
  if (!/[a-z]/.test(password)) {
    return { ok: false, message: "Include at least one lowercase letter" };
  }
  if (!/[0-9]/.test(password)) {
    return { ok: false, message: "Include at least one number" };
  }
  return { ok: true };
}
