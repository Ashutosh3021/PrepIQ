"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Plus, BookOpen, MoreVertical, GraduationCap, Loader2, RefreshCw, Trash2, Pencil } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { subjectService, authService } from "@/src/lib/api"
import { toast } from "sonner"

interface Subject {
  id: string
  name: string
  code: string
  color: string
  materials: number
  prediction: number
  progress?: number // Added for todo progress
}

export default function SubjectsPage() {
  const router = useRouter()
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [loading, setLoading] = useState(true)
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null)
  const [newSubject, setNewSubject] = useState({ name: "", code: "" })
  const [editSubject, setEditSubject] = useState({ name: "", code: "" })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)

  useEffect(() => {
    checkConnection()
    fetchSubjects()
    // Sync wizard subjects on initial load
    syncWizardSubjects()
  }, [])

  // Check backend connection
  const checkConnection = async () => {
    try {
      setConnectionError(null)
      await subjectService.getAll({ limit: 1 })
    } catch (error: any) {
      if (error.message?.includes('Network error') || error.status === 0) {
        setConnectionError('Backend not connected')
      }
    }
  }

  const fetchSubjects = async () => {
    try {
      setLoading(true)
      console.log("Fetching subjects from:", process.env.NEXT_PUBLIC_API_URL)
      const data = await subjectService.getAll()
      
      // Fetch progress from localStorage for each subject
      const subjectsWithProgress = data.map((subject: Subject) => {
        const todosKey = `todos_${subject.id}`
        const todos = JSON.parse(localStorage.getItem(todosKey) || '[]')
        const completedTodos = todos.filter((todo: any) => todo.completed).length
        const totalTodos = todos.length
        const progress = totalTodos > 0 ? Math.round((completedTodos / totalTodos) * 100) : 0
        
        return {
          ...subject,
          progress
        }
      })
      
      setSubjects(subjectsWithProgress)
    } catch (error: any) {
      console.error("Error fetching subjects:", error)
      if (error.message?.includes('Network error')) {
        toast.error("Cannot connect to server. Please check if the backend is running.")
      } else {
        toast.error("Failed to load subjects: " + (error.message || 'Unknown error'))
      }
    } finally {
      setLoading(false)
    }
  }

  // Sync subjects from wizard
  const syncWizardSubjects = async () => {
    try {
      setIsSyncing(true)
      // Get wizard status to check focus subjects
      const wizardStatus = await authService.getWizardStatus()
      
      if (wizardStatus?.focus_subjects && wizardStatus.focus_subjects.length > 0) {
        console.log("Found wizard subjects:", wizardStatus.focus_subjects)
        
        // Get existing subjects
        const existingSubjects = await subjectService.getAll()
        const existingNames = existingSubjects.map((s: Subject) => s.name.toLowerCase())
        
        // Add missing wizard subjects
        let addedCount = 0
        for (const subjectName of wizardStatus.focus_subjects) {
          if (!existingNames.includes(subjectName.toLowerCase())) {
            try {
              await subjectService.create({
                name: subjectName,
                code: `${subjectName.substring(0, 3).toUpperCase()}-${Date.now().toString().slice(-4)}`,
                semester: 1,
                academic_year: new Date().getFullYear().toString()
              })
              addedCount++
            } catch (err) {
              console.error(`Failed to add wizard subject ${subjectName}:`, err)
            }
          }
        }
        
        if (addedCount > 0) {
          toast.success(`Added ${addedCount} subject(s) from your wizard setup`)
          // Refresh subjects list
          fetchSubjects()
        }
      }
    } catch (error) {
      console.error("Error syncing wizard subjects:", error)
      // Don't show error toast here to avoid confusion on initial load
    } finally {
      setIsSyncing(false)
    }
  }

  const handleAddSubject = async () => {
    if (!newSubject.name.trim()) {
      toast.error("Subject name is required")
      return
    }

    try {
      setIsSubmitting(true)
      console.log("Adding subject:", newSubject.name)
      console.log("API URL:", process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
      
      await subjectService.create({
        name: newSubject.name,
        code: newSubject.code || `SUB-${Date.now().toString().slice(-4)}`,
        semester: 1,
        academic_year: new Date().getFullYear().toString()
      })
      toast.success("Subject added successfully")
      setNewSubject({ name: "", code: "" })
      setIsAddDialogOpen(false)
      fetchSubjects()
    } catch (error: any) {
      console.error("Error adding subject:", error)
      console.error("Error details:", {
        message: error.message,
        status: error.status,
        stack: error.stack
      })
      
      if (error.message?.includes('Network error') || error.status === 0) {
        toast.error(
          <div>
            <p className="font-semibold">Cannot connect to server</p>
            <p className="text-sm">Please ensure:</p>
            <ul className="text-sm list-disc ml-4 mt-1">
              <li>Backend is running: <code>uvicorn main:app --reload</code></li>
              <li>Backend URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</li>
            </ul>
          </div>,
          { duration: 6000 }
        )
      } else if (error.status === 401) {
        toast.error("Session expired. Please log in again.")
      } else if (error.status === 422) {
        toast.error("Invalid data. Please check all fields.")
      } else {
        toast.error("Failed to add subject: " + (error.message || 'Unknown error'))
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEditSubject = (subject: Subject) => {
    setSelectedSubject(subject)
    setEditSubject({ name: subject.name, code: subject.code || "" })
    setIsEditDialogOpen(true)
  }

  const handleUpdateSubject = async () => {
    if (!selectedSubject) return
    if (!editSubject.name.trim()) {
      toast.error("Subject name is required")
      return
    }

    try {
      setIsSubmitting(true)
      await subjectService.update(selectedSubject.id, {
        name: editSubject.name,
        code: editSubject.code
      })
      toast.success("Subject updated successfully")
      setIsEditDialogOpen(false)
      setSelectedSubject(null)
      fetchSubjects()
    } catch (error: any) {
      console.error("Error updating subject:", error)
      toast.error("Failed to update subject: " + (error.message || 'Unknown error'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteClick = (subject: Subject) => {
    setSelectedSubject(subject)
    setIsDeleteDialogOpen(true)
  }

  const handleDeleteSubject = async () => {
    if (!selectedSubject) return

    try {
      setIsSubmitting(true)
      await subjectService.delete(selectedSubject.id)
      
      // Also delete associated todos from localStorage
      localStorage.removeItem(`todos_${selectedSubject.id}`)
      
      toast.success("Subject deleted successfully")
      setIsDeleteDialogOpen(false)
      setSelectedSubject(null)
      fetchSubjects()
    } catch (error: any) {
      console.error("Error deleting subject:", error)
      toast.error("Failed to delete subject: " + (error.message || 'Unknown error'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const navigateToTodos = (subjectId: string) => {
    router.push(`/protected/subjects/${subjectId}/todos`)
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Subjects</h1>
            <p className="text-muted-foreground">Loading your subjects...</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Connection Error Banner */}
      {connectionError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-start gap-3">
            <div className="text-red-600 mt-0.5">⚠️</div>
            <div className="flex-1">
              <h3 className="font-semibold text-red-800">Backend Connection Error</h3>
              <p className="text-sm text-red-700 mt-1">
                Cannot connect to the server at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
              </p>
              <div className="text-sm text-red-700 mt-2">
                <p className="font-medium">To fix this:</p>
                <ol className="list-decimal ml-4 mt-1 space-y-1">
                  <li>Open a terminal in the <code>backend</code> folder</li>
                  <li>Run: <code>uvicorn main:app --reload --port 8000</code></li>
                  <li>Wait for the server to start</li>
                  <li>Refresh this page</li>
                </ol>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={checkConnection}
                className="mt-3"
              >
                Retry Connection
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Subjects</h1>
          <p className="text-muted-foreground">
            Manage your courses and track your preparation progress.
            {isSyncing && <span className="ml-2 text-indigo-600">Syncing wizard subjects...</span>}
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={syncWizardSubjects} 
            disabled={isSyncing}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
            Sync Wizard Subjects
          </Button>
          
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" /> Add Subject
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Subject</DialogTitle>
                <DialogDescription>
                  Add a new subject to start tracking your progress and get AI predictions.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Subject Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Mathematics III"
                    value={newSubject.name}
                    onChange={(e) => setNewSubject({ ...newSubject, name: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="code">Subject Code (Optional)</Label>
                  <Input
                    id="code"
                    placeholder="e.g., MAT301"
                    value={newSubject.code}
                    onChange={(e) => setNewSubject({ ...newSubject, code: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddSubject} disabled={isSubmitting}>
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Add Subject"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {subjects.map((subject) => (
          <Card key={subject.id} className="overflow-hidden hover:shadow-md transition-shadow">
            <div className={`h-2 ${subject.color || 'bg-indigo-500'}`} />
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
                  <DropdownMenuItem onClick={() => handleEditSubject(subject)}>
                    <Pencil className="h-4 w-4 mr-2" />
                    Edit Subject
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    className="text-destructive" 
                    onClick={() => handleDeleteClick(subject)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <BookOpen className="h-4 w-4" />
                  {subject.materials || 0} Materials
                </div>
                <div className="flex items-center gap-1">
                  <GraduationCap className="h-4 w-4" />
                  Grade: A-
                </div>
              </div>
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">Exam Preparation</span>
                  <span className="font-bold text-primary">{subject.progress || 0}%</span>
                </div>
                <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all duration-300" 
                    style={{ width: `${subject.progress || 0}%` }} 
                  />
                </div>
              </div>
            </CardContent>
            <CardFooter className="border-t bg-muted/20 p-4">
              <Button 
                variant="ghost" 
                className="w-full text-xs"
                onClick={() => navigateToTodos(subject.id)}
              >
                Track Progress
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {/* Edit Subject Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Subject</DialogTitle>
            <DialogDescription>
              Update the subject details below.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="edit-name">Subject Name</Label>
              <Input
                id="edit-name"
                placeholder="e.g., Mathematics III"
                value={editSubject.name}
                onChange={(e) => setEditSubject({ ...editSubject, name: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-code">Subject Code (Optional)</Label>
              <Input
                id="edit-code"
                placeholder="e.g., MAT301"
                value={editSubject.code}
                onChange={(e) => setEditSubject({ ...editSubject, code: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateSubject} disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Update Subject"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Subject</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{selectedSubject?.name}&quot;? This action cannot be undone.
              All associated todos and progress will also be deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDeleteSubject} 
              disabled={isSubmitting}
            >
              {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Version Stamp */}
      <div className="fixed bottom-4 left-4 text-xs text-gray-400 font-mono">
        v1.2.20
      </div>
    </div>
  )
}
