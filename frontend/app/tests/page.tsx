'use client';

import React, { useState } from 'react';
import DashboardLayout from '@/src/components/dashboard/DashboardLayout';

const TestsPage = () => {
  const [view, setView] = useState<'config' | 'test' | 'results'>('config');
  const [testConfig, setTestConfig] = useState({
    numQuestions: 25,
    difficulty: 'medium',
    timeLimit: 90,
    questionSource: 'mixed'
  });
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<{[key: number]: string}>({});
  const [testStarted, setTestStarted] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(testConfig.timeLimit * 60); // in seconds

  // Mock test data
  const mockTest = {
    id: 'test-1',
    subject: 'Linear Algebra',
    totalQuestions: 25,
    totalMarks: 100,
    questions: [
      {
        id: 1,
        number: 1,
        text: "What is the determinant of the matrix [[2, 3], [1, 4]]?",
        marks: 2,
        unit: "Matrix Theory",
        type: "mcq",
        options: ["A) 5", "B) 8", "C) 11", "D) 6"],
        correctAnswer: "A"
      },
      {
        id: 2,
        number: 2,
        text: "Explain the concept of eigenvalues and eigenvectors.",
        marks: 10,
        unit: "Linear Transformations",
        type: "descriptive",
        correctAnswer: "Eigenvalues and eigenvectors are fundamental concepts..."
      },
      {
        id: 3,
        text: "Solve the system of linear equations: 2x + 3y = 7, x - y = 1",
        marks: 5,
        unit: "Systems of Equations",
        type: "numerical",
        correctAnswer: "x = 2, y = 1"
      }
    ]
  };

  const handleConfigChange = (field: string, value: string | number) => {
    setTestConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const startTest = () => {
    setTestStarted(true);
    setView('test');
    // Start timer
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          finishTest();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleAnswerChange = (questionId: number, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const goToNextQuestion = () => {
    if (currentQuestion < mockTest.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    }
  };

  const goToPrevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  };

  const finishTest = () => {
    setView('results');
  };

  const submitTest = () => {
    finishTest();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const timeColor = timeRemaining > 300 ? 'text-green-600' : timeRemaining > 120 ? 'text-orange-600' : 'text-red-600';

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {view === 'config' && (
          <div className="bg-white rounded-lg shadow p-8">
            <h1 className="text-2xl font-bold mb-6">Create Mock Test - {mockTest.subject}</h1>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <div className="mb-6">
                  <label className="block text-gray-700 mb-2">Number of Questions</label>
                  <div className="flex items-center">
                    <input
                      type="range"
                      min="10"
                      max="50"
                      value={testConfig.numQuestions}
                      onChange={(e) => handleConfigChange('numQuestions', parseInt(e.target.value))}
                      className="w-full mr-4"
                    />
                    <span className="text-lg font-semibold w-12">{testConfig.numQuestions}</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Selected: {testConfig.numQuestions} questions</p>
                </div>
                
                <div className="mb-6">
                  <label className="block text-gray-700 mb-2">Difficulty Level</label>
                  <div className="grid grid-cols-2 gap-4">
                    {['Easy', 'Medium', 'Hard', 'Mixed'].map((level) => (
                      <button
                        key={level}
                        onClick={() => handleConfigChange('difficulty', level.toLowerCase())}
                        className={`p-3 border rounded-lg ${
                          testConfig.difficulty === level.toLowerCase()
                            ? 'border-teal-600 bg-teal-50 text-teal-700'
                            : 'border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div className="mb-6">
                  <label className="block text-gray-700 mb-2">Time Limit</label>
                  <div className="grid grid-cols-3 gap-4">
                    {[30, 60, 90, 120].map((time) => (
                      <button
                        key={time}
                        onClick={() => handleConfigChange('timeLimit', time)}
                        className={`p-3 border rounded-lg ${
                          testConfig.timeLimit === time
                            ? 'border-teal-600 bg-teal-50 text-teal-700'
                            : 'border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {time} minutes
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              
              <div>
                <div className="mb-6">
                  <label className="block text-gray-700 mb-2">Question Source</label>
                  <div className="space-y-3">
                    {[
                      { value: 'high_probability', label: '⭐ High-Probability (from predictions)' },
                      { value: 'previous_year', label: '📚 Previous Year Papers' },
                      { value: 'weak_areas', label: '🎯 Weak Areas (topics you scored low in)' },
                      { value: 'mixed', label: '🔀 Mixed' }
                    ].map((source) => (
                      <div key={source.value} className="flex items-center">
                        <input
                          type="radio"
                          id={source.value}
                          name="questionSource"
                          checked={testConfig.questionSource === source.value}
                          onChange={() => handleConfigChange('questionSource', source.value)}
                          className="mr-2"
                        />
                        <label htmlFor={source.value} className="text-gray-700">
                          {source.label} {source.value === 'mixed' && '[default]'}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <p className="text-blue-800">
                    Questions generated based on your predictions and past performance
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end mt-8">
              <button
                onClick={startTest}
                className="bg-teal-600 text-white px-8 py-3 rounded-lg hover:bg-teal-700 font-semibold"
              >
                Start Mock Test
              </button>
            </div>
          </div>
        )}
        
        {view === 'test' && (
          <div className="bg-white rounded-lg shadow">
            {/* Top Bar */}
            <div className="bg-gray-800 text-white p-4 flex justify-between items-center">
              <div>
                <span className="font-semibold">Mock Test #5 - {mockTest.subject}</span>
                <span className="ml-4">Question {currentQuestion + 1} of {mockTest.questions.length}</span>
              </div>
              <div className={`text-xl font-mono font-bold ${timeColor}`}>
                {formatTime(timeRemaining)}
              </div>
              <div className="flex space-x-3">
                <button className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded">
                  Save & Exit
                </button>
                <button className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded">
                  Settings
                </button>
              </div>
            </div>
            
            <div className="flex">
              {/* Question Section */}
              <div className="w-2/3 p-6 border-r">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <span className="text-lg font-semibold">
                      Question {mockTest.questions[currentQuestion].number} [{mockTest.questions[currentQuestion].marks} marks]
                    </span>
                    <span className="ml-4 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                      {mockTest.questions[currentQuestion].unit}
                    </span>
                  </div>
                  <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
                    {currentQuestion + 1} of {mockTest.questions.length}
                  </span>
                </div>
                
                <div className="mb-8">
                  <p className="text-lg mb-4">{mockTest.questions[currentQuestion].text}</p>
                  
                  {mockTest.questions[currentQuestion].type === 'mcq' && (
                    <div className="space-y-3">
                      {(mockTest.questions[currentQuestion].options as string[]).map((option, idx) => (
                        <div key={idx} className="flex items-center">
                          <input
                            type="radio"
                            id={`option-${idx}`}
                            name={`question-${mockTest.questions[currentQuestion].id}`}
                            value={String.fromCharCode(65 + idx)} // A, B, C, D
                            checked={answers[mockTest.questions[currentQuestion].id] === String.fromCharCode(65 + idx)}
                            onChange={(e) => handleAnswerChange(mockTest.questions[currentQuestion].id, e.target.value)}
                            className="mr-2"
                          />
                          <label htmlFor={`option-${idx}`} className="text-gray-700">
                            {option}
                          </label>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {mockTest.questions[currentQuestion].type === 'descriptive' && (
                    <textarea
                      value={answers[mockTest.questions[currentQuestion].id] || ''}
                      onChange={(e) => handleAnswerChange(mockTest.questions[currentQuestion].id, e.target.value)}
                      placeholder="Type your answer here..."
                      className="w-full h-40 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-300"
                    />
                  )}
                  
                  {mockTest.questions[currentQuestion].type === 'numerical' && (
                    <input
                      type="text"
                      value={answers[mockTest.questions[currentQuestion].id] || ''}
                      onChange={(e) => handleAnswerChange(mockTest.questions[currentQuestion].id, e.target.value)}
                      placeholder="Enter your answer..."
                      className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-300"
                    />
                  )}
                </div>
                
                <div className="flex justify-between">
                  <button
                    onClick={goToPrevQuestion}
                    disabled={currentQuestion === 0}
                    className={`px-4 py-2 rounded ${
                      currentQuestion === 0
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    &lt; Previous
                  </button>
                  
                  <div className="flex space-x-2">
                    <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                      Mark for Review
                    </button>
                    <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                      Clear Answer
                    </button>
                  </div>
                  
                  <button
                    onClick={goToNextQuestion}
                    disabled={currentQuestion === mockTest.questions.length - 1}
                    className={`px-4 py-2 rounded ${
                      currentQuestion === mockTest.questions.length - 1
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Next &gt;
                  </button>
                </div>
              </div>
              
              {/* Question Navigation */}
              <div className="w-1/3 p-6">
                <h3 className="text-lg font-semibold mb-4">Question Palette</h3>
                
                <div className="grid grid-cols-5 gap-2 mb-6">
                  {mockTest.questions.map((question, index) => (
                    <button
                      key={question.id}
                      onClick={() => setCurrentQuestion(index)}
                      className={`p-2 rounded text-center text-sm ${
                        index === currentQuestion
                          ? 'bg-teal-600 text-white border-2 border-teal-700'
                          : answers[question.id]
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-200 text-gray-700'
                      }`}
                    >
                      {question.number}
                    </button>
                  ))}
                </div>
                
                <div className="text-sm text-gray-600 mb-4">
                  <div className="flex items-center mb-1">
                    <div className="w-4 h-4 bg-white border border-gray-300 mr-2"></div>
                    <span>Not answered</span>
                  </div>
                  <div className="flex items-center mb-1">
                    <div className="w-4 h-4 bg-blue-500 mr-2"></div>
                    <span>Answered</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-orange-500 mr-2"></div>
                    <span>Marked for Review</span>
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <p className="font-medium">Summary:</p>
                  <p>Answered: {Object.keys(answers).length} / {mockTest.questions.length}</p>
                  <p>Not answered: {mockTest.questions.length - Object.keys(answers).length}</p>
                  <p>Marked: 0</p>
                  <p className="text-red-600 mt-2">Complete all questions before submitting</p>
                </div>
                
                <button
                  onClick={submitTest}
                  className="w-full mt-6 bg-teal-600 text-white py-3 rounded-lg hover:bg-teal-700 font-semibold"
                >
                  Review & Submit
                </button>
              </div>
            </div>
          </div>
        )}
        
        {view === 'results' && (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-800">Test Results</h1>
              <div className="flex justify-center items-baseline mt-4">
                <span className="text-5xl font-bold text-teal-600">72</span>
                <span className="text-2xl text-gray-600 mx-2">/</span>
                <span className="text-2xl text-gray-600">100</span>
              </div>
              <p className="text-xl text-gray-600 mt-2">72%</p>
              <p className="text-lg text-gray-500">Grade: B+</p>
              <p className="text-gray-500">Attempt #5 • Jan 5, 2025 • 45 mins</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div className="border rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Score Comparison</h3>
                <div className="space-y-2">
                  <p>Your score: <span className="font-semibold">72</span></p>
                  <p>Class average: <span className="font-semibold">75</span></p>
                  <p>Your best: <span className="font-semibold">85</span></p>
                  <p>Previous: <span className="font-semibold text-green-600">68 (↑ +4 points!)</span></p>
                </div>
              </div>
              
              <div className="border rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Performance vs Predicted</h3>
                <div className="space-y-2">
                  <p>Predictions Accuracy: <span className="font-semibold text-green-600">90%</span></p>
                  <p>Of 25 predicted questions, <span className="font-semibold">22</span> were similar to actual</p>
                  <p className="font-semibold text-green-600">Recommendation: 95% ready for exam!</p>
                </div>
              </div>
            </div>
            
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4">Question Analysis</h2>
              <div className="space-y-4">
                {mockTest.questions.map((question, index) => (
                  <div key={question.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center">
                        <span className="font-semibold mr-3">Q{question.number} [{question.marks} marks]</span>
                        {index % 3 === 0 ? (
                          <span className="text-green-600 font-semibold">✅ Correct</span>
                        ) : index % 3 === 1 ? (
                          <span className="text-red-600 font-semibold">❌ Incorrect</span>
                        ) : (
                          <span className="text-yellow-600 font-semibold">⏭️ Skipped</span>
                        )}
                      </div>
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                        {question.unit}
                      </span>
                    </div>
                    
                    <div className="mt-3 pl-6">
                      <p><strong>Your answer:</strong> {answers[question.id] || 'No answer provided'}</p>
                      <p><strong>Correct answer:</strong> {question.correctAnswer}</p>
                      <p className="text-sm text-gray-600 mt-2">Explanation: This question tests your understanding of fundamental concepts in {question.unit.toLowerCase()}.</p>
                      <div className="mt-2">
                        <button className="text-teal-600 hover:underline text-sm mr-4">🎯 Practice this topic</button>
                        <button className="text-blue-600 hover:underline text-sm">📚 View in notes</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4">Performance Insights</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold mb-3">Accuracy by topic</h3>
                  <ul className="space-y-2">
                    <li className="flex justify-between">
                      <span>Matrix Theory:</span>
                      <span className="font-semibold text-green-600">80% (4/5 correct)</span>
                    </li>
                    <li className="flex justify-between">
                      <span>Linear Transformations:</span>
                      <span className="font-semibold text-red-600">60% (3/5 correct) [Weak]</span>
                    </li>
                    <li className="flex justify-between">
                      <span>Systems of Equations:</span>
                      <span className="font-semibold text-green-600">100% (3/3 correct) [Strong]</span>
                    </li>
                  </ul>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold mb-3">Accuracy by question type</h3>
                  <ul className="space-y-2">
                    <li className="flex justify-between">
                      <span>2-mark questions:</span>
                      <span className="font-semibold">90% (9/10)</span>
                    </li>
                    <li className="flex justify-between">
                      <span>5-mark questions:</span>
                      <span className="font-semibold">70% (7/10)</span>
                    </li>
                    <li className="flex justify-between">
                      <span>10-mark questions:</span>
                      <span className="font-semibold text-red-600">50% (2/4) [Needs improvement]</span>
                    </li>
                  </ul>
                </div>
              </div>
              
              <div className="border rounded-lg p-4 mt-4">
                <h3 className="font-semibold mb-3">Weak areas identified</h3>
                <div className="flex flex-wrap gap-2">
                  <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full flex items-center">
                    🔴 Linear Transformations
                  </span>
                  <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full flex items-center">
                    🟠 Eigenvalues
                  </span>
                  <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full flex items-center">
                    🟡 Complex Problems
                  </span>
                </div>
                <p className="mt-2">Recommendation: Take targeted practice on these topics</p>
              </div>
            </div>
            
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4">What to do next?</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold flex items-center">
                    <span className="text-2xl mr-2">🎯</span> Practice Weak Topics
                  </h3>
                  <button className="mt-2 w-full bg-red-100 text-red-700 py-2 rounded hover:bg-red-200">
                    View weak-area questions
                  </button>
                </div>
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold flex items-center">
                    <span className="text-2xl mr-2">💬</span> Chat with Study Buddy
                  </h3>
                  <button className="mt-2 w-full bg-blue-100 text-blue-700 py-2 rounded hover:bg-blue-200">
                    Ask about Linear Transformations
                  </button>
                </div>
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold flex items-center">
                    <span className="text-2xl mr-2">📝</span> Take targeted mock test
                  </h3>
                  <button className="mt-2 w-full bg-purple-100 text-purple-700 py-2 rounded hover:bg-purple-200">
                    Create Linear Transformations-focused test
                  </button>
                </div>
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold flex items-center">
                    <span className="text-2xl mr-2">📊</span> View trend analysis
                  </h3>
                  <button className="mt-2 w-full bg-yellow-100 text-yellow-700 py-2 rounded hover:bg-yellow-200">
                    See difficulty distribution
                  </button>
                </div>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-4">
              <button className="px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium">
                Take Another Test
              </button>
              <button className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium">
                Review Solutions
              </button>
              <button className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium">
                Practice Weak Topics
              </button>
              <button className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium">
                Download Report
              </button>
              <button className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium">
                Share Results
              </button>
              <button className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium">
                Back to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default TestsPage;