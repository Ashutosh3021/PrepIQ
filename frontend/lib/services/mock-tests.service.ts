/**
 * Mock Test API service.
 * Uses the shared apiFetch helper which handles Bearer auth and BASE_URL.
 *
 * These types are purpose-built for the new predictions-backed mock test flow
 * and live alongside the existing tests.service.ts without modifying it.
 *
 * Phase 1 (implementation-plan 1.6): blueprint generation, review + self-grade
 * (hybrid grading) endpoints.
 */

import { apiFetch } from './base.service';

// ── Types ────────────────────────────────────────────────────────────────────

export type Difficulty = 'easy' | 'medium' | 'hard' | 'mixed';
export type TestSource = 'predictions' | 'all_questions';
export type BloomLevel = 'recall' | 'understand' | 'apply' | 'analyze';
export type QuestionTypeFilter = 'any' | 'mcq' | 'descriptive';

/** "auto" | "pending_self_grade" | "self_verified" | "none" */
export type GradingMode = 'auto' | 'pending_self_grade' | 'self_verified' | 'none';

/** Error classes the student picks while self-verifying (plan D4). */
export const ERROR_CLASSES = ['Knowledge', 'Retrieval', 'Conceptual', 'Execution'] as const;
export type ErrorClass = (typeof ERROR_CLASSES)[number];

export interface MockTestCreate {
  subject_id: string;
  num_questions: number;
  difficulty: Difficulty;
  source: TestSource;
  /**
   * Blueprint mode (default) lets the subject blueprint drive section counts,
   * marks and duration — legacy fields (num_questions/time_limit/source) are
   * omitted from the body so they cannot override it.
   */
  useBlueprint?: boolean;
}

export interface MockTestQuestion {
  id: string;
  question_text: string;
  topic: string;
  marks: number;
  type: string;
  group?: string | null;
  attempt?: number | null;
  of?: number | null;
}

export interface MockTest {
  test_id: string;
  subject_id: string;
  subject_name?: string;
  total_questions: number;
  difficulty?: Difficulty;
  status: 'pending' | 'completed';
  score_percentage: number | null;
  created_at: string;
}

export interface MockTestResponse extends MockTest {
  questions: MockTestQuestion[];
  error?: string;
  message?: string;
  total_marks?: number;
  time_limit_minutes?: number;
}

export interface Answer {
  question_id: string;
  answer_text: string;
}

export interface TestSubmitResponse {
  test_id: string;
  score_percentage: number | null;
  total_questions: number;
  answers_graded: number;
  grading_mode?: GradingMode | null;
  pending_self_grade?: number | null;
}

// ── Blueprint types (Phase 1.1 / 1.5) ────────────────────────────────────────

export interface BlueprintSectionSpec {
  name?: string | null;
  count: number;
  marks: number;
  attempt?: number | null;
  difficulty: Difficulty;
  qtype: QuestionTypeFilter;
  bloom?: BloomLevel[];
}

export interface BlueprintSpec {
  preset?: string;
  duration_minutes?: number;
  sections: BlueprintSectionSpec[];
}

export interface BlueprintView {
  subject_id: string;
  source: string; // "subject" | "preset" | "generic"
  preset: string;
  blueprint: BlueprintSpec;
  total_questions: number;
  total_marks: number;
}

export interface BlueprintPreset {
  id: string;
  label: string;
  description: string;
  blueprint: BlueprintSpec;
}

/** PUT /subjects/{id}/blueprint body: a full blueprint or a preset ref. */
export interface BlueprintConfigPayload {
  preset?: string;
  duration_minutes?: number;
  sections?: BlueprintSectionSpec[];
}

// ── Review + self-grade types (Phase 1.4 / 1.5) ──────────────────────────────

export interface TestReviewItem {
  question_id: string;
  question_number: number;
  question_text: string;
  topic: string;
  marks: number;
  mode: 'mcq' | 'descriptive' | string;
  user_answer: string | null;
  auto_result: 'correct' | 'incorrect' | 'skipped' | null;
  provisional_points: number | null;
  verified_points: number | null;
  error_class: string | null;
  model_answer: string | null;
  rubric_bullets: string[] | null;
  keyword_anchors: string[] | null;
  needs_review: boolean;
}

export interface TestReviewResponse {
  test_id: string;
  grading_mode: GradingMode;
  percentage: number | null; // null until every pending item is verified
  pending_self_grade: number;
  total_questions: number;
  total_marks: number;
  items: TestReviewItem[];
}

export interface SelfGradeItemPayload {
  question_id: string;
  points_hit: number;
  error_class: ErrorClass | string;
}

// ── Mock fallbacks ────────────────────────────────────────────────────────────

const EMPTY_TEST: MockTestResponse = {
  test_id: '',
  subject_id: '',
  subject_name: '',
  total_questions: 0,
  difficulty: 'mixed',
  status: 'pending',
  score_percentage: null,
  created_at: '',
  questions: [],
};

const EMPTY_BLUEPRINT_VIEW: BlueprintView = {
  subject_id: '',
  source: 'generic',
  preset: 'generic',
  blueprint: { sections: [] },
  total_questions: 0,
  total_marks: 0,
};

const EMPTY_REVIEW: TestReviewResponse = {
  test_id: '',
  grading_mode: 'none',
  percentage: null,
  pending_self_grade: 0,
  total_questions: 0,
  total_marks: 0,
  items: [],
};

// ── Service ──────────────────────────────────────────────────────────────────

export const mockTestsService = {
  /**
   * POST /tests/generate
   * Generate a new mock test.
   *
   * Blueprint mode (default): only subject_id (+ use_blueprint) is sent, so the
   * subject blueprint drives sections and duration. Legacy mode: full payload
   * including time_limit_minutes for the old behaviour.
   */
  generate: (payload: MockTestCreate) => {
    const body: Record<string, unknown> = { subject_id: payload.subject_id };
    if (payload.useBlueprint === false) {
      body.use_blueprint = false;
      body.num_questions = payload.num_questions;
      body.difficulty = payload.difficulty;
      body.source = payload.source;
      body.time_limit_minutes = payload.num_questions * 3;
    } else {
      body.use_blueprint = true;
    }
    return apiFetch<MockTestResponse>('/tests/generate', EMPTY_TEST, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  /**
   * GET /tests/
   * Returns the list of all mock tests for the authenticated user.
   */
  getAll: () => apiFetch<MockTest[]>('/tests/', []),

  /**
   * GET /tests/{testId}
   * Returns a single mock test with its questions.
   */
  getById: (testId: string) =>
    apiFetch<MockTestResponse>(`/tests/${testId}`, EMPTY_TEST),

  /**
   * POST /tests/{testId}/submit
   * Submit answers and get the result back (hybrid grading).
   */
  submit: (testId: string, answers: Answer[]) =>
    apiFetch<TestSubmitResponse>(
      `/tests/${testId}/submit`,
      { test_id: testId, score_percentage: null, total_questions: 0, answers_graded: 0 },
      {
        method: 'POST',
        body: JSON.stringify({
          answers: Object.fromEntries(
            answers.map((a) => [String(a.question_id), a.answer_text])
          ),
        }),
      }
    ),

  /**
   * GET /tests/{testId}/review
   * Model answers + rubric bullets + keyword anchors per question (Phase 1.4).
   */
  getReview: (testId: string) =>
    apiFetch<TestReviewResponse>(`/tests/${testId}/review`, EMPTY_REVIEW),

  /**
   * POST /tests/{testId}/self-grade
   * Award points + error class per pending answer → Self-Verified score.
   */
  selfGrade: (testId: string, items: SelfGradeItemPayload[]) =>
    apiFetch<TestSubmitResponse>(
      `/tests/${testId}/self-grade`,
      { test_id: testId, score_percentage: null, total_questions: 0, answers_graded: 0 },
      {
        method: 'POST',
        body: JSON.stringify({ items }),
      }
    ),

  /**
   * GET /tests/blueprints/presets
   * Expert-seeded blueprint presets (generic / university / NEET-UG).
   */
  getBlueprintPresets: () => apiFetch<BlueprintPreset[]>('/tests/blueprints/presets', []),

  /**
   * GET /subjects/{subjectId}/blueprint
   * Resolved blueprint for a subject (subject override > track preset > generic).
   */
  getSubjectBlueprint: (subjectId: string) =>
    apiFetch<BlueprintView>(`/subjects/${subjectId}/blueprint`, EMPTY_BLUEPRINT_VIEW),

  /**
   * PUT /subjects/{subjectId}/blueprint
   * Persist an edited blueprint ({sections, duration_minutes}) or a preset ref.
   */
  putSubjectBlueprint: (subjectId: string, body: BlueprintConfigPayload) =>
    apiFetch<BlueprintView>(`/subjects/${subjectId}/blueprint`, EMPTY_BLUEPRINT_VIEW, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
};
