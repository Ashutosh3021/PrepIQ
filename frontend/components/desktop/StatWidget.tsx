import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface StatWidgetProps {
  label: string;
  value: string;
  /** Material Symbol name for the icon */
  icon: string;
  className?: string;
}

/**
 * StatWidget — Dashboard stat block displaying a label, value, and icon.
 * Used in grid layouts on the dashboard to show key metrics.
 */
const StatWidget: React.FC<StatWidgetProps> = ({
  label,
  value,
  icon,
  className,
}) => {
  return (
    <div
      className={cn(
        'bg-surface-container-low p-8 border-r border-b border-outline-variant/20 flex items-start justify-between',
        className
      )}
      role="region"
      aria-label={label}
    >
      <div>
        <p className="text-xs font-bold uppercase tracking-widest text-primary mb-2">
          {label}
        </p>
        <p className="text-5xl font-light tracking-tighter text-on-surface">
          {value}
        </p>
      </div>

      {/* Icon placeholder — Material Symbol name rendered as text/SVG */}
      <span
        className="text-primary text-3xl"
        aria-hidden="true"
        title={icon}
      >
        {/* Render icon name as text placeholder until icon library is chosen */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {icon === 'home' && <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />}
          {icon === 'book-open' && (
            <>
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </>
          )}
          {icon === 'upload' && (
            <>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </>
          )}
          {icon === 'bot' && (
            <>
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <circle cx="12" cy="5" r="2" />
              <path d="M12 7v4" />
              <line x1="8" y1="16" x2="8" y2="16" />
              <line x1="16" y1="16" x2="16" y2="16" />
            </>
          )}
          {icon === 'clipboard' && (
            <>
              <rect x="8" y="2" width="8" height="4" rx="1" />
              <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
            </>
          )}
          {icon === 'bar-chart' && (
            <>
              <line x1="12" y1="20" x2="12" y2="10" />
              <line x1="18" y1="20" x2="18" y2="4" />
              <line x1="6" y1="20" x2="6" y2="16" />
            </>
          )}
          {icon === 'settings' && (
            <>
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </>
          )}
          {icon === 'user' && (
            <>
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </>
          )}
          {icon === 'trending-up' && (
            <>
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </>
          )}
          {/* Fallback: generic circle for unknown icons */}
          {!['home', 'book-open', 'upload', 'bot', 'clipboard', 'bar-chart', 'settings', 'user', 'trending-up'].includes(icon) && (
            <circle cx="12" cy="12" r="10" />
          )}
        </svg>
      </span>
    </div>
  );
};

export default StatWidget;
