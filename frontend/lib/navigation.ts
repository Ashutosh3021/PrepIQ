import type { NavItem } from './types/nav.types';

export const DESKTOP_NAV: NavItem[] = [
  { name: 'Dashboard',  path: '/desktop/dashboard',  icon: 'home' },
  { name: 'Subjects',   path: '/desktop/subjects',   icon: 'book-open',  aliases: ['Library', 'My Subjects'] },
  { name: 'Upload',     path: '/desktop/upload',     icon: 'upload' },
  { name: 'AI Tutor',   path: '/desktop/ai-tutor',   icon: 'bot',        aliases: ['Chat', 'Ask AI'] },
  { name: 'Tests',      path: '/desktop/tests',      icon: 'clipboard',  aliases: ['Mock Tests', 'Exam'] },
  { name: 'Analysis',   path: '/desktop/analysis',   icon: 'bar-chart',  aliases: ['Progress', 'Results', 'AI Predictions', 'Metrics'] },
  { name: 'Settings',   path: '/desktop/settings',   icon: 'settings' },
  { name: 'Profile',    path: '/desktop/profile',    icon: 'user' },
];

export const MOBILE_NAV: NavItem[] = [
  { name: 'Home',       path: '/mobile/dashboard',   icon: 'home',       aliases: ['Dashboard'] },
  { name: 'Subjects',   path: '/mobile/subjects',    icon: 'book-open',  aliases: ['Library', 'Archive'] },
  { name: 'Upload',     path: '/mobile/upload',      icon: 'upload' },
  { name: 'Chat',       path: '/mobile/ai-tutor',    icon: 'bot',        aliases: ['AI Tutor', 'Ask AI'] },
  { name: 'Tests',      path: '/mobile/tests',       icon: 'clipboard',  aliases: ['Mock Tests'] },
  { name: 'Progress',   path: '/mobile/progress',    icon: 'trending-up',aliases: ['Analysis', 'Results', 'AI Predictions'] },
  { name: 'Settings',   path: '/mobile/settings',    icon: 'settings' },
];
