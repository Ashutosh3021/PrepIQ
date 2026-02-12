// PrepIQ API Service Layer
// Centralized API client with authentication and error handling

import { toast } from 'sonner';
import React from 'react';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Error types
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Request configuration
interface RequestConfig extends RequestInit {
  requireAuth?: boolean;
  toastErrors?: boolean;
}

// Auth helper
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token') || localStorage.getItem('supabase.auth.token');
  }
  return null;
};

// Response handler with enhanced error handling
const handleResponse = async <T>(response: Response): Promise<T> => {
  let data: any;
  
  try {
    data = await response.json();
  } catch (e) {
    data = {};
  }
  
  if (!response.ok) {
    // Handle different types of errors
    let errorMessage = 'An error occurred';
    let errorCode = data.code;
    
    // Handle authentication errors
    if (response.status === 401) {
      errorMessage = 'Authentication required. Please log in again.';
      // Clear auth token
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('supabase.auth.token');
      }
    } 
    // Handle forbidden errors
    else if (response.status === 403) {
      errorMessage = 'Access forbidden. You do not have permission to perform this action.';
    }
    // Handle not found errors
    else if (response.status === 404) {
      errorMessage = 'Resource not found.';
    }
    // Handle validation errors
    else if (response.status === 422) {
      if (Array.isArray(data.detail)) {
        errorMessage = data.detail.map((err: any) => err.msg || err).join(', ');
      } else {
        errorMessage = data.detail || 'Validation error';
      }
    }
    // Handle server errors
    else if (response.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    }
    // Handle other errors
    else {
      errorMessage = data.detail || data.message || data.error || `HTTP ${response.status}`;
    }
    
    const error = new APIError(errorMessage, response.status, errorCode);
    throw error;
  }
  
  return data;
};

// Core API client with retry logic
export const apiClient = {
  // Generic request method with retry logic
  async request<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<T> {
    const {
      requireAuth = true,
      toastErrors = true,
      headers = {},
      ...restConfig
    } = config;

    // Build headers
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(headers as Record<string, string>),
    };

    // Add auth header if required
    if (requireAuth) {
      const token = getAuthToken();
      if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
      } else {
        throw new APIError('No authentication token found', 401);
      }
    }

    // Retry logic
    const maxRetries = 3;
    let lastError: Error;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
          headers: defaultHeaders,
          ...restConfig,
        });

        const data = await handleResponse<T>(response);
        return data;
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on authentication errors or client errors
        if (error instanceof APIError) {
          if (error.status === 401 || error.status === 403 || error.status === 404 || error.status === 422) {
            if (toastErrors && error.status !== 401) {
              toast.error(error.message);
            }
            throw error;
          }
          
          // Don't retry on final attempt
          if (attempt === maxRetries) {
            if (toastErrors && error.status !== 401) {
              toast.error(error.message);
            }
            throw error;
          }
        }
        
        // Wait before retry (exponential backoff)
        if (attempt < maxRetries) {
          const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    // If we get here, all retries failed
    const networkError = new APIError('Network error occurred after multiple attempts', 0);
    if (toastErrors) {
      toast.error('Network error - please check your connection');
    }
    throw networkError;
  },

  // HTTP methods
  get<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', ...config });
  },

  post<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...config,
    });
  },

  put<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...config,
    });
  },

  delete<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE', ...config });
  },

  // File upload
  async upload<T>(
    endpoint: string,
    file: File,
    additionalData?: Record<string, any>
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
      });
    }

    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
      headers: {}, // Don't set Content-Type for FormData
    });
  }
};

// Specific API service functions

// Auth services
export const authService = {
  async getCurrentUser() {
    return apiClient.get<UserProfile>('/auth/profile');
  },

  async updateProfile(data: Partial<UserProfile>) {
    return apiClient.put<UserProfile>('/auth/profile', data);
  },

  async getAuthStatus() {
    return apiClient.get('/auth/me');
  },

  async getWizardStatus() {
    return apiClient.get<WizardStatus>('/wizard/status');
  },

  async completeWizardStep1(data: WizardStep1Data) {
    return apiClient.post<UserProfile>('/wizard/step1', data);
  },

  async completeWizardStep2(data: WizardStep2Data) {
    return apiClient.post<UserProfile>('/wizard/step2', data);
  },

  async completeWizardStep3(data: WizardStep3Data) {
    return apiClient.post<UserProfile>('/wizard/step3', data);
  },

  async completeWizard() {
    return apiClient.post<UserProfile>('/wizard/complete', { wizard_completed: true });
  },

  async updateWizardData(data: Partial<UserProfile>) {
    return apiClient.put<UserProfile>('/wizard/update', data);
  }
};

// Prediction services
export const predictionService = {
  async getLatestPredictions() {
    return apiClient.get<PredictionData>('/api/predictions/latest');
  },
  
  async getLatestPredictionsForSubject(subjectId: string) {
    return apiClient.get<PredictionData>(`/api/predictions/${subjectId}/latest`);
  },

  async getPredictionTrend() {
    return apiClient.get<ChartDataPoint[]>('/api/predictions/trend');
  },

  async getTopicProbabilities() {
    return apiClient.get<TopicProbability[]>('/api/predictions/topics');
  },

  async getStudyRecommendations() {
    return apiClient.get<Recommendation[]>('/api/predictions/recommendations');
  }
};

// Dashboard services
export const dashboardService = {
  async getStats() {
    return apiClient.get<DashboardStats>('/api/dashboard/stats');
  },

  async getRecentActivity() {
    return apiClient.get<ActivityItem[]>('/api/dashboard/recent-activity');
  },

  async getStudyProgress() {
    return apiClient.get<ProgressData>('/api/dashboard/progress');
  }
};

// Subject services
export const subjectService = {
  async getAll(params?: { search?: string; semester?: number; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append('search', params.search);
    if (params?.semester) searchParams.append('semester', params.semester.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    
    const queryString = searchParams.toString();
    const url = queryString ? `/api/subjects?${queryString}` : '/api/subjects';
    return apiClient.get<Subject[]>(url);
  },

  async getById(id: string) {
    return apiClient.get<Subject>(`/api/subjects/${id}`);
  },

  async create(data: CreateSubjectData) {
    return apiClient.post<Subject>('/api/subjects', data);
  },

  async update(id: string, data: Partial<Subject>) {
    return apiClient.put<Subject>(`/api/subjects/${id}`, data);
  },

  async delete(id: string) {
    return apiClient.delete(`/api/subjects/${id}`);
  }
};

// Question services
export const questionService = {
  async getImportant() {
    return apiClient.get<ImportantQuestion[]>('/questions/important');
  },

  async search(params: QuestionSearchParams) {
    const queryString = new URLSearchParams(params as any).toString();
    return apiClient.get<Question[]>('/questions/search?' + queryString);
  }
};

// Analysis services
export const analysisService = {
  async getAnalysisData() {
    return apiClient.get<AnalysisData>('/analysis/data');
  },

  async getPerformanceTrends() {
    return apiClient.get<ChartDataPoint[]>('/analysis/performance-trends');
  },

  async getSubjectPerformance() {
    return apiClient.get<SubjectPerformance[]>('/analysis/subject-performance');
  },

  async getWeeklyProgress() {
    return apiClient.get<WeeklyProgress[]>('/analysis/weekly-progress');
  }
};

// Test services
export const testService = {
  async generateTest(data: GenerateTestRequest) {
    return apiClient.post<MockTestResponse>('/tests/generate', data);
  },

  async submitTest(testId: string, data: SubmitTestRequest) {
    return apiClient.post<TestResult>(`/tests/${testId}/submit`, data);
  },

  async getTestHistory(subjectId?: string) {
    const url = subjectId ? `/tests/history?subject_id=${subjectId}` : '/tests/history';
    return apiClient.get<MockTestHistory[]>(url);
  },

  async getTestResult(testId: string) {
    return apiClient.get<TestResult>(`/tests/${testId}/results`);
  }
};

// Types (these should be moved to a separate types file in production)
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  college_name: string;
  program: string;
  year_of_study: number;
  exam_date?: string;
  theme_preference: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface PredictionData {
  confidence: number;
  summary: string;
  questions: PredictionQuestion[];
  topicHeatmap: TopicHeatMapEntry[];
  studyRecommendations: string[];
  generated_at: string;
}

export interface PredictionQuestion {
  id: string;
  number: number;
  text: string;
  marks: number;
  unit: string;
  probability: string;
  appearedIn: number[];
  difficulty: string;
  expectedAnswer: string;
}

export interface TopicHeatMapEntry {
  unit: string;
  veryHigh: number;
  high: number;
  moderate: number;
}

export interface ChartDataPoint {
  month: string;
  score: number;
  [key: string]: any; // For additional chart data
}

export interface TopicProbability {
  topic: string;
  probability: number;
  confidence: number;
}

export interface Recommendation {
  id: string;
  text: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
}

export interface DashboardStats {
  subjects_count: number;
  completion_percentage: number;
  focus_area: string;
  study_streak: number;
  days_to_exam: number;
  recent_activity: Array<{
    action: string;
    timestamp: string;
    details?: string;
  }>;
}

export interface ActivityItem {
  id: string;
  type: 'test' | 'study' | 'prediction' | 'upload';
  title: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ProgressData {
  daily: ProgressPoint[];
  weekly: ProgressPoint[];
  monthly: ProgressPoint[];
}

export interface ProgressPoint {
  date: string;
  value: number;
  target?: number;
}

// Analysis types
export interface AnalysisData {
  performanceData: ChartDataPoint[];
  subjectPerformance: SubjectPerformance[];
  weeklyProgress: WeeklyProgress[];
}

export interface SubjectPerformance {
  subject: string;
  performance: number;
  color?: string;
}

export interface WeeklyProgress {
  week: string;
  progress: number;
}

export interface Subject {
  id: string;
  name: string;
  code?: string;
  semester?: number;
  total_marks?: number;
  exam_date?: string;
  papers_uploaded: number;
  predictions_generated: number;
  mock_tests_created: number;
  created_at: string;
}

export interface CreateSubjectData {
  name: string;
  code?: string;
  semester?: number;
  total_marks?: number;
  exam_date?: string;
}

export interface ImportantQuestion {
  id: string;
  subject: string;
  topic: string;
  question: string;
  difficulty: string;
  importance: string;
  last_asked: string;
}

export interface QuestionSearchParams {
  subject?: string;
  topic?: string;
  difficulty?: string;
  limit?: number;
  offset?: number;
}

export interface Question {
  id: string;
  text: string;
  marks: number;
  difficulty: string;
  subject_id: string;
  topic: string;
  created_at: string;
}

// Test Types
export interface GenerateTestRequest {
  subject_id: string;
  num_questions: number;
  difficulty: 'easy' | 'medium' | 'hard' | 'mixed';
  time_limit_minutes: number;
  question_source: 'high_probability' | 'previous_year' | 'weak_areas' | 'mixed';
}

export interface MockTestQuestion {
  id: string;
  number: number;
  text: string;
  marks: number;
  unit: string;
  type: 'mcq' | 'descriptive' | 'numerical';
  options?: string[];
  correctAnswer?: string;
}

export interface MockTestResponse {
  test_id: string;
  total_questions: number;
  total_marks: number;
  time_limit_minutes: number;
  start_time: string;
  questions: MockTestQuestion[];
}

export interface SubmitTestRequest {
  answers: { [questionId: string]: string };
  time_taken_seconds: number;
}

export interface TestResult {
  test_id: string;
  score: number;
  total_marks: number;
  percentage: number;
  grade: string;
  time_taken_minutes: number;
  correct_count: number;
  incorrect_count: number;
  skipped_count: number;
  question_results: {
    question_id: string;
    is_correct: boolean;
    user_answer: string;
    correct_answer: string;
    marks_obtained: number;
  }[];
  weak_topics: string[];
  strong_topics: string[];
  recommendations: string[];
}

export interface MockTestHistory {
  test_id: string;
  subject_name: string;
  score: number;
  total_marks: number;
  percentage: number;
  completed_at: string;
  duration_minutes: number;
}

// Wizard Types
export interface WizardStatus {
  completed: boolean;
  exam_name?: string;
  days_until_exam?: number;
  focus_subjects?: string[];
  study_hours_per_day?: number;
  target_score?: number;
  preparation_level?: string;
}

export interface WizardStep1Data {
  exam_name: string;
  days_until_exam: number;
}

export interface WizardStep2Data {
  focus_subjects: string[];
  study_hours_per_day: number;
}

export interface WizardStep3Data {
  target_score: number;
  preparation_level: string;
}

// Hook for data fetching (using useEffect pattern)
export const useApi = <T>(
  fetcher: () => Promise<T>,
  deps: React.DependencyList = []
) => {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await fetcher();
        setData(result);
      } catch (err) {
        const errorMessage = err instanceof APIError ? err.message : 'Failed to fetch data';
        setError(errorMessage);
        toast.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, deps);

  const refetch = React.useCallback(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await fetcher();
        setData(result);
      } catch (err) {
        const errorMessage = err instanceof APIError ? err.message : 'Failed to fetch data';
        setError(errorMessage);
        toast.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [fetcher]);

  return { data, loading, error, refetch };
};

// Export everything
export default apiClient;