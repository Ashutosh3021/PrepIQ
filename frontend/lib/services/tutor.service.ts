import { apiFetch } from './base.service';

export type TutorMessage = {
  id: string;
  sender: 'ai' | 'user';
  content: string;
  timestamp: string;
};

/** Shape returned by POST /chat/tutor */
interface TutorResponse {
  response: string;
  context?: {
    conversation_length: number;
    tutor_mode: string;
    model: string;
    subject?: string;
    knowledge_base_active?: boolean;
  } | null;
}

// In-memory conversation history (used in both mock and real mode for context)
let conversationHistory: TutorMessage[] = [];

export const tutorService = {
  /**
   * H-17: The backend has no GET /tutor/messages endpoint.
   * Return the in-memory history directly (no network call needed).
   */
  getMessages: (): Promise<TutorMessage[]> =>
    Promise.resolve([...conversationHistory]),

  /**
   * H-17: Send a message to POST /chat/tutor with the correct payload.
   * The backend expects { message, conversation_history, subject_id? }.
   * Returns the AI response and appends both messages to local history.
   */
  sendMessage: async (content: string, subjectId?: string): Promise<TutorMessage> => {
    // Build the conversation_history payload from local state
    const historyPayload = conversationHistory.map((m) => ({
      role: m.sender === 'user' ? 'user' : 'assistant',
      content: m.content,
    }));

    // Optimistically add the user message to local history
    const userMsg: TutorMessage = {
      id: Date.now().toString(),
      sender: 'user',
      content,
      timestamp: new Date().toLocaleTimeString(),
    };
    conversationHistory.push(userMsg);

    const mockAiMsg: TutorMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'ai',
      content: '',
      timestamp: new Date().toLocaleTimeString(),
    };

    const result = await apiFetch<TutorResponse>(
      '/chat/tutor',
      { response: 'AI response placeholder', context: null },
      {
        method: 'POST',
        body: JSON.stringify({
          message: content,
          conversation_history: historyPayload,
          ...(subjectId ? { subject_id: subjectId } : {}),
        }),
      }
    );

    // Append the AI response to local history
    const aiMsg: TutorMessage = {
      ...mockAiMsg,
      content: result.response,
    };
    conversationHistory.push(aiMsg);

    return aiMsg;
  },

  getHistory: () => [...conversationHistory],

  clearHistory: () => {
    conversationHistory = [];
  },
};
