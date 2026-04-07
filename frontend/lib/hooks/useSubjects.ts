import useSWR from 'swr';
import { subjectsService } from '../services/subjects.service';
import type { Subject } from '../types/subject.types';

export function useSubjects() {
  const { data, error, isLoading } = useSWR<Subject[]>('subjects', subjectsService.getAll);
  return { subjects: data ?? [], isLoading, error };
}
