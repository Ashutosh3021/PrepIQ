import useSWR, { mutate } from 'swr';
import { userService } from '@/lib/services/user.service';
import { apiFetch } from '@/lib/services/base.service';
import type { User } from '@/lib/types/user.types';

// Shared SWR key — both settings and profile pages use this
export const PROFILE_SWR_KEY = '/auth/me';

export function useProfile() {
  const { data, error, isLoading, mutate: revalidate } = useSWR<User>(
    PROFILE_SWR_KEY,
    () => userService.getProfile(),
    { revalidateOnFocus: false }
  );

  const updateProfile = async (patch: {
    full_name?: string;
    college_name?: string;
    program?: string;
    year_of_study?: number;
    exam_date?: string;
  }) => {
    // Optimistic update
    if (data) {
      mutate(PROFILE_SWR_KEY, { ...data, ...patch }, false);
    }

    // Backend defines POST /wizard/update — a PUT here 405'd, so every save
    // silently failed (mobile settings swallowed the error entirely).
    await apiFetch('/wizard/update', {}, {
      method: 'POST',
      body: JSON.stringify(patch),
    });

    // Revalidate from server to confirm
    await revalidate();
  };

  return {
    profile: data ?? null,
    isLoading,
    error,
    updateProfile,
    revalidate,
  };
}
