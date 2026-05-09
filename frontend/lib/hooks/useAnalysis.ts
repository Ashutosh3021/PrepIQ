import useSWR from 'swr';
import { analysisService } from '../services/analysis.service';
import { useAuth } from '../context/AuthContext';
import type { Analysis } from '../types/analysis.types';

/**
 * FIX 3: Scope the SWR cache key to the current user's ID so that switching
 * accounts never shows stale data from the previous user.
 * Key is null until the session resolves, which disables fetching.
 */
export function useAnalysis() {
  const { user } = useAuth();
  const cacheKey = user?.id ? `analysis/data/${user.id}` : null;

  const { data, error, isLoading, mutate } = useSWR<Analysis>(
    cacheKey,
    () => analysisService.getData()
  );

  return {
    analysis: data ?? null,
    isLoading,
    error,
    refresh: mutate,
  };
}
