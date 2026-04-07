import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';

export default function MobileDashboard() {
  const { subjects, isLoading, error } = useSubjects();

  if (isLoading) {
    return (
      <MobileLayout title="Home">
        <div className="space-y-8">
          <Skeleton className="h-24 w-full mb-4" />
          <div className="grid grid-cols-2 gap-3">
            <Skeleton className="h-24 aspect-square" />
            <Skeleton className="h-24 aspect-square" />
            <Skeleton className="h-24 aspect-square" />
            <Skeleton className="h-24 aspect-square" />
          </div>
          <Skeleton className="h-32" />
          <div className="space-y-3">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
        </div>
      </MobileLayout>
    );
  }

  if (error) {
    return (
      <MobileLayout title="Home">
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center px-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-error mb-4">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <h2 className="text-xl font-bold text-on-surface mb-2">Failed to load</h2>
          <p className="text-on-surface/60 mb-6 text-sm">{error.message || 'An unexpected error occurred'}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-primary text-on-primary px-6 py-3 font-bold uppercase tracking-widest text-sm hover:bg-primary/90 transition-colors"
          >
            Try Again
          </button>
        </div>
      </MobileLayout>
    );
  }

  return (
    <>
      <Head>
        <title>PrepIQ - Home</title>
        <meta name="description" content="PrepIQ mobile dashboard" />
      </Head>
      <MobileLayout title="Home">
        <div className="space-y-8">
          {/* Welcome Banner */}
          <section className="bg-surface-container-low p-6 border border-outline-variant/20 relative overflow-hidden">
            <div className="space-y-2 z-10">
              <h1 className="font-serif italic text-3xl text-on-surface">Good morning, Rahul</h1>
              <p className="text-xs uppercase tracking-widest text-secondary">Advanced Neurobiology &bull; Spring 2024</p>
            </div>
            <div className="mt-4 px-4 py-2 bg-primary text-on-primary text-xs font-bold uppercase tracking-tighter z-10 inline-block">
              47 days to exam
            </div>
            <div className="absolute -right-4 -bottom-4 opacity-5 font-serif italic text-[8rem] select-none pointer-events-none">
              IQ
            </div>
          </section>

          {/* Stats Grid */}
          <section className="grid grid-cols-2 gap-3">
            {/* Enrolled Subjects */}
            <div className="bg-surface p-4 border border-outline-variant/20 flex flex-col justify-between aspect-square">
              <p className="text-[10px] uppercase tracking-widest text-secondary">Enrolled Subjects</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-light">08</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </div>
            </div>

            {/* Total Progress */}
            <div className="bg-surface p-4 border border-outline-variant/20 flex flex-col justify-between aspect-square">
              <p className="text-[10px] uppercase tracking-widest text-secondary">Total Progress</p>
              <div className="relative h-12 w-full flex items-end">
                <div className="w-full bg-surface-container-highest h-3">
                  <div className="bg-primary h-full w-[68%]" />
                </div>
              </div>
              <p className="font-bold text-xl">68%</p>
            </div>

            {/* Focus Area */}
            <div className="bg-surface p-4 border border-outline-variant/20 flex flex-col justify-between aspect-square">
              <p className="text-[10px] uppercase tracking-widest text-secondary">Focus Area</p>
              <div className="space-y-1">
                <p className="font-serif italic text-lg leading-tight">Cellular Pathways</p>
                <p className="text-[10px] text-primary uppercase font-bold">Review Needed</p>
              </div>
            </div>

            {/* Study Streak */}
            <div className="bg-surface p-4 border border-outline-variant/20 flex flex-col justify-between aspect-square">
              <p className="text-[10px] uppercase tracking-widest text-secondary">Daily Streak</p>
              <div className="flex items-center gap-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                  <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12c0 2.76 1.12 5.26 2.93 7.07L12 22z" />
                  <path d="M12 6v6l4 2" />
                </svg>
                <span className="text-3xl">14</span>
              </div>
            </div>
          </section>

          {/* Two Column Section */}
          <section className="space-y-8">
            {/* Today's Focus */}
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="h-px flex-grow bg-outline-variant opacity-30" />
                <h2 className="text-[10px] uppercase tracking-[0.3em] text-secondary whitespace-nowrap">Today&apos;s Focus</h2>
              </div>
              <div className="bg-surface-container-highest p-6 space-y-4 border border-outline-variant/20">
                <div className="space-y-2">
                  <h3 className="font-serif italic text-2xl">Module 04: Synaptic Plasticity</h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed">Focusing on long-term potentiation and memory formation mechanisms. Estimated time: 45 mins.</p>
                </div>
                <Link
                  href="/mobile/start-test"
                  className="w-full bg-primary text-on-primary py-3 font-bold uppercase tracking-widest transition-colors hover:bg-on-primary-fixed-variant active:scale-95 duration-100 flex items-center justify-center gap-2"
                >
                  Start Studying
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </Link>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <h2 className="text-[10px] uppercase tracking-[0.3em] text-secondary whitespace-nowrap">Recent Activity</h2>
                <div className="h-px flex-grow bg-outline-variant opacity-30" />
              </div>
              <div className="space-y-3">
                {/* Activity Item 1 */}
                <Link href="/mobile/tests" className="flex gap-3 p-3 border border-outline-variant/10 items-center group hover:bg-surface-container-low transition-colors">
                  <div className="w-10 h-10 bg-surface-container flex items-center justify-center flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                      <path d="M15.5 2H8.5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z" />
                      <path d="M9 12h6" />
                      <path d="M9 16h6" />
                      <path d="M9 8h6" />
                    </svg>
                  </div>
                  <div className="flex-grow min-w-0">
                    <p className="text-sm font-semibold">Mock Test: Organic Chemistry</p>
                    <p className="text-[10px] text-secondary">Yesterday &bull; 84% Score</p>
                  </div>
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-outline-variant opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                    <path d="m9 18 6-6-6-6" />
                  </svg>
                </Link>

                {/* Activity Item 2 */}
                <Link href="/mobile/subjects" className="flex gap-3 p-3 border border-outline-variant/10 items-center group hover:bg-surface-container-low transition-colors">
                  <div className="w-10 h-10 bg-surface-container flex items-center justify-center flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <path d="M14 2v6h6" />
                      <path d="M16 13H8" />
                      <path d="M16 17H8" />
                      <path d="M10 9H8" />
                    </svg>
                  </div>
                  <div className="flex-grow min-w-0">
                    <p className="text-sm font-semibold">Flashcards: Molecular Bio</p>
                    <p className="text-[10px] text-secondary">2 days ago &bull; 12 New Cards</p>
                  </div>
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-outline-variant opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                    <path d="m9 18 6-6-6-6" />
                  </svg>
                </Link>

                {/* Activity Item 3 */}
                <Link href="/mobile/upload" className="flex gap-3 p-3 border border-outline-variant/10 items-center group hover:bg-surface-container-low transition-colors">
                  <div className="w-10 h-10 bg-surface-container flex items-center justify-center flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </div>
                  <div className="flex-grow min-w-0">
                    <p className="text-sm font-semibold">Uploaded Lecture Notes</p>
                    <p className="text-[10px] text-secondary">3 days ago &bull; PDF Processed</p>
                  </div>
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-outline-variant opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                    <path d="m9 18 6-6-6-6" />
                  </svg>
                </Link>
              </div>
            </div>
          </section>
        </div>
      </MobileLayout>
    </>
  );
}
