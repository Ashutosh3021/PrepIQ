import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { useMockTests } from '@/lib/hooks/useMockTests';
import type { Difficulty, TestSource, MockTestCreate } from '@/lib/services/mock-tests.service';
import { cn } from '@/lib/utils/cn';

// ── Config check ──────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}

function StatusBadge({ status }: { status: 'pending' | 'completed' }) {
  return (
    <span
      className={cn(
        'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5',
        status === 'completed'
          ? 'bg-green-100 text-green-700'
          : 'bg-surface-container-high text-on-surface/50'
      )}
    >
      {status === 'completed' ? 'Completed' : 'Pending'}
    </span>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function DesktopMockTests() {
  const router = useRouter();
  const { subjects, isLoading: subjectsLoading } = useSubjects();
  const { tests, isLoading: testsLoading, generate } = useMockTests();

  // Form state
  const [subjectId, setSubjectId] = useState<number | ''>('');
  const [numQuestions, setNumQuestions] = useState(10);
  const [difficulty, setDifficulty] = useState<Difficulty>('mixed');
  const [source, setSource] = useState<TestSource>('predictions');
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState('');

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

  const handleGenerate = async () => {
    if (!subjectId) return;
    setGenerating(true);
    setGenerateError('');
    try {
      const payload: MockTestCreate = {
        subject_id: Number(subjectId),
        num_questions: numQuestions,
        difficulty,
        source,
      };
      const test = await generate(payload);
      if (test.test_id) {
        router.push(`/desktop/mock-tests/${test.test_id}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setGenerateError(msg);
    } finally {
      setGenerating(false);
    }
  };

  const isInsufficientData =
    generateError.toLowerCase().includes('insufficient_data') ||
    generateError.toLowerCase().includes('no questions') ||
    generateError.toLowerCase().includes('not enough');

  return (
    <>
      <Head>
        <title>Mock Tests | PrepIQ</title>
        <meta name="description" content="Generate and take AI-powered mock tests" />
      </Head>
      <DesktopLayout>
        {/* Header */}
        <div className="mb-8 md:mb-12">
          <span className="text-xs font-bold tracking-[0.2em] uppercase text-primary mb-3 block">
            Assessment Engine
          </span>
          <h1 className="text-4xl md:text-6xl font-serif italic leading-none mb-4">Mock Tests</h1>
          <p className="text-on-surface/60 font-light max-w-xl">
            Generate personalised mock tests from your predictions or full question pool, then
            review your results inline.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* ── LEFT: Generate panel ── */}
          <section>
            <h2 className="text-xs font-bold uppercase tracking-widest text-primary mb-6 pb-3 border-b border-outline-variant/20">
              Generate New Test
            </h2>

            <div className="space-y-6">
              {/* Subject */}
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="mt-subject"
                  className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60"
                >
                  Subject
                </label>
                {subjectsLoading ? (
                  <Skeleton className="h-12" />
                ) : (
                  <div className="relative">
                    <select
                      id="mt-subject"
                      className="w-full bg-surface-container-low border-b-2 border-primary/20 focus:border-primary appearance-none py-3 px-4 text-on-surface text-sm font-medium focus:ring-0 cursor-pointer"
                      value={subjectId}
                      onChange={(e) =>
                        setSubjectId(e.target.value ? Number(e.target.value) : '')
                      }
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

              {/* Number of questions */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="mt-questions"
                    className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60"
                  >
                    Number of Questions
                  </label>
                  <span className="text-sm font-bold text-primary">{numQuestions}</span>
                </div>
                <input
                  id="mt-questions"
                  type="range"
                  min={5}
                  max={30}
                  step={5}
                  value={numQuestions}
                  onChange={(e) => setNumQuestions(Number(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-[10px] text-on-surface/40 font-bold">
                  <span>5</span>
                  <span>10</span>
                  <span>15</span>
                  <span>20</span>
                  <span>25</span>
                  <span>30</span>
                </div>
              </div>

              {/* Difficulty */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60">
                  Difficulty
                </span>
                <div className="grid grid-cols-4 gap-2">
                  {(['easy', 'medium', 'hard', 'mixed'] as Difficulty[]).map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setDifficulty(d)}
                      className={cn(
                        'py-2 text-xs font-bold uppercase tracking-wider border transition-colors',
                        difficulty === d
                          ? 'bg-primary text-on-primary border-primary'
                          : 'border-outline-variant/30 text-on-surface/60 hover:border-primary/40'
                      )}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              {/* Source toggle */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60">
                  Question Source
                </span>
                <div className="flex gap-2">
                  {(
                    [
                      { value: 'predictions' as TestSource, label: 'From Predictions' },
                      { value: 'all' as TestSource, label: 'All Questions' },
                    ] as const
                  ).map(({ value, label }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setSource(value)}
                      className={cn(
                        'flex-1 py-2 text-xs font-bold uppercase tracking-wider border transition-colors',
                        source === value
                          ? 'bg-primary text-on-primary border-primary'
                          : 'border-outline-variant/30 text-on-surface/60 hover:border-primary/40'
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Insufficient data notice */}
              {isInsufficientData && (
                <div className="flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-300 text-amber-800 text-sm">
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
                    className="shrink-0 mt-0.5"
                  >
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <p>
                    No questions available yet for this subject. Upload past papers first.
                  </p>
                </div>
              )}

              {/* Generic error */}
              {generateError && !isInsufficientData && (
                <div className="px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
                  {generateError}
                </div>
              )}

              {/* Generate button */}
              <button
                onClick={handleGenerate}
                disabled={!subjectId || generating}
                className="w-full bg-primary text-on-primary py-4 text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {generating ? (
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
                    Generating…
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
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                    </svg>
                    Generate Test
                  </>
                )}
              </button>
            </div>
          </section>

          {/* ── RIGHT: Test History ── */}
          <section>
            <h2 className="text-xs font-bold uppercase tracking-widest text-primary mb-6 pb-3 border-b border-outline-variant/20">
              Test History
            </h2>

            {testsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : tests.length === 0 ? (
              <div className="text-center py-16 text-on-surface/40">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="40"
                  height="40"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="mx-auto mb-3 text-on-surface/20"
                >
                  <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
                  <rect x="9" y="3" width="6" height="4" rx="1" />
                  <line x1="9" y1="12" x2="15" y2="12" />
                  <line x1="9" y1="16" x2="13" y2="16" />
                </svg>
                <p className="text-sm">No tests yet. Generate one to get started.</p>
              </div>
            ) : (
              <div className="divide-y divide-outline-variant/20 border-y border-outline-variant/20">
                {[...tests]
                  .sort(
                    (a, b) =>
                      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                  )
                  .map((test) => (
                    <button
                      key={test.test_id}
                      onClick={() =>
                        router.push(`/desktop/mock-tests/${test.test_id}`)
                      }
                      className="w-full text-left px-4 py-4 hover:bg-surface-container-low transition-colors flex items-center gap-4"
                    >
                      {/* Date */}
                      <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/40 w-20 shrink-0">
                        {formatDate(test.created_at)}
                      </span>

                      {/* Subject + questions */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-on-surface truncate">
                          {test.subject_name || `Subject #${test.subject_id}`}
                        </p>
                        <p className="text-xs text-on-surface/50">
                          {test.total_questions} question
                          {test.total_questions !== 1 ? 's' : ''}
                        </p>
                      </div>

                      {/* Status + score */}
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        <StatusBadge status={test.status} />
                        {test.status === 'completed' && test.score_percentage != null && (
                          <span
                            className={cn(
                              'text-xs font-bold',
                              test.score_percentage >= 70
                                ? 'text-green-700'
                                : test.score_percentage >= 40
                                ? 'text-amber-600'
                                : 'text-red-600'
                            )}
                          >
                            {Math.round(test.score_percentage)}%
                          </span>
                        )}
                      </div>

                      {/* Chevron */}
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
                        className="text-on-surface/30 shrink-0"
                      >
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </button>
                  ))}
              </div>
            )}
          </section>
        </div>
      </DesktopLayout>
    </>
  );
}
