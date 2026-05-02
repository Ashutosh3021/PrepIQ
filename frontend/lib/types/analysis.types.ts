/**
 * Analysis type aligned with the backend GET /analysis/data response.
 * Backend returns: performanceData, subjectPerformance, weeklyProgress,
 * predictionsAccuracy, topicMastery, studyInsights.
 */
export interface Analysis {
  performanceData: { subject: string; unit: string; weightage: number; date: string }[];
  subjectPerformance: { subject: string; performance: number; total_questions: number; color: string }[];
  weeklyProgress: { week: string; progress: number }[];
  predictionsAccuracy: { subject: string; accuracy_score: number; total_predictions: number }[];
  topicMastery: { subject: string; topic: string; mastery_level: number; frequency: number }[];
  studyInsights: {
    total_subjects: number;
    total_questions_analyzed: number;
    average_accuracy: number;
    high_priority_topics: { subject: string; topic: string; impact_score: number }[];
    recommended_focus_areas: string[];
  };
}
