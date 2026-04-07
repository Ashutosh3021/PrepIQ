/**
 * Base API service with mock/real switching (UTIL-04)
 *
 * Switches between mock and real implementations via env var NEXT_PUBLIC_API_MODE.
 * All domain services (subjects, tests, analysis, tutor, user) build on this foundation.
 *
 * Key behaviors:
 * - When NEXT_PUBLIC_API_MODE=mock: returns mockData after ~400ms simulated latency
 * - When NEXT_PUBLIC_API_MODE=real: fetches from BASE_URL + path
 * - Unwraps ApiResponse<T> envelope { data: T, status, message } in real mode
 * - Throws on non-2xx responses in real mode
 * - Generic type T ensures type safety at call site
 */

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
 * Checks if a response matches the ApiResponse<T> envelope shape.
 * Returns true if the response has a `data` property and `status` field.
 */
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
    // Simulate ~400ms latency so UI spinner states work correctly
    await new Promise(resolve => setTimeout(resolve, 400));
    return mockData;
  }

  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  const body = await res.json();

  // Unwrap ApiResponse<T> envelope if present
  if (isApiEnvelope<T>(body)) {
    if (body.status === 'error') {
      throw new Error(body.message ?? 'Unknown API error');
    }
    return body.data;
  }

  // Direct response (no envelope) — return as-is
  return body as T;
}
