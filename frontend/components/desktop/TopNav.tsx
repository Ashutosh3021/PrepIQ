import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { DESKTOP_NAV } from '@/lib/navigation';
import { Avatar } from '@/components/common';
import { cn } from '@/lib/utils/cn';
import { useAuth } from '@/lib/context/AuthContext';

export interface TopNavProps {
  className?: string;
}

const TopNav = React.forwardRef<HTMLElement, TopNavProps>(
  ({ className }, ref) => {
    const router = useRouter();
    const currentPath = router.pathname;
    const { user } = useAuth();

    // ── Mobile menu state ──────────────────────────────────────────────────
    const [mobileOpen, setMobileOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Close menu on route change
    useEffect(() => {
      setMobileOpen(false);
    }, [currentPath]);

    // Close menu when clicking outside
    useEffect(() => {
      if (!mobileOpen) return;
      const handleClick = (e: MouseEvent) => {
        if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
          setMobileOpen(false);
        }
      };
      document.addEventListener('mousedown', handleClick);
      return () => document.removeEventListener('mousedown', handleClick);
    }, [mobileOpen]);

    // Prevent body scroll when mobile menu is open
    useEffect(() => {
      document.body.style.overflow = mobileOpen ? 'hidden' : '';
      return () => { document.body.style.overflow = ''; };
    }, [mobileOpen]);

    const displayName =
      user?.user_metadata?.full_name ??
      user?.user_metadata?.name ??
      user?.email ??
      '?';

    const avatarFallback = displayName
      .split(/[\s@]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part: string) => part[0])
      .join('')
      .toUpperCase() || '?';

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
          className="max-w-7xl mx-auto px-4 md:px-8 h-[73px] flex items-center justify-between"
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

          {/* ── Desktop Nav Items (hidden on mobile) ── */}
          <ul className="hidden md:flex items-center gap-6" role="menubar">
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

          {/* ── Right: Notifications + Avatar + Hamburger ── */}
          <div className="flex items-center gap-3">
            {/* Notifications — visible on all sizes */}
            <button
              className="relative text-on-surface hover:text-primary transition-colors"
              aria-label="Notifications"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
              </svg>
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-primary rounded-full" />
            </button>

            {/* Avatar — visible on all sizes */}
            <Avatar fallback={avatarFallback} alt={`${displayName} avatar`} size="md" />

            {/* ── Hamburger button — mobile only ── */}
            <button
              className="md:hidden flex flex-col justify-center items-center w-10 h-10 gap-1.5 text-on-surface hover:text-primary transition-colors"
              onClick={() => setMobileOpen((o) => !o)}
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
              aria-controls="mobile-nav-menu"
            >
              {/* Animated hamburger → X */}
              <span className={cn(
                'block w-5 h-0.5 bg-current transition-all duration-200 origin-center',
                mobileOpen && 'rotate-45 translate-y-2'
              )} />
              <span className={cn(
                'block w-5 h-0.5 bg-current transition-all duration-200',
                mobileOpen && 'opacity-0 scale-x-0'
              )} />
              <span className={cn(
                'block w-5 h-0.5 bg-current transition-all duration-200 origin-center',
                mobileOpen && '-rotate-45 -translate-y-2'
              )} />
            </button>
          </div>
        </nav>

        {/* ── Mobile Dropdown Menu ── */}
        {/* Backdrop */}
        {mobileOpen && (
          <div
            className="md:hidden fixed inset-0 top-[73px] bg-black/40 z-40"
            aria-hidden="true"
            onClick={() => setMobileOpen(false)}
          />
        )}

        {/* Slide-down panel */}
        <div
          id="mobile-nav-menu"
          ref={menuRef}
          className={cn(
            'md:hidden absolute top-[73px] left-0 right-0 z-50',
            'bg-surface border-b border-[#4A4A4A]/20 shadow-lg',
            'transition-all duration-200 ease-in-out overflow-hidden',
            mobileOpen ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0 pointer-events-none'
          )}
          aria-hidden={!mobileOpen}
        >
          <nav aria-label="Mobile navigation">
            <ul className="py-2">
              {DESKTOP_NAV.map((item) => {
                const isActive =
                  currentPath === item.path ||
                  (item.aliases &&
                    item.aliases.some(
                      (alias) =>
                        currentPath.includes(alias.toLowerCase().replace(/\s+/g, '-'))
                    ));
                return (
                  <li key={item.name}>
                    <Link
                      href={item.path}
                      className={cn(
                        'flex items-center px-6 py-4 text-sm font-medium transition-colors',
                        isActive
                          ? 'text-primary bg-primary/5 border-l-4 border-primary font-bold'
                          : 'text-on-surface hover:bg-surface-container hover:text-primary border-l-4 border-transparent'
                      )}
                      aria-current={isActive ? 'page' : undefined}
                      onClick={() => setMobileOpen(false)}
                    >
                      {item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      </header>
    );
  }
);

TopNav.displayName = 'TopNav';

export default TopNav;
