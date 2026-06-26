import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { usePredictions } from '@/lib/hooks/usePredictions';
import type { Prediction } from '@/lib/services/predictions.service';
import { cn } from '@/lib/utils/cn';

// ── Config check ──────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// ── Sub-components ────────────────────────────────────────────────────────────

/** Horizontal confidence bar colored by threshold. */
function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct <= 40
      ? 'bg-red-500'
      : pct <= 70
      ? 'bg-amber-500'
      : 'bg-green-600';

  return (
    <div className="flex items-center gap-3">
      <div
        className="flex-1 h-2 bg-surface-container-high rounded-full overflow-hidden"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Confidence: ${pct}%`}
      >
        <div
          className={cn('h-full rounded-full transition-all duration-300', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span
        className={cn(
          'text-xs font-bold tabular-nums w-10 text-right',
          pct <= 40
            ? 'text-red-600'
            : pct <= 70
            ? 'text-amber-600'
            : 'text-green-700'
        )}
      >
        {pct}%
      </span>
    </div>
  );
}

/** Source label badge. */
function SourceBadge({ source }: { source: Prediction['source'] }) {
  const label =
    source === 'ml'
      ? 'AI Predicted'
      : source === 'ml_fallback'
      ? 'Pattern Based'
      : 'Syllabus Based';

  return (
    <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/40 border border-outline-variant/30 px-2 py-0.5">
      {label}
    </span>
  );
}

/** Single prediction card with collapsible reasoning. */
function PredictionCard({ prediction }: { prediction: Prediction }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="bg-surface-container p-6 border border-outline-variant/20 flex flex-col gap-4">
      {/* Topic + Source */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-sm">
          {prediction.topic}
        </span>
        <SourceBadge source={prediction.source} />
      </div>

      {/* Question text */}
      <p className="text-on-surface font-medium leading-relaxed text-sm">
        {prediction.question_text}
      </p>

      {/* Confidence bar */}
      <div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/50 mb-1 block">
          Confidence
        </span>
        <ConfidenceBar score={prediction.confidence_score} />
      </div>

      {/* Reasoning accordion */}
      <div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary hover:text-primary/80 transition-colors"
          aria-expanded={expanded}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
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
          <p className="mt-3 text-sm text-on-surface/70 leading-relaxed border-l-2 border-primary/30 pl-4">
            {prediction.reasoning}
          </p>
        )}
      </div>
    </article>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function DesktopPredictions() {
  const { subjects, isLoading: subjectsLoading } = useSubjects();
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState('');

  const { data, isLoading: predictionsLoading, refresh } = usePredictions(selectedSubjectId);

  // Configuration guard
  if (!API_URL) {
    return (
      <DesktopLayout>
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
          <h2 className="text-2xl font-bold text-on-surface mb-2">Configuration Error</h2>
          <p className="text-on-surface/60">
            <code className="bg-surface-container px-1 rounded">NEXT_PUBLIC_API_URL</code> is not
            set. Add it to your <code>.env.local</code> file and restart the dev server.
          </p>
        </div>
      </DesktopLayout>
    );
  }

  const handleRefresh = async () => {
    if (!selectedSubjectId) return;
    setRefreshing(true);
    setRefreshError('');
    try {
      await refresh();
    } catch (err) {
      setRefreshError(err instanceof Error ? err.message : 'Failed to refresh predictions.');
    } finally {
      setRefreshing(false);
    }
  };

  const predictions = data?.predictions ?? [];
  const fallbackUsed = data?.fallback_used ?? false;
  const fallbackReason = data?.fallback_reason ?? null;

  const isLoading = subjectsLoading || (selectedSubjectId != null && predictionsLoading);

  return (
    <>
      <Head>
        <title>Predictions | PrepIQ</title>
        <meta name="description" content="AI-powered exam question predictions for your subjects" />
      </Head>
      <DesktopLayout>
        {/* Header */}
        <div className="mb-8 md:mb-12">
          <span className="text-xs font-bold tracking-[0.2em] uppercase text-primary mb-3 block">
            Intelligence Engine
          </span>
          <h1 className="text-4xl md:text-6xl font-serif italic leading-none mb-4">
            Exam Predictions
          </h1>
          <p className="text-on-surface/60 font-light max-w-xl">
            AI-generated predictions based on your uploaded past papers. Higher confidence scores
            indicate stronger historical patterns.
          </p>
        </div>

        {/* Controls row */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8 items-start sm:items-end">
          {/* Subject selector */}
          <div className="flex flex-col gap-2 flex-1 max-w-xs">
            <label
              htmlFor="subject-select"
              className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60"
            >
              Subject
            </label>
            {subjectsLoading ? (
              <Skeleton className="h-12 w-full" />
            ) : (
              <div className="relative">
                <select
                  id="subject-select"
                  className="w-full bg-surface-container-low border-b-2 border-primary/20 focus:border-primary appearance-none py-3 px-4 text-on-surface text-sm font-medium focus:ring-0 cursor-pointer"
                  value={selectedSubjectId ?? ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (!val || val === '') {
                      setSelectedSubjectId(null);
                      return;
                    }
                    const parsed = parseInt(val, 10);
                    if (!isNaN(parsed)) {
                      setSelectedSubjectId(parsed);
                    }
                  }}
                >
                  <option value="">Select a subject…</option>
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
                <span className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-primary">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </span>
              </div>
            )}
          </div>

          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            disabled={!selectedSubjectId || refreshing}
            className="bg-primary text-on-primary px-6 py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {refreshing ? (
              <>
                <svg
                  className="animate-spin"
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                Refreshing…
              </>
            ) : (
              <>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="1 4 1 10 7 10" />
                  <polyline points="23 20 23 14 17 14" />
                  <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                </svg>
                Refresh Predictions
              </>
            )}
          </button>
        </div>

        {/* Refresh error */}
        {refreshError && (
          <div className="mb-6 px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
            {refreshError}
          </div>
        )}

        {/* No subject selected */}
        {!selectedSubjectId && !subjectsLoading && (
          <div className="text-center py-24 text-on-surface/50">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="mx-auto mb-4 text-on-surface/20"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <p className="text-sm">Select a subject above to view predictions.</p>
          </div>
        )}

        {/* Loading state */}
        {isLoading && selectedSubjectId != null && (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-40 w-full" />
            ))}
          </div>
        )}

        {/* Content */}
        {!isLoading && selectedSubjectId != null && (
          <>
            {/* Fallback banner */}
            {fallbackUsed && fallbackReason === 'no_papers' && (
              <div className="mb-6 flex items-start gap-3 px-5 py-4 bg-amber-50 border border-amber-300 text-amber-800 text-sm">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="shrink-0 mt-0.5"
                >
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <p>
                  No papers uploaded yet. Upload past papers for personalised predictions. Showing
                  general exam predictions.
                </p>
              </div>
            )}

            {fallbackUsed && fallbackReason === 'syllabus_fallback' && (
              <div className="mb-6 flex items-start gap-3 px-5 py-4 bg-blue-50 border border-blue-300 text-blue-800 text-sm">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="shrink-0 mt-0.5"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <p>
                  Fewer than 3 papers uploaded. Predictions based on standard exam patterns. Upload
                  more papers for personalised results.
                </p>
              </div>
            )}

            {/* Empty state — no papers at all */}
            {predictions.length === 0 && fallbackReason === 'no_papers' && (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="w-16 h-16 bg-surface-container-highest flex items-center justify-center mb-6">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="text-primary"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                </div>
                <h3 className="text-xl font-serif italic mb-3 text-on-surface">
                  Upload your first past paper to unlock predictions
                </h3>
                <p className="text-on-surface/60 text-sm mb-6 max-w-sm">
                  PrepIQ analyses your past papers to generate personalised question predictions for
                  your upcoming exam.
                </p>
                <Link
                  href="/desktop/upload"
                  className="bg-primary text-on-primary px-8 py-3 text-sm font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  Upload Past Papers
                </Link>
              </div>
            )}

            {/* Empty state — other reasons */}
            {predictions.length === 0 && fallbackReason !== 'no_papers' && (
              <div className="text-center py-24 text-on-surface/50">
                <p className="text-sm">No predictions available yet for this subject.</p>
              </div>
            )}

            {/* Predictions list */}
            {predictions.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-widest text-primary">
                    {predictions.length} Prediction{predictions.length !== 1 ? 's' : ''}
                  </span>
                  {data?.message && (
                    <span className="text-xs text-on-surface/50 italic">{data.message}</span>
                  )}
                </div>
                {predictions.map((p) => (
                  <PredictionCard key={p.id} prediction={p} />
                ))}
              </div>
            )}
          </>
        )}
      </DesktopLayout>
    </>
  );
}
