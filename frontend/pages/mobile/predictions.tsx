import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { usePredictions } from '@/lib/hooks/usePredictions';
import type { Prediction } from '@/lib/services/predictions.service';
import { cn } from '@/lib/utils/cn';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct <= 40 ? 'bg-red-500' : pct <= 70 ? 'bg-amber-500' : 'bg-green-600';
  return (
    <div className="flex items-center gap-2">
      <div
        className="flex-1 h-1.5 bg-surface-container-high rounded-full overflow-hidden"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className={cn('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span
        className={cn(
          'text-xs font-bold tabular-nums w-8 text-right',
          pct <= 40 ? 'text-red-600' : pct <= 70 ? 'text-amber-600' : 'text-green-700'
        )}
      >
        {pct}%
      </span>
    </div>
  );
}

function PredictionCard({ prediction }: { prediction: Prediction }) {
  const [expanded, setExpanded] = useState(false);
  const sourceLabel =
    prediction.source === 'ml'
      ? 'AI Predicted'
      : prediction.source === 'ml_fallback'
      ? 'Pattern Based'
      : 'Syllabus Based';

  return (
    <article className="bg-surface-container p-5 border border-outline-variant/20 space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider px-2 py-0.5">
          {prediction.topic}
        </span>
        <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/40 border border-outline-variant/30 px-2 py-0.5">
          {sourceLabel}
        </span>
      </div>
      <p className="text-sm text-on-surface font-medium leading-relaxed">
        {prediction.question_text}
      </p>
      <ConfidenceBar score={prediction.confidence_score} />
      <div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-xs font-bold uppercase tracking-widest text-primary flex items-center gap-1"
          aria-expanded={expanded}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn('transition-transform duration-200', expanded && 'rotate-180')}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
          {expanded ? 'Hide' : 'Show'} Reasoning
        </button>
        {expanded && (
          <p className="mt-2 text-xs text-on-surface/70 leading-relaxed border-l-2 border-primary/30 pl-3">
            {prediction.reasoning}
          </p>
        )}
      </div>
    </article>
  );
}

export default function MobilePredictions() {
  const { subjects, isLoading: subjectsLoading } = useSubjects();
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const { data, isLoading: predictionsLoading, refresh } = usePredictions(selectedSubjectId);

  if (!API_URL) {
    return (
      <MobileLayout title="Predictions">
        <div className="text-center py-16 px-4">
          <p className="text-sm text-on-surface/60">
            <code>NEXT_PUBLIC_API_URL</code> is not configured.
          </p>
        </div>
      </MobileLayout>
    );
  }

  const predictions = data?.predictions ?? [];
  const fallbackUsed = data?.fallback_used ?? false;
  const fallbackReason = data?.fallback_reason ?? null;
  const isLoading = subjectsLoading || (selectedSubjectId != null && predictionsLoading);

  const handleRefresh = async () => {
    if (!selectedSubjectId) return;
    setRefreshing(true);
    try { await refresh(); } finally { setRefreshing(false); }
  };

  return (
    <>
      <Head>
        <title>PrepIQ – Predictions</title>
      </Head>
      <MobileLayout title="Predictions">
        <div className="space-y-6">
          <div>
            <h1 className="font-serif italic text-3xl leading-tight mb-1">Exam Predictions</h1>
            <p className="text-on-surface-variant text-xs uppercase tracking-widest font-medium">
              AI-powered based on your past papers
            </p>
          </div>

          {/* Subject selector */}
          {subjectsLoading ? (
            <Skeleton className="h-12 w-full" />
          ) : (
            <div className="relative">
              <select
                className="w-full bg-surface-container-low border-b-2 border-primary/20 focus:border-primary appearance-none py-3 px-4 text-on-surface text-sm font-medium cursor-pointer"
                value={selectedSubjectId ?? ''}
                onChange={(e) =>
                  setSelectedSubjectId(e.target.value ? Number(e.target.value) : null)
                }
              >
                <option value="">Select a subject…</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              <span className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-primary">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </span>
            </div>
          )}

          {/* Refresh */}
          {selectedSubjectId != null && (
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="w-full bg-primary text-on-primary py-3 text-xs font-bold uppercase tracking-widest disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {refreshing ? (
                <>
                  <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                  </svg>
                  Refreshing…
                </>
              ) : (
                'Refresh Predictions'
              )}
            </button>
          )}

          {/* Fallback banners */}
          {fallbackUsed && fallbackReason === 'no_papers' && (
            <div className="flex items-start gap-2 px-4 py-3 bg-amber-50 border border-amber-300 text-amber-800 text-xs">
              <span>⚠️</span>
              <p>No papers uploaded yet. Showing general exam predictions. Upload past papers for personalised results.</p>
            </div>
          )}
          {fallbackUsed && fallbackReason === 'syllabus_fallback' && (
            <div className="flex items-start gap-2 px-4 py-3 bg-blue-50 border border-blue-300 text-blue-800 text-xs">
              <span>ℹ️</span>
              <p>Fewer than 3 papers uploaded. Predictions based on standard exam patterns. Upload more papers for personalised results.</p>
            </div>
          )}

          {/* Loading */}
          {isLoading && selectedSubjectId != null && (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-36" />
              ))}
            </div>
          )}

          {/* Empty: no subject selected */}
          {!selectedSubjectId && !subjectsLoading && (
            <div className="text-center py-16 text-on-surface/40">
              <p className="text-sm">Select a subject to view predictions.</p>
            </div>
          )}

          {/* Empty: no papers */}
          {!isLoading && selectedSubjectId != null && predictions.length === 0 && fallbackReason === 'no_papers' && (
            <div className="flex flex-col items-center text-center py-12">
              <h3 className="font-serif italic text-xl mb-3">Upload your first past paper to unlock predictions</h3>
              <Link href="/mobile/upload" className="bg-primary text-on-primary px-6 py-3 text-xs font-bold uppercase tracking-widest">
                Upload Past Papers
              </Link>
            </div>
          )}

          {/* Predictions list */}
          {!isLoading && predictions.length > 0 && (
            <div className="space-y-4">
              {predictions.map((p) => (
                <PredictionCard key={p.id} prediction={p} />
              ))}
            </div>
          )}
        </div>
      </MobileLayout>
    </>
  );
}
