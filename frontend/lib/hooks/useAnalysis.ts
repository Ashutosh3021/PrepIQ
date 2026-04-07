import useSWR, { mutate } from 'swr';
import { analysisService } from '../services/analysis.service';
import type { Analysis } from '../types/analysis.types';

export function useAnalysis(userId: string) {
  const { data, error, isLoading } = useSWR<Analysis>(
    userId ? `analysis/${userId}` : null,
    () => analysisService.getByUserId(userId)
  );
  return { analysis: data ?? null, isLoading, error };
}
