// TODO: Replace with your mock data
import { apiFetch } from './base.service';
import { SUBJECTS_MOCK } from '../mocks/subjects.mock';
import type { Subject } from '../types/subject.types';

export const subjectsService = {
  getAll: () => apiFetch<Subject[]>('/subjects', SUBJECTS_MOCK),
  getById: (id: string) => {
    const subject = SUBJECTS_MOCK.find((s) => s.id === id);
    if (!subject) {
      throw new Error(`Subject not found: ${id}`);
    }
    return apiFetch<Subject>(`/subjects/${id}`, subject);
  },
};
