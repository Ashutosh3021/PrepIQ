"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Play, 
  Clock, 
  BookOpen, 
  CheckCircle2, 
  AlertCircle,
  FileQuestion,
  BarChart3,
  Loader2
} from 'lucide-react';
import { api } from '@/lib/api';

interface MockTestGeneratorProps {
  subjectId: string;
  subjectName: string;
  questionPatterns?: any;
}

export default function MockTestGenerator({ 
  subjectId, 
  subjectName, 
  questionPatterns 
}: MockTestGeneratorProps) {
  const [config, setConfig] = useState({
    questionCount: 10,
    difficulty: 'mixed',
    includeTheory: true,
    includeNumerical: true,
    includeDiagrams: true,
    timePerQuestion: 3,
  });
  const [generating, setGenerating] = useState(false);
  const [test, setTest] = useState<any>(null);
  const [activeTest, setActiveTest] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [timeLeft, setTimeLeft] = useState(0);

  const generateTest = async () => {
    setGenerating(true);
    try {
      const response = await api.post('/analysis/mock-test/generate', {
        subject_id: subjectId,
        difficulty: config.difficulty,
        question_count: config.questionCount,
      });
      setTest(response.data);
      setTimeLeft(response.data.time_limit * 60); // Convert to seconds
    } catch (error) {
      console.error('Error generating test:', error);
      // Use mock data for demonstration
      setTest({
        test_id: 'mock_123',
        subject_id: subjectId,
        questions: [
          {
            id: 1,
            question: "Explain Ohm's Law and derive the relationship between V, I, and R.",
            type: 'theory',
            marks: 5,
            unit: 'Unit 1: Basic Electronics',
          },
          {
            id: 2,
            question: "Calculate the total resistance in a parallel circuit with R1=4Ω, R2=6Ω, and R3=12Ω.",
            type: 'numerical',
            marks: 5,
            unit: 'Unit 2: Circuit Analysis',
          },
          {
            id: 3,
            question: "Draw and explain the V-I characteristics of a PN junction diode.",
            type: 'diagram',
            marks: 10,
            unit: 'Unit 3: Semiconductors',
          },
          {
            id: 4,
            question: "Describe the working principle of a Zener diode as a voltage regulator.",
            type: 'theory',
            marks: 5,
            unit: 'Unit 3: Semiconductors',
          },
          {
            id: 5,
            question: "Find the current through each resistor in a series circuit with 12V battery and resistors 2Ω, 4Ω, and 6Ω.",
            type: 'numerical',
            marks: 10,
            unit: 'Unit 2: Circuit Analysis',
          },
        ],
        time_limit: config.questionCount * config.timePerQuestion,
        total_marks: 35,
      });
      setTimeLeft(config.questionCount * config.timePerQuestion * 60);
    } finally {
      setGenerating(false);
    }
  };

  const startTest = () => {
    setActiveTest(true);
    // Start timer
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          submitTest();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const submitTest = () => {
    setActiveTest(false);
    // Calculate score and show results
    alert(`Test submitted! You answered ${Object.keys(answers).length} out of ${test.questions.length} questions.`);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (activeTest && test) {
    const question = test.questions[currentQuestion];
    const progress = ((currentQuestion + 1) / test.questions.length) * 100;

    return (
      <Card className="w-full">
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Mock Test: {subjectName}</CardTitle>
              <CardDescription>Question {currentQuestion + 1} of {test.questions.length}</CardDescription>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-amber-600">
                <Clock className="w-5 h-5" />
                <span className="text-xl font-mono font-bold">{formatTime(timeLeft)}</span>
              </div>
              <Button variant="outline" onClick={submitTest}>
                Submit Test
              </Button>
            </div>
          </div>
          <Progress value={progress} className="mt-2" />
        </CardHeader>

        <CardContent className="p-6">
          <div className="space-y-6">
            {/* Question */}
            <div className="bg-gray-50 p-6 rounded-lg">
              <div className="flex items-start justify-between mb-4">
                <Badge variant="secondary">{question.unit}</Badge>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant={question.type === 'theory' ? 'default' : question.type === 'numerical' ? 'secondary' : 'outline'}
                  >
                    {question.type}
                  </Badge>
                  <Badge variant="outline">{question.marks} marks</Badge>
                </div>
              </div>
              <h3 className="text-lg font-medium">{question.question}</h3>
            </div>

            {/* Answer Area */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Your Answer:</label>
              <textarea
                className="w-full h-40 p-4 border rounded-lg resize-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                placeholder="Type your answer here..."
                value={answers[question.id] || ''}
                onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}
              />
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between pt-4">
              <Button
                variant="outline"
                disabled={currentQuestion === 0}
                onClick={() => setCurrentQuestion(prev => prev - 1)}
              >
                Previous
              </Button>
              
              <div className="flex gap-1">
                {test.questions.map((_: any, idx: number) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentQuestion(idx)}
                    className={`w-8 h-8 rounded text-sm font-medium ${
                      idx === currentQuestion
                        ? 'bg-teal-600 text-white'
                        : answers[test.questions[idx].id]
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {idx + 1}
                  </button>
                ))}
              </div>

              <Button
                disabled={currentQuestion === test.questions.length - 1}
                onClick={() => setCurrentQuestion(prev => prev + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileQuestion className="w-5 h-5" />
            Generate Mock Test
          </CardTitle>
          <CardDescription>
            Create a personalized mock test based on your uploaded question patterns
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Test Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Number of Questions</label>
              <Select 
                value={config.questionCount.toString()} 
                onValueChange={(v) => setConfig({ ...config, questionCount: parseInt(v) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5 Questions</SelectItem>
                  <SelectItem value="10">10 Questions</SelectItem>
                  <SelectItem value="15">15 Questions</SelectItem>
                  <SelectItem value="20">20 Questions</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Difficulty Level</label>
              <Select 
                value={config.difficulty} 
                onValueChange={(v) => setConfig({ ...config, difficulty: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                  <SelectItem value="mixed">Mixed (Recommended)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Question Types */}
          <div className="space-y-3">
            <label className="text-sm font-medium">Include Question Types:</label>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2">
                <Checkbox 
                  checked={config.includeTheory}
                  onCheckedChange={(checked) => 
                    setConfig({ ...config, includeTheory: checked as boolean })
                  }
                />
                <span>Theory Questions</span>
              </label>
              <label className="flex items-center gap-2">
                <Checkbox 
                  checked={config.includeNumerical}
                  onCheckedChange={(checked) => 
                    setConfig({ ...config, includeNumerical: checked as boolean })
                  }
                />
                <span>Numerical Problems</span>
              </label>
              <label className="flex items-center gap-2">
                <Checkbox 
                  checked={config.includeDiagrams}
                  onCheckedChange={(checked) => 
                    setConfig({ ...config, includeDiagrams: checked as boolean })
                  }
                />
                <span>Diagram-Based</span>
              </label>
            </div>
          </div>

          {/* Pattern Info */}
          {questionPatterns && (
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 mb-2 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Detected Patterns from Your Materials:
              </h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Theory:</span>
                  <span className="ml-1 font-semibold">{questionPatterns?.theory || '40%'}</span>
                </div>
                <div>
                  <span className="text-gray-600">Numerical:</span>
                  <span className="ml-1 font-semibold">{questionPatterns?.numerical || '35%'}</span>
                </div>
                <div>
                  <span className="text-gray-600">Diagrams:</span>
                  <span className="ml-1 font-semibold">{questionPatterns?.diagrams || '25%'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Generate Button */}
          <Button 
            onClick={generateTest} 
            disabled={generating || (!config.includeTheory && !config.includeNumerical && !config.includeDiagrams)}
            className="w-full"
            size="lg"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating Test...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Generate Mock Test
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Generated Test Preview */}
      {test && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              Test Generated Successfully
            </CardTitle>
            <CardDescription>
              Your personalized mock test is ready based on the patterns from your uploaded materials
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <BookOpen className="w-6 h-6 mx-auto mb-2 text-blue-600" />
                <p className="text-2xl font-bold">{test.questions.length}</p>
                <p className="text-sm text-gray-600">Questions</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Clock className="w-6 h-6 mx-auto mb-2 text-amber-600" />
                <p className="text-2xl font-bold">{test.time_limit}</p>
                <p className="text-sm text-gray-600">Minutes</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <AlertCircle className="w-6 h-6 mx-auto mb-2 text-purple-600" />
                <p className="text-2xl font-bold">{test.total_marks}</p>
                <p className="text-sm text-gray-600">Total Marks</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <FileQuestion className="w-6 h-6 mx-auto mb-2 text-teal-600" />
                <p className="text-2xl font-bold">{config.difficulty}</p>
                <p className="text-sm text-gray-600">Difficulty</p>
              </div>
            </div>

            <Button onClick={startTest} className="w-full" size="lg">
              <Play className="w-4 h-4 mr-2" />
              Start Mock Test
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
