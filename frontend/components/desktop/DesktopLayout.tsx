import React from 'react';
import Link from 'next/link';
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
        className={cn('max-w-7xl mx-auto px-8 py-12 flex-1 w-full', className)}
        role="main"
      >
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>

      <footer
        className="border-t border-[#4A4A4A]/20 py-6"
        role="contentinfo"
      >
        <div className="max-w-7xl mx-auto px-8 flex items-center justify-between">
          <p className="text-sm text-on-surface/60">
            &copy; {new Date().getFullYear()} PrepIQ. All rights reserved.
          </p>
          <nav aria-label="Footer navigation">
            <ul className="flex items-center gap-6">
              <li>
                <Link
                  href="/privacy"
                  className="text-sm text-on-surface/60 hover:text-primary transition-colors"
                >
                  Privacy
                </Link>
              </li>
              <li>
                <Link
                  href="/terms"
                  className="text-sm text-on-surface/60 hover:text-primary transition-colors"
                >
                  Terms
                </Link>
              </li>
              <li>
                <Link
                  href="/help"
                  className="text-sm text-on-surface/60 hover:text-primary transition-colors"
                >
                  Help
                </Link>
              </li>
              <li>
                <Link
                  href="/contact"
                  className="text-sm text-on-surface/60 hover:text-primary transition-colors"
                >
                  Contact
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </footer>
    </div>
  );
};

export default DesktopLayout;
