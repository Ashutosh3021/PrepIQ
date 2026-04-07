// TODO: Replace with your mock data
import type { User, UserSettings } from '../types/user.types';

export const USER_MOCK: User = {
  id: '',
  name: '',
  email: '',
  createdAt: '',
  studyStreak: 0,
  totalStudyTime: 0,
};

export const USER_SETTINGS_MOCK: UserSettings = {
  userId: '',
  preferredVariant: 'desktop',
  notifications: true,
  theme: 'light',
};
