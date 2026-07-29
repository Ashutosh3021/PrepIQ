// Classic email/password auth helpers (no OAuth)
const API_BASE =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

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
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Login failed");
  }
  const session: AuthSession = {
    access_token: data.access_token || data.token,
    user: data.user || { id: data.user_id, email },
  };
  persistSession(session);
  return session;
}

export async function signupWithEmail(
  email: string,
  password: string,
  fullName?: string
): Promise<AuthSession> {
  const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
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
    throw new Error(data.detail || data.message || "Signup failed");
  }
  const session: AuthSession = {
    access_token: data.access_token || data.token,
    user: data.user || { id: data.user_id, email, full_name: fullName },
  };
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
