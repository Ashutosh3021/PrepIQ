/**
 * Predictions API service.
 * Uses the shared apiFetch helper which handles Bearer auth and BASE_URL.
 */

import { apiFetch } from './base.service';

// ── Types ────────────────────────────────────────────────────────────────────

/** Mirrors backend schemas.PredictedQuestionFull. */
export interface Prediction {
  question_number: number;
  text: string;
  topic: string | null;
  unit: string | null;
  marks: number;
  probability: string;
  confidence_score: number;
  reasoning: string;
  source: string | null;
}

/** Mirrors backend schemas.SubjectPredictionResponse. */
export interface PredictionResponse {
  id?: string | null;
  subject_id?: string;
  predictions: Prediction[];
  total_marks?: number;
  coverage_percentage?: number;
  fallback_used: boolean;
  fallback_reason: string | null;
  warning?: string | null;
  message: string | null;
}

// ── Mock fallback ────────────────────────────────────────────────────────────

const EMPTY_RESPONSE: PredictionResponse = {
  predictions: [],
  fallback_used: false,
  fallback_reason: null,
  message: null,
};

// ── Service ──────────────────────────────────────────────────────────────────

export const predictionsService = {
  /**
   * GET /predictions/subject/{subjectId}
   * Returns predictions for the subject. The backend regenerates them
   * server-side on every call, so this is always fresh.
   *
   * Note: GET /predictions/{id} is a DIFFERENT route — it fetches a single
   * stored prediction by prediction id and 404s for subject ids.
   */
  getBySubject: (subjectId: string) =>
    apiFetch<PredictionResponse>(`/predictions/subject/${subjectId}`, EMPTY_RESPONSE),

  /**
   * Refresh predictions for the subject (same route — regeneration is
   * server-side; there is no separate POST /refresh route on the backend).
   */
  refresh: (subjectId: string) =>
    apiFetch<PredictionResponse>(`/predictions/subject/${subjectId}`, EMPTY_RESPONSE),
};
