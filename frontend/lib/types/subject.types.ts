/**
 * Subject type aligned with the backend SubjectResponse schema.
 * Backend returns: id, name, code, semester, academic_year, total_marks,
 * exam_date, exam_duration_minutes, syllabus_json, papers_uploaded,
 * predictions_generated, created_at, user_id.
 *
 * H-19: removed `description` and `progress` (not in backend response).
 * `progress` is derived from papers_uploaded + predictions_generated.
 */
export interface Subject {
  id: string;
  name: string;
  code?: string | null;
  semester?: number | null;
  academic_year?: string | null;
  total_marks?: number | null;
  exam_date?: string | null;
  exam_duration_minutes?: number | null;
  syllabus_json?: Record<string, unknown> | null;
  papers_uploaded: number;
  predictions_generated: number;
  created_at: string;
  user_id?: string;
}

/**
 * Derive a 0-100 progress value from the subject's activity counts.
 * A subject with at least one paper uploaded and one prediction generated
 * is considered "complete" (100%). Partial credit for each step.
 */
export function deriveSubjectProgress(subject: Subject): number {
  const hasPaper = (subject.papers_uploaded ?? 0) > 0;
  const hasPrediction = (subject.predictions_generated ?? 0) > 0;
  if (hasPaper && hasPrediction) return 100;
  if (hasPaper) return 50;
  return 0;
}
