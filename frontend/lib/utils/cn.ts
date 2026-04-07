/**
 * Tailwind className merge helper (UTIL-03)
 *
 * Merges Tailwind CSS classes using clsx for conditional logic
 * and tailwind-merge to resolve conflicts between overlapping classes.
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
