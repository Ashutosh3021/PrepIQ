import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface SubjectPillProps {
  name: string;
  /** Optional icon name (uses the shared Icon component) */
  icon?: string;
  /** Whether the pill is in an active/selected state */
  active?: boolean;
  /** Optional click handler for interactive pills */
  onClick?: () => void;
  className?: string;
}

/**
 * SubjectPill — Compact pill/chip for displaying subjects on mobile.
 *
 * Used in horizontal scrollable lists on mobile dashboards and subject pages.
 * Supports active state and optional icon.
 */
const SubjectPill: React.FC<SubjectPillProps> = ({
  name,
  icon,
  active = false,
  onClick,
  className,
}) => {
  const isInteractive = typeof onClick === 'function';

  const Tag = isInteractive ? 'button' : 'span';

  return (
    <Tag
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm whitespace-nowrap',
        'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        active
          ? 'bg-primary text-on-primary font-semibold'
          : 'bg-surface-container-high text-on-surface border border-outline-variant/30',
        isInteractive && 'cursor-pointer hover:bg-surface-container-highest active:opacity-80',
        className
      )}
      onClick={onClick}
      aria-pressed={isInteractive ? active : undefined}
      role={isInteractive ? 'button' : undefined}
    >
      {icon && (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
      )}
      {name}
    </Tag>
  );
};

export default SubjectPill;
