import { apiFetch } from './base.service';
import type { User, UserSettings } from '../types/user.types';

const USER_MOCK: User = { id: '', email: '' };
const USER_SETTINGS_MOCK: UserSettings = {
  userId: '',
  preferredVariant: 'desktop',
  notifications: true,
  theme: 'light',
};

export const userService = {
  /**
   * GET /auth/me — returns the full user profile from the backend.
   * The backend identifies the user from the Bearer token.
   */
  getProfile: () => apiFetch<User>('/auth/me', USER_MOCK),

  getSettings: () => apiFetch<UserSettings>('/user/settings', USER_SETTINGS_MOCK),

  updateSettings: (settings: Partial<UserSettings>) =>
    apiFetch<UserSettings>('/user/settings', USER_SETTINGS_MOCK, {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),
};
