import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { testsService, BackendTestResults } from '@/lib/services/tests.service';

export default function TestResults() {
  const router = useRouter();
  const { testId } = router.query;

  const [results, setResults] = useState<BackendTestResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);

  useEffect(() => {
    if (!testId) return;

    const loadResults = async () => {
      try {
        const data = await testsService.getResults(testId as string);
        setResults(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load test results');
        setLoading(false);
      }
    };

    loadResults();
  }, [testId]);

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
  const scoreColor = scorePercentage >= 70 ? 'text-green-600' : scorePercentage >= 50 ? 'text-yellow-600' : 'text-red-600';

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
            Detailed analysis of your test performance and areas for improvement.
          </p>
        </section>

        {/* Score Card */}
        <section className="mb-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Main Score */}
          <div className="md:col-span-1 bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-4">Your Score</p>
            <div className={`text-6xl font-bold ${scoreColor} mb-4`}>
              {results.score}
            </div>
            <p className="text-sm text-tertiary">
              <span className={scoreColor}>{results.percentage.toFixed(1)}%</span> of total marks
            </p>
          </div>

          {/* Performance Breakdown */}
          <div className="md:col-span-2 bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-6">Performance Breakdown</p>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-xs text-tertiary uppercase mb-2">Correct</p>
                <p className="text-4xl font-bold text-green-600">
                  {results.question_analysis.filter((q) => q.status === 'correct').length}
                </p>
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase mb-2">Incorrect</p>
                <p className="text-4xl font-bold text-red-600">
                  {results.question_analysis.filter((q) => q.status === 'incorrect').length}
                </p>
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase mb-2">Skipped</p>
                <p className="text-4xl font-bold text-gray-600">
                  {results.question_analysis.filter((q) => q.user_answer === 'Skipped').length}
                </p>
              </div>
            </div>
          </div>
        </section>

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
              {results.question_analysis.length} Questions
            </span>
          </div>

          <div className="space-y-4">
            {results.question_analysis.map((q, idx) => {
              const isExpanded = expandedQuestion === q.question_id;
              const isCorrect = q.status === 'correct';

              return (
                <div
                  key={q.question_id}
                  className={`border rounded-lg overflow-hidden transition-colors ${
                    isCorrect
                      ? 'border-green-500/30 bg-green-500/5'
                      : 'border-red-500/30 bg-red-500/5'
                  }`}
                >
                  {/* Question Header */}
                  <button
                    onClick={() => setExpandedQuestion(isExpanded ? null : q.question_id)}
                    className="w-full p-4 flex items-start justify-between hover:bg-black/5 transition-colors"
                  >
                    <div className="flex items-start gap-4 flex-1 text-left">
                      <div className="flex-shrink-0">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${
                          isCorrect
                            ? 'bg-green-500 text-white'
                            : 'bg-red-500 text-white'
                        }`}>
                          {isCorrect ? '✓' : '✗'}
                        </span>
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-sm mb-1">Question {idx + 1}</p>
                        <p className="text-xs text-tertiary">
                          Marks: {q.marks} | Status: {isCorrect ? 'Correct' : 'Incorrect'}
                        </p>
                      </div>
                    </div>
                    <span className="text-tertiary">{isExpanded ? '−' : '+'}</span>
                  </button>

                  {/* Question Details */}
                  {isExpanded && (
                    <div className="border-t border-current/10 p-4 space-y-4 bg-black/2">
                      <div>
                        <p className="text-xs text-tertiary uppercase mb-2">Your Answer</p>
                        <p className={`text-sm font-mono p-3 rounded ${
                          isCorrect
                            ? 'bg-green-500/10 text-green-700'
                            : 'bg-red-500/10 text-red-700'
                        }`}>
                          {q.user_answer}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-tertiary uppercase mb-2">Correct Answer</p>
                        <p className="text-sm font-mono p-3 rounded bg-green-500/10 text-green-700">
                          {q.correct_answer}
                        </p>
                      </div>

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
