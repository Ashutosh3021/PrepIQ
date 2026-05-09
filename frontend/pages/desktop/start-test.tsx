import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { useAuth } from '@/lib/context/AuthContext';
import { testsService, BackendQuestion } from '@/lib/services/tests.service';

interface TestState {
  testId: string;
  questions: BackendQuestion[];
  currentQuestionIndex: number;
  answers: Record<string, string>;
  markedForReview: Set<string>;
  timeRemaining: number;
  isSubmitting: boolean;
  showConfirmation: boolean;
}

export default function StartTest() {
  const router = useRouter();
  const { user } = useAuth();
  const { testId } = router.query;

  const [testState, setTestState] = useState<TestState>({
    testId: testId as string,
    questions: [],
    currentQuestionIndex: 0,
    answers: {},
    markedForReview: new Set(),
    timeRemaining: 0,
    isSubmitting: false,
    showConfirmation: false,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load test on mount
  useEffect(() => {
    if (!testId) return;

    const loadTest = async () => {
      try {
        const tests = await testsService.getAll();
        const test = tests.find((t) => t.test_id === testId);

        if (!test) {
          setError('Test not found');
          return;
        }

        setTestState((prev) => ({
          ...prev,
          questions: test.questions,
          timeRemaining: test.time_limit_minutes * 60,
        }));
        setLoading(false);
      } catch (err) {
        setError('Failed to load test');
        setLoading(false);
      }
    };

    loadTest();
  }, [testId]);

  // Timer effect
  useEffect(() => {
    if (testState.timeRemaining <= 0 || testState.showConfirmation) return;

    const timer = setInterval(() => {
      setTestState((prev) => ({
        ...prev,
        timeRemaining: Math.max(0, prev.timeRemaining - 1),
      }));
    }, 1000);

    return () => clearInterval(timer);
  }, [testState.timeRemaining, testState.showConfirmation]);

  // Auto-submit when time runs out
  useEffect(() => {
    if (testState.timeRemaining === 0 && testState.questions.length > 0) {
      handleSubmitTest();
    }
  }, [testState.timeRemaining]);

  const currentQuestion = testState.questions[testState.currentQuestionIndex];
  const currentAnswer = testState.answers[currentQuestion?.id] || '';

  const handleAnswerChange = (answer: string) => {
    setTestState((prev) => ({
      ...prev,
      answers: {
        ...prev.answers,
        [currentQuestion.id]: answer,
      },
    }));
  };

  const handleMarkForReview = () => {
    setTestState((prev) => {
      const newMarked = new Set(prev.markedForReview);
      if (newMarked.has(currentQuestion.id)) {
        newMarked.delete(currentQuestion.id);
      } else {
        newMarked.add(currentQuestion.id);
      }
      return { ...prev, markedForReview: newMarked };
    });
  };

  const handleNavigateQuestion = (index: number) => {
    setTestState((prev) => ({
      ...prev,
      currentQuestionIndex: index,
    }));
  };

  const handleSubmitTest = async () => {
    if (testState.showConfirmation) {
      setTestState((prev) => ({ ...prev, isSubmitting: true }));

      try {
        await testsService.submitTest(testState.testId, testState.answers);
        router.push(`/desktop/test-results?testId=${testState.testId}`);
      } catch (err) {
        setError('Failed to submit test');
        setTestState((prev) => ({ ...prev, isSubmitting: false }));
      }
    } else {
      setTestState((prev) => ({ ...prev, showConfirmation: true }));
    }
  };

  const handleCancelConfirmation = () => {
    setTestState((prev) => ({ ...prev, showConfirmation: false }));
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const answeredCount = Object.keys(testState.answers).length;
  const reviewCount = testState.markedForReview.size;
  const skippedCount = testState.questions.length - answeredCount;

  if (loading) {
    return (
      <DesktopLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading test...</p>
          </div>
        </div>
      </DesktopLayout>
    );
  }

  if (error) {
    return (
      <DesktopLayout>
        <div className="text-red-600 text-center py-12">
          <p className="text-lg">{error}</p>
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

  if (!currentQuestion) {
    return (
      <DesktopLayout>
        <div className="text-center py-12">
          <p>No questions available</p>
        </div>
      </DesktopLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Test - PrepIQ</title>
      </Head>
      <div className="flex h-screen bg-surface">
        {/* Main Test Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-surface-container border-b border-primary/10 px-8 py-4 flex justify-between items-center">
            <div className="flex items-center gap-8">
              <div>
                <p className="text-xs text-tertiary uppercase">Question</p>
                <p className="text-lg font-semibold">
                  {testState.currentQuestionIndex + 1} / {testState.questions.length}
                </p>
              </div>
              <div>
                <p className="text-xs text-tertiary uppercase">Marks</p>
                <p className="text-lg font-semibold">{currentQuestion.marks}</p>
              </div>
            </div>

            {/* Timer */}
            <div className={`text-center px-6 py-3 rounded ${testState.timeRemaining < 300 ? 'bg-red-500/10 border border-red-500' : 'bg-primary/10'}`}>
              <p className="text-xs text-tertiary uppercase">Time Remaining</p>
              <p className={`text-2xl font-mono font-bold ${testState.timeRemaining < 300 ? 'text-red-600' : 'text-primary'}`}>
                {formatTime(testState.timeRemaining)}
              </p>
            </div>

            {/* Stats */}
            <div className="flex gap-6">
              <div className="text-center">
                <p className="text-xs text-tertiary uppercase">Answered</p>
                <p className="text-lg font-semibold text-green-600">{answeredCount}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-tertiary uppercase">Review</p>
                <p className="text-lg font-semibold text-yellow-600">{reviewCount}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-tertiary uppercase">Skipped</p>
                <p className="text-lg font-semibold text-gray-600">{skippedCount}</p>
              </div>
            </div>
          </div>

          {/* Question Content */}
          <div className="flex-1 overflow-auto px-8 py-8">
            <div className="max-w-4xl">
              {/* Question Text */}
              <div className="mb-8">
                <h2 className="text-2xl font-serif mb-4">{currentQuestion.text}</h2>
                <p className="text-sm text-tertiary">
                  Type: {currentQuestion.type} | Unit: {currentQuestion.unit}
                </p>
              </div>

              {/* Answer Options */}
              <div className="space-y-4 mb-8">
                {currentQuestion.type === 'mcq' && currentQuestion.options ? (
                  currentQuestion.options.map((option, idx) => {
                    const optionKey = String.fromCharCode(65 + idx); // A, B, C, D
                    const isSelected = currentAnswer === optionKey;
                    return (
                      <button
                        key={idx}
                        onClick={() => handleAnswerChange(optionKey)}
                        className={`w-full p-4 text-left border-2 rounded transition-colors ${
                          isSelected
                            ? 'border-primary bg-primary/10'
                            : 'border-primary/20 hover:border-primary/40'
                        }`}
                      >
                        <span className="font-semibold">{optionKey})</span> {option}
                      </button>
                    );
                  })
                ) : (
                  <textarea
                    value={currentAnswer}
                    onChange={(e) => handleAnswerChange(e.target.value)}
                    placeholder="Enter your answer here..."
                    className="w-full p-4 border border-primary/20 rounded focus:border-primary focus:outline-none"
                    rows={6}
                  />
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={handleMarkForReview}
                  className={`px-6 py-2 border rounded text-sm font-semibold transition-colors ${
                    testState.markedForReview.has(currentQuestion.id)
                      ? 'bg-yellow-500/10 border-yellow-500 text-yellow-600'
                      : 'border-primary/20 hover:border-primary/40'
                  }`}
                >
                  {testState.markedForReview.has(currentQuestion.id) ? '✓ Marked for Review' : 'Mark for Review'}
                </button>
              </div>
            </div>
          </div>

          {/* Navigation Footer */}
          <div className="bg-surface-container border-t border-primary/10 px-8 py-4 flex justify-between items-center">
            <button
              onClick={() => handleNavigateQuestion(Math.max(0, testState.currentQuestionIndex - 1))}
              disabled={testState.currentQuestionIndex === 0}
              className="px-6 py-2 bg-primary text-white rounded disabled:opacity-50"
            >
              ← Previous
            </button>

            <button
              onClick={handleSubmitTest}
              className="px-8 py-2 bg-red-600 text-white rounded font-semibold hover:bg-red-700"
            >
              Submit Test
            </button>

            <button
              onClick={() => handleNavigateQuestion(Math.min(testState.questions.length - 1, testState.currentQuestionIndex + 1))}
              disabled={testState.currentQuestionIndex === testState.questions.length - 1}
              className="px-6 py-2 bg-primary text-white rounded disabled:opacity-50"
            >
              Next →
            </button>
          </div>
        </div>

        {/* Question Navigator Sidebar */}
        <div className="w-64 bg-surface-container border-l border-primary/10 overflow-auto">
          <div className="p-4 border-b border-primary/10">
            <h3 className="text-sm font-bold uppercase">Questions</h3>
          </div>
          <div className="p-4 space-y-2">
            {testState.questions.map((q, idx) => {
              const isAnswered = testState.answers[q.id];
              const isMarked = testState.markedForReview.has(q.id);
              const isCurrent = idx === testState.currentQuestionIndex;

              return (
                <button
                  key={q.id}
                  onClick={() => handleNavigateQuestion(idx)}
                  className={`w-full p-3 text-left text-sm rounded transition-colors ${
                    isCurrent
                      ? 'bg-primary text-white'
                      : isAnswered
                      ? 'bg-green-500/10 border border-green-500 text-green-600'
                      : isMarked
                      ? 'bg-yellow-500/10 border border-yellow-500 text-yellow-600'
                      : 'bg-gray-500/10 border border-gray-500 text-gray-600'
                  }`}
                >
                  <div className="font-semibold">Q{idx + 1}</div>
                  <div className="text-xs opacity-70">
                    {isAnswered ? '✓ Answered' : isMarked ? '⚠ Review' : '○ Skipped'}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {testState.showConfirmation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md">
            <h2 className="text-2xl font-bold mb-4">Submit Test?</h2>
            <p className="text-gray-600 mb-6">
              You have answered {answeredCount} out of {testState.questions.length} questions.
              {skippedCount > 0 && ` ${skippedCount} questions will be marked as skipped.`}
            </p>
            <div className="flex gap-4">
              <button
                onClick={handleCancelConfirmation}
                className="flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                Continue Test
              </button>
              <button
                onClick={handleSubmitTest}
                disabled={testState.isSubmitting}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                {testState.isSubmitting ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
