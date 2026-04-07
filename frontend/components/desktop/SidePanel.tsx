import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface SidePanelItem {
  label: string;
  active?: boolean;
  onClick?: () => void;
}

export interface SidePanelProps {
  title?: string;
  items: SidePanelItem[];
  className?: string;
}

/**
 * SidePanel — Optional left sidebar panel for dashboard navigation or filters.
 * Hidden on mobile, visible on lg screens and up.
 */
const SidePanel: React.FC<SidePanelProps> = ({
  title = 'Sessions',
  items,
  className,
}) => {
  return (
    <aside
      className={cn(
        'hidden lg:flex flex-col w-72 bg-surface-container-low border-r border-[#4A4A4A]/10 h-[calc(100vh-73px)] p-8',
        className
      )}
      aria-label={title}
    >
      {/* Title */}
      <h2 className="text-[0.75rem] uppercase tracking-widest text-tertiary mb-6">
        {title}
      </h2>

      {/* Items */}
      <nav aria-label={`${title} list`}>
        <ul className="space-y-1">
          {items.map((item, index) => (
            <li key={item.label || index}>
              <button
                className={cn(
                  'w-full text-left px-4 py-3 text-sm rounded-r-md transition-colors',
                  item.active
                    ? 'bg-surface-container-highest border-l-4 border-primary text-on-surface font-medium'
                    : 'text-on-surface/70 hover:bg-surface-container hover:text-on-surface border-l-4 border-transparent'
                )}
                onClick={item.onClick}
                aria-current={item.active ? 'page' : undefined}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Session Progress Bar */}
      <div className="mt-auto pt-6 border-t border-outline-variant/20">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold uppercase tracking-widest text-secondary">
            Session
          </span>
          <span className="text-xs text-on-surface/60">3/5 topics</span>
        </div>
        <div
          className="w-full h-1.5 bg-surface-container-high rounded-full overflow-hidden"
          role="progressbar"
          aria-valuenow={60}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Session progress: 3 of 5 topics"
        >
          <div className="h-full bg-primary w-3/5 transition-all duration-300" />
        </div>
      </div>
    </aside>
  );
};

export default SidePanel;
