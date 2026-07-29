/**
 * Base API service — Bearer token from classic PrepIQ auth (localStorage).
 */

import { clearSession, getStoredToken } from '@/lib/auth';

const IS_MOCK = process.env.NEXT_PUBLIC_API_MODE === 'mock';

function resolveBaseUrl(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL ?? '').replace(/\/$/, '');
  if (!raw) return '/api/v1';
  // Avoid double /api/v1 when env already includes it
  if (raw.endsWith('/api/v1')) return raw;
  return `${raw}/api/v1`;
}

const BASE_URL = resolveBaseUrl();

interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  timestamp?: string;
}

export async function getAccessTokenAsync(): Promise<string | null> {
  return getStoredToken();
}

export function getAccessToken(): string | null {
  return getStoredToken();
}

function isApiEnvelope<T>(body: unknown): body is ApiResponse<T> {
  return (
    typeof body === 'object' &&
    body !== null &&
    'data' in body &&
    'status' in body
  );
}

export async function apiFetch<T>(
  path: string,
  mockData: T,
  options?: RequestInit
): Promise<T> {
  if (IS_MOCK) {
    await new Promise((r) => setTimeout(r, 400));
    return mockData;
  }

  const url = `${BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const token = getStoredToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    clearSession();
    throw new Error('Session expired. Please sign in again.');
  }

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const errBody = await res.json();
      if (typeof errBody.detail === 'string') detail = errBody.detail;
      else if (errBody.message) detail = errBody.message;
    } catch {
      /* ignore */
    }
    throw new Error(`API error: ${detail}`);
  }

  // Some endpoints return empty body
  const text = await res.text();
  if (!text) return mockData;

  const body = JSON.parse(text);

  if (isApiEnvelope<T>(body)) {
    if (body.status === 'error') {
      throw new Error(body.message ?? 'Unknown API error');
    }
    return body.data;
  }

  return body as T;
}
