"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Repeat, 
  TrendingUp, 
  Target, 
  Calendar, 
  Bookmark, 
  Share2,
  Filter,
  Loader2
} from 'lucide-react';
import { api } from '@/lib/api';

interface ImportantQuestionsProps {
  subjectId: string;
  subjectName: string;
}

export default function ImportantQuestions({ subjectId, subjectName }: ImportantQuestionsProps) {
  const [questions, setQuestions] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchImportantQuestions();
  }, [subjectId]);

  const fetchImportantQuestions = async () => {
    try {
      const response = await api.get(`/analysis/important-questions/${subjectId}`);
      setQuestions(response.data);
    } catch (error) {
      console.error('Error fetching questions:', error);
      // Use sample data
      setQuestions({
        most_repeating: [
          {
            question: "State and explain Ohm's Law with its mathematical expression",
            appearances: 5,
            years: [2020, 2021, 2022, 2023, 2024],
            marks: 5,
            unit: "Unit 1",
            type: "theory"
          },
          {
            question: "Explain the working principle of PN junction diode",
            appearances: 4,
            years: [2021, 2022, 2023, 2024],
            marks: 10,
            unit: "Unit 3",
            type: "theory"
          },
          {
            question: "Calculate total resistance in series and parallel combination",
            appearances: 4,
            years: [2020, 2022, 2023, 2024],
            marks: 5,
            unit: "Unit 2",
            type: "numerical"
          },
          {
            question: "Draw and explain V-I characteristics of Zener diode",
            appearances: 3,
            years: [2021, 2023, 2024],
            marks: 10,
            unit: "Unit 3",
            type: "diagram"
          }
        ],
        high_probability: [
          {
            question: "Explain Kirchhoff's Voltage and Current Laws with examples",
            probability: 85,
            reason: "Appeared 3 times in last 5 years",
            marks: 10,
            unit: "Unit 2",
            type: "theory"
          },
          {
            question: "Describe applications of diodes in rectifier circuits",
            probability: 80,
            reason: "Trending topic, appears consistently",
            marks: 10,
            unit: "Unit 3",
            type: "theory"
          },
          {
            question: "Solve circuit using nodal analysis method",
            probability: 75,
            reason: "Common numerical pattern",
            marks: 10,
            unit: "Unit 2",
            type: "numerical"
          },
          {
            question: "Explain construction and working of LED",
            probability: 70,
            reason: "Emerging topic, appeared twice recently",
            marks: 5,
            unit: "Unit 3",
            type: "theory"
          }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const getTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      theory: 'bg-blue-100 text-blue-800',
      numerical: 'bg-green-100 text-green-800',
      diagram: 'bg-purple-100 text-purple-800'
    };
    return styles[type] || 'bg-gray-100 text-gray-800';
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 80) return 'text-green-600';
    if (probability >= 60) return 'text-blue-600';
    return 'text-amber-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Most Repeating</p>
                <p className="text-2xl font-bold text-blue-600">
                  {questions?.most_repeating?.length || 0}
                </p>
              </div>
              <Repeat className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">High Probability</p>
                <p className="text-2xl font-bold text-green-600">
                  {questions?.high_probability?.length || 0}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Important</p>
                <p className="text-2xl font-bold text-purple-600">
                  {(questions?.most_repeating?.length || 0) + (questions?.high_probability?.length || 0)}
                </p>
              </div>
              <Target className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter Buttons */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-500" />
        <Button 
          variant={filter === 'all' ? 'default' : 'outline'} 
          size="sm"
          onClick={() => setFilter('all')}
        >
          All
        </Button>
        <Button 
          variant={filter === 'theory' ? 'default' : 'outline'} 
          size="sm"
          onClick={() => setFilter('theory')}
        >
          Theory
        </Button>
        <Button 
          variant={filter === 'numerical' ? 'default' : 'outline'} 
          size="sm"
          onClick={() => setFilter('numerical')}
        >
          Numerical
        </Button>
        <Button 
          variant={filter === 'diagram' ? 'default' : 'outline'} 
          size="sm"
          onClick={() => setFilter('diagram')}
        >
          Diagram
        </Button>
      </div>

      {/* Tabs for Questions */}
      <Tabs defaultValue="repeating" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="repeating" className="flex items-center gap-2">
            <Repeat className="w-4 h-4" />
            Most Repeating
          </TabsTrigger>
          <TabsTrigger value="probability" className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            High Probability
          </TabsTrigger>
        </TabsList>

        {/* Most Repeating Tab */}
        <TabsContent value="repeating">
          <Card>
            <CardHeader>
              <CardTitle>Questions That Appear Most Frequently</CardTitle>
              <CardDescription>
                These questions have appeared multiple times in previous exams
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {questions?.most_repeating
                  ?.filter((q: any) => filter === 'all' || q.type === filter)
                  ?.map((question: any, index: number) => (
                  <div 
                    key={index} 
                    className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium text-gray-500">
                            #{index + 1}
                          </span>
                          <Badge className={getTypeBadge(question.type)}>
                            {question.type}
                          </Badge>
                          <Badge variant="outline">{question.marks} marks</Badge>
                          <Badge variant="secondary">{question.unit}</Badge>
                        </div>
                        <h4 className="font-medium text-gray-900 mb-3">
                          {question.question}
                        </h4>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Repeat className="w-4 h-4 text-blue-600" />
                            <span className="font-medium text-blue-600">
                              {question.appearances} appearances
                            </span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            <span>Years: {question.years.join(', ')}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Button variant="ghost" size="icon">
                          <Bookmark className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon">
                          <Share2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* High Probability Tab */}
        <TabsContent value="probability">
          <Card>
            <CardHeader>
              <CardTitle>Questions with Highest Probability</CardTitle>
              <CardDescription>
                AI-predicted questions likely to appear in upcoming exams
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {questions?.high_probability
                  ?.filter((q: any) => filter === 'all' || q.type === filter)
                  ?.map((question: any, index: number) => (
                  <div 
                    key={index} 
                    className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium text-gray-500">
                            #{index + 1}
                          </span>
                          <Badge className={getTypeBadge(question.type)}>
                            {question.type}
                          </Badge>
                          <Badge variant="outline">{question.marks} marks</Badge>
                          <Badge variant="secondary">{question.unit}</Badge>
                        </div>
                        <h4 className="font-medium text-gray-900 mb-3">
                          {question.question}
                        </h4>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-1">
                            <Target className={`w-4 h-4 ${getProbabilityColor(question.probability)}`} />
                            <span className={`font-bold ${getProbabilityColor(question.probability)}`}>
                              {question.probability}% Probability
                            </span>
                          </div>
                          <span className="text-gray-600">• {question.reason}</span>
                        </div>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Button variant="ghost" size="icon">
                          <Bookmark className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon">
                          <Share2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Study Tips */}
      <Card className="bg-gradient-to-r from-blue-50 to-teal-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Smart Study Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">1.</span>
              <span>Prioritize questions with 80%+ probability - they have the highest chance of appearing</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">2.</span>
              <span>Focus on repeating questions first - they've appeared multiple times historically</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">3.</span>
              <span>Practice numerical problems daily - they carry high marks and test understanding</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">4.</span>
              <span>Don't ignore diagram-based questions - they often repeat with slight variations</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
