"use client"

import { Clock, BookOpen, ChevronRight, Award, Timer } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useEffect, useState } from "react"
import { apiClient, subjectService } from "@/src/lib/api"
import { toast } from "sonner"
import type { Subject } from "@/src/lib/api"

interface Test {
  id: string;
  subject: string;
  title: string;
  questions: number;
  time: string;
  difficulty: string;
  completed: boolean;
  score?: number;
}

export default function MockTestsPage() {
  const [tests, setTests] = useState<Test[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch user's subjects
        const userSubjects = await subjectService.getAll();
        setSubjects(userSubjects);
        
        // Fetch user's tests
        const userTests = await apiClient.get<any[]>("/api/tests");
        
        // Transform tests data to match frontend interface
        const transformedTests = userTests.map(test => ({
          id: test.test_id,
          subject: userSubjects.find(s => s.id === test.subject_id)?.name || "Unknown Subject",
          title: `Mock Test - ${userSubjects.find(s => s.id === test.subject_id)?.name || "Subject"}`,
          questions: test.total_questions,
          time: `${test.time_limit_minutes} mins`,
          difficulty: test.difficulty_level || "Medium",
          completed: test.is_completed || false,
          score: test.percentage
        }));
        
        setTests(transformedTests);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load tests";
        setError(errorMessage);
        toast.error(errorMessage);
        
        // Fallback to empty array if fetch fails
        setTests([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const generateTest = async (subjectId: string) => {
    try {
      setLoading(true);
      const response = await apiClient.post("/api/tests/generate", {
        subject_id: subjectId,
        num_questions: 20,
        time_limit_minutes: 60,
        difficulty: "Medium"
      });
      
      toast.success("Test generated successfully!");
      
      // Refresh tests list
      const updatedTests = await apiClient.get<any[]>("/api/tests");
      const userSubjects = await subjectService.getAll();
      
      const transformedTests = updatedTests.map(test => ({
        id: test.test_id,
        subject: userSubjects.find(s => s.id === test.subject_id)?.name || "Unknown Subject",
        title: `Mock Test - ${userSubjects.find(s => s.id === test.subject_id)?.name || "Subject"}`,
        questions: test.total_questions,
        time: `${test.time_limit_minutes} mins`,
        difficulty: test.difficulty_level || "Medium",
        completed: test.is_completed || false,
        score: test.percentage
      }));
      
      setTests(transformedTests);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to generate test";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  if (loading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Mock Tests</h1>
            <p className="text-muted-foreground">AI-generated tests based on your predicted exam patterns.</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-lg text-gray-600">Loading tests...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Mock Tests</h1>
            <p className="text-muted-foreground">AI-generated tests based on your predicted exam patterns.</p>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading Tests</h3>
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
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mock Tests</h1>
          <p className="text-muted-foreground">AI-generated tests based on your predicted exam patterns.</p>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Generate New Test Section */}
        <Card className="bg-primary/5 border-primary/20">
          <CardHeader>
            <div className="flex items-center gap-2 text-primary font-semibold mb-2">
              <Award className="h-5 w-5" />
              Generate New Test
            </div>
            <CardTitle>Create AI-Powered Mock Test</CardTitle>
            <CardDescription>
              Generate a personalized test based on your subjects and predicted exam patterns.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2 mb-4">
              {subjects.map((subject) => (
                <Button
                  key={subject.id}
                  onClick={() => generateTest(subject.id)}
                  disabled={loading}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <BookOpen className="h-4 w-4" />
                  {subject.name}
                </Button>
              ))}
            </div>
            {subjects.length === 0 && (
              <p className="text-gray-500">No subjects found. Please add subjects first to generate tests.</p>
            )}
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Available Tests</h2>
            <span className="text-sm text-muted-foreground">{tests.length} tests</span>
          </div>
          
          {tests.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No tests available</h3>
              <p className="text-gray-500 mb-4">Generate your first mock test using the button above</p>
              {subjects.length > 0 && (
                <Button onClick={() => generateTest(subjects[0].id)}>
                  Generate First Test
                </Button>
              )}
            </div>
          ) : (
            tests.map((test) => (
              <Card key={test.id} className="overflow-hidden hover:border-primary/50 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-6 gap-4">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px] uppercase tracking-wider">
                        {test.subject}
                      </Badge>
                      {test.completed && (
                        <Badge className="bg-green-500/10 text-green-600 hover:bg-green-500/10 border-green-500/20">
                          Completed
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-lg">{test.title}</CardTitle>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Timer className="h-4 w-4" /> {test.time}
                      </span>
                      <span>{test.questions} Questions</span>
                      <span>{test.difficulty}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {test.completed && test.score && (
                      <div className="text-right hidden sm:block">
                        <p className="text-2xl font-bold text-primary">{test.score}%</p>
                        <p className="text-xs text-muted-foreground">Last score</p>
                      </div>
                    )}
                    <Button variant={test.completed ? "outline" : "default"} className="gap-2">
                      {test.completed ? "Retake Test" : "Start Test"}
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
