import useSWR, { mutate as globalMutate } from 'swr';
import { useAuth } from '../context/AuthContext';
import { predictionsService, PredictionResponse } from '../services/predictions.service';

function cacheKey(userId: string, subjectId: number) {
  return `predictions/${subjectId}/${userId}`;
}

export function usePredictions(subjectId: number | null) {
  const { user } = useAuth();
  // Guard: only enable the fetch when subjectId is a valid, non-NaN number
  const validSubjectId =
    subjectId !== null && subjectId !== undefined && !isNaN(subjectId)
      ? subjectId
      : null;
  const key =
    user?.id && validSubjectId != null ? cacheKey(user.id, validSubjectId) : null;

  const { data, error, isLoading, mutate } = useSWR<PredictionResponse>(
    key,
    () => predictionsService.getBySubject(validSubjectId!)
  );

  const refresh = async (): Promise<void> => {
    if (!validSubjectId) return;
    const fresh = await predictionsService.refresh(validSubjectId);
    // Update local SWR cache with the refreshed data
    await mutate(fresh, false);
  };

  return {
    data: data ?? null,
    isLoading,
    error,
    refresh,
  };
}
