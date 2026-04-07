import React from 'react';
import { cn } from '@/lib/utils/cn';
import BottomNav from './BottomNav';
import StickyHeader from './StickyHeader';

export interface MobileLayoutProps {
  /** Page title shown in the sticky header */
  title?: string;
  /** Show back button in header */
  showBack?: boolean;
  /** Optional right-side action slot in header */
  headerActions?: React.ReactNode;
  /** Whether to show the bottom navigation bar */
  showBottomNav?: boolean;
  /** Custom header component (overrides title/showBack/headerActions) */
  customHeader?: React.ReactNode;
  /** Page content */
  children: React.ReactNode;
  className?: string;
}

/**
 * MobileLayout — Layout wrapper for mobile pages.
 *
 * Provides a consistent mobile shell with a sticky header and bottom navigation.
 * Wraps page content with appropriate spacing to avoid overlap with fixed elements.
 */
const MobileLayout: React.FC<MobileLayoutProps> = ({
  title,
  showBack = false,
  headerActions,
  showBottomNav = true,
  customHeader,
  children,
  className,
}) => {
  const hasHeader = customHeader || title;

  return (
    <div className={cn('min-h-screen bg-background flex flex-col', className)}>
      {/* Header */}
      {hasHeader && (
        customHeader ? (
          customHeader
        ) : (
          <StickyHeader
            title={title!}
            showBack={showBack}
            actions={headerActions}
          />
        )
      )}

      {/* Page Content */}
      <main
        className={cn(
          'flex-1 px-4 py-4',
          showBottomNav && 'pb-20'
        )}
        role="main"
      >
        {children}
      </main>

      {/* Bottom Navigation */}
      {showBottomNav && <BottomNav />}
    </div>
  );
};

export default MobileLayout;
