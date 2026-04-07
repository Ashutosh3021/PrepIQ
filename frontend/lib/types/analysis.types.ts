export interface Analysis {
  userId: string;
  overallProgress: number; // 0-100
  subjectProgress: { subjectId: string; name: string; progress: number }[];
  testHistory: { testId: string; title: string; score: number; date: string }[];
  strengths: string[];
  weaknesses: string[];
  predictions?: { topic: string; predictedScore: number; confidence: number }[];
}
