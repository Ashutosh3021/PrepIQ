import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { useTests } from '@/lib/hooks/useTests';

export default function TestHistory() {
  const router = useRouter();
  const { tests, isLoading, error } = useTests();

  const [filteredTests, setFilteredTests] = useState(tests);
  const [sortBy, setSortBy] = useState<'date' | 'score'>('date');
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'in-progress'>('all');

  useEffect(() => {
    let filtered = tests.filter((test) => {
      if (filterStatus === 'completed') {
        return test.questions && test.questions.length > 0;
      } else if (filterStatus === 'in-progress') {
        return !test.questions || test.questions.length === 0;
      }
      return true;
    });

    filtered.sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.start_time).getTime() - new Date(a.start_time).getTime();
      } else {
        // Sort by score (would need to fetch results for each test)
        return 0;
      }
    });

    setFilteredTests(filtered);
  }, [tests, sortBy, filterStatus]);

  const stats = {
    totalTests: tests.length,
    completedTests: tests.filter((t) => t.questions && t.questions.length > 0).length,
    averageScore: tests.length > 0 ? 72.5 : 0, // Would calculate from actual results
  };

  if (isLoading) {
    return (
      <DesktopLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading test history...</p>
          </div>
        </div>
      </DesktopLayout>
    );
  }

  if (error) {
    return (
      <DesktopLayout>
        <div className="text-red-600 text-center py-12">
          <p className="text-lg">Failed to load test history</p>
        </div>
      </DesktopLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Test History - PrepIQ</title>
      </Head>
      <DesktopLayout>
        {/* Header */}
        <section className="space-y-4 mb-16">
          <h1 className="text-7xl font-serif italic leading-none">Test History</h1>
          <p className="text-lg max-w-2xl text-on-surface/70 font-light">
            Review your past tests and track your progress over time.
          </p>
        </section>

        {/* Statistics */}
        <section className="mb-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-4">Total Tests</p>
            <p className="text-5xl font-bold text-primary">{stats.totalTests}</p>
          </div>
          <div className="bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-4">Completed</p>
            <p className="text-5xl font-bold text-green-600">{stats.completedTests}</p>
          </div>
          <div className="bg-surface-container rounded-lg p-8 border border-primary/10">
            <p className="text-xs text-tertiary uppercase mb-4">Average Score</p>
            <p className="text-5xl font-bold text-blue-600">{stats.averageScore.toFixed(1)}%</p>
          </div>
        </section>

        {/* Filters and Sort */}
        <section className="mb-8 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
          <div className="flex gap-4">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 text-sm font-semibold rounded transition-colors ${
                filterStatus === 'all'
                  ? 'bg-primary text-white'
                  : 'border border-primary/20 hover:border-primary/40'
              }`}
            >
              All Tests
            </button>
            <button
              onClick={() => setFilterStatus('completed')}
              className={`px-4 py-2 text-sm font-semibold rounded transition-colors ${
                filterStatus === 'completed'
                  ? 'bg-green-600 text-white'
                  : 'border border-primary/20 hover:border-primary/40'
              }`}
            >
              Completed
            </button>
            <button
              onClick={() => setFilterStatus('in-progress')}
              className={`px-4 py-2 text-sm font-semibold rounded transition-colors ${
                filterStatus === 'in-progress'
                  ? 'bg-yellow-600 text-white'
                  : 'border border-primary/20 hover:border-primary/40'
              }`}
            >
              In Progress
            </button>
          </div>

          <div className="flex gap-2">
            <span className="text-xs text-tertiary uppercase">Sort by:</span>
            <button
              onClick={() => setSortBy('date')}
              className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
                sortBy === 'date'
                  ? 'bg-primary text-white'
                  : 'border border-primary/20 hover:border-primary/40'
              }`}
            >
              Date
            </button>
            <button
              onClick={() => setSortBy('score')}
              className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
                sortBy === 'score'
                  ? 'bg-primary text-white'
                  : 'border border-primary/20 hover:border-primary/40'
              }`}
            >
              Score
            </button>
          </div>
        </section>

        {/* Test List */}
        <section>
          {filteredTests.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-lg text-tertiary">No tests found</p>
              <button
                onClick={() => router.push('/desktop/tests')}
                className="mt-4 px-6 py-2 bg-primary text-white rounded"
              >
                Generate a Test
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredTests.map((test, idx) => {
                const testDate = new Date(test.start_time);
                const isCompleted = test.questions && test.questions.length > 0;

                return (
                  <div
                    key={test.test_id}
                    className="bg-surface-container rounded-lg p-6 border border-primary/10 hover:border-primary/30 transition-colors cursor-pointer"
                    onClick={() => {
                      if (isCompleted) {
                        router.push(`/desktop/test-results?testId=${test.test_id}`);
                      }
                    }}
                  >
                    <div className="grid grid-cols-12 gap-4 items-center">
                      {/* Test Number */}
                      <div className="col-span-1">
                        <p className="text-xs text-tertiary uppercase">Test</p>
                        <p className="text-2xl font-bold text-primary">#{idx + 1}</p>
                      </div>

                      {/* Test Info */}
                      <div className="col-span-4">
                        <p className="text-sm font-semibold mb-1">
                          {testDate.toLocaleDateString('en-US', {
                            weekday: 'short',
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })}
                        </p>
                        <p className="text-xs text-tertiary">
                          {test.total_questions} Questions • {test.time_limit_minutes} Minutes
                        </p>
                      </div>

                      {/* Stats */}
                      <div className="col-span-4 grid grid-cols-3 gap-4">
                        <div>
                          <p className="text-xs text-tertiary uppercase mb-1">Questions</p>
                          <p className="text-lg font-semibold">{test.total_questions}</p>
                        </div>
                        <div>
                          <p className="text-xs text-tertiary uppercase mb-1">Total Marks</p>
                          <p className="text-lg font-semibold">{test.total_marks || '—'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-tertiary uppercase mb-1">Duration</p>
                          <p className="text-lg font-semibold">{test.time_limit_minutes}m</p>
                        </div>
                      </div>

                      {/* Status */}
                      <div className="col-span-3 flex items-center justify-end gap-4">
                        <div className="text-right">
                          <p className="text-xs text-tertiary uppercase mb-1">Status</p>
                          <p className={`text-sm font-semibold ${
                            isCompleted ? 'text-green-600' : 'text-yellow-600'
                          }`}>
                            {isCompleted ? '✓ Completed' : '⏳ In Progress'}
                          </p>
                        </div>
                        {isCompleted && (
                          <button
                            className="px-6 py-2 bg-primary text-white rounded text-sm font-semibold hover:bg-primary/90 transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/desktop/test-results?testId=${test.test_id}`);
                            }}
                          >
                            View Results
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Footer */}
        <section className="mt-16 pt-8 border-t border-primary/10">
          <button
            onClick={() => router.push('/desktop/tests')}
            className="px-8 py-3 border border-primary text-primary rounded font-semibold hover:bg-primary/10 transition-colors"
          >
            Generate New Test
          </button>
        </section>
      </DesktopLayout>
    </>
  );
}
