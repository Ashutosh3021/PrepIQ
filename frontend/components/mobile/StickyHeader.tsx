import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface StickyHeaderProps {
  title: string;
  /** Show a back button that navigates to the previous page */
  showBack?: boolean;
  /** Optional right-side action slot (e.g. action buttons) */
  actions?: React.ReactNode;
  className?: string;
}

/**
 * StickyHeader — Sticky page header for mobile views.
 *
 * Displays a page title with an optional back button and action slot.
 * Sticks to the top of the viewport with a subtle border separator.
 */
const StickyHeader: React.FC<StickyHeaderProps> = ({
  title,
  showBack = false,
  actions,
  className,
}) => {
  const handleBack = () => {
    if (typeof window !== 'undefined') {
      window.history.back();
    }
  };

  return (
    <header
      className={cn(
        'sticky top-0 z-40 bg-surface border-b border-outline-variant/20',
        'px-4 py-3 flex items-center gap-3',
        className
      )}
      role="banner"
    >
      {showBack && (
        <button
          onClick={handleBack}
          className="flex-shrink-0 p-1 -ml-1 text-on-surface hover:text-primary transition-colors rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-label="Go back"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      )}

      <h1 className="flex-1 text-lg font-semibold text-on-surface truncate">
        {title}
      </h1>

      {actions && (
        <div className="flex-shrink-0 flex items-center gap-2">
          {actions}
        </div>
      )}
    </header>
  );
};

export default StickyHeader;
