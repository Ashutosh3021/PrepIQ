/**
 * Base API service with mock/real switching.
 *
 * Token source: Supabase JS SDK session (supabase.auth.getSession).
 * Falls back to scanning localStorage for Supabase's own keys so existing
 * sessions are not broken on first load after the OAuth migration.
 */

import { supabase } from '@/lib/supabase';

const IS_MOCK = process.env.NEXT_PUBLIC_API_MODE === 'mock';
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

/** Standard API response envelope from backend */
interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  timestamp?: string;
}

/**
 * Get the current access token from the live Supabase session.
 * Exported so other callers (e.g. upload page) can read it directly.
 */
export async function getAccessTokenAsync(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

/**
 * Synchronous fallback — reads from Supabase's own localStorage keys.
 * Used in places that cannot await (e.g. SWR fetcher initialisation).
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const keys = Object.keys(localStorage).filter(
      (k) => k.includes('supabase') || k.includes('sb-')
    );
    for (const key of keys) {
      const item = localStorage.getItem(key);
      if (item) {
        const parsed = JSON.parse(item);
        const token =
          parsed.access_token ??
          parsed?.session?.access_token ??
          null;
        if (token) return token;
      }
    }
  } catch {
    // Corrupted storage — ignore
  }
  return null;
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

  // Prefer the async Supabase session; fall back to sync localStorage scan
  const token = (await getAccessTokenAsync()) ?? getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  // 401 — session expired; sign out so the auth guard redirects to /auth
  if (res.status === 401) {
    await supabase.auth.signOut();
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
