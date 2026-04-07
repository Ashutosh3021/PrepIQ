import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { DESKTOP_NAV } from '@/lib/navigation';
import { Avatar } from '@/components/common';
import { cn } from '@/lib/utils/cn';

export interface TopNavProps {
  className?: string;
}

const TopNav = React.forwardRef<HTMLElement, TopNavProps>(
  ({ className }, ref) => {
    const router = useRouter();
    const currentPath = router.pathname;

    return (
      <header
        ref={ref}
        className={cn(
          'sticky top-0 z-50 bg-surface border-b border-[#4A4A4A]/20',
          className
        )}
        role="banner"
      >
        <nav
          className="max-w-7xl mx-auto px-8 h-[73px] flex items-center justify-between"
          aria-label="Main navigation"
        >
          {/* Logo */}
          <Link
            href="/desktop/dashboard"
            className="text-2xl font-serif italic text-on-surface hover:text-primary transition-colors"
            aria-label="PrepIQ Home"
          >
            PrepIQ
          </Link>

          {/* Nav Items */}
          <ul className="flex items-center gap-6" role="menubar">
            {DESKTOP_NAV.map((item) => {
              const isActive =
                currentPath === item.path ||
                (item.aliases &&
                  item.aliases.some(
                    (alias) =>
                      currentPath.includes(alias.toLowerCase().replace(/\s+/g, '-'))
                  ));

              return (
                <li key={item.name} role="none">
                  <Link
                    href={item.path}
                    className={cn(
                      'text-sm font-medium transition-colors py-1',
                      isActive
                        ? 'text-primary font-bold border-b-2 border-primary'
                        : 'text-on-surface hover:text-primary'
                    )}
                    role="menuitem"
                    aria-current={isActive ? 'page' : undefined}
                  >
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>

          {/* Right: Notifications + Avatar */}
          <div className="flex items-center gap-4">
            <button
              className="relative text-on-surface hover:text-primary transition-colors"
              aria-label="Notifications"
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
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
              </svg>
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-primary rounded-full" />
            </button>
            <Avatar fallback="JD" alt="User avatar" size="md" />
          </div>
        </nav>
      </header>
    );
  }
);

TopNav.displayName = 'TopNav';

export default TopNav;
