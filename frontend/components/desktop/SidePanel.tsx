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
  /** Mobile drawer: controlled open state */
  mobileOpen?: boolean;
  /** Mobile drawer: called when user closes the panel */
  onMobileClose?: () => void;
}

/**
 * SidePanel — Left sidebar panel.
 * Desktop: always visible (lg+).
 * Mobile: hidden by default, slides in as a drawer when mobileOpen=true.
 */
const SidePanel: React.FC<SidePanelProps> = ({
  title = 'Sessions',
  items,
  className,
  mobileOpen = false,
  onMobileClose,
}) => {
  const panelContent = (
    <>
      {/* Title + mobile close button */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-[0.75rem] uppercase tracking-widest text-tertiary">
          {title}
        </h2>
        {/* Close button — mobile only */}
        {onMobileClose && (
          <button
            className="lg:hidden text-on-surface/50 hover:text-on-surface transition-colors p-1"
            onClick={onMobileClose}
            aria-label="Close sidebar"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>

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
                onClick={() => {
                  item.onClick?.();
                  // Auto-close drawer on mobile after selection
                  onMobileClose?.();
                }}
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
    </>
  );

  return (
    <>
      {/* ── Desktop sidebar — always visible on lg+ ── */}
      <aside
        className={cn(
          'hidden lg:flex flex-col w-72 bg-surface-container-low border-r border-[#4A4A4A]/10 h-[calc(100vh-73px)] p-8',
          className
        )}
        aria-label={title}
      >
        {panelContent}
      </aside>

      {/* ── Mobile drawer — slide in from left ── */}
      {/* Backdrop */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/50"
          aria-hidden="true"
          onClick={onMobileClose}
        />
      )}

      {/* Drawer panel */}
      <aside
        className={cn(
          // Mobile only — fixed drawer
          'lg:hidden fixed top-[73px] left-0 bottom-0 z-50',
          'w-72 bg-surface-container-low border-r border-[#4A4A4A]/10 p-8 flex flex-col',
          // Slide transition
          'transition-transform duration-300 ease-in-out',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        aria-label={title}
        aria-hidden={!mobileOpen}
      >
        {panelContent}
      </aside>
    </>
  );
};

export default SidePanel;
