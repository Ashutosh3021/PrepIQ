import useSWR, { mutate } from 'swr';
import { testsService } from '../services/tests.service';
import type { Test, TestResult, Question } from '../types/test.types';

export function useTests() {
  const { data, error, isLoading } = useSWR<Test[]>('tests', testsService.getAll);

  const startTest = async (id: string) => {
    const result = await testsService.startTest(id);
    mutate('tests');
    return result;
  };

  const submitTest = async (id: string, answers: { questionId: string; selected: number }[]) => {
    const result = await testsService.submitTest(id, answers);
    mutate('tests');
    return result;
  };

  return { tests: data ?? [], isLoading, error, startTest, submitTest };
}

export function useTestQuestions(testId: string) {
  const { data, error, isLoading } = useSWR<Question[]>(
    testId ? `tests/${testId}/questions` : null,
    () => testsService.getQuestions(testId)
  );
  return { questions: data ?? [], isLoading, error };
}
