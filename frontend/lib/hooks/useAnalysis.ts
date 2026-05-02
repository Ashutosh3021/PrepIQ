import useSWR from 'swr';
import { analysisService } from '../services/analysis.service';
import type { Analysis } from '../types/analysis.types';

/**
 * H-16 / M-16: Fetch analysis data for the current user.
 * - Old: called analysisService.getByUserId(userId) → GET /analysis/{userId} (404)
 * - New: calls analysisService.getData() → GET /analysis/data (correct endpoint)
 * - Cache key is the stable string 'analysis/data' (no userId needed).
 */
export function useAnalysis() {
  const { data, error, isLoading, mutate } = useSWR<Analysis>(
    'analysis/data',
    () => analysisService.getData()
  );

  return {
    analysis: data ?? null,
    isLoading,
    error,
    refresh: mutate,
  };
}
