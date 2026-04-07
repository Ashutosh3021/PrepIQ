export interface Subject {
  id: string;
  name: string;
  description: string;
  icon?: string;
  materialCount: number;
  lastStudied?: string;
  progress: number; // 0-100
}
