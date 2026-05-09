import useSWR, { mutate } from 'swr';
import { useAuth } from '../context/AuthContext';
import { testsService, BackendTest, BackendTestResult, BackendTestResults } from '../services/tests.service';

/**
 * FIX 4: Scope the SWR cache key to the current user's ID so that switching
 * accounts never shows stale tests from the previous user.
 * Key is null until the session resolves, which disables fetching.
 */
export function useTests() {
  const { user } = useAuth();
  const cacheKey = user?.id ? `tests/${user.id}` : null;

  const { data, error, isLoading } = useSWR<BackendTest[]>(cacheKey, testsService.getAll);

  const submitTest = async (id: string, answers: Record<string, string>): Promise<BackendTestResult> => {
    const result = await testsService.submitTest(id, answers);
    // Invalidate the user-scoped cache key after submission
    if (cacheKey) mutate(cacheKey);
    return result;
  };

  const getResults = async (id: string): Promise<BackendTestResults> => {
    return testsService.getResults(id);
  };

  return { tests: data ?? [], isLoading, error, submitTest, getResults };
}

export function useTestQuestions(testId: string) {
  const { data, error, isLoading } = useSWR(
    testId ? `tests/${testId}/questions` : null,
    () => testsService.getQuestions(testId)
  );
  return { questions: data ?? [], isLoading, error };
}
