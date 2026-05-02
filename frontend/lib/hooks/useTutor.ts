import { useState, useCallback } from 'react';
import { tutorService, TutorMessage } from '../services/tutor.service';

/**
 * H-17: useTutor no longer uses SWR for getMessages (there is no GET endpoint).
 * Instead it manages local state and calls POST /chat/tutor for each message.
 */
export function useTutor(subjectId?: string) {
  const [messages, setMessages] = useState<TutorMessage[]>(() =>
    tutorService.getHistory()
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      setError(null);

      // Optimistic: add user message immediately
      const userMsg: TutorMessage = {
        id: Date.now().toString(),
        sender: 'user',
        content,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const aiMsg = await tutorService.sendMessage(content, subjectId);
        // tutorService already appended both messages to its internal history;
        // sync local state from the service's history to stay consistent.
        setMessages(tutorService.getHistory());
        return aiMsg;
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
        // Revert optimistic update on error
        setMessages(tutorService.getHistory());
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [subjectId]
  );

  const clearHistory = useCallback(() => {
    tutorService.clearHistory();
    setMessages([]);
  }, []);

  return { messages, isLoading, error, sendMessage, clearHistory };
}
