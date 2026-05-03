import { apiFetch } from './base.service';
import type { User, UserSettings } from '../types/user.types';

const USER_MOCK: User = { id: '', email: '' };

const SETTINGS_KEY = 'prepiq-user-settings';

const DEFAULT_SETTINGS: UserSettings = {
  userId: '',
  preferredVariant: 'desktop',
  notifications: true,
  theme: 'light',
};

/**
 * BUG-M14: /user/settings endpoints do not exist on the backend.
 * Settings are persisted in localStorage instead of making network calls
 * that would always 404.
 */
function readLocalSettings(): UserSettings {
  if (typeof window === 'undefined') return DEFAULT_SETTINGS;
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    // corrupted — ignore
  }
  return DEFAULT_SETTINGS;
}

function writeLocalSettings(patch: Partial<UserSettings>): UserSettings {
  const current = readLocalSettings();
  const updated = { ...current, ...patch };
  if (typeof window !== 'undefined') {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(updated));
  }
  return updated;
}

export const userService = {
  /**
   * GET /auth/me — returns the full user profile from the backend.
   * The backend identifies the user from the Bearer token.
   */
  getProfile: () => apiFetch<User>('/auth/me', USER_MOCK),

  /** BUG-M14: read from localStorage — no network call */
  getSettings: (): Promise<UserSettings> =>
    Promise.resolve(readLocalSettings()),

  /** BUG-M14: write to localStorage — no network call */
  updateSettings: (settings: Partial<UserSettings>): Promise<UserSettings> =>
    Promise.resolve(writeLocalSettings(settings)),
};
