import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { useStudyPlan } from '@/lib/hooks/useStudyPlan';
import StudyPlanView from '@/components/desktop/StudyPlanView';

export default function DesktopStudyPlan() {
  const router = useRouter();
  const { subjects, isLoading: subjectsLoading } = useSubjects();
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const selectedSubject = subjects.find((s) => s.id === selectedSubjectId);

  const { plan, isLoading: planLoading } = useStudyPlan(selectedSubjectId);

  if (subjectsLoading) {
    return (
      <DesktopLayout>
        <Skeleton className="h-12 w-96 mb-8" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Skeleton className="h-96 lg:col-span-1" />
          <Skeleton className="h-96 lg:col-span-2" />
        </div>
      </DesktopLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Study Plan | PrepIQ</title>
        <meta name="description" content="AI-powered personalized study plans" />
      </Head>
      <DesktopLayout>
        {/* Header */}
        <header className="mb-16">
          <span className="text-xs font-bold uppercase tracking-widest text-primary mb-2 block">
            Academic Atelier / Study Planning
          </span>
          <h1 className="text-6xl md:text-7xl font-serif italic leading-none mb-4">
            Study Plan
          </h1>
          <p className="text-on-surface/70 max-w-2xl text-base leading-relaxed">
            Generate AI-powered study schedules optimized for your exam date with spaced repetition and personalized focus on weak areas.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Subject Selector Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-surface-container-low p-8 border border-outline-variant/20">
              <h2 className="text-sm font-bold uppercase tracking-widest text-secondary mb-6">
                Select Subject
              </h2>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {subjects.length === 0 ? (
                  <p className="text-sm text-on-surface/50 italic">No subjects yet. Create one first.</p>
                ) : (
                  subjects.map((subject) => (
                    <button
                      key={subject.id}
                      onClick={() => setSelectedSubjectId(subject.id)}
                      className={`w-full text-left p-4 border-l-4 transition-all text-sm ${
                        selectedSubjectId === subject.id
                          ? 'border-primary bg-primary/5 font-semibold text-on-surface'
                          : 'border-outline-variant bg-surface hover:bg-surface-container text-on-surface/70'
                      }`}
                    >
                      <div className="font-medium">{subject.name}</div>
                      <div className="text-xs text-on-surface/60 mt-1">
                        {subject.code || 'No code'}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Study Plan View */}
          <div className="lg:col-span-2">
            {selectedSubjectId && selectedSubject ? (
              <StudyPlanView
                subjectId={selectedSubjectId}
                subjectName={selectedSubject.name}
              />
            ) : (
              <div className="bg-surface-container-low p-12 border border-outline-variant/20 text-center">
                <p className="text-on-surface/50 text-base mb-4">Select a subject to view or create a study plan</p>
              </div>
            )}
          </div>
        </div>
      </DesktopLayout>
    </>
  );
}
