/**
 * User type aligned with the backend /auth/me response.
 * Backend returns: id, email, full_name, college_name, program,
 * year_of_study, wizard_completed, exam_name, days_until_exam,
 * focus_subjects, study_hours_per_day, target_score, preparation_level,
 * exam_date, supabase_user.
 */
export interface User {
  id: string;
  email: string;
  full_name?: string;
  college_name?: string;
  program?: string;
  year_of_study?: number;
  wizard_completed?: boolean;
  exam_name?: string;
  days_until_exam?: number;
  focus_subjects?: string[];
  study_hours_per_day?: number;
  target_score?: number;
  preparation_level?: string;
  exam_date?: string | null;
}

export interface UserSettings {
  userId: string;
  preferredVariant: 'desktop' | 'mobile';
  notifications: boolean;
  theme: 'light' | 'dark';
}
