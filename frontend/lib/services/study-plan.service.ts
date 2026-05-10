import { apiFetch } from './base.service';

export interface StudyPlanDay {
  day: number;
  date: string;
  topics: string[];
  recommended_hours: number;
  priority_topics: string[];
}

export interface StudyPlan {
  plan_id: string;
  subject_id: string;
  total_days: number;
  daily_schedule: StudyPlanDay[];
  days_completed?: number;
  completion_percentage?: number;
  on_track?: boolean;
}

export interface StudyPlanRequest {
  subject_id: string;
  start_date: string;
  exam_date: string;
}

export interface StudyPlanUpdate {
  days_completed?: number;
  on_track?: boolean;
}

export const studyPlanService = {
  /** POST /plan/generate - Generate a new study plan */
  generate: (data: StudyPlanRequest) =>
    apiFetch<StudyPlan>('/plan/generate', {} as StudyPlan, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** GET /plan/me - Get current study plan */
  getCurrent: () =>
    apiFetch<StudyPlan>('/plan/me', {} as StudyPlan),

  /** GET /plan/subject/{subject_id} - Get study plan for a specific subject */
  getBySubject: (subjectId: string) =>
    apiFetch<StudyPlan>(`/plan/subject/${subjectId}`, {} as StudyPlan),

  /** PUT /plan/{plan_id} - Update study plan progress */
  update: (planId: string, data: StudyPlanUpdate) =>
    apiFetch<{ message: string; plan: StudyPlan }>(`/plan/${planId}`, { message: '', plan: {} as StudyPlan }, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};
