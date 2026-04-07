// TODO: Replace with your mock data

export type TutorMessage = {
  id: string;
  sender: 'ai' | 'user';
  content: string;
  timestamp: string;
};

export const TUTOR_MESSAGES_MOCK: TutorMessage[] = [];
