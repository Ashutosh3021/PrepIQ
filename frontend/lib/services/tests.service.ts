import { apiFetch } from './base.service';

// ── Backend-aligned types ────────────────────────────────────────────────────

/** Shape returned by GET /tests/ */
export interface BackendTest {
  test_id: string;
  total_questions: number;
  total_marks: number;
  time_limit_minutes: number;
  start_time: string;
  questions: BackendQuestion[];
}

export interface BackendQuestion {
  id: string;
  number: number;
  text: string;
  marks: number;
  unit: string;
  options?: string[] | null;
  type: string;
}

/** Shape returned by POST /tests/{id}/submit */
export interface BackendTestResult {
  test_id: string;
  score: number;
  total_marks: number;
  percentage: number;
  duration_minutes: number;
  results: { correct: number; incorrect: number; skipped: number };
}

/** Shape returned by GET /tests/{id}/results */
export interface BackendTestResults {
  test_id: string;
  score: number;
  percentage: number;
  question_analysis: {
    question_id: string;
    marks: number;
    status: string;
    user_answer: string;
    correct_answer: string;
    explanation: string;
  }[];
  weak_topics: string[];
  strong_topics: string[];
  recommendations: string[];
}

// ── Legacy types kept for backward compatibility with existing hooks ──────────
export interface Test {
  id: string;
  title: string;
  subject: string;
  duration: number;
  questionCount: number;
  difficulty: 'easy' | 'medium' | 'hard';
  status: 'available' | 'in-progress' | 'completed';
  score?: number;
  completedAt?: string;
}

export interface Question {
  id: string;
  testId: string;
  text: string;
  options: string[];
  correctAnswer: number;
  explanation?: string;
}

export interface TestResult {
  testId: string;
  score: number;
  totalQuestions: number;
  correctAnswers: number;
  timeTaken: number;
  answers: { questionId: string; selected: number; correct: boolean }[];
}

// ── Service ──────────────────────────────────────────────────────────────────

export const testsService = {
  /** GET /tests/ */
  getAll: () => apiFetch<BackendTest[]>('/tests/', []),

  /** GET /tests/{id} — not a real backend endpoint; use getAll and filter */
  getById: (id: string) => apiFetch<BackendTest>(`/tests/${id}`, {} as BackendTest),

  /** GET /tests/{testId}/questions — questions are embedded in the test object */
  getQuestions: (testId: string) =>
    apiFetch<BackendQuestion[]>(`/tests/${testId}/questions`, []),

  /**
   * POST /tests/generate — generate a new mock test
   */
  generateTest: (subjectId: string, numQuestions = 10, difficulty = 'medium') =>
    apiFetch<BackendTest>(
      '/tests/generate',
      {} as BackendTest,
      {
        method: 'POST',
        body: JSON.stringify({
          subject_id: subjectId,
          num_questions: numQuestions,
          difficulty,
          time_limit_minutes: numQuestions * 3,
        }),
      }
    ),

  /**
   * POST /tests/{id}/submit
   *
   * M-17 / FE-05: The backend expects { answers: Dict[str, str], end_time: datetime }.
   * `answers` maps question_id → answer string (e.g. "A", "B", ...).
   * We no longer do any local scoring — the backend computes the real score.
   *
   * @param id       Test ID
   * @param answers  Map of { questionId → answerString }
   */
  submitTest: (id: string, answers: Record<string, string>) =>
    apiFetch<BackendTestResult>(
      `/tests/${id}/submit`,
      {} as BackendTestResult,
      {
        method: 'POST',
        body: JSON.stringify({
          answers,
          end_time: new Date().toISOString(),
        }),
      }
    ),

  /** GET /tests/{id}/results */
  getResults: (id: string) =>
    apiFetch<BackendTestResults>(`/tests/${id}/results`, {} as BackendTestResults),
};
