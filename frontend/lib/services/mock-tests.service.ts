/**
 * Mock Test API service.
 * Uses the shared apiFetch helper which handles Bearer auth and BASE_URL.
 *
 * These types are purpose-built for the new predictions-backed mock test flow
 * and live alongside the existing tests.service.ts without modifying it.
 */

import { apiFetch } from './base.service';

// ── Types ────────────────────────────────────────────────────────────────────

export type Difficulty = 'easy' | 'medium' | 'hard' | 'mixed';
export type TestSource = 'predictions' | 'all';

export interface MockTestCreate {
  subject_id: number;
  num_questions: number;
  difficulty: Difficulty;
  source: TestSource;
}

export interface MockTestQuestion {
  id: number;
  question_text: string;
  topic: string;
  marks: number;
  type: string;
}

export interface MockTest {
  test_id: number;
  subject_id: number;
  subject_name: string;
  total_questions: number;
  difficulty: Difficulty;
  status: 'pending' | 'completed';
  score_percentage: number | null;
  created_at: string;
}

export interface MockTestResponse extends MockTest {
  questions: MockTestQuestion[];
}

export interface Answer {
  question_id: number;
  answer_text: string;
}

export interface TestSubmitResponse {
  test_id: number;
  score_percentage: number | null;
  message: string;
  answers_recorded: number;
}

// ── Mock fallbacks ────────────────────────────────────────────────────────────

const EMPTY_TEST: MockTestResponse = {
  test_id: 0,
  subject_id: 0,
  subject_name: '',
  total_questions: 0,
  difficulty: 'mixed',
  status: 'pending',
  score_percentage: null,
  created_at: '',
  questions: [],
};

// ── Service ──────────────────────────────────────────────────────────────────

export const mockTestsService = {
  /**
   * POST /tests/generate
   * Generate a new mock test from predictions or question pool.
   */
  generate: (payload: MockTestCreate) =>
    apiFetch<MockTestResponse>('/tests/generate', EMPTY_TEST, {
      method: 'POST',
      body: JSON.stringify({
        subject_id: payload.subject_id,
        num_questions: payload.num_questions,
        difficulty: payload.difficulty,
        source: payload.source,
        time_limit_minutes: payload.num_questions * 3,
      }),
    }),

  /**
   * GET /tests/
   * Returns the list of all mock tests for the authenticated user.
   */
  getAll: () => apiFetch<MockTest[]>('/tests/', []),

  /**
   * GET /tests/{testId}
   * Returns a single mock test with its questions.
   */
  getById: (testId: number) =>
    apiFetch<MockTestResponse>(`/tests/${testId}`, EMPTY_TEST),

  /**
   * POST /tests/{testId}/submit
   * Submit answers and get the result back.
   */
  submit: (testId: number, answers: Answer[]) =>
    apiFetch<TestSubmitResponse>(
      `/tests/${testId}/submit`,
      { test_id: testId, score_percentage: null, message: '', answers_recorded: 0 },
      {
        method: 'POST',
        body: JSON.stringify({
          answers: Object.fromEntries(
            answers.map((a) => [String(a.question_id), a.answer_text])
          ),
          end_time: new Date().toISOString(),
        }),
      }
    ),
};
