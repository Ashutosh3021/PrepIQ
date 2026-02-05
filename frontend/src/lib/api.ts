// PrepIQ API Service Layer
// Centralized API client with authentication and error handling

import { toast } from 'sonner';
import React from 'react';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3009';

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

// Response handler
const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = await response.json().catch(() => ({}));
  
  if (!response.ok) {
    const error = new APIError(
      data.detail || data.message || `HTTP ${response.status}`,
      response.status,
      data.code
    );
    
    throw error;
  }
  
  return data;
};

// Core API client
export const apiClient = {
  // Generic request method
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

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: defaultHeaders,
        ...restConfig,
      });

      const data = await handleResponse<T>(response);
      return data;
    } catch (error) {
      if (error instanceof APIError) {
        if (toastErrors && error.status !== 401) {
          toast.error(error.message);
        }
        throw error;
      }
      
      const networkError = new APIError('Network error occurred', 0);
      if (toastErrors) {
        toast.error('Network error - please check your connection');
      }
      throw networkError;
    }
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
  }
};

// Prediction services
export const predictionService = {
  async getLatestPredictions() {
    return apiClient.get<PredictionData>('/api/predictions/latest');
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
  async getAll() {
    return apiClient.get<Subject[]>('/api/subjects');
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
    return apiClient.get<ImportantQuestion[]>('/api/questions/important');
  },

  async search(params: QuestionSearchParams) {
    const queryString = new URLSearchParams(params as any).toString();
    return apiClient.get<Question[]>('/api/questions/search?' + queryString);
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