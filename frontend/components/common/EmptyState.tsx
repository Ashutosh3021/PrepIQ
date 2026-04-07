import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

const EmptyState = React.forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ className, icon, title, description, action, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex flex-col items-center justify-center py-12 text-center',
          className
        )}
        role="status"
        {...props}
      >
        {icon && (
          <span
            className="material-symbols-outlined text-6xl text-outline-variant mb-4"
            aria-hidden="true"
          >
            {icon}
          </span>
        )}
        <h3 className="font-headline italic text-2xl text-on-surface mb-2">
          {title}
        </h3>
        {description && (
          <p className="text-secondary text-sm max-w-sm mb-6">{description}</p>
        )}
        {action && <div className="mt-2">{action}</div>}
      </div>
    );
  }
);

EmptyState.displayName = 'EmptyState';

export default EmptyState;
