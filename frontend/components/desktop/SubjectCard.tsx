import React from 'react';
import { Card, Button } from '@/components/common';
import { cn } from '@/lib/utils/cn';

export interface SubjectCardProps {
  subject: {
    code: string;
    name: string;
    description: string;
    progress: number;
  };
  className?: string;
  onTrackProgress?: () => void;
  onDelete?: () => void;
}

const SubjectCard: React.FC<SubjectCardProps> = ({
  subject,
  className,
  onTrackProgress,
  onDelete,
}) => {
  const progressPercent = Math.min(100, Math.max(0, subject.progress));

  return (
    <Card
      variant="bordered"
      className={cn(
        'p-8 flex flex-col h-full',
        className
      )}
    >
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start gap-4">
          <div className="flex-1">
            <span className="text-xs font-bold uppercase tracking-tighter text-secondary">
              {subject.code}
            </span>
            <h3 className="text-3xl font-serif italic text-on-surface mt-1">
              {subject.name}
            </h3>
            <p className="text-sm text-on-surface/70 mt-3 leading-relaxed">
              {subject.description}
            </p>
          </div>
          {onDelete && (
            <button
              onClick={onDelete}
              className="text-on-surface/40 hover:text-error transition-colors flex-shrink-0"
              aria-label="Delete subject"
              title="Delete subject"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                <line x1="10" y1="11" x2="10" y2="17" />
                <line x1="14" y1="11" x2="14" y2="17" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Progress */}
      <div className="mt-auto">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold uppercase tracking-widest text-secondary">
            Progress
          </span>
          <span className="text-sm font-medium text-on-surface">
            {progressPercent}%
          </span>
        </div>
        <div
          className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden"
          role="progressbar"
          aria-valuenow={progressPercent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${subject.name} progress: ${progressPercent}%`}
        >
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Track Progress Button */}
        {onTrackProgress && (
          <Button
            variant="secondary"
            size="sm"
            className="mt-4"
            onClick={onTrackProgress}
          >
            Track Progress
          </Button>
        )}
      </div>
    </Card>
  );
};

export default SubjectCard;
