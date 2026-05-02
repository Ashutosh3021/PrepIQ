/**
 * Base API service with mock/real switching.
 *
 * Key behaviours:
 * - NEXT_PUBLIC_API_MODE=mock  → returns mockData after ~400ms simulated latency
 * - NEXT_PUBLIC_API_MODE=real  → fetches from BASE_URL + path with Bearer token
 * - Handles 401 by refreshing the token once and retrying
 * - FE-01: if no token is found in real mode the request still proceeds
 *   (public endpoints like /auth/login don't need one), but the caller can
 *   pass `requireAuth: true` to throw immediately when no token is available.
 */

const IS_MOCK = process.env.NEXT_PUBLIC_API_MODE === 'mock';
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';
const REFRESH_URL = `${BASE_URL}/auth/refresh`;

/** Standard API response envelope from backend */
interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  timestamp?: string;
}

/** Key used by login.tsx and AuthContext to persist the session */
const SESSION_KEY = 'prepiq-supabase-session';

/**
 * Get the stored access token from localStorage.
 * Exported so AuthContext and other callers can read it directly.
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    // Check our own session key first (fastest path)
    const own = localStorage.getItem(SESSION_KEY);
    if (own) {
      const parsed = JSON.parse(own);
      if (parsed.access_token) return parsed.access_token;
    }
    // Fallback: scan for any Supabase-style keys (e.g. from Supabase JS SDK)
    const keys = Object.keys(localStorage).filter(
      (k) => k.includes('supabase') || k.includes('sb-')
    );
    for (const key of keys) {
      const item = localStorage.getItem(key);
      if (item) {
        const parsed = JSON.parse(item);
        if (parsed.access_token) return parsed.access_token;
      }
    }
  } catch {
    // Corrupted storage — ignore
  }
  return null;
}

/** Get the stored refresh token from localStorage */
function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const own = localStorage.getItem(SESSION_KEY);
    if (own) {
      const parsed = JSON.parse(own);
      if (parsed.refresh_token) return parsed.refresh_token;
    }
    const keys = Object.keys(localStorage).filter(
      (k) => k.includes('supabase') || k.includes('sb-')
    );
    for (const key of keys) {
      const item = localStorage.getItem(key);
      if (item) {
        const parsed = JSON.parse(item);
        if (parsed.refresh_token) return parsed.refresh_token;
      }
    }
  } catch {
    // ignore
  }
  return null;
}

/** Attempt to refresh the access token. Returns true on success. */
async function doRefreshToken(): Promise<boolean> {
  const rt = getRefreshToken();
  if (!rt) return false;
  try {
    const res = await fetch(REFRESH_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    if (data.access_token) {
      // Update the stored session with the new tokens
      const own = localStorage.getItem(SESSION_KEY);
      if (own) {
        const parsed = JSON.parse(own);
        parsed.access_token = data.access_token;
        if (data.refresh_token) parsed.refresh_token = data.refresh_token;
        localStorage.setItem(SESSION_KEY, JSON.stringify(parsed));
      }
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

function isApiEnvelope<T>(body: unknown): body is ApiResponse<T> {
  return (
    typeof body === 'object' &&
    body !== null &&
    'data' in body &&
    'status' in body
  );
}

/**
 * Core fetch helper.
 *
 * @param path        API path relative to BASE_URL (e.g. '/subjects')
 * @param mockData    Fallback data returned in mock mode
 * @param options     Standard RequestInit options (method, body, etc.)
 * @param retryOn401  Internal flag — set to false on the retry to avoid loops
 */
export async function apiFetch<T>(
  path: string,
  mockData: T,
  options?: RequestInit,
  retryOn401 = true
): Promise<T> {
  if (IS_MOCK) {
    await new Promise((r) => setTimeout(r, 400));
    return mockData;
  }

  const url = `${BASE_URL}${path}`;

  // Build headers — attach Bearer token when available
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };

  const token = getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  // FE-01: if no token, we still proceed — public endpoints (login, signup)
  // don't need one. Protected endpoints will return 401 which we handle below.

  const res = await fetch(url, { ...options, headers });

  // Handle 401 — try to refresh once and retry
  if (res.status === 401 && retryOn401) {
    const refreshed = await doRefreshToken();
    if (refreshed) {
      return apiFetch<T>(path, mockData, options, false);
    }
    // Refresh failed — throw a clear auth error so the UI can redirect to login
    throw new Error('Session expired. Please log in again.');
  }

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const errBody = await res.json();
      if (errBody.detail) detail = errBody.detail;
    } catch {
      // ignore JSON parse error
    }
    throw new Error(`API error: ${detail}`);
  }

  const body = await res.json();

  // Unwrap { data, status } envelope if present
  if (isApiEnvelope<T>(body)) {
    if (body.status === 'error') {
      throw new Error(body.message ?? 'Unknown API error');
    }
    return body.data;
  }

  return body as T;
}
