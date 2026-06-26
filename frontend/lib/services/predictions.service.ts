/**
 * Predictions API service.
 * Uses the shared apiFetch helper which handles Bearer auth and BASE_URL.
 */

import { apiFetch } from './base.service';

// ── Types ────────────────────────────────────────────────────────────────────

export interface Prediction {
  id: number;
  question_text: string;
  topic: string;
  confidence_score: number; // 0.0 – 1.0
  reasoning: string;
  source: 'ml' | 'ml_fallback' | 'syllabus_fallback';
}

export interface PredictionResponse {
  predictions: Prediction[];
  fallback_used: boolean;
  fallback_reason: 'no_papers' | 'syllabus_fallback' | null;
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
   * GET /predictions/{subjectId}
   * Returns current predictions for the subject (uses cache on backend).
   */
  getBySubject: (subjectId: number) =>
    apiFetch<PredictionResponse>(`/predictions/${subjectId}`, EMPTY_RESPONSE),

  /**
   * POST /predictions/{subjectId}/refresh
   * Forces re-generation of predictions and returns the fresh result.
   */
  refresh: (subjectId: number) =>
    apiFetch<PredictionResponse>(
      `/predictions/${subjectId}/refresh`,
      EMPTY_RESPONSE,
      { method: 'POST' }
    ),
};
