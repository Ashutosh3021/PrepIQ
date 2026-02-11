"use client"
import { Plus, BookOpen, MoreVertical, GraduationCap } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

// Subjects are now fetched from the API
// This array serves as a fallback/loading state only
const subjects: Subject[] = []

export default function SubjectsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Subjects</h1>
          <p className="text-muted-foreground">Manage your courses and view academic performance predictions.</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" /> Add Subject
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {subjects.map((subject) => (
          <Card key={subject.id} className="overflow-hidden hover:shadow-md transition-shadow">
            <div className={`h-2 ${subject.color}`} />
            <CardHeader className="flex flex-row items-start justify-between space-y-0">
              <div className="space-y-1">
                <CardTitle className="text-xl">{subject.name}</CardTitle>
                <CardDescription>{subject.code}</CardDescription>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>Edit Subject</DropdownMenuItem>
                  <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <BookOpen className="h-4 w-4" />
                  {subject.materials} Materials
                </div>
                <div className="flex items-center gap-1">
                  <GraduationCap className="h-4 w-4" />
                  Grade: A-
                </div>
              </div>
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">Exam Prediction</span>
                  <span className="font-bold text-primary">{subject.prediction}%</span>
                </div>
                <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: `${subject.prediction}%` }} />
                </div>
              </div>
            </CardContent>
            <CardFooter className="border-t bg-muted/20 p-4">
              <Button variant="ghost" className="w-full text-xs" asChild>
                <a href={`/protected/subjects/${subject.id}`}>View Details & Analysis</a>
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
