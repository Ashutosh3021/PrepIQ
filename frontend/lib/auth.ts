/**
 * Classic email/password auth helpers (backend Pyronites).
 * Token stored in localStorage — no Supabase / OAuth.
 */

const TOKEN_KEY = 'prepiq_access_token';
const REFRESH_KEY = 'prepiq_refresh_token';
const USER_KEY = 'prepiq_user';

export interface AuthUser {
  id: string;
  email: string;
  full_name?: string;
  college_name?: string;
  program?: string;
  year_of_study?: string | number;
  wizard_completed?: boolean;
  access_token?: string;
  needs_confirmation?: boolean;
}

function apiBase(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL ?? '').replace(/\/$/, '');
  if (!raw) return '/api/v1';
  if (raw.endsWith('/api/v1')) return raw;
  return `${raw}/api/v1`;
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function persistSession(user: AuthUser, accessToken: string, refreshToken?: string | null) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(USER_KEY, JSON.stringify({ ...user, access_token: undefined }));
  if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === 'string') return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ');
    }
    if (body.message) return body.message;
  } catch {
    /* ignore */
  }
  return `${res.status} ${res.statusText}`;
}

export async function loginWithEmail(email: string, password: string): Promise<AuthUser> {
  const res = await fetch(`${apiBase()}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  const data = await res.json();
  if (!data.access_token) {
    throw new Error('Login succeeded but no access token was returned');
  }
  const user: AuthUser = {
    id: String(data.id),
    email: data.email,
    full_name: data.full_name,
    college_name: data.college_name,
    program: data.program,
    year_of_study: data.year_of_study,
  };
  persistSession(user, data.access_token, data.refresh_token);
  return user;
}

export async function signupWithEmail(payload: {
  email: string;
  password: string;
  full_name?: string;
}): Promise<{ user: AuthUser; needsConfirmation: boolean }> {
  const res = await fetch(`${apiBase()}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: payload.email.trim().toLowerCase(),
      password: payload.password,
      full_name: payload.full_name || '',
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  const data = await res.json();
  const user: AuthUser = {
    id: String(data.id),
    email: data.email,
    full_name: data.full_name,
    college_name: data.college_name,
    program: data.program,
    year_of_study: data.year_of_study,
    needs_confirmation: Boolean(data.needs_confirmation),
  };
  if (data.access_token) {
    persistSession(user, data.access_token, data.refresh_token);
    return { user, needsConfirmation: false };
  }
  return { user, needsConfirmation: true };
}

export async function fetchMe(token?: string): Promise<AuthUser> {
  const t = token || getStoredToken();
  if (!t) throw new Error('Not authenticated');
  const res = await fetch(`${apiBase()}/auth/me`, {
    headers: { Authorization: `Bearer ${t}` },
  });
  if (!res.ok) throw new Error(await parseError(res));
  const data = await res.json();
  const user: AuthUser = {
    id: String(data.id),
    email: data.email,
    full_name: data.full_name,
    college_name: data.college_name,
    program: data.program,
    year_of_study: data.year_of_study,
    wizard_completed: data.wizard_completed,
  };
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  return user;
}

export function passwordStrengthHint(password: string): string | null {
  if (password.length < 8) return 'At least 8 characters';
  if (!/[A-Z]/.test(password)) return 'Add an uppercase letter';
  if (!/[a-z]/.test(password)) return 'Add a lowercase letter';
  if (!/\d/.test(password)) return 'Add a digit';
  if (!/[!@#$%^&*()_+\-=[\]{}|;:',.<>?/`~]/.test(password)) return 'Add a special character';
  return null;
}
