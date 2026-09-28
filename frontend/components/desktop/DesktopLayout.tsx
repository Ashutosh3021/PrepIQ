import React from 'react';
import TopNav from './TopNav';
import { ErrorBoundary } from '@/components/common';
import { cn } from '@/lib/utils/cn';

export interface DesktopLayoutProps {
  children: React.ReactNode;
  className?: string;
}

const DesktopLayout: React.FC<DesktopLayoutProps> = ({
  children,
  className,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-surface">
      <TopNav />

      <main
        className={cn('max-w-7xl mx-auto px-4 md:px-8 py-6 md:py-12 flex-1 w-full', className)}
        role="main"
      >
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>

      <footer
        className="border-t border-[#4A4A4A]/20 py-6"
        role="contentinfo"
      >
        <div className="max-w-7xl mx-auto px-4 md:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-on-surface/60">
            &copy; {new Date().getFullYear()} PrepIQ. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default DesktopLayout;
