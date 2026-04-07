import React, { useState } from 'react';
import Head from 'next/head';
import { SidePanel } from '@/components/desktop';
import { Skeleton, Spinner } from '@/components/common';
import { useTutor } from '@/lib/hooks/useTutor';

const courseItems = [
  { label: 'Advanced Physics', active: true },
  { label: 'Organic Chemistry', active: false },
  { label: 'Calculus III', active: false },
  { label: 'Macroeconomics', active: false },
  { label: 'Modern World History', active: false },
];

export default function DesktopAITutor() {
  const [input, setInput] = useState('');
  const { messages, isLoading, error, sendMessage } = useTutor();

  const handleSend = async () => {
    if (!input.trim()) return;
    try {
      await sendMessage(input.trim());
      setInput('');
    } catch (err) {
      // Error handled by SWR revalidation
    }
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="text-red-600">Failed to load tutor messages</div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>AI Tutor | PrepIQ</title>
        <meta name="description" content="AI-powered tutoring session" />
      </Head>
      <div className="min-h-screen flex flex-col bg-surface">
        <div className="flex flex-row">
          {/* Left Sidebar */}
          <SidePanel title="Course Archive" items={courseItems} />

          {/* Main Chat Area */}
          <section className="flex-1 flex flex-col min-h-[calc(100vh-73px)] relative bg-surface">
            {/* Chat Header */}
            <header className="px-12 py-8 flex items-baseline justify-between">
              <h1 className="font-serif italic text-4xl text-on-surface">AI Tutor</h1>
              <div className="flex items-center space-x-2 text-[0.75rem] uppercase tracking-tighter text-tertiary">
                <span className="w-2 h-2 bg-primary" />
                <span>Live Context: Quantum Mechanics</span>
              </div>
            </header>

            {/* Scrollable Messages */}
            <div className="flex-1 overflow-y-auto px-12 pb-24 space-y-10 scroll-smooth">
              {messages.length === 0 && !isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-on-surface/50 text-lg">No messages yet. Start a conversation!</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} ${msg.sender === 'ai' ? 'max-w-3xl' : ''}`}
                  >
                    <div
                      className={`font-label text-[0.65rem] uppercase tracking-widest text-tertiary mb-3 ${msg.sender === 'user' ? 'text-right' : ''}`}
                    >
                      {msg.sender === 'ai' ? 'PrepIQ Assistant' : 'You'} &mdash; {msg.timestamp}
                    </div>

                    <div
                      className={`p-6 leading-relaxed shadow-sm max-w-xl ${
                        msg.sender === 'ai'
                          ? 'bg-surface border-l-4 border-primary text-on-surface'
                          : 'bg-primary text-white'
                      }`}
                    >
                      {msg.content.split('\n\n').map((paragraph, idx) => (
                        <p key={idx} className={idx > 0 ? 'mt-4 text-sm' : 'text-sm'}>
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </div>
                ))
              )}
              {isLoading && messages.length === 0 && (
                <div className="space-y-6 py-10">
                  <Skeleton className="h-24 w-full max-w-3xl" />
                  <Skeleton className="h-24 w-full max-w-xl ml-auto" />
                  <Skeleton className="h-24 w-full max-w-3xl" />
                </div>
              )}
              <div className="h-12" />
            </div>

            {/* Input Area (Docked) */}
            <div className="absolute bottom-0 left-0 w-full px-12 pb-8 bg-gradient-to-t from-surface via-surface to-transparent pt-12">
              <div className="flex items-end space-x-0 border-b-2 border-primary bg-surface-container-low p-2">
                <textarea
                  className="flex-1 bg-transparent border-none focus:ring-0 text-sm py-4 px-4 resize-none placeholder:text-tertiary/50"
                  placeholder="Inquire about the concepts or submit your answer..."
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                />
                <div className="flex items-center pb-2 pr-2 space-x-4">
                  <button className="text-tertiary hover:text-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                    </svg>
                  </button>
                  <button
                    className="bg-primary text-white w-12 h-12 flex items-center justify-center hover:bg-primary/90 transition-colors"
                    onClick={handleSend}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="mt-2 flex justify-between">
                <div className="flex space-x-4">
                  <button className="text-[0.65rem] uppercase text-tertiary hover:text-on-surface">
                    Show Formulas
                  </button>
                  <button className="text-[0.65rem] uppercase text-tertiary hover:text-on-surface">
                    Reference Textbook
                  </button>
                </div>
                <span className="text-[0.65rem] uppercase text-tertiary/40">
                  Enter to send \u2022 Shift + Enter for new line
                </span>
              </div>
            </div>
          </section>

          {/* Right Sidebar: Focus Keywords + Related Archives */}
          <aside className="hidden xl:flex flex-col w-64 bg-surface-container border-l border-[#4A4A4A]/10 p-8 space-y-8">
            <div>
              <h4 className="text-[0.7rem] uppercase tracking-widest text-tertiary mb-4">
                Focus Keywords
              </h4>
              <div className="flex flex-wrap gap-2">
                <span className="bg-primary/10 text-primary px-2 py-1 text-[0.6rem] font-bold">
                  PLANCK&apos;S CONSTANT
                </span>
                <span className="bg-primary/10 text-primary px-2 py-1 text-[0.6rem] font-bold">
                  PHOTONS
                </span>
                <span className="bg-primary/10 text-primary px-2 py-1 text-[0.6rem] font-bold">
                  WORK FUNCTION
                </span>
              </div>
            </div>
            <div className="pt-8 border-t border-[#4A4A4A]/10">
              <h4 className="text-[0.7rem] uppercase tracking-widest text-tertiary mb-4">
                Related Archives
              </h4>
              <div className="space-y-4">
                <div className="group cursor-pointer">
                  <p className="text-xs font-bold text-on-surface group-hover:text-primary transition-colors">
                    Wave-Particle Duality
                  </p>
                  <p className="text-[0.6rem] text-tertiary">Last reviewed 2 days ago</p>
                </div>
                <div className="group cursor-pointer">
                  <p className="text-xs font-bold text-on-surface group-hover:text-primary transition-colors">
                    Atomic Transitions
                  </p>
                  <p className="text-[0.6rem] text-tertiary">Recommended for your path</p>
                </div>
              </div>
            </div>
            <div className="mt-auto">
              <div className="relative w-full aspect-square bg-surface-variant overflow-hidden">
                <div className="absolute inset-0 bg-primary/20 mix-blend-multiply" />
                <div className="absolute inset-0 p-4 flex flex-col justify-end bg-gradient-to-t from-surface-variant to-transparent">
                  <span className="text-[0.6rem] font-bold uppercase tracking-widest">
                    Scientific Library
                  </span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </>
  );
}
