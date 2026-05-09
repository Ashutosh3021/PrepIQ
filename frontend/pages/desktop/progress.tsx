import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';
import { useAuth } from '@/lib/context/AuthContext';
import { apiFetch } from '@/lib/services/base.service';

interface ProgressData {
  total_tests: number;
  average_score: number;
  average_percentage: number;
  trend: Array<{
    test_number: number;
    score: number;
    percentage: number;
    date: string;
    total_marks: number;
  }>;
  weak_topics: Record<string, number>;
  strong_topics: Record<string, number>;
}

export default function Progress() {
  const { user } = useAuth();
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProgress = async () => {
      try {
        const data = await apiFetch<ProgressData>('/tests/progress', {} as ProgressData);
        setProgress(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load progress data');
        setLoading(false);
      }
    };

    loadProgress();
  }, []);

  if (loading) {
    return (
      <DesktopLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading progress...</p>
          </div>
        </div>
      </DesktopLayout>
    );
  }

  if (error || !progress) {
    return (
      <DesktopLayout>
        <div className="text-red-600 text-center py-12">
          <p className="text-lg">{error || 'No progress data available'}</p>
        </div>
      </DesktopLayout>
    );
  }

  const weakTopicsList = Object.entries(progress.weak_topics)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  const strongTopicsList = Object.entries(progress.strong_topics)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  const maxWeakCount = Math.max(...weakTopicsList.map(([, count]) => count), 1);
  const maxStrongCount = Math.max(...strongTopicsList.map(([, count]) => count), 1);

  return (
    <>
      <Head>
        <title>Progress - PrepIQ</title>
      </Head>
      <DesktopLayout>
        {/* Header */}
        <section className="space-y-4 mb-16">
          <h1 className="text-7xl font-serif italic leading-none">Your Progress</h1>
          <p className="text-lg max-w-2xl text-on-surface/70 font-light">
            Track your learning journey and identify areas for improvement.
          </p>
        </section>

        {/* Key Metrics */}
        <section className="mb-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-4">Total Tests</p>
            <p className="text-6xl font-bold text-primary mb-2">{progress.total_tests}</p>
            <p className="text-sm text-tertiary">Tests completed</p>
          </div>

          <div className="bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-4">Average Score</p>
            <p className="text-6xl font-bold text-blue-600 mb-2">{progress.average_score.toFixed(1)}</p>
            <p className="text-sm text-tertiary">{progress.average_percentage.toFixed(1)}% average</p>
          </div>

          <div className="bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-4">Performance</p>
            <div className="flex items-end gap-2 mb-2">
              {progress.trend.slice(-5).map((t, idx) => (
                <div
                  key={idx}
                  className="flex-1 bg-primary/20 rounded-t"
                  style={{
                    height: `${(t.percentage / 100) * 60}px`,
                    backgroundColor: t.percentage >= 70 ? '#10b981' : t.percentage >= 50 ? '#f59e0b' : '#ef4444',
                  }}
                  title={`${t.percentage.toFixed(1)}%`}
                />
              ))}
            </div>
            <p className="text-xs text-tertiary">Last 5 tests</p>
          </div>
        </section>

        {/* Score Trend Chart */}
        {progress.trend.length > 0 && (
          <section className="mb-16 bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-6 font-bold">Score Trend</p>
            <div className="space-y-4">
              {progress.trend.map((t, idx) => {
                const date = new Date(t.date);
                const dateStr = date.toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                });

                return (
                  <div key={idx} className="flex items-center gap-4">
                    <div className="w-16 text-sm font-semibold text-tertiary">
                      Test {t.test_number}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              t.percentage >= 70
                                ? 'bg-green-600'
                                : t.percentage >= 50
                                ? 'bg-yellow-600'
                                : 'bg-red-600'
                            }`}
                            style={{ width: `${t.percentage}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold w-12 text-right">
                          {t.percentage.toFixed(1)}%
                        </span>
                      </div>
                      <p className="text-xs text-tertiary">
                        {t.score} / {t.total_marks} marks • {dateStr}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Topics Analysis */}
        <section className="mb-16 grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Weak Topics - Grey Area */}
          <div className="bg-surface-container rounded-lg p-8 border border-red-500/20">
            <p className="text-xs text-tertiary uppercase mb-6 font-bold">Areas for Improvement (Grey Area)</p>
            {weakTopicsList.length > 0 ? (
              <div className="space-y-4">
                {weakTopicsList.map(([topic, count]) => (
                  <div key={topic}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold">{topic}</span>
                      <span className="text-xs text-tertiary">{count} times</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-red-500 rounded-full transition-all"
                        style={{ width: `${(count / maxWeakCount) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-tertiary">No weak topics identified yet</p>
            )}
          </div>

          {/* Strong Topics - Green Area */}
          <div className="bg-surface-container rounded-lg p-8 border border-green-500/20">
            <p className="text-xs text-tertiary uppercase mb-6 font-bold">Strong Areas</p>
            {strongTopicsList.length > 0 ? (
              <div className="space-y-4">
                {strongTopicsList.map(([topic, count]) => (
                  <div key={topic}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold">{topic}</span>
                      <span className="text-xs text-tertiary">{count} times</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-green-500 rounded-full transition-all"
                        style={{ width: `${(count / maxStrongCount) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-tertiary">No strong topics identified yet</p>
            )}
          </div>
        </section>

        {/* Recommendations */}
        <section className="mb-16 bg-primary/10 rounded-lg p-8 border border-primary/20">
          <p className="text-xs text-tertiary uppercase mb-6 font-bold">Personalized Recommendations</p>
          <ul className="space-y-3">
            {weakTopicsList.length > 0 && (
              <li className="flex items-start gap-3">
                <span className="text-primary font-bold mt-1">→</span>
                <span className="text-sm">
                  Focus on <strong>{weakTopicsList[0][0]}</strong> - you've struggled with this topic {weakTopicsList[0][1]} times
                </span>
              </li>
            )}
            {progress.average_percentage < 50 && (
              <li className="flex items-start gap-3">
                <span className="text-primary font-bold mt-1">→</span>
                <span className="text-sm">
                  Your average score is {progress.average_percentage.toFixed(1)}%. Try practicing more questions on weak topics.
                </span>
              </li>
            )}
            {progress.average_percentage >= 70 && (
              <li className="flex items-start gap-3">
                <span className="text-primary font-bold mt-1">→</span>
                <span className="text-sm">
                  Great job! Your average score is {progress.average_percentage.toFixed(1)}%. Try harder difficulty levels.
                </span>
              </li>
            )}
            {progress.total_tests < 5 && (
              <li className="flex items-start gap-3">
                <span className="text-primary font-bold mt-1">→</span>
                <span className="text-sm">
                  Take more tests to get better insights into your performance patterns.
                </span>
              </li>
            )}
          </ul>
        </section>

        {/* Call to Action */}
        <section className="flex gap-4 mb-16">
          <a
            href="/desktop/tests"
            className="px-8 py-3 bg-primary text-white rounded font-semibold hover:bg-primary/90 transition-colors"
          >
            Generate New Test
          </a>
          <a
            href="/desktop/test-history"
            className="px-8 py-3 border border-primary text-primary rounded font-semibold hover:bg-primary/10 transition-colors"
          >
            View Test History
          </a>
        </section>
      </DesktopLayout>
    </>
  );
}
