import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { SidePanel } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useTutor } from '@/lib/hooks/useTutor';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { tutorService } from '@/lib/services/tutor.service';

export default function DesktopAITutor() {
  const [input, setInput] = useState('');

  const { subjects, isLoading: subjectsLoading } = useSubjects();
  const [activeSubjectId, setActiveSubjectId] = useState<string | undefined>(undefined);
  const [kbActive, setKbActive] = useState(false);

  const { messages, isLoading, error, sendMessage } = useTutor(activeSubjectId);

  // Clear conversation history when subject changes so context is fresh
  const handleSubjectSelect = (subjectId: string) => {
    if (subjectId === activeSubjectId) {
      setActiveSubjectId(undefined);
      setKbActive(false);
    } else {
      tutorService.clearHistory();
      setActiveSubjectId(subjectId);
      setKbActive(false); // will be set true after first response confirms KB
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    try {
      const aiMsg = await sendMessage(input.trim());
      setInput('');
      // Check if the backend confirmed knowledge base is active
      // (we infer from the fact that a subject is selected and materials exist)
    } catch {
      // error surfaced via useTutor error state
    }
  };

  // Build sidebar items from real subjects
  const sidebarItems = subjectsLoading
    ? []
    : subjects.map((s) => ({
        label: s.name,
        active: s.id === activeSubjectId,
        onClick: () => handleSubjectSelect(s.id),
      }));

  const activeSubjectName = subjects.find((s) => s.id === activeSubjectId)?.name;
  const activeSubject = subjects.find((s) => s.id === activeSubjectId);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="text-red-600">Failed to connect to AI Tutor. Please try again.</div>
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

          {/* ── Left Sidebar: real subjects ── */}
          {subjectsLoading ? (
            <aside className="hidden lg:flex flex-col w-72 bg-surface-container-low border-r border-[#4A4A4A]/10 h-[calc(100vh-73px)] p-8 gap-3">
              <Skeleton className="h-4 w-24 mb-4" />
              {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </aside>
          ) : (
            <SidePanel
              title="Your Subjects"
              items={
                sidebarItems.length > 0
                  ? sidebarItems
                  : [{ label: 'No subjects yet — add one first', active: false }]
              }
            />
          )}

          {/* ── Main Chat Area ── */}
          <section className="flex-1 flex flex-col min-h-[calc(100vh-73px)] relative bg-surface">

            {/* Chat Header */}
            <header className="px-12 py-8 flex items-baseline justify-between">
              <h1 className="font-serif italic text-4xl text-on-surface">AI Tutor</h1>
              <div className="flex items-center gap-4 text-[0.75rem] uppercase tracking-tighter text-tertiary">
                {activeSubjectId && activeSubject ? (
                  <>
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-primary" />
                      <span>Context: {activeSubjectName}</span>
                    </div>
                    <div className="flex items-center gap-2 text-on-surface/40">
                      <span className={`w-2 h-2 rounded-full ${activeSubject.papers_uploaded > 0 ? 'bg-green-500' : 'bg-yellow-500'}`} />
                      <span>
                        {activeSubject.papers_uploaded > 0
                          ? `Knowledge base: ${activeSubject.papers_uploaded} paper${activeSubject.papers_uploaded !== 1 ? 's' : ''}`
                          : 'No materials uploaded yet'}
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-on-surface/20" />
                    <span>No subject selected — select one from the sidebar</span>
                  </div>
                )}
              </div>
            </header>

            {/* Scrollable Messages */}
            <div className="flex-1 overflow-y-auto px-12 pb-24 space-y-10 scroll-smooth">
              {messages.length === 0 && !isLoading ? (
                <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
                  <p className="text-on-surface/50 text-lg">No messages yet.</p>
                  {!activeSubjectId && subjects.length > 0 && (
                    <p className="text-on-surface/30 text-sm max-w-xs">
                      Select a subject from the sidebar. The tutor will load its knowledge base from your uploaded materials.
                    </p>
                  )}
                  {activeSubjectId && activeSubject && activeSubject.papers_uploaded === 0 && (
                    <p className="text-on-surface/30 text-sm max-w-xs">
                      No materials uploaded for this subject yet. Upload papers or notes to give the tutor a knowledge base.
                    </p>
                  )}
                  {activeSubjectId && activeSubject && activeSubject.papers_uploaded > 0 && (
                    <p className="text-on-surface/30 text-sm max-w-xs">
                      Knowledge base ready. Ask anything about {activeSubjectName}.
                    </p>
                  )}
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start max-w-3xl'}`}
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
              {isLoading && (
                <div className="flex items-start gap-3">
                  <div className="p-6 bg-surface border-l-4 border-primary max-w-xl">
                    <div className="flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <span
                          key={i}
                          className="w-2 h-2 bg-primary/40 rounded-full animate-bounce"
                          style={{ animationDelay: `${i * 0.15}s` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div className="h-12" />
            </div>

            {/* Input Area (Docked) */}
            <div className="absolute bottom-0 left-0 w-full px-12 pb-8 bg-gradient-to-t from-surface via-surface to-transparent pt-12">
              <div className="flex items-end space-x-0 border-b-2 border-primary bg-surface-container-low p-2">
                <textarea
                  className="flex-1 bg-transparent border-none focus:ring-0 text-sm py-4 px-4 resize-none placeholder:text-tertiary/50"
                  placeholder={
                    activeSubjectId
                      ? 'Ask a question about your subject…'
                      : 'Select a subject from the sidebar, then ask a question…'
                  }
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
                <div className="flex items-center pb-2 pr-2">
                  <button
                    className="bg-primary text-white w-12 h-12 flex items-center justify-center hover:bg-primary/90 transition-colors disabled:opacity-40"
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    aria-label="Send message"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="mt-2 flex justify-end">
                <span className="text-[0.65rem] uppercase text-tertiary/40">
                  Enter to send · Shift + Enter for new line
                </span>
              </div>
            </div>
          </section>

          {/* ── Right Sidebar: removed hardcoded keywords/archives (no API) ── */}
          {/* No backend endpoint provides per-session keywords or related archives.
              Removed to avoid showing stale hardcoded data. */}

        </div>
      </div>
    </>
  );
}
