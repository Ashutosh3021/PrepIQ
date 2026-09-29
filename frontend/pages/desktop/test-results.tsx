import React, { useCallback, useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { testsService, BackendTestResults } from '@/lib/services/tests.service';
import { mockTestsService } from '@/lib/services/mock-tests.service';
import {
  ERROR_CLASSES,
  TestReviewItem,
  TestReviewResponse,
} from '@/lib/services/mock-tests.service';
import { cn } from '@/lib/utils/cn';

// ── Self-verify form state ────────────────────────────────────────────────────

interface VerifyEntry {
  points: number;
  checked: number[];
  errorClass: string;
}
type VerifyForm = Record<string, VerifyEntry>;

/** Pending = answered descriptive, never auto-graded, not yet self-verified. */
function isPending(item: TestReviewItem): boolean {
  return !item.auto_result && !!item.user_answer && item.verified_points == null;
}

function statusMeta(status: string): { label: string; badge: string; card: string } {
  switch (status) {
    case 'correct':
      return { label: 'Correct · auto', badge: 'bg-green-100 text-green-700', card: 'border-green-500/30 bg-green-500/5' };
    case 'incorrect':
      return { label: 'Incorrect · auto', badge: 'bg-red-100 text-red-700', card: 'border-red-500/30 bg-red-500/5' };
    case 'verified':
      return { label: 'Self-verified', badge: 'bg-teal-100 text-teal-700', card: 'border-teal-500/30 bg-teal-500/5' };
    case 'pending_self_grade':
      return { label: 'Awaiting self-check', badge: 'bg-amber-100 text-amber-700', card: 'border-amber-500/30 bg-amber-500/5' };
    case 'skipped':
    default:
      return { label: 'Skipped', badge: 'bg-gray-100 text-gray-600', card: 'border-outline-variant/30 bg-surface-container' };
  }
}

function GradingBadge({ mode }: { mode: string | null | undefined }) {
  switch (mode) {
    case 'auto':
      return (
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-blue-100 text-blue-700">
          Auto-graded
        </span>
      );
    case 'pending_self_grade':
      return (
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-amber-100 text-amber-700">
          Awaiting self-check
        </span>
      );
    case 'self_verified':
      return (
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-teal-600 text-white">
          Self-Verified
        </span>
      );
    case 'none':
      return (
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-gray-100 text-gray-600">
          Not auto-gradable
        </span>
      );
    default:
      return null;
  }
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function TestResults() {
  const router = useRouter();
  const { testId } = router.query;

  const [results, setResults] = useState<BackendTestResults | null>(null);
  const [review, setReview] = useState<TestReviewResponse | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);

  const [verifyForm, setVerifyForm] = useState<VerifyForm>({});
  const [verifySubmitting, setVerifySubmitting] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [verifyDone, setVerifyDone] = useState(false);

  const load = useCallback(async () => {
    const id = testId as string;
    const [res, rev] = await Promise.all([
      testsService.getResults(id),
      mockTestsService
        .getReview(id)
        .then((r) => ({ ok: true as const, r }))
        .catch((e: unknown) => ({
          ok: false as const,
          msg: e instanceof Error ? e.message : 'Failed to load review',
        })),
    ]);
    setResults(res);
    if (rev.ok) {
      setReview(rev.r);
      setReviewError(null);
      // Seed the self-verify form for still-pending items.
      const form: VerifyForm = {};
      for (const it of rev.r.items) {
        if (isPending(it)) {
          form[it.question_id] = {
            points: it.provisional_points ?? 0,
            checked: [],
            errorClass: '',
          };
        }
      }
      setVerifyForm(form);
    } else {
      setReview(null);
      setReviewError(rev.msg);
    }
  }, [testId]);

  useEffect(() => {
    if (!testId) return;
    setLoading(true);
    setError(null);
    load()
      .catch((err: unknown) => {
        setError(err instanceof Error && err.message ? err.message : 'Failed to load test results');
      })
      .finally(() => setLoading(false));
  }, [testId, load]);

  const gradingMode = results?.grading_mode ?? review?.grading_mode ?? null;
  const pendingItems = (review?.items ?? []).filter(isPending);
  const revByQ: Record<string, TestReviewItem> = {};
  for (const it of review?.items ?? []) revByQ[it.question_id] = it;

  const toggleBullet = (item: TestReviewItem, idx: number) => {
    setVerifyForm((prev) => {
      const cur = prev[item.question_id] ?? { points: 0, checked: [], errorClass: '' };
      const checked = cur.checked.includes(idx)
        ? cur.checked.filter((i) => i !== idx)
        : [...cur.checked, idx];
      const total = (item.rubric_bullets ?? []).length;
      const points =
        total > 0
          ? Math.round((item.marks * checked.length / total) * 100) / 100
          : cur.points;
      return { ...prev, [item.question_id]: { ...cur, checked, points } };
    });
  };

  const setEntry = (qid: string, patch: Partial<VerifyEntry>) => {
    setVerifyForm((prev) => {
      const cur = prev[qid] ?? { points: 0, checked: [], errorClass: '' };
      return { ...prev, [qid]: { ...cur, ...patch } };
    });
  };

  const submitVerify = async () => {
    if (!testId || pendingItems.length === 0) return;
    const missing = pendingItems.filter((it) => !verifyForm[it.question_id]?.errorClass);
    if (missing.length > 0) {
      setVerifyError(
        `Pick what went wrong (Knowledge / Retrieval / Conceptual / Execution) for ${missing.length} question${missing.length === 1 ? '' : 's'}.`
      );
      return;
    }
    setVerifySubmitting(true);
    setVerifyError(null);
    try {
      const items = pendingItems.map((it) => {
        const entry = verifyForm[it.question_id] ?? { points: 0, checked: [], errorClass: 'conceptual' };
        return {
          question_id: it.question_id,
          points_hit: Math.min(Math.max(entry.points, 0), it.marks),
          error_class: entry.errorClass,
        };
      });
      const res = await mockTestsService.selfGrade(testId as string, items);
      setVerifyDone(res.grading_mode === 'self_verified');
      await load();
    } catch (e: unknown) {
      setVerifyError(e instanceof Error ? e.message : 'Failed to save self-check.');
    } finally {
      setVerifySubmitting(false);
    }
  };

  if (loading) {
    return (
      <DesktopLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading results...</p>
          </div>
        </div>
      </DesktopLayout>
    );
  }

  if (error || !results) {
    return (
      <DesktopLayout>
        <div className="text-red-600 text-center py-12">
          <p className="text-lg">{error || 'No results found'}</p>
          <button
            onClick={() => router.push('/desktop/tests')}
            className="mt-4 px-6 py-2 bg-primary text-white rounded"
          >
            Back to Tests
          </button>
        </div>
      </DesktopLayout>
    );
  }

  const scorePercentage = results.percentage;
  const hasScore = scorePercentage != null;
  const scoreColor = !hasScore
    ? 'text-amber-600'
    : scorePercentage >= 70
    ? 'text-green-600'
    : scorePercentage >= 50
    ? 'text-yellow-600'
    : 'text-red-600';

  const analysis = results.question_analysis;
  const countStatus = (s: string) => analysis.filter((q) => q.status === s).length;

  return (
    <>
      <Head>
        <title>Test Results - PrepIQ</title>
      </Head>
      <DesktopLayout>
        {/* Header */}
        <section className="space-y-4 mb-16">
          <h1 className="text-7xl font-serif italic leading-none">Test Results</h1>
          <p className="text-lg max-w-2xl text-on-surface/70 font-light">
            Objective questions are auto-marked. Descriptive answers stay honest — you verify them
            against the rubric, and your final score says exactly which parts were auto vs
            self-checked.
          </p>
        </section>

        {/* Score Card */}
        <section className="mb-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Main Score */}
          <div className="md:col-span-1 bg-surface-container rounded-lg p-8 border border-primary/10">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs text-tertiary uppercase">Your Score</p>
              <GradingBadge mode={gradingMode} />
            </div>
            <div className={cn('text-6xl font-bold mb-4', scoreColor)}>
              {hasScore ? results.score : '—'}
            </div>
            {hasScore ? (
              <p className="text-sm text-tertiary">
                <span className={scoreColor}>{scorePercentage.toFixed(1)}%</span>{' '}
                {gradingMode === 'self_verified'
                  ? 'of total marks · objective + your verified marks'
                  : 'of total marks · auto-graded objective questions'}
              </p>
            ) : (
              <p className="text-sm text-amber-700 leading-relaxed">
                Objective marks banked so far:{' '}
                <strong>{results.score}</strong>. Descriptive answers await your self-check — the
                final percentage appears once you verify them below.
              </p>
            )}
            {!hasScore && pendingItems.length === 0 && (
              <p className="text-xs text-tertiary mt-3">
                This test has no auto-gradable questions, so no percentage is shown.
              </p>
            )}
          </div>

          {/* Performance Breakdown */}
          <div className="md:col-span-2 bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-6">Performance Breakdown</p>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
              <div>
                <p className="text-xs text-tertiary uppercase mb-2">Correct (auto)</p>
                <p className="text-4xl font-bold text-green-600">{countStatus('correct')}</p>
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase mb-2">Wrong (auto)</p>
                <p className="text-4xl font-bold text-red-600">{countStatus('incorrect')}</p>
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase mb-2">Skipped</p>
                <p className="text-4xl font-bold text-gray-600">{countStatus('skipped')}</p>
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase mb-2">Await self-check</p>
                <p className="text-4xl font-bold text-amber-600">
                  {countStatus('pending_self_grade')}
                </p>
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase mb-2">Self-verified</p>
                <p className="text-4xl font-bold text-teal-600">{countStatus('verified')}</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── Self-verify panel ── */}
        {pendingItems.length > 0 && (
          <section className="mb-16 border-2 border-amber-300 bg-amber-50/50 rounded-lg overflow-hidden">
            <div className="p-8 border-b border-amber-200">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xs font-bold uppercase tracking-widest text-amber-700">
                  Self-Verify Your Descriptive Answers
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-amber-100 text-amber-700">
                  {pendingItems.length} pending
                </span>
              </div>
              <p className="text-sm text-amber-800 leading-relaxed">
                No LLM can grade a long answer honestly on free tiers — so you do it, with a rubric
                in your hand. Tick every point your answer actually earned, be honest about what
                went wrong, and tag the mistake type. Gaps you catch today stop costing marks in
                the exam.
              </p>
              {verifyDone && !isPendingReview(review) && (
                <p className="mt-3 text-sm font-bold text-teal-700">
                  ✓ Self-check saved — your final score above now includes your verified marks.
                </p>
              )}
            </div>

            <div className="p-8 space-y-6">
              {pendingItems.map((item) => {
                const entry = verifyForm[item.question_id] ?? {
                  points: 0,
                  checked: [],
                  errorClass: '',
                };
                const bullets = item.rubric_bullets ?? [];
                const anchors = item.keyword_anchors ?? [];
                return (
                  <div
                    key={item.question_id}
                    className="bg-surface-container border border-outline-variant/20 p-6"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-[10px] font-bold text-on-surface/40 uppercase tracking-wider">
                        Q{item.question_number}
                      </span>
                      <span className="text-xs bg-primary/10 text-primary font-bold uppercase tracking-wider px-2 py-0.5">
                        {item.topic}
                      </span>
                      <span className="text-xs text-on-surface/50">{item.marks} marks</span>
                    </div>

                    <p className="text-sm font-medium text-on-surface mb-3">
                      {item.question_text}
                    </p>

                    <div className="border-l-2 border-primary/30 pl-4 mb-4">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/40 block mb-1">
                        Your answer
                      </span>
                      <p className="text-sm text-on-surface/70 whitespace-pre-wrap">
                        {item.user_answer}
                      </p>
                    </div>

                    {item.model_answer && (
                      <div className="border-l-2 border-green-500/40 pl-4 mb-4">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-green-700 block mb-1">
                          Model answer
                        </span>
                        <p className="text-sm text-on-surface/70 whitespace-pre-wrap">
                          {item.model_answer}
                        </p>
                      </div>
                    )}

                    {/* Rubric checklist */}
                    {bullets.length > 0 ? (
                      <div className="mb-4">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/50 block mb-2">
                          Rubric — tick what your answer includes
                        </span>
                        <ul className="space-y-1.5">
                          {bullets.map((b, idx) => (
                            <li key={idx}>
                              <label className="flex items-start gap-2 text-sm text-on-surface/80 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={entry.checked.includes(idx)}
                                  onChange={() => toggleBullet(item, idx)}
                                  className="mt-0.5 accent-primary"
                                />
                                <span>{b}</span>
                              </label>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      anchors.length > 0 && (
                        <div className="mb-4">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/50 block mb-2">
                            Key ideas your answer should mention
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {anchors.map((a, idx) => (
                              <span
                                key={idx}
                                className="text-xs bg-surface-container-high px-2 py-0.5 text-on-surface/70"
                              >
                                {a}
                              </span>
                            ))}
                          </div>
                        </div>
                      )
                    )}

                    {/* Points + error class */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <label className="flex items-center justify-between gap-3 border border-outline-variant/30 px-3 py-2">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
                          Points you earned (of {item.marks})
                        </span>
                        <input
                          type="number"
                          min={0}
                          max={item.marks}
                          step={0.5}
                          value={entry.points}
                          onChange={(e) =>
                            setEntry(item.question_id, { points: Number(e.target.value) })
                          }
                          className="w-16 bg-surface border border-outline-variant/30 focus:border-primary focus:ring-0 px-2 py-1 text-sm text-on-surface text-right"
                        />
                      </label>
                      <label className="flex items-center justify-between gap-3 border border-outline-variant/30 px-3 py-2">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
                          What went wrong?
                        </span>
                        <select
                          value={entry.errorClass}
                          onChange={(e) =>
                            setEntry(item.question_id, { errorClass: e.target.value })
                          }
                          className="bg-surface border border-outline-variant/30 focus:border-primary focus:ring-0 px-2 py-1 text-sm text-on-surface cursor-pointer"
                        >
                          <option value="">Choose…</option>
                          {ERROR_CLASSES.map((c) => (
                            <option key={c} value={c.toLowerCase()}>
                              {c}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                  </div>
                );
              })}

              {reviewError && (
                <div className="px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
                  {reviewError}{' '}
                  <button onClick={() => load()} className="font-bold underline">
                    Retry
                  </button>
                </div>
              )}
              {verifyError && (
                <div className="px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
                  {verifyError}
                </div>
              )}

              <button
                onClick={submitVerify}
                disabled={verifySubmitting}
                className="w-full bg-primary text-on-primary py-4 text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
              >
                {verifySubmitting ? (
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
                    Saving self-check…
                  </>
                ) : (
                  `Submit self-check (${pendingItems.length} question${pendingItems.length === 1 ? '' : 's'})`
                )}
              </button>
            </div>
          </section>
        )}

        {/* Verified-complete note */}
        {gradingMode === 'self_verified' && pendingItems.length === 0 && (
          <section className="mb-16 border-2 border-teal-300 bg-teal-50 p-6 flex items-start gap-4">
            <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-teal-600 text-white shrink-0">
              Self-Verified
            </span>
            <p className="text-sm text-teal-900 leading-relaxed">
              You checked every descriptive answer against the rubric yourself — the score above
              mixes auto-marked objective questions with marks you honestly awarded. Mistakes you
              catch yourself are the ones you stop repeating.
            </p>
          </section>
        )}

        {/* Topics Analysis */}
        <section className="mb-16 grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Weak Topics */}
          <div className="bg-surface-container rounded-lg p-8 border border-red-500/20">
            <p className="text-xs text-tertiary uppercase mb-4 font-bold">Areas for Improvement</p>
            {results.weak_topics && results.weak_topics.length > 0 ? (
              <div className="space-y-3">
                {results.weak_topics.map((topic, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 bg-red-500/10 rounded">
                    <span className="text-red-600 font-bold">⚠</span>
                    <span className="text-sm">{topic}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-tertiary">No weak topics identified</p>
            )}
          </div>

          {/* Strong Topics */}
          <div className="bg-surface-container rounded-lg p-8 border border-green-500/20">
            <p className="text-xs text-tertiary uppercase mb-4 font-bold">Strong Areas</p>
            {results.strong_topics && results.strong_topics.length > 0 ? (
              <div className="space-y-3">
                {results.strong_topics.map((topic, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 bg-green-500/10 rounded">
                    <span className="text-green-600 font-bold">✓</span>
                    <span className="text-sm">{topic}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-tertiary">No strong topics identified</p>
            )}
          </div>
        </section>

        {/* Recommendations */}
        {results.recommendations && results.recommendations.length > 0 && (
          <section className="mb-16 bg-primary/10 rounded-lg p-8 border border-primary/20">
            <p className="text-xs text-tertiary uppercase mb-4 font-bold">Recommendations</p>
            <ul className="space-y-2">
              {results.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-primary font-bold mt-1">→</span>
                  <span className="text-sm">{rec}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Question Analysis */}
        <section className="mb-16">
          <div className="flex items-end justify-between border-b border-primary/10 pb-4 mb-8">
            <h2 className="text-xs font-bold uppercase tracking-widest text-primary">
              Question-by-Question Analysis
            </h2>
            <span className="text-xs text-tertiary">
              {results.question_analysis.length} Questions · auto &amp; self-verified labelled per
              question
            </span>
          </div>

          <div className="space-y-4">
            {results.question_analysis.map((q, idx) => {
              const isExpanded = expandedQuestion === q.question_id;
              const meta = statusMeta(q.status);
              const rev = revByQ[q.question_id];

              return (
                <div key={q.question_id} className={cn('border rounded-lg overflow-hidden transition-colors', meta.card)}>
                  {/* Question Header */}
                  <button
                    onClick={() => setExpandedQuestion(isExpanded ? null : q.question_id)}
                    className="w-full p-4 flex items-start justify-between hover:bg-black/5 transition-colors"
                  >
                    <div className="flex items-start gap-4 flex-1 text-left">
                      <div className="flex-shrink-0">
                        <span
                          className={cn(
                            'inline-flex items-center justify-center min-w-8 h-8 rounded-full font-bold text-[10px] px-1 text-center',
                            q.status === 'correct' || q.status === 'verified'
                              ? 'bg-green-500 text-white'
                              : q.status === 'incorrect'
                              ? 'bg-red-500 text-white'
                              : q.status === 'pending_self_grade'
                              ? 'bg-amber-500 text-white'
                              : 'bg-gray-400 text-white'
                          )}
                        >
                          {q.status === 'correct'
                            ? '✓'
                            : q.status === 'incorrect'
                            ? '✗'
                            : q.status === 'verified'
                            ? `${q.points ?? ''}/${q.marks}`
                            : q.status === 'pending_self_grade'
                            ? '?'
                            : '—'}
                        </span>
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-sm mb-1">Question {idx + 1}</p>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-tertiary">
                          <span>Marks: {q.marks}</span>
                          <span
                            className={cn(
                              'text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5',
                              meta.badge
                            )}
                          >
                            {meta.label}
                          </span>
                          {q.status === 'verified' && q.points != null && (
                            <span className="text-teal-700 font-bold">
                              {q.points}/{q.marks} marks
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <span className="text-tertiary">{isExpanded ? '−' : '+'}</span>
                  </button>

                  {/* Question Details */}
                  {isExpanded && (
                    <div className="border-t border-current/10 p-4 space-y-4 bg-black/2">
                      <div>
                        <p className="text-xs text-tertiary uppercase mb-2">Your Answer</p>
                        <p className="text-sm font-mono p-3 rounded bg-surface-container whitespace-pre-wrap">
                          {q.user_answer}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-tertiary uppercase mb-2">
                          {q.correct_answer && q.correct_answer !== 'N/A'
                            ? 'Correct Answer'
                            : 'Model Answer'}
                        </p>
                        <p className="text-sm font-mono p-3 rounded bg-green-500/10 text-green-800 whitespace-pre-wrap">
                          {q.correct_answer && q.correct_answer !== 'N/A'
                            ? q.correct_answer
                            : rev?.model_answer || 'No model answer available for this question.'}
                        </p>
                      </div>

                      {q.status === 'pending_self_grade' && rev && (
                        <div>
                          <p className="text-xs text-tertiary uppercase mb-2">Provisional (keyword coverage)</p>
                          <p className="text-sm text-amber-700 font-bold">
                            {rev.provisional_points ?? 0} / {q.marks} marks — pending your
                            self-check above.
                          </p>
                        </div>
                      )}

                      {q.status === 'verified' && rev?.error_class && (
                        <div>
                          <p className="text-xs text-tertiary uppercase mb-2">Error class</p>
                          <span className="text-xs bg-teal-100 text-teal-800 font-bold uppercase tracking-wider px-2 py-0.5">
                            {rev.error_class}
                          </span>
                        </div>
                      )}

                      {q.explanation && (
                        <div>
                          <p className="text-xs text-tertiary uppercase mb-2">Explanation</p>
                          <p className="text-sm text-on-surface/70">{q.explanation}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* Action Buttons */}
        <section className="flex gap-4 mb-16">
          <button
            onClick={() => router.push('/desktop/tests')}
            className="px-8 py-3 border border-primary text-primary rounded font-semibold hover:bg-primary/10 transition-colors"
          >
            Back to Tests
          </button>
          <button
            onClick={() => router.push('/desktop/test-history')}
            className="px-8 py-3 bg-primary text-white rounded font-semibold hover:bg-primary/90 transition-colors"
          >
            View History
          </button>
        </section>
      </DesktopLayout>
    </>
  );
}

/** True while any review item is still awaiting self-grade. */
function isPendingReview(review: TestReviewResponse | null): boolean {
  return (review?.items ?? []).some(isPending);
}
