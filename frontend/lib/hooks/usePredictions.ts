import useSWR, { mutate as globalMutate } from 'swr';
import { useAuth } from '../context/AuthContext';
import { predictionsService, PredictionResponse } from '../services/predictions.service';

function cacheKey(userId: string, subjectId: number) {
  return `predictions/${subjectId}/${userId}`;
}

export function usePredictions(subjectId: number | null) {
  const { user } = useAuth();
  const key =
    user?.id && subjectId != null ? cacheKey(user.id, subjectId) : null;

  const { data, error, isLoading, mutate } = useSWR<PredictionResponse>(
    key,
    () => predictionsService.getBySubject(subjectId!)
  );

  const refresh = async (): Promise<void> => {
    if (!subjectId) return;
    const fresh = await predictionsService.refresh(subjectId);
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
