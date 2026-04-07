import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface StatCardProps {
  label: string;
  value: string | number;
  /** Material Symbol / icon name for the stat icon */
  icon?: string;
  /** Optional trend indicator (e.g. "+12%", "-3%") */
  trend?: string;
  /** Trend direction: positive (green), negative (red), or neutral */
  trendDirection?: 'positive' | 'negative' | 'neutral';
  className?: string;
}

/**
 * StatCard — Compact single-stat card for mobile views.
 *
 * Displays a label, value, optional icon, and optional trend indicator.
 * Designed for dense mobile layouts where space is at a premium.
 */
const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  trend,
  trendDirection = 'neutral',
  className,
}) => {
  const trendColor =
    trendDirection === 'positive'
      ? 'text-green-500'
      : trendDirection === 'negative'
      ? 'text-red-500'
      : 'text-on-surface-variant';

  return (
    <div
      className={cn(
        'bg-surface-container-low rounded-xl p-3 border border-outline-variant/20',
        'flex flex-col gap-1',
        className
      )}
      role="region"
      aria-label={label}
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-on-surface-variant uppercase tracking-wide">
          {label}
        </p>
        {icon && (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-primary"
            aria-hidden="true"
          >
            {icon === 'home' && <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />}
            {icon === 'book-open' && (
              <>
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </>
            )}
            {icon === 'trending-up' && (
              <>
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                <polyline points="17 6 23 6 23 12" />
              </>
            )}
            {icon === 'bar-chart' && (
              <>
                <line x1="12" y1="20" x2="12" y2="10" />
                <line x1="18" y1="20" x2="18" y2="4" />
                <line x1="6" y1="20" x2="6" y2="16" />
              </>
            )}
            {icon === 'clipboard' && (
              <>
                <rect x="8" y="2" width="8" height="4" rx="1" />
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
              </>
            )}
            {icon === 'target' && (
              <>
                <circle cx="12" cy="12" r="10" />
                <circle cx="12" cy="12" r="6" />
                <circle cx="12" cy="12" r="2" />
              </>
            )}
            {icon === 'clock' && (
              <>
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </>
            )}
            {/* Fallback for unknown icon names */}
            {!['home', 'book-open', 'trending-up', 'bar-chart', 'clipboard', 'target', 'clock'].includes(icon) && (
              <circle cx="12" cy="12" r="10" />
            )}
          </svg>
        )}
      </div>

      <p className="text-2xl font-bold text-on-surface tracking-tight">
        {value}
      </p>

      {trend && (
        <p className={cn('text-xs font-medium', trendColor)} aria-label={`Trend: ${trend}`}>
          {trend}
        </p>
      )}
    </div>
  );
};

export default StatCard;
