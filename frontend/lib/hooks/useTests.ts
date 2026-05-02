import useSWR, { mutate } from 'swr';
import { testsService, BackendTest, BackendTestResult, BackendTestResults } from '../services/tests.service';

export function useTests() {
  const { data, error, isLoading } = useSWR<BackendTest[]>('tests', testsService.getAll);

  /**
   * M-17 / FE-05: submitTest now accepts a Record<string, string> (questionId → answer)
   * and sends it directly to the backend. No local scoring.
   */
  const submitTest = async (id: string, answers: Record<string, string>): Promise<BackendTestResult> => {
    const result = await testsService.submitTest(id, answers);
    mutate('tests');
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
