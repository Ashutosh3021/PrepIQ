export interface Test {
  id: string;
  title: string;
  subject: string;
  duration: number; // minutes
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
  correctAnswer: number; // index
  explanation?: string;
}

export interface TestResult {
  testId: string;
  score: number;
  totalQuestions: number;
  correctAnswers: number;
  timeTaken: number; // seconds
  answers: { questionId: string; selected: number; correct: boolean }[];
}
