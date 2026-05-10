import useSWR from 'swr';
import { studyPlanService, StudyPlan, StudyPlanRequest, StudyPlanUpdate } from '@/lib/services/study-plan.service';

export function useStudyPlan(subjectId?: string) {
  const { data, error, isLoading, mutate } = useSWR<StudyPlan>(
    subjectId ? `/plan/subject/${subjectId}` : null,
    () => (subjectId ? studyPlanService.getBySubject(subjectId) : null),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  );

  const generate = async (request: StudyPlanRequest) => {
    try {
      const result = await studyPlanService.generate(request);
      mutate(result);
      return result;
    } catch (err) {
      console.error('Failed to generate study plan:', err);
      throw err;
    }
  };

  const updateProgress = async (planId: string, update: StudyPlanUpdate) => {
    try {
      const result = await studyPlanService.update(planId, update);
      mutate(result.plan);
      return result;
    } catch (err) {
      console.error('Failed to update study plan:', err);
      throw err;
    }
  };

  return {
    plan: data,
    isLoading,
    error,
    generate,
    updateProgress,
    refresh: mutate,
  };
}
