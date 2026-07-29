/**
 * Base API service with mock/real switching.
 *
 * Token source: localStorage key "prepiq_access_token" (set by lib/auth.ts).
 */

import { clearSession } from '@/lib/auth';

const IS_MOCK = process.env.NEXT_PUBLIC_API_MODE === 'mock';
// NEXT_PUBLIC_API_URL should be the bare origin, e.g. https://host.railway.app
// (no trailing slash). /api/v1 is appended here so every apiFetch path resolves
// to the correct backend prefix.
const BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/v1`;

const TOKEN_KEY = 'prepiq_access_token';

/** Standard API response envelope from backend */
interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  timestamp?: string;
}

/**
 * Read the JWT from localStorage.
 * Synchronous — safe to call anywhere, returns null on SSR or when not logged in.
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Async wrapper kept for call-sites that previously awaited getAccessTokenAsync().
 * Simply resolves to the synchronous value so no migration is needed at call sites.
 */
export async function getAccessTokenAsync(): Promise<string | null> {
  return getAccessToken();
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
 * @param path      API path relative to BASE_URL (e.g. '/subjects')
 * @param mockData  Fallback data returned in mock mode
 * @param options   Standard RequestInit options (method, body, etc.)
 */
export async function apiFetch<T>(
  path: string,
  mockData: T,
  options?: RequestInit
): Promise<T> {
  if (IS_MOCK) {
    await new Promise((r) => setTimeout(r, 400));
    return mockData;
  }

  const url = `${BASE_URL}${path}`;
  const token = getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  // 401 — session expired; clear local session so the auth guard redirects
  if (res.status === 401) {
    clearSession();
    throw new Error('Session expired. Please sign in again.');
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

  if (isApiEnvelope<T>(body)) {
    if (body.status === 'error') {
      throw new Error(body.message ?? 'Unknown API error');
    }
    return body.data;
  }

  return body as T;
}
