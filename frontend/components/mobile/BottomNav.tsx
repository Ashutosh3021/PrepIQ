import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { MOBILE_NAV } from '@/lib/navigation';
import { cn } from '@/lib/utils/cn';
import Icon from './Icon';

export interface BottomNavProps {
  className?: string;
}

/**
 * BottomNav — Mobile bottom navigation bar.
 *
 * Displays navigation items from MOBILE_NAV with active state highlighting
 * based on the current route. Includes iOS safe area padding.
 */
const BottomNav: React.FC<BottomNavProps> = ({ className }) => {
  const router = useRouter();
  const currentPath = router.asPath.split('?')[0].split('#')[0];

  const isActive = (path: string, aliases?: string[]): boolean => {
    if (currentPath === path) return true;
    if (aliases) {
      return aliases.some((alias) =>
        currentPath.includes(alias.toLowerCase().replace(/\s+/g, '-'))
      );
    }
    return false;
  };

  return (
    <nav
      className={cn(
        'fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-outline-variant/20',
        'pb-[env(safe-area-inset-bottom)]',
        className
      )}
      role="navigation"
      aria-label="Mobile navigation"
    >
      <ul className="flex items-stretch justify-around max-w-lg mx-auto">
        {MOBILE_NAV.map((item) => {
          const active = isActive(item.path, item.aliases);

          return (
            <li key={item.name} className="flex-1 min-w-0">
              <Link
                href={item.path}
                className={cn(
                  'flex flex-col items-center justify-center py-2 px-1 transition-colors',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1',
                  active
                    ? 'text-primary'
                    : 'text-on-surface-variant hover:text-on-surface'
                )}
                aria-current={active ? 'page' : undefined}
              >
                <Icon
                  name={item.icon}
                  size={22}
                  className={cn(
                    'mb-0.5',
                    active ? 'stroke-[2.5]' : 'stroke-[1.5]'
                  )}
                />
                <span
                  className={cn(
                    'text-[10px] leading-none truncate max-w-full',
                    active ? 'font-semibold' : 'font-medium'
                  )}
                >
                  {item.name}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};

export default BottomNav;
