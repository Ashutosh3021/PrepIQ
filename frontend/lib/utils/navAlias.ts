/**
 * Navigation alias resolver (UTIL-02)
 *
 * Finds navigation items by both canonical name and alias.
 * Used by navigation components to resolve user-facing labels
 * to their canonical routes.
 */

import { DESKTOP_NAV, MOBILE_NAV } from '../navigation';
import type { NavItem, NavVariant } from '../types/nav.types';

export function resolveAlias(label: string, variant: NavVariant): NavItem | undefined {
  const nav = variant === 'desktop' ? DESKTOP_NAV : MOBILE_NAV;
  return nav.find(
    item => item.name === label || item.aliases?.includes(label)
  );
}
