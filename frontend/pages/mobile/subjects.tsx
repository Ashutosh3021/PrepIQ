import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';

interface SubjectCardProps {
  code: string;
  name: string;
  progress: number;
}

function SubjectCard({ code, name, progress }: SubjectCardProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant/30 border-t-4 border-t-primary">
      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div>
            <p className="text-[10px] uppercase tracking-widest text-secondary mb-1">CODE: {code}</p>
            <h2 className="text-lg font-bold text-on-surface">{name}</h2>
          </div>
          <div className="flex gap-2">
            <button className="text-on-surface-variant p-1 active:opacity-60" aria-label="Edit subject">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                <path d="m15 5 4 4" />
              </svg>
            </button>
            <button className="text-error p-1 active:opacity-60" aria-label="Delete subject">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18" />
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              </svg>
            </button>
          </div>
        </div>
        <div className="mb-4">
          <div className="flex justify-between items-end mb-1">
            <span className="text-xs font-bold text-secondary">PROGRESS</span>
            <span className="text-xs font-bold text-primary">{progress}%</span>
          </div>
          <div className="w-full bg-secondary-container h-2">
            <div className="bg-primary h-full" style={{ width: `${progress}%` }} />
          </div>
        </div>
        <Link href="/mobile/progress" className="w-full py-2 border border-primary text-primary font-bold flex items-center justify-center gap-2 hover:bg-surface-container-high transition-colors">
          <span>Track Progress</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
        </Link>
      </div>
    </div>
  );
}

export default function MobileSubjects() {
  const { subjects, isLoading, error } = useSubjects();

  if (isLoading) {
    return (
      <MobileLayout title="My Subjects">
        <div className="space-y-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </MobileLayout>
    );
  }

  if (error) {
    return (
      <MobileLayout title="My Subjects">
        <div className="text-red-600 p-4">Failed to load subjects</div>
      </MobileLayout>
    );
  }

  return (
    <>
      <Head>
        <title>PrepIQ - My Subjects</title>
        <meta name="description" content="Manage your subjects on PrepIQ" />
      </Head>
      <MobileLayout title="My Subjects">
        <div className="space-y-8">
          {/* Action Buttons */}
          <div className="flex flex-col gap-3">
            <button className="w-full bg-primary text-on-primary py-3 px-4 font-bold flex items-center justify-center gap-2 active:scale-[0.98] transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5v14" />
                <path d="M5 12h14" />
              </svg>
              <span>Add Subject</span>
            </button>
            <button className="w-full bg-transparent border border-outline-variant text-on-surface-variant py-3 px-4 font-bold flex items-center justify-center gap-2 active:scale-[0.98] transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.5 2v6h-6" />
                <path d="M2.5 22v-6h6" />
                <path d="M2 11.5a10 10 0 0 1 18.8-4.3" />
                <path d="M22 12.5a10 10 0 0 1-18.8 4.2" />
              </svg>
              <span>Sync from Wizard</span>
            </button>
          </div>

          {/* Subject List */}
          <div className="space-y-4">
            {subjects.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-on-surface-variant/50 text-sm">No subjects yet.</p>
              </div>
            ) : (
              subjects.map((subject) => (
                <SubjectCard
                  key={subject.id}
                  code={subject.id}
                  name={subject.name}
                  progress={subject.progress}
                />
              ))
            )}

            {/* Empty State Hint */}
            <div className="border-2 border-dashed border-outline-variant p-8 flex flex-col items-center justify-center text-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-outline-variant mb-3">
                <path d="m16 6 4 14" />
                <path d="M12 6v14" />
                <path d="M8 8v12" />
                <path d="M4 4v16" />
              </svg>
              <p className="font-serif italic text-xl text-on-surface mb-2">New semester?</p>
              <p className="text-secondary text-sm max-w-[200px]">Import your syllabus using the PrepIQ Study Wizard.</p>
            </div>
          </div>
        </div>
      </MobileLayout>
    </>
  );
}
