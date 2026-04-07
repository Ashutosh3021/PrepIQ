import useSWR, { mutate } from 'swr';
import { tutorService } from '../services/tutor.service';
import type { TutorMessage } from '../mocks/tutor.mock';

export function useTutor() {
  const { data, error, isLoading } = useSWR<TutorMessage[]>('tutor/messages', tutorService.getMessages);

  const sendMessage = async (content: string) => {
    // Optimistic update: add user message immediately
    const optimisticMsg: TutorMessage = {
      id: Date.now().toString(),
      sender: 'user',
      content,
      timestamp: new Date().toLocaleTimeString(),
    };
    mutate('tutor/messages', [...(data ?? []), optimisticMsg], false);

    try {
      const result = await tutorService.sendMessage(content);
      mutate('tutor/messages'); // Revalidate after server response
      return result;
    } catch (err) {
      mutate('tutor/messages'); // Revert on error
      throw err;
    }
  };

  return { messages: data ?? [], isLoading, error, sendMessage };
}
