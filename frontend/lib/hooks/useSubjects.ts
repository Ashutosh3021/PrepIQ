import useSWR from 'swr';
import { subjectsService } from '../services/subjects.service';
import type { Subject } from '../types/subject.types';

// Get user ID from localStorage to scope the SWR cache per user.
function getUserId(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const keys = Object.keys(localStorage).filter(
      (k) => k.includes('supabase') || k.includes('sb-') || k === 'prepiq-supabase-session'
    );
    for (const key of keys) {
      const item = localStorage.getItem(key);
      if (item) {
        const parsed = JSON.parse(item);
        if (parsed.user?.id) return parsed.user.id;
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
