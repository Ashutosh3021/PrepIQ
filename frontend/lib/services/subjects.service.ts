import { apiFetch } from './base.service';
import type { Subject } from '../types/subject.types';

// Empty array used as mock fallback in mock mode
const SUBJECTS_MOCK: Subject[] = [];

export const subjectsService = {
  /** GET /subjects — returns all subjects for the authenticated user */
  getAll: () => apiFetch<Subject[]>('/subjects', SUBJECTS_MOCK),

  /**
   * GET /subjects/{id}
   * H-18: removed the SUBJECTS_MOCK lookup that caused failures in real mode
   * when the mock array was empty. The backend handles 404 correctly.
   */
  getById: (id: string) => apiFetch<Subject>(`/subjects/${id}`, {} as Subject),

  /** POST /subjects */
  create: (data: { name: string; code?: string; semester?: number }) =>
    apiFetch<Subject>('/subjects', {} as Subject, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** PUT /subjects/{id} */
  update: (id: string, data: Partial<Subject>) =>
    apiFetch<Subject>(`/subjects/${id}`, {} as Subject, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  /** DELETE /subjects/{id} */
  delete: (id: string) =>
    apiFetch<{ message: string }>(`/subjects/${id}`, { message: '' }, {
      method: 'DELETE',
    }),
};
