import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { DesktopLayout, SubjectCard } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';

export default function DesktopSubjects() {
  const { subjects, isLoading, error } = useSubjects();

  if (isLoading) {
    return (
      <DesktopLayout>
        <Skeleton className="h-12 w-96 mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </DesktopLayout>
    );
  }

  if (error) {
    return (
      <DesktopLayout>
        <div className="text-red-600">Failed to load subjects</div>
      </DesktopLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Subjects | PrepIQ</title>
        <meta name="description" content="Browse and manage your study subjects" />
      </Head>
      <DesktopLayout>
        {/* Header Row */}
        <header className="flex flex-col md:flex-row justify-between items-end mb-16 gap-6">
          <div className="flex flex-col">
            <span className="text-xs font-bold uppercase tracking-widest text-primary mb-2">
              Academic Atelier / 2024
            </span>
            <h1 className="text-6xl md:text-7xl font-serif italic leading-none">My Subjects</h1>
          </div>
          <div className="flex gap-4">
            <button className="bg-primary text-on-primary px-6 py-3 text-sm font-semibold uppercase tracking-wider hover:bg-primary/90 transition-all flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <span>Add Subject</span>
            </button>
            <button className="border border-primary text-primary px-6 py-3 text-sm font-semibold uppercase tracking-wider hover:bg-primary hover:text-on-primary transition-all flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="1 4 1 10 7 10" />
                <polyline points="23 20 23 14 17 14" />
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
              </svg>
              <span>Sync from Wizard</span>
            </button>
          </div>
        </header>

        {/* Subjects Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {subjects.length === 0 ? (
            <div className="col-span-full text-center py-16">
              <p className="text-on-surface/50 text-lg">No subjects yet. Add one to get started.</p>
            </div>
          ) : (
            subjects.map((subject) => (
              <SubjectCard
                key={subject.id}
                subject={{
                  code: subject.id,
                  name: subject.name,
                  description: subject.description,
                  progress: subject.progress,
                }}
                onTrackProgress={() => {
                  // Future: navigate to subject detail page
                }}
              />
            ))
          )}
        </div>

        {/* Asymmetric Archive Detail Section */}
        <section className="mt-24 grid grid-cols-12 gap-8 border-t border-primary/10 pt-16">
          <div className="col-span-12 lg:col-span-4">
            <h3 className="text-4xl font-serif italic mb-6">Active Archive</h3>
            <p className="text-sm text-on-surface/70 leading-loose max-w-xs">
              Your study materials are curated into focused modules. Each subject represents a
              curated archive of past papers, predictive analytics, and personalized AI tutoring
              sessions.
            </p>
          </div>
          <div className="col-span-12 lg:col-span-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-surface-container-lowest p-6 flex items-center justify-between border border-outline-variant/20">
                <div>
                  <p className="text-[0.65rem] font-bold text-primary uppercase mb-1">Last Sync</p>
                  <p className="text-lg font-serif">Today, 09:14 AM</p>
                </div>
                <span className="text-primary">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </span>
              </div>
              <div className="bg-surface-container-lowest p-6 flex items-center justify-between border border-outline-variant/20">
                <div>
                  <p className="text-[0.65rem] font-bold text-primary uppercase mb-1">
                    Total Study Hours
                  </p>
                  <p className="text-lg font-serif">124.5 hrs</p>
                </div>
                <span className="text-primary">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                </span>
              </div>
            </div>
            <div className="mt-8">
              <div className="relative overflow-hidden bg-surface-container-highest h-48 w-full group">
                <div className="absolute inset-0 bg-primary/10 mix-blend-multiply" />
                <div className="absolute inset-0 flex flex-col justify-center px-12">
                  <span className="text-xs font-bold uppercase tracking-widest text-primary mb-2">
                    Next Scheduled Exam
                  </span>
                  <h4 className="text-3xl font-serif italic">
                    Advanced Calculus - Final Mock
                  </h4>
                  <p className="text-sm font-bold uppercase mt-2">
                    MARCH 15, 2024 / 09:00 EST
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </DesktopLayout>
    </>
  );
}
