import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { useTests } from '@/lib/hooks/useTests';

interface TestCardProps {
  id: string;
  category: string;
  title: string;
  time: string;
  questions: string;
  level: string;
  levelColor?: string;
  completed?: boolean;
  score?: string;
}

function TestCard({ id, category, title, time, questions, level, levelColor, completed, score }: TestCardProps) {
  return (
    <article className={`p-5 border border-outline-variant/30 relative ${completed ? 'bg-surface-container-high opacity-75' : 'bg-surface-container-low'}`}>
      <div className="flex justify-between items-start mb-3">
        <span className="bg-primary text-on-primary text-[10px] px-2 py-0.5 font-bold tracking-widest">{category}</span>
        {completed ? (
          <div className="flex gap-2">
            <span className="bg-green-700 text-white text-[10px] px-2 py-0.5 font-bold tracking-widest uppercase">COMPLETED</span>
          </div>
        ) : (
          <span className="text-[10px] font-bold opacity-40">{id}</span>
        )}
      </div>
      <h3 className="font-serif italic text-xl mb-3">{title}</h3>
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="flex flex-col">
          <span className="text-[10px] opacity-40 font-bold">TIME</span>
          <span className="text-sm font-bold">{time}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] opacity-40 font-bold">QUESTIONS</span>
          <span className="text-sm font-bold">{questions}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] opacity-40 font-bold">LEVEL</span>
          <span className={`text-sm font-bold ${levelColor || 'text-primary'}`}>{level}</span>
        </div>
      </div>
      {completed ? (
        <div className="flex gap-2">
          <button className="flex-1 border border-primary text-primary font-bold py-2 text-xs tracking-widest">
            REVIEW
          </button>
          <button className="flex-1 bg-transparent border border-outline-variant text-on-surface-variant font-bold py-2 text-xs tracking-widest">
            RETAKE
          </button>
        </div>
      ) : (
        <Link href="/mobile/start-test" className="w-full bg-primary text-on-primary font-bold py-3 text-xs tracking-widest hover:bg-on-primary-fixed-variant transition-colors flex items-center justify-center">
          START TEST
        </Link>
      )}
    </article>
  );
}

export default function MobileTests() {
  const { tests, isLoading, error, startTest, submitTest } = useTests();

  if (isLoading) {
    return (
      <MobileLayout title="Tests">
        <Skeleton className="h-8 w-48 mb-4" />
        <div className="space-y-4">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      </MobileLayout>
    );
  }

  if (error) {
    return (
      <MobileLayout title="Tests">
        <div className="text-red-600 p-4">Failed to load tests</div>
      </MobileLayout>
    );
  }

  return (
    <>
      <Head>
        <title>PrepIQ - Mock Tests</title>
        <meta name="description" content="Take mock tests on PrepIQ" />
      </Head>
      <MobileLayout title="Tests">
        <div className="space-y-8">
          {/* Page Title */}
          <section>
            <h1 className="font-serif italic text-4xl leading-tight">Mock Tests</h1>
            <p className="text-on-surface-variant text-xs mt-2 font-medium tracking-tight uppercase">SELECT A DOMAIN TO BEGIN GENERATING QUESTIONS</p>
          </section>

          {/* Subject Generation Pills */}
          <section className="grid grid-cols-2 gap-3">
            {['QUANTITATIVE', 'VERBAL REASONING', 'LOGICAL ANALYSIS', 'DATA INSIGHTS'].map((domain) => (
              <button key={domain} className="bg-primary text-on-primary py-4 px-4 flex flex-col justify-between items-start active:scale-95 transition-transform">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-on-primary">
                  <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
                <span className="mt-3 font-bold text-xs tracking-wide">{domain}</span>
              </button>
            ))}
          </section>

          {/* Filter Tabs */}
          <div className="flex gap-4 border-b border-outline-variant pb-2">
            <span className="text-primary font-bold text-xs tracking-widest border-b-2 border-primary pb-2">AVAILABLE</span>
            <span className="text-on-surface-variant opacity-40 font-bold text-xs tracking-widest pb-2">COMPLETED</span>
          </div>

          {/* Test Cards List */}
          <section className="space-y-4">
            {tests.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-on-surface-variant/50 text-sm">No tests available yet.</p>
              </div>
            ) : (
              tests.map((test) => {
                const isCompleted = test.status === 'completed';
                const levelColor =
                  test.difficulty === 'hard'
                    ? 'text-error'
                    : test.difficulty === 'medium'
                      ? 'text-primary'
                      : 'text-green-700';
                return (
                  <TestCard
                    key={test.id}
                    id={test.id}
                    category={test.subject}
                    title={test.title}
                    time={`${test.duration} MIN`}
                    questions={`${test.questionCount} Qs`}
                    level={test.difficulty.toUpperCase()}
                    levelColor={levelColor}
                    completed={isCompleted}
                    score={test.score ? `${test.score}%` : undefined}
                  />
                );
              })
            )}
          </section>

          {/* Motivation Banner */}
          <section className="bg-on-surface text-surface p-6 mt-8 flex flex-col items-center text-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-surface mb-3">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
            <p className="font-serif italic text-xl italic mb-3">&quot;Success is a collection of problems solved with quiet discipline.&quot;</p>
            <div className="h-px w-10 bg-primary mb-3" />
            <p className="text-[10px] tracking-[0.2em] font-bold opacity-60">ACADEMIC EXCELLENCE SERIES 2024</p>
          </section>
        </div>
      </MobileLayout>
    </>
  );
}
