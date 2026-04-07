// TODO: Replace with your mock data
import { apiFetch } from './base.service';
import { ANALYSIS_MOCK } from '../mocks/analysis.mock';
import type { Analysis } from '../types/analysis.types';

export const analysisService = {
  getByUserId: (userId: string) =>
    apiFetch<Analysis>(`/analysis/${userId}`, { ...ANALYSIS_MOCK, userId }),
};
