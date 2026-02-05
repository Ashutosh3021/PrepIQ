'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Star, BookOpen, Clock, TrendingUp } from 'lucide-react';

const QuestionsPage = () => {
  const importantQuestions = [
    {
      id: 1,
      subject: 'Linear Algebra',
      topic: 'Eigenvalues and Eigenvectors',
      question: 'Find the eigenvalues of the matrix A = [[3, 1], [0, 2]]',
      difficulty: 'Medium',
      importance: 'High',
      last_asked: '2025-12-15'
    },
    {
      id: 2,
      subject: 'Calculus',
      topic: 'Definite Integrals',
      question: 'Evaluate ∫₀¹ x² dx using fundamental theorem',
      difficulty: 'Easy',
      importance: 'Very High',
      last_asked: '2025-12-20'
    },
    {
      id: 3,
      subject: 'Physics',
      topic: 'Newton\'s Laws',
      question: 'A 5kg block is pulled with 20N force on frictionless surface. Find acceleration.',
      difficulty: 'Medium',
      importance: 'High',
      last_asked: '2025-12-18'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Important Questions</h1>
        <p className="text-gray-600">High probability questions for your upcoming exams</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Questions</CardTitle>
            <Star className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">Across all subjects</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Priority</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">Very likely to appear</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Practice Time</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.5h</div>
            <p className="text-xs text-muted-foreground">Recommended study time</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        {importantQuestions.map((question) => (
          <Card key={question.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{question.subject}</CardTitle>
                  <p className="text-sm text-muted-foreground">{question.topic}</p>
                </div>
                <div className="flex gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    question.importance === 'Very High' 
                      ? 'bg-red-100 text-red-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {question.importance}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    question.difficulty === 'Easy' 
                      ? 'bg-green-100 text-green-800' 
                      : question.difficulty === 'Medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {question.difficulty}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 mb-4">{question.question}</p>
              <div className="flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  Last asked: {new Date(question.last_asked).toLocaleDateString()}
                </p>
                <Button variant="outline" size="sm">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Practice Now
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default QuestionsPage;