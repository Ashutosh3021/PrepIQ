import useSWR, { mutate } from 'swr';
import { userService } from '../services/user.service';
import type { UserSettings } from '../types/user.types';

export function usePreferredVariant() {
  const { data, error, isLoading } = useSWR<UserSettings>('user/settings', userService.getSettings);

  const setPreferredVariant = async (variant: 'desktop' | 'mobile') => {
    await userService.updateSettings({ preferredVariant: variant });
    mutate('user/settings');
  };

  return {
    preferredVariant: data?.preferredVariant ?? 'desktop',
    isLoading,
    error,
    setPreferredVariant,
  };
}
