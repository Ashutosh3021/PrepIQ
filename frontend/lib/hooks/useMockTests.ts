import useSWR, { mutate as globalMutate } from 'swr';
import { useAuth } from '../context/AuthContext';
import {
  mockTestsService,
  MockTest,
  MockTestResponse,
  MockTestCreate,
  Answer,
  TestSubmitResponse,
} from '../services/mock-tests.service';

function listKey(userId: string) {
  return `mock-tests/list/${userId}`;
}

/** Hook for the list of mock tests (test history). */
export function useMockTests() {
  const { user } = useAuth();
  const key = user?.id ? listKey(user.id) : null;

  const { data, error, isLoading, mutate } = useSWR<MockTest[]>(
    key,
    () => mockTestsService.getAll()
  );

  const generate = async (
    payload: MockTestCreate
  ): Promise<MockTestResponse> => {
    const result = await mockTestsService.generate(payload);
    // Invalidate list so history refreshes
    if (key) await globalMutate(key);
    return result;
  };

  const submit = async (
    testId: number,
    answers: Answer[]
  ): Promise<TestSubmitResponse> => {
    const result = await mockTestsService.submit(testId, answers);
    if (key) await globalMutate(key);
    return result;
  };

  return {
    tests: data ?? [],
    isLoading,
    error,
    generate,
    submit,
    refresh: mutate,
  };
}

/** Hook for a single test with its questions. */
export function useMockTest(testId: number | null) {
  const { data, error, isLoading } = useSWR<MockTestResponse>(
    testId != null ? `mock-tests/${testId}` : null,
    () => mockTestsService.getById(testId!)
  );

  return { test: data ?? null, isLoading, error };
}
