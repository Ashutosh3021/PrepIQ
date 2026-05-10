import React, { useState } from 'react';
import { useStudyPlan } from '@/lib/hooks/useStudyPlan';
import { Skeleton, Button } from '@/components/common';
import { cn } from '@/lib/utils/cn';

interface StudyPlanViewProps {
  subjectId: string;
  subjectName: string;
  className?: string;
}

export const StudyPlanView: React.FC<StudyPlanViewProps> = ({
  subjectId,
  subjectName,
  className,
}) => {
  const { plan, isLoading, error, generate, updateProgress } = useStudyPlan(subjectId);
  const [showGenerateForm, setShowGenerateForm] = useState(!plan);
  const [startDate, setStartDate] = useState('');
  const [examDate, setExamDate] = useState('');
  const [generating, setGenerating] = useState(false);
  const [updating, setUpdating] = useState(false);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!startDate || !examDate) return;

    setGenerating(true);
    try {
      await generate({
        subject_id: subjectId,
        start_date: startDate,
        exam_date: examDate,
      });
      setShowGenerateForm(false);
      setStartDate('');
      setExamDate('');
    } catch (err) {
      console.error('Failed to generate plan:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleMarkDayComplete = async (daysCompleted: number) => {
    if (!plan) return;
    setUpdating(true);
    try {
      const newDaysCompleted = Math.min(daysCompleted + 1, plan.total_days);
      await updateProgress(plan.plan_id, { days_completed: newDaysCompleted });
    } catch (err) {
      console.error('Failed to update progress:', err);
    } finally {
      setUpdating(false);
    }
  };

  if (isLoading) {
    return (
      <div className={cn('space-y-4', className)}>
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('text-error text-sm p-4 bg-error/5 border border-error/20', className)}>
        Failed to load study plan
      </div>
    );
  }

  if (!plan || showGenerateForm) {
    return (
      <div className={cn('bg-surface-container-low p-8 border border-outline-variant/20', className)}>
        <div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-secondary mb-6">
            Generate Study Plan
          </h3>
          <form onSubmit={handleGenerate} className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-widest text-primary">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className="w-full bg-surface border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-widest text-primary">
                Exam Date
              </label>
              <input
                type="date"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
                required
                className="w-full bg-surface border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
              />
            </div>

            <div className="flex gap-4 pt-4">
              {plan && (
                <button
                  type="button"
                  onClick={() => setShowGenerateForm(false)}
                  className="flex-1 border border-primary text-primary py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary hover:text-on-primary transition-all"
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                disabled={generating}
                className="flex-1 bg-primary text-on-primary py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-all disabled:opacity-40 flex items-center justify-center gap-2"
              >
                {generating && (
                  <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                  </svg>
                )}
                {generating ? 'Generating…' : 'Generate Plan'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  const completionPercent = plan.completion_percentage || 0;
  const daysCompleted = plan.days_completed || 0;

  return (
    <div className={cn('bg-surface-container-low p-8 border border-outline-variant/20', className)}>
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-secondary mb-2">
            Study Plan
          </h3>
          <p className="text-xs text-on-surface/70">
            {daysCompleted} of {plan.total_days} days completed
          </p>
        </div>
        <button
          onClick={() => setShowGenerateForm(true)}
          className="text-xs font-bold uppercase tracking-widest text-primary hover:text-primary/80 transition-colors"
        >
          Regenerate
        </button>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2 mb-6">
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold uppercase tracking-widest text-secondary">
            Progress
          </span>
          <span className="text-sm font-medium text-on-surface">
            {Math.round(completionPercent)}%
          </span>
        </div>
        <div
          className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden"
          role="progressbar"
          aria-valuenow={completionPercent}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${completionPercent}%` }}
          />
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-2 text-xs mb-8 pb-8 border-b border-outline-variant/20">
        <div
          className={cn(
            'w-2 h-2 rounded-full',
            plan.on_track ? 'bg-green-500' : 'bg-yellow-500'
          )}
        />
        <span className="text-on-surface/70">
          {plan.on_track ? 'On track' : 'Behind schedule'}
        </span>
      </div>

      {/* Daily Schedule */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-widest text-secondary mb-4">
          Daily Schedule
        </h4>
        <div className="max-h-96 overflow-y-auto space-y-2">
          {plan.daily_schedule.map((day, idx) => (
            <div
              key={day.day}
              className={cn(
                'p-4 border-l-4 transition-all',
                idx < daysCompleted
                  ? 'border-green-500 bg-green-500/5'
                  : 'border-outline-variant bg-surface'
              )}
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs font-bold uppercase tracking-widest text-secondary">
                      Day {day.day}
                    </span>
                    <span className="text-xs text-on-surface/60">{day.date}</span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest text-secondary mb-2">
                        Topics
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {day.topics.map((topic, i) => (
                          <span
                            key={i}
                            className="text-xs bg-primary/10 text-primary px-2 py-1 rounded"
                          >
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>

                    {day.priority_topics.length > 0 && (
                      <div>
                        <p className="text-xs font-bold uppercase tracking-widest text-error mb-2">
                          Priority Topics
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {day.priority_topics.map((topic, i) => (
                            <span
                              key={i}
                              className="text-xs bg-error/10 text-error px-2 py-1 rounded"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <p className="text-xs text-on-surface/70">
                      Recommended: <span className="font-semibold">{day.recommended_hours.toFixed(1)} hours</span>
                    </p>
                  </div>
                </div>

                {idx < daysCompleted ? (
                  <div className="flex-shrink-0 text-green-500 mt-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                ) : idx === daysCompleted ? (
                  <button
                    onClick={() => handleMarkDayComplete(daysCompleted)}
                    disabled={updating}
                    className="flex-shrink-0 px-3 py-2 text-xs font-bold uppercase tracking-widest bg-primary text-on-primary hover:bg-primary/90 transition-all disabled:opacity-40 whitespace-nowrap"
                  >
                    {updating ? '…' : 'Mark Done'}
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StudyPlanView;
