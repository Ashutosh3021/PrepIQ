import type { Analysis } from '../types/analysis.types';

export const ANALYSIS_MOCK: Analysis = {
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
