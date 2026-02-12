'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardLayout from '@/src/components/dashboard/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { apiClient, subjectService } from '@/src/lib/api';
import type { Subject, MockTestResponse, MockTestQuestion } from '@/src/lib/api';

// Types for test data
interface TestConfig {
  subjectId: string;
  numQuestions: number;
  difficulty: 'easy' | 'medium' | 'hard' | 'mixed';
  timeLimit: number;
  questionSource: 'high_probability' | 'previous_year' | 'weak_areas' | 'mixed';
}

const TestsPage = () => {
  const router = useRouter();
  const [view, setView] = useState<'list' | 'config' | 'test' | 'results'>('list');
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Test configuration
  const [testConfig, setTestConfig] = useState<TestConfig>({
    subjectId: '',
    numQuestions: 25,
    difficulty: 'medium',
    timeLimit: 90,
    questionSource: 'mixed'
  });
  
  // Active test state
  const [activeTest, setActiveTest] = useState<MockTestResponse | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<{[key: string]: string}>({});
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [testResults, setTestResults] = useState<any>(null);

  // Fetch subjects on mount
  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await subjectService.getAll();
        setSubjects(data);
        
        // Auto-select first subject if available
        if (data.length > 0 && !testConfig.subjectId) {
          setTestConfig(prev => ({ ...prev, subjectId: data[0].id }));
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load subjects';
        setError(errorMessage);
        toast.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchSubjects();
  }, []);

  const handleConfigChange = (field: keyof TestConfig, value: string | number) => {
    setTestConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const startTest = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Create test via API
      const response = await apiClient.post<MockTestResponse>('/api/tests', {
        subject_id: testConfig.subjectId,
        num_questions: testConfig.numQuestions,
        difficulty: testConfig.difficulty,
        time_limit_minutes: testConfig.timeLimit,
        question_source: testConfig.questionSource
      });
      
      setActiveTest(response);
      setTimeRemaining(response.time_limit_minutes * 60);
      setView('test');
      setCurrentQuestion(0);
      setAnswers({});
      
      toast.success('Test created successfully!');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create test';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const goToNextQuestion = () => {
    if (activeTest && currentQuestion < activeTest.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    }
  };

  const goToPrevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  };

  const finishTest = async () => {
    if (!activeTest) return;
    
    try {
      setLoading(true);
      
      // Submit test via API
      const results = await apiClient.post(`/api/tests/${activeTest.test_id}/submit`, {
        answers: answers,
        end_time: new Date().toISOString()
      });
      
      setTestResults(results);
      setView('results');
      toast.success('Test submitted successfully!');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit test';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const timeColor = timeRemaining > 300 ? 'text-green-600' : timeRemaining > 120 ? 'text-orange-600' : 'text-red-600';

  // Loading state
  if (loading && view === 'list') {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
              <p className="mt-4 text-lg text-gray-600">Loading...</p>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Error state
  if (error && view === 'list') {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-red-800 mb-2">Error</h3>
            <p className="text-red-700">{error}</p>
            <Button 
              onClick={() => window.location.reload()} 
              className="mt-4"
              variant="outline"
            >
              Retry
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Test List View */}
        {view === 'list' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold">Mock Tests</h1>
              <Button 
                onClick={() => setView('config')}
                className="bg-indigo-600 hover:bg-indigo-700"
                disabled={subjects.length === 0}
              >
                Create New Test
              </Button>
            </div>

            {subjects.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <div className="text-4xl mb-4">📝</div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">No subjects found</h3>
                  <p className="text-gray-600 mb-4">Add subjects first to create mock tests</p>
                  <Button 
                    onClick={() => router.push('/subjects')}
                    className="bg-indigo-600 hover:bg-indigo-700"
                  >
                    Add Subjects
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <div className="text-4xl mb-4">📝</div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Ready to practice?</h3>
                  <p className="text-gray-600 mb-4">Create a mock test to assess your knowledge</p>
                  <Button 
                    onClick={() => setView('config')}
                    className="bg-indigo-600 hover:bg-indigo-700"
                  >
                    Start Mock Test
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Configuration View */}
        {view === 'config' && (
          <Card>
            <CardHeader>
              <CardTitle>Create Mock Test</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  {/* Subject Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Subject
                    </label>
                    <select
                      value={testConfig.subjectId}
                      onChange={(e) => handleConfigChange('subjectId', e.target.value)}
                      className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {subjects.map((subject) => (
                        <option key={subject.id} value={subject.id}>
                          {subject.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Number of Questions */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Number of Questions: {testConfig.numQuestions}
                    </label>
                    <input
                      type="range"
                      min="10"
                      max="50"
                      value={testConfig.numQuestions}
                      onChange={(e) => handleConfigChange('numQuestions', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>10</span>
                      <span>50</span>
                    </div>
                  </div>
                  
                  {/* Difficulty */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Difficulty Level
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {['easy', 'medium', 'hard', 'mixed'].map((level) => (
                        <button
                          key={level}
                          onClick={() => handleConfigChange('difficulty', level)}
                          className={`p-3 border rounded-lg capitalize transition-colors ${
                            testConfig.difficulty === level
                              ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                              : 'border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {level}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="space-y-6">
                  {/* Time Limit */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Time Limit
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {[30, 60, 90, 120].map((time) => (
                        <button
                          key={time}
                          onClick={() => handleConfigChange('timeLimit', time)}
                          className={`p-3 border rounded-lg transition-colors ${
                            testConfig.timeLimit === time
                              ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                              : 'border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {time} minutes
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Question Source */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Question Source
                    </label>
                    <div className="space-y-2">
                      {[
                        { value: 'high_probability', label: 'High-Probability Questions' },
                        { value: 'previous_year', label: 'Previous Year Papers' },
                        { value: 'weak_areas', label: 'Weak Areas Focus' },
                        { value: 'mixed', label: 'Mixed (Recommended)' }
                      ].map((source) => (
                        <div key={source.value} className="flex items-center">
                          <input
                            type="radio"
                            id={source.value}
                            name="questionSource"
                            checked={testConfig.questionSource === source.value}
                            onChange={() => handleConfigChange('questionSource', source.value)}
                            className="mr-3 h-4 w-4 text-indigo-600"
                          />
                          <label htmlFor={source.value} className="text-gray-700">
                            {source.label}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end gap-4 mt-8">
                <Button
                  variant="outline"
                  onClick={() => setView('list')}
                >
                  Cancel
                </Button>
                <Button
                  onClick={startTest}
                  disabled={loading || !testConfig.subjectId}
                  className="bg-indigo-600 hover:bg-indigo-700"
                >
                  {loading ? 'Creating...' : 'Start Test'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Test View */}
        {view === 'test' && activeTest && (
          <div className="bg-white rounded-lg shadow">
            {/* Header */}
            <div className="bg-gray-800 text-white p-4 flex justify-between items-center">
              <div>
                <span className="font-semibold">Mock Test</span>
                <span className="ml-4">
                  Question {currentQuestion + 1} of {activeTest.questions.length}
                </span>
              </div>
              <div className={`text-xl font-mono font-bold ${timeColor}`}>
                {formatTime(timeRemaining)}
              </div>
            </div>
            
            <div className="flex">
              {/* Question */}
              <div className="flex-1 p-6 border-r">
                {activeTest.questions[currentQuestion] && (
                  <>
                    <div className="flex justify-between items-center mb-6">
                      <div>
                        <span className="text-lg font-semibold">
                          Question {activeTest.questions[currentQuestion].number} 
                          [{activeTest.questions[currentQuestion].marks} marks]
                        </span>
                      </div>
                    </div>
                    
                    <div className="mb-8">
                      <p className="text-lg mb-6">{activeTest.questions[currentQuestion].text}</p>
                      
                      {activeTest.questions[currentQuestion].type === 'mcq' && activeTest.questions[currentQuestion].options && (
                        <div className="space-y-3">
                          {activeTest.questions[currentQuestion].options.map((option, idx) => (
                            <div key={idx} className="flex items-center">
                              <input
                                type="radio"
                                id={`option-${idx}`}
                                name={`question-${activeTest.questions[currentQuestion].id}`}
                                value={String.fromCharCode(65 + idx)}
                                checked={answers[activeTest.questions[currentQuestion].id] === String.fromCharCode(65 + idx)}
                                onChange={(e) => handleAnswerChange(activeTest.questions[currentQuestion].id, e.target.value)}
                                className="mr-3 h-4 w-4 text-indigo-600"
                              />
                              <label htmlFor={`option-${idx}`} className="text-gray-700">
                                {option}
                              </label>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {activeTest.questions[currentQuestion].type === 'descriptive' && (
                        <textarea
                          value={answers[activeTest.questions[currentQuestion].id] || ''}
                          onChange={(e) => handleAnswerChange(activeTest.questions[currentQuestion].id, e.target.value)}
                          placeholder="Type your answer here..."
                          className="w-full h-40 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      )}
                      
                      {activeTest.questions[currentQuestion].type === 'numerical' && (
                        <input
                          type="text"
                          value={answers[activeTest.questions[currentQuestion].id] || ''}
                          onChange={(e) => handleAnswerChange(activeTest.questions[currentQuestion].id, e.target.value)}
                          placeholder="Enter your answer..."
                          className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      )}
                    </div>
                    
                    <div className="flex justify-between">
                      <Button
                        variant="outline"
                        onClick={goToPrevQuestion}
                        disabled={currentQuestion === 0}
                      >
                        Previous
                      </Button>
                      
                      {currentQuestion === activeTest.questions.length - 1 ? (
                        <Button
                          onClick={finishTest}
                          disabled={loading}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          {loading ? 'Submitting...' : 'Submit Test'}
                        </Button>
                      ) : (
                        <Button
                          onClick={goToNextQuestion}
                          className="bg-indigo-600 hover:bg-indigo-700"
                        >
                          Next
                        </Button>
                      )}
                    </div>
                  </>
                )}
              </div>
              
              {/* Question Palette */}
              <div className="w-64 p-6 bg-gray-50">
                <h3 className="font-semibold mb-4">Questions</h3>
                <div className="grid grid-cols-5 gap-2 mb-6">
                  {activeTest.questions.map((question, index) => (
                    <button
                      key={question.id}
                      onClick={() => setCurrentQuestion(index)}
                      className={`p-2 rounded text-center text-sm ${
                        index === currentQuestion
                          ? 'bg-indigo-600 text-white'
                          : answers[question.id]
                            ? 'bg-green-500 text-white'
                            : 'bg-white border border-gray-300'
                      }`}
                    >
                      {question.number}
                    </button>
                  ))}
                </div>
                
                <div className="text-sm text-gray-600 space-y-2">
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-white border border-gray-300 mr-2 rounded"></div>
                    <span>Not answered</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-green-500 mr-2 rounded"></div>
                    <span>Answered</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-indigo-600 mr-2 rounded"></div>
                    <span>Current</span>
                  </div>
                </div>
                
                <div className="border-t pt-4 mt-4">
                  <p className="font-medium">Progress:</p>
                  <p className="text-2xl font-bold text-indigo-600">
                    {Object.keys(answers).length} / {activeTest.questions.length}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results View */}
        {view === 'results' && testResults && (
          <div className="space-y-6">
            <Card>
              <CardContent className="p-8 text-center">
                <h1 className="text-3xl font-bold mb-4">Test Results</h1>
                <div className="flex justify-center items-baseline mb-2">
                  <span className="text-5xl font-bold text-indigo-600">
                    {testResults.score}
                  </span>
                  <span className="text-2xl text-gray-600 mx-2">/</span>
                  <span className="text-2xl text-gray-600">{testResults.total_marks}</span>
                </div>
                <p className="text-xl text-gray-600">{testResults.percentage}%</p>
                <p className="text-gray-500 mt-2">
                  Completed on {new Date().toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
            
            <div className="flex flex-wrap gap-4 justify-center">
              <Button
                onClick={() => setView('list')}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                Take Another Test
              </Button>
              <Button
                variant="outline"
                onClick={() => router.push('/protected')}
              >
                Back to Dashboard
              </Button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default TestsPage;
