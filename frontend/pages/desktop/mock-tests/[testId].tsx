import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useMockTest, useMockTests } from '@/lib/hooks/useMockTests';
import type { Answer, TestSubmitResponse } from '@/lib/services/mock-tests.service';
import { cn } from '@/lib/utils/cn';

// ── Config check ──────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// ── Score display ─────────────────────────────────────────────────────────────

function ScoreDisplay({ pct }: { pct: number | null }) {
  if (pct == null) {
    return (
      <div className="text-center py-4">
        <p className="text-on-surface/50 text-sm italic">Score unavailable</p>
      </div>
    );
  }

  const color =
    pct >= 70 ? 'text-green-700' : pct >= 40 ? 'text-amber-600' : 'text-red-600';
  const bg =
    pct >= 70 ? 'bg-green-50 border-green-300' : pct >= 40 ? 'bg-amber-50 border-amber-300' : 'bg-red-50 border-red-300';

  return (
    <div className={cn('flex flex-col items-center justify-center py-8 border-2', bg)}>
      <span className="text-xs font-bold uppercase tracking-widest text-on-surface/50 mb-2">
        Your Score
      </span>
      <span className={cn('text-7xl font-bold tabular-nums', color)}>{Math.round(pct)}%</span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function MockTestPage() {
  const router = useRouter();
  const testId = router.query.testId ? Number(router.query.testId) : null;

  const { test, isLoading } = useMockTest(testId);
  const { submit } = useMockTests();

  // Per-question answers: questionId → answer text
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [result, setResult] = useState<TestSubmitResponse | null>(null);

  if (!API_URL) {
    return (
      <DesktopLayout>
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
          <h2 className="text-2xl font-bold text-on-surface mb-2">Configuration Error</h2>
          <p className="text-on-surface/60">
            <code className="bg-surface-container px-1 rounded">NEXT_PUBLIC_API_URL</code> is not
            set.
          </p>
        </div>
      </DesktopLayout>
    );
  }

  if (isLoading || testId == null) {
    return (
      <DesktopLayout>
        <Skeleton className="h-8 w-64 mb-6" />
        <Skeleton className="h-48 w-full mb-4" />
        <Skeleton className="h-32 w-full" />
      </DesktopLayout>
    );
  }

  if (!test || !test.test_id) {
    return (
      <DesktopLayout>
        <div className="text-center py-24">
          <p className="text-on-surface/50">Test not found.</p>
          <button
            onClick={() => router.push('/desktop/mock-tests')}
            className="mt-4 text-primary text-sm font-bold underline"
          >
            Back to Mock Tests
          </button>
        </div>
      </DesktopLayout>
    );
  }

  const questions = test.questions ?? [];
  const total = questions.length;

  // ── Results screen ────────────────────────────────────────────────────────

  if (result) {
    return (
      <>
        <Head>
          <title>Test Results | PrepIQ</title>
        </Head>
        <DesktopLayout>
          <div className="max-w-2xl mx-auto">
            <button
              onClick={() => router.push('/desktop/mock-tests')}
              className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary mb-8 hover:text-primary/70 transition-colors"
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
              >
                <polyline points="15 18 9 12 15 6" />
              </svg>
              All Tests
            </button>

            <h1 className="text-3xl font-serif italic mb-8">Test Results</h1>

            <ScoreDisplay pct={result.score_percentage} />

            <div className="mt-10 space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-widest text-primary pb-3 border-b border-outline-variant/20">
                Your Answers
              </h2>
              {questions.map((q, idx) => (
                <div
                  key={q.id}
                  className="bg-surface-container p-5 border border-outline-variant/20"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-[10px] font-bold text-on-surface/40 uppercase tracking-wider">
                      Q{idx + 1}
                    </span>
                    <span className="text-xs bg-primary/10 text-primary font-bold uppercase tracking-wider px-2 py-0.5">
                      {q.topic}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-on-surface mb-3">{q.question_text}</p>
                  <div className="border-l-2 border-primary/30 pl-4">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/40 block mb-1">
                      Your Answer
                    </span>
                    <p className="text-sm text-on-surface/70 italic">
                      {answers[q.id] || (
                        <span className="text-on-surface/30">No answer provided</span>
                      )}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </DesktopLayout>
      </>
    );
  }

  // ── Test-taking screen ────────────────────────────────────────────────────

  if (total === 0) {
    return (
      <DesktopLayout>
        <div className="text-center py-24 text-on-surface/50">
          <p className="text-sm">This test has no questions.</p>
          <button
            onClick={() => router.push('/desktop/mock-tests')}
            className="mt-4 text-primary text-sm font-bold underline"
          >
            Back to Mock Tests
          </button>
        </div>
      </DesktopLayout>
    );
  }

  const currentQuestion = questions[currentIndex];
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === total - 1;

  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmitError('');
    try {
      const payload: Answer[] = Object.entries(answers).map(([qId, text]) => ({
        question_id: Number(qId),
        answer_text: text,
      }));
      const res = await submit(test.test_id, payload);
      setResult(res);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit test.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Head>
        <title>Mock Test | PrepIQ</title>
      </Head>
      <DesktopLayout>
        <div className="max-w-2xl mx-auto">
          {/* Back link */}
          <button
            onClick={() => router.push('/desktop/mock-tests')}
            className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary mb-8 hover:text-primary/70 transition-colors"
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
            >
              <polyline points="15 18 9 12 15 6" />
            </svg>
            All Tests
          </button>

          {/* Progress bar + indicator */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-widest text-primary">
                Question {currentIndex + 1} of {total}
              </span>
              <span className="text-xs text-on-surface/50">
                {Object.keys(answers).length}/{total} answered
              </span>
            </div>
            <div
              className="w-full h-1.5 bg-surface-container-high rounded-full overflow-hidden"
              role="progressbar"
              aria-valuenow={currentIndex + 1}
              aria-valuemin={1}
              aria-valuemax={total}
              aria-label={`Question ${currentIndex + 1} of ${total}`}
            >
              <div
                className="h-full bg-primary rounded-full transition-all duration-300"
                style={{ width: `${((currentIndex + 1) / total) * 100}%` }}
              />
            </div>
          </div>

          {/* Question card */}
          <div className="bg-surface-container p-8 border border-outline-variant/20 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <span className="bg-primary text-on-primary text-xs font-bold uppercase tracking-wider px-3 py-1">
                {currentQuestion.topic}
              </span>
              {currentQuestion.marks && (
                <span className="text-xs text-on-surface/50 font-medium">
                  {currentQuestion.marks} mark{currentQuestion.marks !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            <p className="text-on-surface font-medium leading-relaxed mb-6">
              {currentQuestion.question_text}
            </p>

            <div>
              <label
                htmlFor={`answer-${currentQuestion.id}`}
                className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50 mb-2 block"
              >
                Your Answer
              </label>
              <textarea
                id={`answer-${currentQuestion.id}`}
                rows={4}
                value={answers[currentQuestion.id] ?? ''}
                onChange={(e) =>
                  setAnswers((prev) => ({
                    ...prev,
                    [currentQuestion.id]: e.target.value,
                  }))
                }
                placeholder="Type your answer here…"
                className="w-full bg-surface border border-outline-variant/30 focus:border-primary focus:ring-0 p-4 text-sm text-on-surface resize-none"
              />
            </div>
          </div>

          {/* Submit error */}
          {submitError && (
            <div className="mb-6 px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
              {submitError}
            </div>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => setCurrentIndex((i) => i - 1)}
              disabled={isFirst}
              className="flex items-center gap-2 px-6 py-3 border border-primary text-primary text-xs font-bold uppercase tracking-widest hover:bg-primary hover:text-on-primary transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
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
              >
                <polyline points="15 18 9 12 15 6" />
              </svg>
              Previous
            </button>

            {isLast ? (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex items-center gap-2 px-8 py-3 bg-primary text-on-primary text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <>
                    <svg
                      className="animate-spin"
                      xmlns="http://www.w3.org/2000/svg"
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                    Submitting…
                  </>
                ) : (
                  'Submit Test'
                )}
              </button>
            ) : (
              <button
                onClick={() => setCurrentIndex((i) => i + 1)}
                disabled={isLast}
                className="flex items-center gap-2 px-6 py-3 bg-primary text-on-primary text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors disabled:opacity-30"
              >
                Next
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
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </DesktopLayout>
    </>
  );
}
