export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  createdAt: string;
  studyStreak: number;
  totalStudyTime: number; // minutes
}

export interface UserSettings {
  userId: string;
  preferredVariant: 'desktop' | 'mobile';
  notifications: boolean;
  theme: 'light' | 'dark';
}
