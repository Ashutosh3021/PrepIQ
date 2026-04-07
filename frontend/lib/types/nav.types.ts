export type NavVariant = 'desktop' | 'mobile';
export type NavPosition = 'top' | 'bottom';

export interface NavItem {
  name: string;
  path: string;
  icon: string;
  aliases?: string[];
}
