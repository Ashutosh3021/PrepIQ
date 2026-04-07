import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { useAnalysis } from '@/lib/hooks/useAnalysis';

export default function MobileProgress() {
  const { analysis, isLoading, error } = useAnalysis('default-user');

  if (isLoading) {
    return (
      <MobileLayout title="Progress">
        <Skeleton className="h-8 w-64 mb-6" />
        <Skeleton className="h-48 w-full mb-6" />
        <Skeleton className="h-32 w-full" />
      </MobileLayout>
    );
  }

  if (error) {
    return (
      <MobileLayout title="Progress">
        <div className="text-red-600 p-4">Failed to load progress</div>
      </MobileLayout>
    );
  }

  const completion = analysis?.overallProgress ?? 0;
  const predictions = analysis?.predictions ?? [];
  const testHistory = analysis?.testHistory ?? [];

  return (
    <>
      <Head>
        <title>PrepIQ - Progress</title>
        <meta name="description" content="Track your study progress and AI predictions" />
      </Head>
      <MobileLayout title="Progress">
        <div className="space-y-8">
          {/* Hero Section */}
          <div className="relative text-center border-b border-outline-variant/20 pb-10">
            <div className="space-y-4">
              <div className="flex flex-col items-center gap-2">
                <span className="text-on-surface-variant/60 font-medium tracking-widest text-[10px] uppercase mb-2 block">Current Mastery Journey</span>
                <h1 className="text-4xl font-serif italic leading-tight tracking-tight text-on-surface">
                  Advanced Quantum Physics
                </h1>
              </div>
              <button className="mt-6 bg-primary text-on-primary font-bold h-12 px-8 flex items-center gap-3 hover:bg-on-primary-fixed-variant mx-auto">
                <span className="text-sm uppercase tracking-widest">Resume Study</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>

          {/* High-Level Stats Grid */}
          <div className="border border-outline-variant/20">
            {/* Completion */}
            <div className="p-6 border-b border-outline-variant/20">
              <span className="text-on-surface-variant/60 text-xs font-bold uppercase tracking-widest block mb-4">Syllabus completion</span>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-light text-on-surface">{completion}</span>
                <span className="text-primary text-xl font-serif italic">%</span>
              </div>
              <div className="mt-6 h-px w-full bg-outline-variant/20 relative">
                <div className="absolute top-0 left-0 h-0.5 bg-primary" style={{ width: `${completion}%` }} />
              </div>
            </div>

            {/* Materials read */}
            <div className="p-6 border-b border-outline-variant/20">
              <span className="text-on-surface-variant/60 text-xs font-bold uppercase tracking-widest block mb-4">Materials read</span>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-light text-on-surface">{analysis?.subjectProgress?.length ?? 0}</span>
                <span className="text-on-surface-variant/40 text-xl">/ {analysis?.subjectProgress?.length ? analysis.subjectProgress.length + 8 : 20}</span>
              </div>
              <p className="text-[10px] uppercase tracking-widest text-on-surface-variant/60 mt-6">Next: Wave-Particle Duality II</p>
            </div>

            {/* AI Prediction */}
            <div className="p-6 bg-surface-container">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-primary text-xs font-bold uppercase tracking-widest">AI Prediction</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-light text-on-surface">
                  {predictions.length > 0 ? predictions[0].predictedScore : 85}
                </span>
                <span className="text-primary text-xl font-serif italic">%</span>
              </div>
              <p className="text-xs text-on-surface-variant/80 mt-6 leading-relaxed italic">
                Predicted final score: <span className="text-primary font-bold not-italic">A-</span>
              </p>
            </div>
          </div>

          {/* Activity Timeline */}
          <div className="space-y-6">
            <h2 className="text-sm font-bold uppercase tracking-[0.2em] flex items-center gap-3 border-b border-outline-variant pb-2">
              Activity timeline
            </h2>
            <div className="space-y-8">
              {testHistory.length > 0 ? (
                testHistory.slice(0, 3).map((item, index) => (
                  <div key={item.testId} className="relative pl-5 border-l border-outline-variant/30">
                    <div className={`absolute left-[-3px] top-1 w-1.5 h-1.5 ${index === 0 ? 'bg-primary' : 'bg-outline-variant/30'}`} />
                    <span className="text-[10px] text-on-surface-variant/60 block mb-1 uppercase tracking-wider">{item.date}</span>
                    <h4 className="text-sm font-bold text-on-surface mb-1">{item.title}</h4>
                    <p className="text-xs text-on-surface-variant/70">Scored {item.score}%</p>
                  </div>
                ))
              ) : (
                <>
                  <div className="relative pl-5 border-l border-outline-variant/30">
                    <div className="absolute left-[-3px] top-1 w-1.5 h-1.5 bg-primary" />
                    <span className="text-[10px] text-on-surface-variant/60 block mb-1 uppercase tracking-wider">Today, 2:30 PM</span>
                    <h4 className="text-sm font-bold text-on-surface mb-1">Practice Quiz: Uncertainty Principle</h4>
                    <p className="text-xs text-on-surface-variant/70">Scored 18/20 &bull; 45 mins session</p>
                  </div>
                  <div className="relative pl-5 border-l border-outline-variant/30">
                    <div className="absolute left-[-3px] top-1 w-1.5 h-1.5 bg-outline-variant/30" />
                    <span className="text-[10px] text-on-surface-variant/60 block mb-1 uppercase tracking-wider">Yesterday</span>
                    <h4 className="text-sm font-bold text-on-surface mb-1">Reading: Quantum Entanglement</h4>
                    <p className="text-xs text-on-surface-variant/70">Completed 12 pages &bull; Deep focus</p>
                  </div>
                  <div className="relative pl-5 border-l border-outline-variant/30">
                    <div className="absolute left-[-3px] top-1 w-1.5 h-1.5 bg-outline-variant/30" />
                    <span className="text-[10px] text-on-surface-variant/60 block mb-1 uppercase tracking-wider">Oct 12, 2023</span>
                    <h4 className="text-sm font-bold text-on-surface mb-1">Subject Initialized</h4>
                    <p className="text-xs text-on-surface-variant/70">Diagnostic exam completed</p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Topic Breakdown */}
          <div className="border border-outline-variant/20 p-5">
            <div className="flex justify-between items-center mb-6 border-b border-outline-variant/20 pb-3">
              <h2 className="text-xl font-serif italic">Topic Breakdown</h2>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-on-surface-variant/60 cursor-pointer">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
              </svg>
            </div>
            <div className="space-y-6">
              {analysis?.subjectProgress && analysis.subjectProgress.length > 0 ? (
                analysis.subjectProgress.map((topic) => (
                  <div key={topic.subjectId}>
                    <div className="flex justify-between items-end mb-2">
                      <div>
                        <h3 className="font-bold text-xs uppercase tracking-wider text-on-surface">{topic.name}</h3>
                        <p className="text-[10px] uppercase text-on-surface-variant/60">
                          {topic.progress >= 80 ? 'Mastered' : topic.progress >= 50 ? 'In progress' : 'Not yet started'}
                        </p>
                      </div>
                      <span className={`text-sm font-bold ${topic.progress >= 50 ? 'text-primary' : 'text-on-surface-variant/40'}`}>{topic.progress}%</span>
                    </div>
                    <div className="h-px w-full bg-outline-variant/20 relative">
                      <div
                        className={`absolute top-0 left-0 h-0.5 ${topic.progress >= 50 ? 'bg-primary' : 'bg-on-surface-variant/20'}`}
                        style={{ width: `${topic.progress}%` }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <>
                  <div>
                    <div className="flex justify-between items-end mb-2">
                      <div>
                        <h3 className="font-bold text-xs uppercase tracking-wider text-on-surface">Foundations of Wave Mechanics</h3>
                        <p className="text-[10px] uppercase text-on-surface-variant/60">4 core concepts mastered</p>
                      </div>
                      <span className="text-primary text-sm font-bold">92%</span>
                    </div>
                    <div className="h-px w-full bg-outline-variant/20 relative">
                      <div className="absolute top-0 left-0 h-0.5 bg-primary w-[92%]" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-end mb-2">
                      <div>
                        <h3 className="font-bold text-xs uppercase tracking-wider text-on-surface">The Schr&ouml;dinger Equation</h3>
                        <p className="text-[10px] uppercase text-on-surface-variant/60">2 core concepts remaining</p>
                      </div>
                      <span className="text-primary text-sm font-bold">55%</span>
                    </div>
                    <div className="h-px w-full bg-outline-variant/20 relative">
                      <div className="absolute top-0 left-0 h-0.5 bg-primary w-[55%]" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-end mb-2">
                      <div>
                        <h3 className="font-bold text-xs uppercase tracking-wider text-on-surface">Quantum Field Theory Basics</h3>
                        <p className="text-[10px] uppercase text-on-surface-variant/60">Not yet started</p>
                      </div>
                      <span className="text-on-surface-variant/40 text-sm font-bold">12%</span>
                    </div>
                    <div className="h-px w-full bg-outline-variant/20 relative">
                      <div className="absolute top-0 left-0 h-0.5 bg-on-surface-variant/20 w-[12%]" />
                    </div>
                  </div>
                </>
              )}
            </div>
            <div className="mt-8 flex justify-center border-t border-outline-variant/20 pt-6">
              <button className="text-primary text-xs font-bold uppercase tracking-[0.2em] flex items-center gap-2 hover:underline">
                View Detailed Analytics
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>

          {/* AI Predictions Section */}
          <div className="space-y-6">
            <p className="text-[10px] uppercase tracking-[0.2em] text-primary font-bold">Performance Intelligence</p>
            <h2 className="font-serif italic text-2xl leading-tight">AI Predictions</h2>
            <p className="text-on-surface-variant text-sm leading-relaxed">Based on your recent 12 study blocks and 3 mock examinations.</p>

            {/* Bento Grid: Main Metrics */}
            <div className="grid grid-cols-2 gap-3">
              {/* Predicted Score Card */}
              <div className="col-span-2 bg-surface-container-highest p-5 flex flex-col justify-between min-h-[140px] border border-outline-variant/20">
                <div className="flex justify-between items-start">
                  <span className="text-[10px] uppercase tracking-widest text-primary font-bold">Predicted Score</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" />
                    <path d="M3 5v14a2 2 0 0 0 2 2h16v-5" />
                    <path d="M18 12a2 2 0 0 0 0 4h4v-4Z" />
                  </svg>
                </div>
                <div className="mt-3">
                  <div className="flex items-baseline gap-2">
                    <span className="font-serif italic text-5xl">742</span>
                    <span className="text-on-surface-variant text-sm font-medium">/ 800</span>
                  </div>
                  <div className="flex items-center gap-1 mt-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-600">
                      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                      <polyline points="17 6 23 6 23 12" />
                    </svg>
                    <p className="text-[10px] text-green-700 font-bold tracking-tight uppercase">+14 pts from last week</p>
                  </div>
                </div>
              </div>

              {/* Probability Card */}
              <div className="bg-surface-container p-4 border border-outline-variant/20">
                <span className="text-[10px] uppercase tracking-widest text-on-surface-variant font-bold mb-3 block">Pass Probability</span>
                <div className="font-serif italic text-2xl mb-1">94%</div>
                <div className="w-full h-1.5 bg-surface-container-high mt-3 relative">
                  <div className="absolute left-0 top-0 h-full bg-primary w-[94%]" />
                </div>
              </div>

              {/* Focus Level Card */}
              <div className="bg-surface-container p-4 border border-outline-variant/20">
                <span className="text-[10px] uppercase tracking-widest text-on-surface-variant font-bold mb-3 block">Study Intensity</span>
                <div className="font-serif italic text-2xl mb-1">High</div>
                <p className="text-[10px] text-on-surface-variant leading-tight">4.2h daily average</p>
              </div>
            </div>

            {/* Score Projection Chart */}
            <section>
              <h3 className="font-serif italic text-xl mb-4">Score Projection</h3>
              <div className="bg-surface-container-low p-5 aspect-[4/3] flex flex-col justify-end gap-3 relative border border-outline-variant/20">
                {/* Background grid lines */}
                <div className="absolute inset-0 p-6 flex items-end justify-between overflow-hidden opacity-20">
                  <div className="absolute w-full h-px bg-outline-variant bottom-1/4" />
                  <div className="absolute w-full h-px bg-outline-variant bottom-1/2" />
                  <div className="absolute w-full h-px bg-outline-variant bottom-3/4" />
                </div>
                <svg className="w-full h-full z-10 overflow-visible" viewBox="0 0 400 200">
                  <polyline fill="none" points="0,180 80,160 160,170 240,110 320,80 400,50" stroke="#4a5e72" strokeWidth="3" />
                  <rect fill="#4a5e72" height="10" width="10" x="315" y="75" />
                </svg>
                <div className="flex justify-between text-[10px] tracking-tighter text-on-surface-variant uppercase pt-3 border-t border-outline-variant/30">
                  <span>Oct 12</span>
                  <span>Oct 19</span>
                  <span>Oct 26</span>
                  <span>Current</span>
                  <span className="text-primary font-bold">Target</span>
                </div>
              </div>
            </section>

            {/* Topic Weightage Table */}
            <section>
              <div className="flex justify-between items-baseline mb-4">
                <h3 className="font-serif italic text-xl">Topic Weightage</h3>
                <span className="text-[10px] text-primary uppercase tracking-widest font-bold">Critical Path</span>
              </div>
              <div className="space-y-px">
                <div className="bg-surface-container-low p-4 flex items-center justify-between border border-outline-variant/20">
                  <div className="flex flex-col">
                    <span className="font-bold text-sm">Advanced Calculus</span>
                    <span className="text-[10px] uppercase tracking-widest text-on-surface-variant">Predicted Weight: 22%</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-error">NEEDS WORK</span>
                  </div>
                </div>
                <div className="bg-surface-container-low p-4 flex items-center justify-between border border-outline-variant/20">
                  <div className="flex flex-col">
                    <span className="font-bold text-sm">Thermodynamics</span>
                    <span className="text-[10px] uppercase tracking-widest text-on-surface-variant">Predicted Weight: 18%</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-primary">STABLE</span>
                  </div>
                </div>
                <div className="bg-surface-container-low p-4 flex items-center justify-between border border-outline-variant/20">
                  <div className="flex flex-col">
                    <span className="font-bold text-sm">Material Science</span>
                    <span className="text-[10px] uppercase tracking-widest text-on-surface-variant">Predicted Weight: 15%</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-green-700">MASTERY</span>
                  </div>
                </div>
                <div className="bg-surface-container-low p-4 flex items-center justify-between border border-outline-variant/20">
                  <div className="flex flex-col">
                    <span className="font-bold text-sm">Fluid Mechanics</span>
                    <span className="text-[10px] uppercase tracking-widest text-on-surface-variant">Predicted Weight: 12%</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-primary">STABLE</span>
                  </div>
                </div>
              </div>
            </section>

            {/* AI Insight Card */}
            <div className="bg-primary p-5 mb-8">
              <div className="flex items-center gap-3 mb-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-surface">
                  <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z" />
                  <path d="M9 21h6" />
                  <path d="M10 24h4" />
                </svg>
                <span className="text-[10px] uppercase tracking-[0.2em] text-surface font-bold">Strategic Insight</span>
              </div>
              <p className="font-serif italic text-lg text-surface leading-tight">
                &quot;Prioritize &apos;Integration by Parts&apos; over the next 48 hours. The algorithm predicts a high probability of this appearing in your next 3 mocks.&quot;
              </p>
              <button className="mt-4 w-full bg-surface text-primary font-bold py-2 uppercase text-[10px] tracking-widest active:scale-[0.98] transition-transform">
                Generate Study Plan
              </button>
            </div>
          </div>
        </div>
      </MobileLayout>
    </>
  );
}
