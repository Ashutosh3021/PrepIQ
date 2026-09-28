import useSWR from 'swr';
import { subjectsService } from '../services/subjects.service';
import { getStoredUser } from '../auth';
import type { Subject } from '../types/subject.types';

// Fallback: read the user id straight from the JWT sub claim.
function decodeJwtSub(token: string): string | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    const parsed = JSON.parse(json);
    return typeof parsed?.sub === 'string' && parsed.sub ? parsed.sub : null;
  } catch {
    return null;
  }
}

// Get user ID from localStorage to scope the SWR cache per user.
function getUserId(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    // Current session shape: lib/auth.ts stores {id, email, ...} under 'prepiq_user'.
    const stored = getStoredUser();
    if (stored?.id) return stored.id;

    // Token is always present while signed in; its sub claim is the user id.
    const token = localStorage.getItem('prepiq_access_token');
    const sub = token ? decodeJwtSub(token) : null;
    if (sub) return sub;

    // Legacy sessions (removed Supabase auth) — accept either nesting.
    const keys = Object.keys(localStorage).filter(
      (k) => k.includes('supabase') || k.includes('sb-') || k === 'prepiq-supabase-session'
    );
    for (const key of keys) {
      const item = localStorage.getItem(key);
      if (item) {
        const parsed = JSON.parse(item);
        const id = parsed?.user?.id ?? parsed?.id;
        if (id) return String(id);
      }
    }
  } catch {
    // ignore
  }
  return null;
}

// SWR fetcher that ignores the cache-key argument and always calls the service.
// The cache key includes the userId so different users get isolated caches,
// but the actual fetch is always the same authenticated call.
const fetchSubjects = (_key: unknown) => subjectsService.getAll();

export function useSubjects() {
  const userId = getUserId();
  // Scope cache key to the current user; null key disables fetching until userId resolves.
  const cacheKey = userId ? ['subjects', userId] : null;

  const { data, error, isLoading, mutate } = useSWR<Subject[]>(cacheKey, fetchSubjects, {
    revalidateOnFocus: false,
  });

  return {
    subjects: data ?? [],
    isLoading,
    error,
    refresh: mutate,
  };
}
