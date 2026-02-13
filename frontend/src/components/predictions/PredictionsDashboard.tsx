"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import { Target, TrendingUp, AlertTriangle, CheckCircle2, BookOpen } from 'lucide-react';
import { api } from '@/lib/api';

interface PredictionsDashboardProps {
  subjectId: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function PredictionsDashboard({ subjectId }: PredictionsDashboardProps) {
  const [predictions, setPredictions] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPredictions();
  }, [subjectId]);

  const fetchPredictions = async () => {
    try {
      const response = await api.get(`/analysis/predictions/${subjectId}`);
      setPredictions(response.data);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  // Sample data for demonstration
  const trendData = predictions?.predictions?.trend_data || [
    { year: '2020', topic: 'Unit 1', frequency: 5 },
    { year: '2021', topic: 'Unit 1', frequency: 7 },
    { year: '2022', topic: 'Unit 1', frequency: 6 },
    { year: '2023', topic: 'Unit 1', frequency: 8 },
    { year: '2024', topic: 'Unit 1', frequency: 7 },
  ];

  const probabilityData = [
    { name: 'Very High (80-100%)', value: 3, color: '#10b981' },
    { name: 'High (60-79%)', value: 5, color: '#3b82f6' },
    { name: 'Medium (40-59%)', value: 8, color: '#f59e0b' },
    { name: 'Low (<40%)', value: 12, color: '#6b7280' },
  ];

  const highProbabilityQuestions = predictions?.predictions?.high_probability || [
    { question: "Explain Ohm's Law with derivation", confidence: 95, topic: "Basic Electronics" },
    { question: "Draw and explain PN junction diode characteristics", confidence: 88, topic: "Semiconductors" },
    { question: "Calculate current in parallel resistance circuit", confidence: 85, topic: "Circuit Analysis" },
    { question: "Describe working of Zener diode as voltage regulator", confidence: 82, topic: "Semiconductors" },
    { question: "Explain Kirchhoff's Current and Voltage Laws", confidence: 80, topic: "Circuit Analysis" },
  ];

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">High Probability</p>
                <p className="text-2xl font-bold text-green-600">{highProbabilityQuestions.length}</p>
              </div>
              <Target className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Avg. Confidence</p>
                <p className="text-2xl font-bold text-blue-600">85%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Topics Covered</p>
                <p className="text-2xl font-bold text-purple-600">12</p>
              </div>
              <BookOpen className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Prediction Accuracy</p>
                <p className="text-2xl font-bold text-teal-600">88%</p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Analysis Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Topic Frequency Trends (5 Years)
            </CardTitle>
            <CardDescription>Historical appearance of topics in exams</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="frequency" 
                  stroke="#0088FE" 
                  strokeWidth={2}
                  name="Questions"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Probability Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5" />
              Question Probability Distribution
            </CardTitle>
            <CardDescription>Distribution of questions by probability</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={probabilityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {probabilityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap gap-2 mt-4 justify-center">
              {probabilityData.map((item, index) => (
                <div key={index} className="flex items-center gap-1 text-xs">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span>{item.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* High Probability Questions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            High Probability Questions for Next Exam
          </CardTitle>
          <CardDescription>
            Questions with highest likelihood of appearing based on pattern analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {highProbabilityQuestions.map((q: any, index: number) => (
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
                      <Badge variant="secondary">{q.topic}</Badge>
                    </div>
                    <p className="text-gray-800 font-medium">{q.question}</p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <Badge 
                      className={`
                        ${q.confidence >= 90 ? 'bg-green-100 text-green-800' : ''}
                        ${q.confidence >= 80 && q.confidence < 90 ? 'bg-blue-100 text-blue-800' : ''}
                        ${q.confidence < 80 ? 'bg-amber-100 text-amber-800' : ''}
                      `}
                    >
                      {q.confidence}% Probability
                    </Badge>
                    <Progress 
                      value={q.confidence} 
                      className="w-24 h-2"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Unit-wise Weightage */}
      <Card>
        <CardHeader>
          <CardTitle>Unit-wise Question Weightage</CardTitle>
          <CardDescription>Distribution of questions across different units</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart
              data={[
                { unit: 'Unit 1', questions: 12, weightage: 25 },
                { unit: 'Unit 2', questions: 10, weightage: 20 },
                { unit: 'Unit 3', questions: 15, weightage: 30 },
                { unit: 'Unit 4', questions: 8, weightage: 15 },
                { unit: 'Unit 5', questions: 5, weightage: 10 },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="unit" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="questions" fill="#0088FE" name="Questions" />
              <Bar dataKey="weightage" fill="#00C49F" name="Weightage %" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
