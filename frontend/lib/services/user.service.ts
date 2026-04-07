// TODO: Replace with your mock data
import { apiFetch } from './base.service';
import { USER_MOCK, USER_SETTINGS_MOCK } from '../mocks/user.mock';
import type { User, UserSettings } from '../types/user.types';

export const userService = {
  getProfile: () => apiFetch<User>('/user/profile', USER_MOCK),
  getSettings: () => apiFetch<UserSettings>('/user/settings', USER_SETTINGS_MOCK),
  updateSettings: (settings: Partial<UserSettings>) =>
    apiFetch<UserSettings>('/user/settings', { ...USER_SETTINGS_MOCK, ...settings }, {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),
};
