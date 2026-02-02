"use client"

import { Clock, BookOpen, ChevronRight, Award, Timer } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

const mockTests = [
  {
    id: 1,
    subject: "Calculus III",
    title: "Midterm Simulation (Vectors & Surfaces)",
    questions: 20,
    time: "45 mins",
    difficulty: "Hard",
    completed: false,
  },
  {
    id: 2,
    subject: "Modern History",
    title: "Final Exam Practice Set",
    questions: 50,
    time: "90 mins",
    difficulty: "Medium",
    completed: true,
    score: 92,
  },
  {
    id: 3,
    subject: "Organic Chemistry",
    title: "Reaction Mechanisms Quiz",
    questions: 15,
    time: "30 mins",
    difficulty: "Hard",
    completed: false,
  },
]

export default function MockTestsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mock Tests</h1>
          <p className="text-muted-foreground">AI-generated tests based on your predicted exam patterns.</p>
        </div>
      </div>

      <div className="grid gap-6">
        <Card className="bg-primary/5 border-primary/20">
          <CardHeader>
            <div className="flex items-center gap-2 text-primary font-semibold mb-2">
              <Award className="h-5 w-5" />
              AI Recommended Test
            </div>
            <CardTitle>Calculus III: Vector Fields & Integration</CardTitle>
            <CardDescription>
              We've identified this as your weakest area. This test focuses on topics likely to appear in your final.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-4">
            <div className="flex items-center gap-1.5 text-sm">
              <Clock className="h-4 w-4 text-muted-foreground" />
              60 Minutes
            </div>
            <div className="flex items-center gap-1.5 text-sm">
              <BookOpen className="h-4 w-4 text-muted-foreground" />
              25 Questions
            </div>
            <Badge variant="secondary">Calculus III</Badge>
          </CardContent>
          <CardFooter>
            <Button className="w-full sm:w-auto">Start Recommended Test</Button>
          </CardFooter>
        </Card>

        <div className="grid gap-4">
          <h2 className="text-xl font-semibold">Available Tests</h2>
          {mockTests.map((test) => (
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
                  {test.completed ? (
                    <div className="text-right hidden sm:block">
                      <p className="text-2xl font-bold text-primary">{test.score}%</p>
                      <p className="text-xs text-muted-foreground">Last score</p>
                    </div>
                  ) : null}
                  <Button variant={test.completed ? "outline" : "default"} className="gap-2">
                    {test.completed ? "Retake Test" : "Start Test"}
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
