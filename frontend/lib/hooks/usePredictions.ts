import useSWR, { mutate as globalMutate } from 'swr';
import { useAuth } from '../context/AuthContext';
import { predictionsService, PredictionResponse } from '../services/predictions.service';

function cacheKey(userId: string, subjectId: string) {
  return `predictions/${subjectId}/${userId}`;
}

export function usePredictions(subjectId: string | null) {
  const { user } = useAuth();
  // Guard: only enable the fetch when subjectId is a non-empty string (UUID).
  // Never coerce ids with parseInt — UUIDs would be truncated to leading digits.
  const validSubjectId = subjectId ? subjectId : null;
  const key =
    user?.id && validSubjectId ? cacheKey(user.id, validSubjectId) : null;

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
