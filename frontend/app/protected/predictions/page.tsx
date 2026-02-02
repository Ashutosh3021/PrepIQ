"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Brain, TrendingUp, AlertTriangle, CheckCircle2, Info } from "lucide-react"
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Area, AreaChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer } from "recharts"

const chartData = [
  { month: "Jan", score: 65 },
  { month: "Feb", score: 68 },
  { month: "Mar", score: 75 },
  { month: "Apr", score: 72 },
  { month: "May", score: 84 },
  { month: "Jun", score: 88 },
]

const chartConfig = {
  score: {
    label: "Predicted Score",
    color: "var(--primary)",
  },
} satisfies ChartConfig

const topics = [
  { name: "Vector Calculus", probability: 95, weight: "High", status: "Focus Needed" },
  { name: "Partial Derivatives", probability: 82, weight: "Medium", status: "Review" },
  { name: "Multiple Integrals", probability: 78, weight: "High", status: "Mastered" },
  { name: "Line Integrals", probability: 45, weight: "Low", status: "Optional" },
]

export default function PredictionsPage() {
  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Exam Predictions</h1>
        <p className="text-muted-foreground">
          Detailed breakdown of predicted topics and performance trends based on your study materials.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Performance Trend
            </CardTitle>
            <CardDescription>Predicted exam score trajectory over time.</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ChartContainer config={chartConfig}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ left: -20, right: 10, top: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={10} />
                  <YAxis tickLine={false} axisLine={false} domain={[0, 100]} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="var(--primary)"
                    fill="var(--primary)"
                    fillOpacity={0.1}
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              Overall Outlook
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center py-4">
              <span className="text-5xl font-bold text-primary">88%</span>
              <p className="text-sm text-muted-foreground mt-1">Predicted Score</p>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Confidence Level</span>
                <span className="font-medium">High (92%)</span>
              </div>
              <Progress value={92} className="h-2" />
            </div>
            <Alert variant="default" className="bg-primary/5 border-primary/20">
              <Info className="h-4 w-4" />
              <AlertTitle>Smart Tip</AlertTitle>
              <AlertDescription className="text-xs">
                Focus on 'Vector Calculus' as it has the highest weightage in upcoming exams.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Topic Weightage & Probability</CardTitle>
          <CardDescription>AI-identified topics most likely to appear on the final exam.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative w-full overflow-auto">
            <table className="w-full caption-bottom text-sm">
              <thead className="[&_tr]:border-b">
                <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Topic Name</th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Exam Probability
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Weightage</th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Status</th>
                </tr>
              </thead>
              <tbody className="[&_tr:last-child]:border-0">
                {topics.map((topic) => (
                  <tr key={topic.name} className="border-b transition-colors hover:bg-muted/50">
                    <td className="p-4 align-middle font-medium">{topic.name}</td>
                    <td className="p-4 align-middle">
                      <div className="flex items-center gap-2">
                        <span className="w-8">{topic.probability}%</span>
                        <div className="flex-1 max-w-[100px] h-1.5 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: `${topic.probability}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="p-4 align-middle">
                      <Badge
                        variant={topic.weight === "High" ? "destructive" : "secondary"}
                        className="bg-transparent border-current font-normal"
                      >
                        {topic.weight}
                      </Badge>
                    </td>
                    <td className="p-4 align-middle">
                      <div className="flex items-center gap-2">
                        {topic.status === "Focus Needed" ? (
                          <AlertTriangle className="h-4 w-4 text-destructive" />
                        ) : topic.status === "Mastered" ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <Info className="h-4 w-4 text-blue-500" />
                        )}
                        <span>{topic.status}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
