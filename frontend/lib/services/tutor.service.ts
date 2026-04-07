// TODO: Replace with your mock data
import { apiFetch } from './base.service';
import { TUTOR_MESSAGES_MOCK } from '../mocks/tutor.mock';
import type { TutorMessage } from '../mocks/tutor.mock';

// In-memory conversation state
let conversationHistory: TutorMessage[] = [...TUTOR_MESSAGES_MOCK];

export const tutorService = {
  getMessages: () => apiFetch<TutorMessage[]>('/tutor/messages', conversationHistory),
  sendMessage: (content: string) => {
    const userMsg: TutorMessage = {
      id: Date.now().toString(),
      sender: 'user',
      content,
      timestamp: new Date().toLocaleTimeString(),
    };
    conversationHistory.push(userMsg);
    // Simulate AI response
    const aiMsg: TutorMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'ai',
      content: 'AI response placeholder',
      timestamp: new Date().toLocaleTimeString(),
    };
    conversationHistory.push(aiMsg);
    return apiFetch<TutorMessage>('/tutor/message', aiMsg);
  },
  getHistory: () => conversationHistory,
  clearHistory: () => {
    conversationHistory = [];
  },
};
