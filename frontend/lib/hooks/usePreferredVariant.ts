import { useCallback, useEffect, useState } from 'react';
import { userService } from '../services/user.service';

type Variant = 'desktop' | 'mobile';

/**
 * Desktop/mobile shell preference, backed by userService (localStorage).
 *
 * The value is hydrated in an effect: reading localStorage during render
 * (and calling setState from render) produced an always-'desktop' initial
 * state plus a React render-phase update warning.
 */
export function usePreferredVariant() {
  const [preferredVariant, setVariantState] = useState<Variant>('desktop');
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    let active = true;
    userService.getSettings().then((settings) => {
      if (!active) return;
      setVariantState(settings.preferredVariant === 'mobile' ? 'mobile' : 'desktop');
      setHydrated(true);
    });
    return () => {
      active = false;
    };
  }, []);

  const setPreferredVariant = useCallback((variant: Variant) => {
    setVariantState(variant);
    return userService.updateSettings({ preferredVariant: variant });
  }, []);

  return {
    preferredVariant,
    isLoading: !hydrated,
    error: null,
    setPreferredVariant,
  };
}
