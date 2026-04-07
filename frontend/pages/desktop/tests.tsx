import React from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useTests } from '@/lib/hooks/useTests';

const testDomains = [
  { name: 'Quantitative', focus: 'Focus: Arithmetic, Algebra, Geometry' },
  { name: 'Verbal', focus: 'Focus: RC, Sentence Equivalence' },
  { name: 'Logical', focus: 'Focus: Induction, Deduction, Systems' },
  { name: 'Data Insights', focus: 'Focus: Multi-Source Reasoning' },
];

export default function DesktopTests() {
  const router = useRouter();
  const { tests, isLoading, error, startTest, submitTest } = useTests();

  if (isLoading) {
    return (
      <DesktopLayout>
        <Skeleton className="h-16 w-[600px] mb-8" />
        <div className="space-y-4">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      </DesktopLayout>
    );
  }

  if (error) {
    return (
      <DesktopLayout>
        <div className="text-red-600">Failed to load tests</div>
      </DesktopLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Mock Tests | PrepIQ</title>
        <meta name="description" content="Customized rigorous simulations for intellectual discipline" />
      </Head>
      <DesktopLayout>
        {/* Heading & Introduction */}
        <section className="space-y-4 mb-16">
          <h1 className="text-7xl font-serif italic leading-none">Mock Tests</h1>
          <p className="text-lg max-w-2xl text-on-surface/70 font-light">
            Customized rigorous simulations designed for modern intellectual discipline. Select a
            domain to generate a precision-focused examination.
          </p>
        </section>

        {/* Generate New Test Row */}
        <section className="space-y-8 mb-24">
          <div className="flex items-end justify-between border-b border-[#4A4A4A]/10 pb-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-primary">
              Generate Adaptive Session
            </h2>
            <span className="text-xs text-tertiary">SELECT DOMAIN TO INITIATE</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-0 border border-primary/20">
            {testDomains.map((domain) => (
              <button
                key={domain.name}
                className="group flex flex-col items-start p-8 bg-primary text-white border-r border-white/10 last:border-r-0 hover:bg-primary/90 transition-colors duration-200"
              >
                <span className="mb-6 text-4xl">
                  <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                  </svg>
                </span>
                <span className="text-2xl font-serif italic mb-2">{domain.name}</span>
                <span className="text-[0.65rem] uppercase tracking-tighter opacity-70">
                  {domain.focus}
                </span>
              </button>
            ))}
          </div>
        </section>

        {/* Available Tests List */}
        <section className="space-y-12">
          <div className="flex items-end justify-between border-b border-[#4A4A4A]/10 pb-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-primary">
              Archived &amp; Available Modules
            </h2>
            <div className="flex space-x-4">
              <span className="text-xs font-bold border-b border-primary text-primary">
                ALL TESTS
              </span>
              <span className="text-xs text-tertiary">COMPLETED</span>
              <span className="text-xs text-tertiary">IN PROGRESS</span>
            </div>
          </div>
          <div className="space-y-0 divide-y divide-primary/10 border-y border-primary/10">
            {tests.length === 0 ? (
              <div className="py-16 text-center">
                <p className="text-on-surface/50 text-lg">No tests available yet.</p>
              </div>
            ) : (
              tests.map((test, index) => {
                const isCompleted = test.status === 'completed';
                return (
                  <div
                    key={test.id}
                    className="grid grid-cols-12 items-center py-10 px-4 hover:bg-surface-container-low transition-colors duration-100 group"
                  >
                    <div className="col-span-1 text-xs font-bold text-tertiary">
                      {String(index + 1).padStart(2, '0')}.
                    </div>
                    <div className="col-span-4">
                      <h3 className="text-2xl font-serif italic">{test.title}</h3>
                      <p className="text-[0.7rem] uppercase tracking-wider text-primary mt-1">
                        {test.subject} {isCompleted ? '\u2022 COMPLETED' : '\u2022 FULL MODULE'}
                      </p>
                    </div>
                    <div className="col-span-5 grid grid-cols-3 gap-4">
                      <div>
                        <span className="block text-[0.6rem] uppercase font-bold text-tertiary mb-1">
                          Duration
                        </span>
                        <span className="text-sm font-medium">{test.duration} Minutes</span>
                      </div>
                      <div>
                        <span className="block text-[0.6rem] uppercase font-bold text-tertiary mb-1">
                          Complexity
                        </span>
                        <span className="text-sm font-medium capitalize">{test.difficulty}</span>
                      </div>
                      <div>
                        <span className="block text-[0.6rem] uppercase font-bold text-tertiary mb-1">
                          Inventory
                        </span>
                        <span className="text-sm font-medium">{test.questionCount} Questions</span>
                      </div>
                    </div>
                    <div className="col-span-2 flex justify-end">
                      <button
                        className={
                          isCompleted
                            ? 'border border-primary text-primary px-8 py-3 text-xs font-bold tracking-widest uppercase hover:bg-primary hover:text-white transition-all duration-150'
                            : 'bg-primary text-white px-8 py-3 text-xs font-bold tracking-widest uppercase hover:bg-primary/90 transition-colors duration-150'
                        }
                        onClick={() => router.push('/desktop/start-test')}
                      >
                        {isCompleted ? 'Review' : 'Start Test'}
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </section>

        {/* Academic Quote / Aesthetic Divider */}
        <section className="py-24 border-t border-primary/10 mt-24">
          <div className="flex flex-col md:flex-row justify-between items-start gap-12">
            <div className="md:w-1/2">
              <p className="text-4xl font-serif italic text-primary leading-tight">
                &quot;Efficiency is the result of disciplined repetition within a structured
                environment.&quot;
              </p>
            </div>
            <div className="md:w-1/3 space-y-6">
              <div className="h-[200px] bg-surface-container">
                <div className="w-full h-full bg-surface-container-high flex items-center justify-center">
                  <span className="text-on-surface/20 text-sm uppercase tracking-widest">
                    THE FOLIO ARCHIVE SERIES \u2022 VOL 04
                  </span>
                </div>
              </div>
              <p className="text-[0.65rem] uppercase tracking-widest leading-loose font-medium opacity-60">
                THE FOLIO ARCHIVE SERIES \u2022 VOL 04 \u2022 PREPIQ RESEARCH LABS
              </p>
            </div>
          </div>
        </section>
      </DesktopLayout>
    </>
  );
}
