import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { DesktopLayout, StatWidget } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';

const recentActivity = [
  {
    icon: 'quiz',
    title: 'Mock Test: Organic Chemistry',
    meta: 'Completed with 84% accuracy \u2022 2h ago',
  },
  {
    icon: 'style',
    title: 'Flashcards: Cardiac Anatomy',
    meta: 'Reviewed 45 cards \u2022 5h ago',
  },
  {
    icon: 'description',
    title: 'Uploaded Notes: Renal Physiology',
    meta: 'AI Summary generated \u2022 Yesterday',
  },
  {
    icon: 'psychology_alt',
    title: 'AI Tutor Session',
    meta: 'Topic: Protein Folding Errors \u2022 Oct 18',
  },
];

export default function DesktopDashboard() {
  const { subjects, isLoading, error } = useSubjects();

  if (isLoading) {
    return (
      <DesktopLayout>
        <Skeleton className="h-8 w-64 mb-2" />
        <Skeleton className="h-4 w-48 mb-12" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-0 mb-12 border-t border-l border-outline-variant/20">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 items-start">
          <div className="lg:col-span-2">
            <Skeleton className="h-64" />
          </div>
          <Skeleton className="h-64" />
        </div>
      </DesktopLayout>
    );
  }

  if (error) {
    return (
      <DesktopLayout>
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-error mb-4">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <h2 className="text-2xl font-bold text-on-surface mb-2">Failed to load dashboard</h2>
          <p className="text-on-surface/60 mb-6">{error.message || 'An unexpected error occurred'}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-primary text-on-primary px-6 py-3 font-bold uppercase tracking-widest text-sm hover:bg-primary/90 transition-colors"
          >
            Try Again
          </button>
        </div>
      </DesktopLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Dashboard | PrepIQ</title>
        <meta name="description" content="PrepIQ Desktop Dashboard - Your study overview" />
      </Head>
      <DesktopLayout>
        {/* Hero Section */}
        <section className="mb-16">
          <h1 className="text-6xl font-serif italic text-on-surface mb-2 tracking-tight">
            Good morning, Rahul
          </h1>
          <p className="text-on-surface/60 font-medium uppercase tracking-widest text-xs">
            A quiet environment is prepared for your focused study session.
          </p>
        </section>

        {/* Stats Row */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-0 mb-12 border-t border-l border-outline-variant/20">
          <StatWidget label="Subjects" value="08" icon="book-open" />
          <StatWidget label="Progress" value="68%" icon="bar-chart" />
          <StatWidget label="Focus Area" value="Cellular Pathways" icon="target" />
          <StatWidget label="Streak" value="14" icon="trending-up" />
        </section>

        {/* Main Content Split */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-12 items-start">
          {/* Left: Today's Focus + Secondary Row */}
          <div className="lg:col-span-2">
            <div className="bg-surface-container-highest p-12 relative overflow-hidden">
              <div className="relative z-10">
                <span className="text-xs font-bold uppercase tracking-[0.2em] text-primary mb-12 block">
                  Current Focus Module
                </span>
                <h2 className="text-5xl font-serif italic text-on-surface mb-4">
                  Synaptic Plasticity
                </h2>
                <p className="text-lg text-on-surface/70 mb-12 max-w-md font-light leading-relaxed">
                  A deep dive into the cellular mechanisms of memory formation and long-term
                  potentiation. Reviewing 24 key concepts today.
                </p>
                <Link
                  href="/desktop/start-test"
                  className="bg-primary text-on-primary px-10 py-5 font-bold uppercase tracking-widest text-sm inline-flex items-center group hover:bg-primary/90 transition-colors"
                >
                  Start Studying
                  <span className="ml-3 group-hover:translate-x-1 transition-transform">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                  </span>
                </Link>
              </div>
            </div>

            {/* Secondary Row (Bento Style) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
              <div className="bg-surface-container p-8">
                <h3 className="text-xs font-bold uppercase tracking-widest text-primary mb-6">
                  Study Timer
                </h3>
                <div className="flex items-center justify-between">
                  <span className="text-4xl font-light tracking-tight">00:45:00</span>
                  <button className="text-primary border border-primary px-4 py-2 text-xs font-bold uppercase hover:bg-primary hover:text-on-primary transition-colors">
                    Focus Mode
                  </button>
                </div>
              </div>
              <div className="bg-surface-container p-8">
                <h3 className="text-xs font-bold uppercase tracking-widest text-primary mb-6">
                  Upcoming Test
                </h3>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="block text-xl font-bold">Neurobiology Midterm</span>
                    <span className="text-xs opacity-60">Scheduled: Oct 24, 2024</span>
                  </div>
                  <span className="text-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Recent Activity */}
          <div className="bg-surface p-0">
            <h3 className="text-xs font-bold uppercase tracking-widest text-primary mb-8 pb-4 border-b border-outline-variant/20">
              Recent Activity
            </h3>
            <div className="space-y-0">
              {recentActivity.map((item, index) => (
                <div
                  key={index}
                  className="flex items-start gap-4 py-6 border-b border-outline-variant/10 group cursor-pointer hover:bg-surface-container-low transition-colors px-2 last:border-b-0"
                >
                  <div className="w-12 h-12 bg-surface-container-high flex items-center justify-center text-primary shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      {item.icon === 'quiz' && (
                        <>
                          <circle cx="12" cy="12" r="10" />
                          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                          <line x1="12" y1="17" x2="12.01" y2="17" />
                        </>
                      )}
                      {item.icon === 'style' && (
                        <>
                          <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z" />
                          <line x1="16" y1="8" x2="2" y2="22" />
                          <line x1="17.5" y1="15" x2="9" y2="15" />
                        </>
                      )}
                      {item.icon === 'description' && (
                        <>
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                          <line x1="16" y1="13" x2="8" y2="13" />
                          <line x1="16" y1="17" x2="8" y2="17" />
                        </>
                      )}
                      {item.icon === 'psychology_alt' && (
                        <>
                          <path d="M12 2a10 10 0 1 0 10 10H12V2z" />
                          <path d="M20 12a8 8 0 0 0-8-8v8h8z" />
                        </>
                      )}
                    </svg>
                  </div>
                  <div>
                    <p className="font-bold text-on-surface">{item.title}</p>
                    <p className="text-sm text-on-surface/60">{item.meta}</p>
                  </div>
                </div>
              ))}
            </div>
            <button className="mt-8 text-xs font-bold uppercase tracking-widest text-primary underline underline-offset-4 hover:text-on-surface transition-colors">
              View Full Archive
            </button>
          </div>
        </section>
      </DesktopLayout>
    </>
  );
}
