import React, { useState } from 'react';
import Head from 'next/head';
import { MobileLayout } from '@/components/mobile';
import { SubjectPill } from '@/components/mobile';
import { Skeleton, Spinner } from '@/components/common';
import { useTutor } from '@/lib/hooks/useTutor';

const subjectChips = ['Advanced Calculus', 'Linear Algebra', 'Mock Exam #4'];

export default function MobileAITutor() {
  const [inputValue, setInputValue] = useState('');
  const [activeChip, setActiveChip] = useState(0);
  const { messages, isLoading, error, sendMessage } = useTutor();

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    try {
      await sendMessage(inputValue.trim());
      setInputValue('');
    } catch (err) {
      // Error handled by SWR revalidation
    }
  };

  if (error) {
    return (
      <MobileLayout title="AI Tutor">
        <div className="text-red-600 p-4">Failed to load tutor messages</div>
      </MobileLayout>
    );
  }

  return (
    <>
      <Head>
        <title>PrepIQ - AI Tutor</title>
        <meta name="description" content="Chat with your AI Tutor" />
      </Head>
      <MobileLayout title="AI Tutor">
        <div className="flex flex-col">
          {/* Subject Context Chips */}
          <div className="flex gap-2 overflow-x-auto py-4 hide-scrollbar">
            {subjectChips.map((chip, index) => (
              <button
                key={chip}
                onClick={() => setActiveChip(index)}
                className={
                  index === activeChip
                    ? 'bg-primary text-on-primary px-4 py-2 flex items-center gap-2 border-0 whitespace-nowrap text-xs font-bold tracking-widest uppercase flex-shrink-0'
                    : 'bg-surface-container text-primary px-4 py-2 border border-primary/10 whitespace-nowrap text-xs font-bold tracking-widest uppercase flex-shrink-0'
                }
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Chat History */}
          <div className="flex flex-col gap-6 mb-8">
            {messages.length === 0 && !isLoading ? (
              <div className="text-center py-16">
                <p className="text-on-surface-variant/50 text-sm">No messages yet. Start a conversation!</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col gap-1 max-w-[90%] ${
                    msg.sender === 'user' ? 'self-end' : 'self-start'
                  }`}
                >
                  <div
                    className={
                      msg.sender === 'user'
                        ? 'bg-primary text-on-primary p-4'
                        : 'bg-surface-container-low border-l-4 border-primary p-4'
                    }
                  >
                    <p className="font-body text-sm leading-relaxed">{msg.content}</p>
                  </div>
                  <span
                    className={`text-[10px] uppercase tracking-tighter opacity-50 ${
                      msg.sender === 'user' ? 'text-right mr-1' : 'ml-1'
                    }`}
                  >
                    {msg.sender === 'user' ? 'YOU' : 'AI TUTOR'} &bull; {msg.timestamp}
                  </span>
                </div>
              ))
            )}
            {isLoading && messages.length === 0 && (
              <div className="space-y-4 py-8">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-16 w-3/4 ml-auto" />
                <Skeleton className="h-24 w-full" />
              </div>
            )}
          </div>
        </div>

        {/* Bottom Input Area */}
        <div className="fixed bottom-16 left-0 w-full bg-surface p-3 z-20 border-t border-outline-variant/20">
          <div className="max-w-3xl mx-auto flex gap-3 items-end">
            <div className="flex-grow bg-surface-container-low border-b-2 border-primary">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="w-full bg-transparent border-0 focus:ring-0 font-body text-sm p-3 resize-none min-h-[48px] placeholder:opacity-50"
                placeholder="Type your question here..."
                rows={1}
              />
            </div>
            <button
              className="bg-primary text-on-primary w-12 h-12 flex items-center justify-center active:scale-95 transition-transform flex-shrink-0"
              onClick={handleSend}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="m22 2-7 20-4-9-9-4Z" />
                <path d="M22 2 11 13" />
              </svg>
            </button>
          </div>
        </div>
      </MobileLayout>
    </>
  );
}
