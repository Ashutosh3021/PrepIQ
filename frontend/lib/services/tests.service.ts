// TODO: Replace with your mock data
import { apiFetch } from './base.service';
import { TESTS_MOCK } from '../mocks/tests.mock';
import type { Test, TestResult, Question } from '../types/test.types';

// In-memory state for mock mode
const testStates = new Map<string, 'not-started' | 'in-progress' | 'completed'>();
const testAnswers = new Map<string, { questionId: string; selected: number }[]>();

export const testsService = {
  getAll: () => apiFetch<Test[]>('/tests', TESTS_MOCK),
  getById: (id: string) =>
    apiFetch<Test>(`/tests/${id}`, TESTS_MOCK.find((t) => t.id === id)!),
  getQuestions: (testId: string) => apiFetch<Question[]>(`/tests/${testId}/questions`, []),
  startTest: (id: string) => {
    testStates.set(id, 'in-progress');
    testAnswers.set(id, []);
    return apiFetch<{ status: string }>(`/tests/${id}/start`, { status: 'in-progress' });
  },
  submitTest: (id: string, answers: { questionId: string; selected: number }[]) => {
    testStates.set(id, 'completed');
    testAnswers.set(id, answers);
    const correct = answers.filter((a) => a.selected === 0).length; // placeholder scoring
    return apiFetch<TestResult>(`/tests/${id}/submit`, {
      testId: id,
      score: Math.round((correct / Math.max(answers.length, 1)) * 100),
      totalQuestions: answers.length,
      correctAnswers: correct,
      timeTaken: 1200,
      answers: answers.map((a) => ({ ...a, correct: a.selected === 0 })),
    });
  },
  getState: (id: string) => testStates.get(id) ?? 'not-started',
  getAnswers: (id: string) => testAnswers.get(id) ?? [],
};
