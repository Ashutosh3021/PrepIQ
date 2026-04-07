import React from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useAnalysis } from '@/lib/hooks/useAnalysis';

export default function DesktopAnalysis() {
  const { analysis, isLoading, error } = useAnalysis('default-user');

  if (isLoading) {
    return (
      <DesktopLayout>
        <Skeleton className="h-12 w-80 mb-8" />
        <div className="grid grid-cols-12 gap-8">
          <Skeleton className="col-span-4 h-80" />
          <Skeleton className="col-span-8 h-80" />
        </div>
      </DesktopLayout>
    );
  }

  if (error) {
    return (
      <DesktopLayout>
        <div className="text-red-600">Failed to load analysis</div>
      </DesktopLayout>
    );
  }

  const overallScore = analysis?.overallProgress ?? 0;
  const gaugeOffset = 691 - (691 * overallScore) / 100;

  return (
    <>
      <Head>
        <title>AI Analysis Results | PrepIQ</title>
        <meta name="description" content="AI-powered analysis of your study performance" />
      </Head>
      <DesktopLayout>
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-baseline mb-16 gap-8">
          <div className="max-w-2xl">
            <h1 className="text-6xl font-serif italic mb-4 leading-tight">
              AI Analysis Results
            </h1>
            <p className="text-on-surface/70 text-lg font-light tracking-wide uppercase text-sm">
              Session ID: FA-9982-X | Generated October 24, 2023
            </p>
          </div>
          <div className="flex gap-4">
            <button className="bg-primary text-on-primary px-8 py-3 font-bold flex items-center gap-2 hover:bg-primary/90 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              EXPORT PDF
            </button>
          </div>
        </div>

        {/* Dashboard Bento Grid */}
        <div className="grid grid-cols-12 gap-8">
          {/* Overall Score Gauge (Large) */}
          <div className="col-span-12 lg:col-span-4 bg-surface-container-high p-10 flex flex-col items-center justify-center relative">
            <div className="absolute top-6 left-6">
              <span className="text-xs font-extrabold uppercase tracking-widest text-on-surface/70">
                Overall Proficiency
              </span>
            </div>
            <div className="relative w-64 h-64 flex items-center justify-center mt-8">
              {/* SVG Gauge */}
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  className="text-secondary-container"
                  cx="128"
                  cy="128"
                  fill="transparent"
                  r="110"
                  stroke="currentColor"
                  strokeWidth="12"
                />
                <circle
                  className="text-primary"
                  cx="128"
                  cy="128"
                  fill="transparent"
                  r="110"
                  stroke="currentColor"
                  strokeDasharray="691"
                  strokeDashoffset={gaugeOffset}
                  strokeWidth="20"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-7xl font-bold tracking-tighter">{overallScore}</span>
                <span className="text-xs font-bold uppercase text-on-surface/70 tracking-widest">
                  Percentile
                </span>
              </div>
            </div>
            <div className="mt-8 text-center">
              <p className="font-serif italic text-2xl">
                &quot;Exceptional mastery in theoretical logic with minor gaps in applied
                calculus.&quot;
              </p>
            </div>
          </div>

          {/* Topic Weightage Bar Chart (Medium) */}
          <div className="col-span-12 lg:col-span-8 bg-surface-container p-10">
            <div className="flex justify-between items-center mb-10">
              <h3 className="text-xl font-bold uppercase tracking-widest">
                Topic Weightage &amp; Performance
              </h3>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-primary" />
                  <span className="text-[10px] font-bold uppercase tracking-tighter">
                    Current Score
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-secondary-container" />
                  <span className="text-[10px] font-bold uppercase tracking-tighter">
                    Global Avg
                  </span>
                </div>
              </div>
            </div>
            <div className="space-y-8">
              {analysis?.subjectProgress && analysis.subjectProgress.length > 0 ? (
                analysis.subjectProgress.map((topic) => (
                  <div key={topic.subjectId}>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="font-bold uppercase tracking-wider">{topic.name}</span>
                      <span className="font-bold">{topic.progress}%</span>
                    </div>
                    <div className="h-10 bg-surface-container-low relative">
                      <div
                        className="absolute inset-0 bg-secondary-container"
                        style={{ width: `${Math.round(topic.progress * 0.85)}%` }}
                      />
                      <div
                        className="absolute inset-0 bg-primary"
                        style={{ width: `${topic.progress}%` }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-on-surface/50 text-center py-8">No subject data available yet.</p>
              )}
            </div>
          </div>

          {/* Chronological Roadmap List */}
          <div className="col-span-12 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="md:col-span-3">
              <h2 className="text-4xl font-serif italic mt-8">Recommended Study Roadmap</h2>
              <div className="h-px bg-outline-variant w-full mt-4 opacity-20" />
            </div>
            {analysis?.weaknesses && analysis.weaknesses.length > 0 ? (
              analysis.weaknesses.map((weakness, index) => {
                const variant = index === 0 ? 'primary' : index === 1 ? 'secondary' : 'outline';
                const priority = index === 0 ? 'HIGH' : index === 1 ? 'MED' : 'LOW';
                return (
                  <div
                    key={index}
                    className={`p-8 flex flex-col border-l-4 ${
                      variant === 'primary'
                        ? 'bg-surface-container-highest border-primary'
                        : variant === 'secondary'
                          ? 'bg-surface-container-high border-secondary'
                          : 'bg-surface-container-low border-outline-variant'
                    }`}
                  >
                    <span className="text-6xl font-bold text-outline-variant opacity-30 mb-4 italic leading-none">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                    <h4 className="text-lg font-bold uppercase tracking-tight mb-2">{weakness}</h4>
                    <p className="text-sm text-on-surface/70 leading-relaxed flex-grow">
                      Focus on strengthening this area to improve overall performance.
                    </p>
                    <div className="mt-6 flex items-center justify-between">
                      <span
                        className={`text-[10px] font-bold px-2 py-1 ${
                          variant === 'primary'
                            ? 'bg-primary text-on-primary'
                            : variant === 'secondary'
                              ? 'bg-secondary text-on-primary'
                              : 'border border-outline text-on-surface/70'
                        }`}
                      >
                        PRIORITY: {priority}
                      </span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="col-span-3 text-center py-8">
                <p className="text-on-surface/50">No roadmap items available yet.</p>
              </div>
            )}
          </div>

          {/* Insight Section */}
          <div className="col-span-12 lg:col-span-7 bg-surface-container p-10">
            <h3 className="text-xl font-bold uppercase tracking-widest mb-6">
              Cognitive Behavioral Insights
            </h3>
            <div className="space-y-6">
              {analysis?.strengths && analysis.strengths.length > 0 ? (
                analysis.strengths.map((strength, index) => (
                  <div key={index} className="flex gap-4">
                    <span className="text-primary shrink-0">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                      </svg>
                    </span>
                    <div>
                      <h5 className="font-bold">{strength}</h5>
                      <p className="text-sm text-on-surface/70 leading-relaxed">
                        Strong performance in this area. Continue building on this foundation.
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-on-surface/50">No insights available yet.</p>
              )}
            </div>
          </div>

          {/* Visual Content / Data Decoration */}
          <div className="col-span-12 lg:col-span-5 relative h-[350px]">
            <div className="w-full h-full bg-surface-container-high flex items-center justify-center grayscale brightness-110">
              <span className="text-on-surface/20 text-sm uppercase tracking-widest">
                Minimalist Library
              </span>
            </div>
            <div className="absolute inset-0 bg-primary/20 mix-blend-multiply" />
            <div className="absolute bottom-6 left-6 right-6 p-6 bg-surface/90 backdrop-blur-sm">
              <span className="text-[10px] font-extrabold uppercase tracking-[0.2em] block mb-2">
                ARCHIVE NOTE
              </span>
              <p className="font-serif italic text-lg">
                &quot;The capacity to learn is a gift; the ability to learn is a skill; the
                willingness to learn is a choice.&quot;
              </p>
            </div>
          </div>
        </div>
      </DesktopLayout>
    </>
  );
}
