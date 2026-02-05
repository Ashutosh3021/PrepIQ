"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Brain, TrendingUp, AlertTriangle, CheckCircle2, Info, BarChart3 } from "lucide-react"
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Area, AreaChart, Bar, BarChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer } from "recharts"

// Performance Trend Data (65% to 88%)
const performanceData = [
  { month: "Jan", score: 65 },
  { month: "Feb", score: 68 },
  { month: "Mar", score: 75 },
  { month: "Apr", score: 72 },
  { month: "May", score: 84 },
  { month: "Jun", score: 88 },
]

// Topic Weightage Data (45% to 95% with dip)
const topicWeightageData = [
  { month: "Jan", probability: 55 },
  { month: "Feb", probability: 58 },
  { month: "Mar", probability: 62 },
  { month: "Apr", probability: 55 }, // Dip
  { month: "May", probability: 85 },
  { month: "Jun", probability: 95 },
]

const chartConfig = {
  score: {
    label: "Predicted Score",
    color: "hsl(var(--primary))",
  },
  probability: {
    label: "Topic Probability",
    color: "hsl(var(--chart-2))",
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
    <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center md:text-left">
          <h1 className="text-3xl font-bold tracking-tight">AI Exam Predictions</h1>
          <p className="text-muted-foreground mt-2">
            Detailed breakdown of predicted topics and performance trends based on your study materials.
          </p>
        </div>

        {/* Performance Trend Chart */}
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Performance Trend
            </CardTitle>
            <CardDescription>Predicted exam score trajectory over time.</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[320px] md:h-[380px] w-full">
              <ResponsiveContainer width="99%" height="100%">
                <AreaChart 
                  data={performanceData}
                  margin={{ 
                    top: 15, 
                    right: 20, 
                    left: 45, 
                    bottom: 40 
                  }}
                >
                  <CartesianGrid 
                    strokeDasharray="3 3" 
                    vertical={true}
                    horizontal={true}
                    stroke="hsl(var(--border))"
                  />
                  <XAxis 
                    dataKey="month"
                    tickLine={true}
                    axisLine={true}
                    tickMargin={10}
                    interval={0}
                    padding={{ left: 10, right: 10 }}
                    tick={{ 
                      fill: 'hsl(var(--muted-foreground))', 
                      fontSize: 12,
                      fontWeight: 500
                    }}
                  />
                  <YAxis 
                    tickLine={true}
                    axisLine={true}
                    domain={[0, 100]}
                    tickCount={6}
                    width={50}
                    tick={{ 
                      fill: 'hsl(var(--muted-foreground))', 
                      fontSize: 12,
                      fontWeight: 500
                    }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <ChartTooltip 
                    content={
                      <ChartTooltipContent 
                        indicator="line"
                        labelFormatter={(value) => `Month: ${value}`}
                        formatter={(value) => [`${value}%`, "Score"]}
                      />
                    } 
                  />
                  <defs>
                    <clipPath id="chartClip">
                      <rect x="0" y="0" width="100%" height="100%" />
                    </clipPath>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="hsl(var(--primary))"
                    fill="hsl(var(--primary))"
                    fillOpacity={0.15}
                    strokeWidth={3}
                    activeDot={{ 
                      r: 6, 
                      fill: 'hsl(var(--primary))',
                      stroke: 'hsl(var(--background))',
                      strokeWidth: 2
                    }}
                    dot={{ 
                      r: 4, 
                      fill: 'hsl(var(--primary))'
                    }}
                    clipPath="url(#chartClip)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Topic Weightage Chart */}
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-chart-2" />
              Topic Weightage & Probability
            </CardTitle>
            <CardDescription>Probability trends for key exam topics over time.</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[320px] md:h-[380px] w-full">
              <ResponsiveContainer width="99%" height="100%">
                <BarChart
                  data={topicWeightageData}
                  margin={{ 
                    top: 15, 
                    right: 20, 
                    left: 45, 
                    bottom: 40 
                  }}
                >
                  <CartesianGrid 
                    strokeDasharray="3 3" 
                    vertical={true}
                    horizontal={true}
                    stroke="hsl(var(--border))"
                  />
                  <XAxis 
                    dataKey="month"
                    tickLine={true}
                    axisLine={true}
                    tickMargin={10}
                    interval={0}
                    padding={{ left: 10, right: 10 }}
                    tick={{ 
                      fill: 'hsl(var(--muted-foreground))', 
                      fontSize: 12,
                      fontWeight: 500
                    }}
                  />
                  <YAxis 
                    tickLine={true}
                    axisLine={true}
                    domain={[0, 100]}
                    tickCount={6}
                    width={50}
                    tick={{ 
                      fill: 'hsl(var(--muted-foreground))', 
                      fontSize: 12,
                      fontWeight: 500
                    }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <ChartTooltip 
                    content={
                      <ChartTooltipContent 
                        indicator="dashed"
                        labelFormatter={(value) => `Month: ${value}`}
                        formatter={(value) => [`${value}%`, "Probability"]}
                      />
                    } 
                  />
                  <defs>
                    <clipPath id="barClip">
                      <rect x="0" y="0" width="100%" height="100%" />
                    </clipPath>
                  </defs>
                  <Bar
                    dataKey="probability"
                    fill="hsl(var(--chart-2))"
                    radius={[4, 4, 0, 0]}
                    clipPath="url(#barClip)"
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Overall Outlook Section */}
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-2">
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

          <Card>
            <CardHeader>
              <CardTitle>Key Topics</CardTitle>
              <CardDescription>High probability exam topics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topics.slice(0, 3).map((topic) => (
                  <div key={topic.name} className="space-y-1">
                    <div className="flex justify-between">
                      <span className="font-medium text-sm">{topic.name}</span>
                      <Badge 
                        variant={topic.weight === "High" ? "destructive" : "secondary"}
                        className="text-xs"
                      >
                        {topic.weight}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground w-10">{topic.probability}%</span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary" 
                          style={{ width: `${topic.probability}%` }} 
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Topic Details Table */}
        <Card>
          <CardHeader>
            <CardTitle>Detailed Topic Analysis</CardTitle>
            <CardDescription>AI-identified topics most likely to appear on the final exam.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
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
                            <div 
                              className="h-full bg-primary" 
                              style={{ width: `${topic.probability}%` }} 
                            />
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
    </div>
  )
}