import { apiFetch } from './base.service';
import type { Analysis } from '../types/analysis.types';

const ANALYSIS_MOCK: Analysis = {
  performanceData: [],
  subjectPerformance: [],
  weeklyProgress: [],
  predictionsAccuracy: [],
  topicMastery: [],
  studyInsights: {
    total_subjects: 0,
    total_questions_analyzed: 0,
    average_accuracy: 0,
    high_priority_topics: [],
    recommended_focus_areas: [],
  },
};

export const analysisService = {
  /**
   * GET /analysis/data
   * H-16 / M-16: The backend identifies the user from the Bearer token.
   * No userId in the path. Replaces the old getByUserId(userId) call.
   */
  getData: () => apiFetch<Analysis>('/analysis/data', ANALYSIS_MOCK),

  /** GET /analysis/{subjectId}/frequency */
  getFrequency: (subjectId: string) =>
    apiFetch<Analysis>(`/analysis/${subjectId}/frequency`, ANALYSIS_MOCK),

  /** GET /analysis/{subjectId}/weightage */
  getWeightage: (subjectId: string) =>
    apiFetch<Analysis>(`/analysis/${subjectId}/weightage`, ANALYSIS_MOCK),

  /** GET /analysis/{subjectId}/repetitions */
  getRepetitions: (subjectId: string) =>
    apiFetch<Analysis>(`/analysis/${subjectId}/repetitions`, ANALYSIS_MOCK),

  /** GET /analysis/{subjectId}/trends */
  getTrends: (subjectId: string) =>
    apiFetch<Analysis>(`/analysis/${subjectId}/trends`, ANALYSIS_MOCK),
};
