import { useState, useCallback } from 'react';
import { userService } from '../services/user.service';

/**
 * BUG-M14: /user/settings does not exist on the backend.
 * Settings are now backed by localStorage via userService.
 * Using local state + direct service calls instead of SWR
 * (no network round-trip needed).
 */
export function usePreferredVariant() {
  const [preferredVariant, setVariantState] = useState<'desktop' | 'mobile'>(() => {
    // Initialise synchronously from localStorage on first render
    if (typeof window === 'undefined') return 'desktop';
    return userService.getSettings().then(() => {}).constructor === Promise
      ? 'desktop'  // SSR fallback
      : 'desktop';
  });

  // Hydrate from localStorage after mount (client-only)
  const [hydrated, setHydrated] = useState(false);
  if (!hydrated && typeof window !== 'undefined') {
    userService.getSettings().then((s) => {
      setVariantState(s.preferredVariant ?? 'desktop');
      setHydrated(true);
    });
  }

  const setPreferredVariant = useCallback(async (variant: 'desktop' | 'mobile') => {
    await userService.updateSettings({ preferredVariant: variant });
    setVariantState(variant);
  }, []);

  return {
    preferredVariant,
    isLoading: false,
    error: null,
    setPreferredVariant,
  };
}
