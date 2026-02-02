'use client';

import React, { useState } from 'react';
import DashboardLayout from '@/src/components/dashboard/DashboardLayout';

const PredictionsPage = () => {
  const [activeTab, setActiveTab] = useState('predictions');
  const [expandedQuestions, setExpandedQuestions] = useState<{[key: string]: boolean}>({});

  const toggleQuestion = (id: string) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Mock data for predictions
  const predictionData = {
    confidence: 85,
    summary: "Covers 95% of likely topics",
    questions: [
      {
        id: 'q1',
        number: 1,
        text: "Explain the concept of eigenvalues and eigenvectors. Provide an example with a 2x2 matrix.",
        marks: 10,
        unit: "Linear Transformations",
        probability: "very_high",
        appearedIn: [2020, 2022, 2024],
        difficulty: "Medium",
        expectedAnswer: "Eigenvalues and eigenvectors are fundamental concepts in linear algebra..."
      },
      {
        id: 'q2',
        number: 2,
        text: "Define the rank of a matrix and explain its properties.",
        marks: 5,
        unit: "Matrix Theory",
        probability: "high",
        appearedIn: [2021, 2023],
        difficulty: "Easy",
        expectedAnswer: "The rank of a matrix is defined as..."
      },
      {
        id: 'q3',
        number: 3,
        text: "Solve the system of linear equations using Gaussian elimination method.",
        marks: 5,
        unit: "Systems of Equations",
        probability: "moderate",
        appearedIn: [2022],
        difficulty: "Hard",
        expectedAnswer: "To solve using Gaussian elimination..."
      }
    ],
    topicHeatmap: [
      { unit: "Matrix Theory", veryHigh: 4, high: 2, moderate: 1 },
      { unit: "Linear Transformations", veryHigh: 3, high: 3, moderate: 0 },
      { unit: "Systems of Equations", veryHigh: 2, high: 4, moderate: 2 },
      { unit: "Vector Spaces", veryHigh: 1, high: 2, moderate: 3 }
    ],
    studyRecommendations: [
      "Focus on Unit 1 (Matrix Theory) - appears in 45% of papers",
      "Unit 2 (Linear Transformations) is important - appears in 30% of papers",
      "Day 1-5: Deep dive into Matrix Theory",
      "Day 6-8: Linear Transformations concepts",
      "Day 9-10: Revision and mock tests"
    ]
  };

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold">Predicted Question Paper - Linear Algebra</h1>
              <p className="text-gray-600">Generated Jan 5, 2025 • Confidence: {predictionData.confidence}%</p>
              <p className="text-teal-600 font-semibold">{predictionData.summary}</p>
            </div>
            
            <div className="flex space-x-2">
              <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300">
                Download PDF
              </button>
              <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300">
                Download Excel
              </button>
              <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300">
                Print
              </button>
              <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300">
                Share
              </button>
              <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300">
                View Analysis
              </button>
            </div>
          </div>
        </div>

        {/* Confidence Indicator */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-center">
            <div className="relative w-48 h-48">
              {/* Circular progress ring */}
              <svg className="w-full h-full" viewBox="0 0 100 100">
                {/* Background circle */}
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="#e5e7eb"
                  strokeWidth="8"
                />
                {/* Progress circle */}
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="#208091"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${predictionData.confidence} ${100 - predictionData.confidence}`}
                  strokeDashoffset="25"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold">{predictionData.confidence}%</span>
                <span className="text-gray-600">Confidence</span>
              </div>
            </div>
            
            <div className="ml-8">
              <h3 className="text-lg font-semibold mb-2">Confidence Breakdown</h3>
              <p>Based on analysis of 5 previous year papers</p>
              <div className="mt-4 space-y-2">
                <p>Very High Probability: 15 questions</p>
                <p>High Probability: 25 questions</p>
                <p>Moderate Probability: 10 questions</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recommended Strategy */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">📋 Study Recommendation</h2>
          <div className="space-y-2">
            <p className="font-semibold text-red-600">1. Unit 3 (45% weightage) - FOCUS HERE</p>
            <p className="font-semibold text-orange-500">2. Unit 2 (30% weightage) - Important</p>
            <p className="font-semibold text-yellow-500">3. Unit 1 (25% weightage) - Standard</p>
          </div>
          
          <div className="mt-4">
            <h3 className="font-semibold">Time allocation:</h3>
            <p>10 days till exam?</p>
            <ul className="list-disc pl-5 mt-1">
              <li>Day 1-5: Deep dive into Unit 3</li>
              <li>Day 6-8: Unit 2 concepts + practice</li>
              <li>Day 9-10: Revision + full mock tests</li>
            </ul>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b mb-6">
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'predictions' 
                ? 'border-b-2 border-teal-600 text-teal-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('predictions')}
          >
            Predicted Questions
          </button>
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'heatmap' 
                ? 'border-b-2 border-teal-600 text-teal-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('heatmap')}
          >
            Topic Heatmap
          </button>
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'matrix' 
                ? 'border-b-2 border-teal-600 text-teal-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('matrix')}
          >
            Priority Matrix
          </button>
        </div>

        {/* Predicted Questions by Section */}
        {activeTab === 'predictions' && (
          <div className="space-y-6">
            {/* Part A - 2 Mark Questions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">SECTION 1: Part A (2-Mark Questions) - Total: 30 marks</h3>
              <p>Probability breakdown: Very High: 6, High: 3, Moderate: 1</p>
              
              {predictionData.questions.filter(q => q.marks === 2).map((question) => (
                <div key={question.id} className="border rounded-lg mb-4">
                  <div 
                    className="p-4 cursor-pointer flex justify-between items-center"
                    onClick={() => toggleQuestion(question.id)}
                  >
                    <div className="flex items-center">
                      <span className="mr-2">Q{question.number}</span>
                      {question.probability === 'very_high' && <span className="text-red-500 mr-2">🔴</span>}
                      {question.probability === 'high' && <span className="text-orange-500 mr-2">🟠</span>}
                      {question.probability === 'moderate' && <span className="text-yellow-500 mr-2">🟡</span>}
                      <span>Probability: {question.probability}</span>
                    </div>
                    <span>{expandedQuestions[question.id] ? '▲' : '▼'}</span>
                  </div>
                  
                  {expandedQuestions[question.id] && (
                    <div className="p-4 border-t">
                      <p className="mb-2"><strong>Question:</strong> {question.text}</p>
                      <p className="mb-2"><strong>Unit:</strong> {question.unit}</p>
                      <p className="mb-2"><strong>Appeared in:</strong> {question.appearedIn.join(', ')} ({question.appearedIn.length} times)</p>
                      <p className="mb-2"><strong>Difficulty:</strong> {question.difficulty}</p>
                      <p className="mb-2"><strong>Expected answer:</strong> {question.expectedAnswer}</p>
                      <button className="text-teal-600 hover:underline">Add to revision</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {/* Part B - 5 Mark Questions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">SECTION 2: Part B (5-Mark Questions) - Total: 40 marks</h3>
              <p>Probability breakdown: Very High: 4, High: 4, Moderate: 2</p>
              
              {predictionData.questions.filter(q => q.marks === 5).map((question) => (
                <div key={question.id} className="border rounded-lg mb-4">
                  <div 
                    className="p-4 cursor-pointer flex justify-between items-center"
                    onClick={() => toggleQuestion(question.id)}
                  >
                    <div className="flex items-center">
                      <span className="mr-2">Q{question.number}</span>
                      {question.probability === 'very_high' && <span className="text-red-500 mr-2">🔴</span>}
                      {question.probability === 'high' && <span className="text-orange-500 mr-2">🟠</span>}
                      {question.probability === 'moderate' && <span className="text-yellow-500 mr-2">🟡</span>}
                      <span>Probability: {question.probability}</span>
                    </div>
                    <span>{expandedQuestions[question.id] ? '▲' : '▼'}</span>
                  </div>
                  
                  {expandedQuestions[question.id] && (
                    <div className="p-4 border-t">
                      <p className="mb-2"><strong>Question:</strong> {question.text}</p>
                      <p className="mb-2"><strong>Unit:</strong> {question.unit}</p>
                      <p className="mb-2"><strong>Appeared in:</strong> {question.appearedIn.join(', ')} ({question.appearedIn.length} times)</p>
                      <p className="mb-2"><strong>Difficulty:</strong> {question.difficulty}</p>
                      <p className="mb-2"><strong>Expected answer:</strong> {question.expectedAnswer}</p>
                      <button className="text-teal-600 hover:underline">Add to revision</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {/* Part C - 10 Mark Questions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">SECTION 3: Part C (10-Mark Questions) - Total: 30 marks</h3>
              <p>Probability breakdown: Very High: 2, High: 1, Moderate: 1</p>
              
              {predictionData.questions.filter(q => q.marks === 10).map((question) => (
                <div key={question.id} className="border rounded-lg mb-4">
                  <div 
                    className="p-4 cursor-pointer flex justify-between items-center"
                    onClick={() => toggleQuestion(question.id)}
                  >
                    <div className="flex items-center">
                      <span className="mr-2">Q{question.number}</span>
                      {question.probability === 'very_high' && <span className="text-red-500 mr-2">🔴</span>}
                      {question.probability === 'high' && <span className="text-orange-500 mr-2">🟠</span>}
                      {question.probability === 'moderate' && <span className="text-yellow-500 mr-2">🟡</span>}
                      <span>Probability: {question.probability}</span>
                    </div>
                    <span>{expandedQuestions[question.id] ? '▲' : '▼'}</span>
                  </div>
                  
                  {expandedQuestions[question.id] && (
                    <div className="p-4 border-t">
                      <p className="mb-2"><strong>Question:</strong> {question.text}</p>
                      <p className="mb-2"><strong>Unit:</strong> {question.unit}</p>
                      <p className="mb-2"><strong>Appeared in:</strong> {question.appearedIn.join(', ')} ({question.appearedIn.length} times)</p>
                      <p className="mb-2"><strong>Difficulty:</strong> {question.difficulty}</p>
                      <p className="mb-2"><strong>Expected answer:</strong> {question.expectedAnswer}</p>
                      <button className="text-teal-600 hover:underline">Add to revision</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Topic Heatmap */}
        {activeTab === 'heatmap' && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Topic Probability Heatmap</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Very High</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">High</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Moderate</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {predictionData.topicHeatmap.map((row, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap font-medium">{row.unit}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-32 bg-gray-200 rounded-full h-2.5 mr-2">
                            <div 
                              className="bg-red-500 h-2.5 rounded-full" 
                              style={{ width: `${row.veryHigh * 20}%` }}
                            ></div>
                          </div>
                          <span>{row.veryHigh}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-32 bg-gray-200 rounded-full h-2.5 mr-2">
                            <div 
                              className="bg-orange-500 h-2.5 rounded-full" 
                              style={{ width: `${row.high * 20}%` }}
                            ></div>
                          </div>
                          <span>{row.high}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-32 bg-gray-200 rounded-full h-2.5 mr-2">
                            <div 
                              className="bg-yellow-500 h-2.5 rounded-full" 
                              style={{ width: `${row.moderate * 20}%` }}
                            ></div>
                          </div>
                          <span>{row.moderate}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Priority Matrix */}
        {activeTab === 'matrix' && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Study Priority Matrix</h2>
            <div className="h-96 border rounded-lg flex items-center justify-center">
              <p>2D plot showing frequency vs importance of topics</p>
              <p>Placeholder for priority matrix visualization</p>
            </div>
          </div>
        )}

        {/* Next Steps */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">What to do next?</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold">Take a mock test</h3>
              <button className="mt-2 w-full bg-purple-100 text-purple-700 py-2 rounded hover:bg-purple-200">
                Start Mock Test
              </button>
            </div>
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold">Chat with AI</h3>
              <button className="mt-2 w-full bg-blue-100 text-blue-700 py-2 rounded hover:bg-blue-200">
                Ask Study Buddy
              </button>
            </div>
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold">View detailed analysis</h3>
              <button className="mt-2 w-full bg-yellow-100 text-yellow-700 py-2 rounded hover:bg-yellow-200">
                Trend Report
              </button>
            </div>
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold">Download full report</h3>
              <button className="mt-2 w-full bg-green-100 text-green-700 py-2 rounded hover:bg-green-200">
                Export PDF
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default PredictionsPage;