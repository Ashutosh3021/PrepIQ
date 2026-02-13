"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Plus, Trash2, CheckCircle2, Circle, ChevronLeft, BookOpen, Target, TrendingUp } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Progress } from "@/components/ui/progress"
import { subjectService } from "@/src/lib/api"
import { toast } from "sonner"

interface Todo {
  id: string
  text: string
  completed: boolean
  subTodos: SubTodo[]
}

interface SubTodo {
  id: string
  text: string
  completed: boolean
}

export default function SubjectTodosPage() {
  const params = useParams()
  const router = useRouter()
  const subjectId = params.subjectId as string
  
  const [subject, setSubject] = useState<any>(null)
  const [todos, setTodos] = useState<Todo[]>([])
  const [newTodo, setNewTodo] = useState("")
  const [newSubTodo, setNewSubTodo] = useState<{[key: string]: string}>({})
  const [loading, setLoading] = useState(true)

  // Load subject and todos from localStorage
  useEffect(() => {
    loadSubject()
    loadTodos()
  }, [subjectId])

  const loadSubject = async () => {
    try {
      const data = await subjectService.getById(subjectId)
      setSubject(data)
    } catch (error) {
      console.error("Error loading subject:", error)
      toast.error("Failed to load subject")
    } finally {
      setLoading(false)
    }
  }

  const loadTodos = () => {
    const todosKey = `todos_${subjectId}`
    const savedTodos = localStorage.getItem(todosKey)
    if (savedTodos) {
      setTodos(JSON.parse(savedTodos))
    }
  }

  const saveTodos = (updatedTodos: Todo[]) => {
    const todosKey = `todos_${subjectId}`
    localStorage.setItem(todosKey, JSON.stringify(updatedTodos))
    setTodos(updatedTodos)
  }

  const calculateProgress = () => {
    if (todos.length === 0) return 0
    
    let totalItems = 0
    let completedItems = 0
    
    todos.forEach(todo => {
      totalItems++
      if (todo.completed) completedItems++
      
      todo.subTodos.forEach(subTodo => {
        totalItems++
        if (subTodo.completed) completedItems++
      })
    })
    
    return totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0
  }

  const addTodo = () => {
    if (!newTodo.trim()) {
      toast.error("Please enter a topic/chapter name")
      return
    }

    const todo: Todo = {
      id: Date.now().toString(),
      text: newTodo.trim(),
      completed: false,
      subTodos: []
    }

    const updatedTodos = [...todos, todo]
    saveTodos(updatedTodos)
    setNewTodo("")
    toast.success("Topic added successfully")
  }

  const addSubTodo = (todoId: string) => {
    const text = newSubTodo[todoId]?.trim()
    if (!text) {
      toast.error("Please enter a sub-topic")
      return
    }

    const updatedTodos = todos.map(todo => {
      if (todo.id === todoId) {
        return {
          ...todo,
          subTodos: [
            ...todo.subTodos,
            {
              id: Date.now().toString(),
              text: text,
              completed: false
            }
          ]
        }
      }
      return todo
    })

    saveTodos(updatedTodos)
    setNewSubTodo({ ...newSubTodo, [todoId]: "" })
    toast.success("Sub-topic added")
  }

  const toggleTodo = (todoId: string) => {
    const updatedTodos = todos.map(todo => {
      if (todo.id === todoId) {
        const newCompleted = !todo.completed
        // If marking as completed, also complete all sub-todos
        // If unchecking, keep sub-todos as is
        return {
          ...todo,
          completed: newCompleted,
          subTodos: newCompleted 
            ? todo.subTodos.map(st => ({ ...st, completed: true }))
            : todo.subTodos
        }
      }
      return todo
    })

    saveTodos(updatedTodos)
  }

  const toggleSubTodo = (todoId: string, subTodoId: string) => {
    const updatedTodos = todos.map(todo => {
      if (todo.id === todoId) {
        const updatedSubTodos = todo.subTodos.map(st => 
          st.id === subTodoId ? { ...st, completed: !st.completed } : st
        )
        
        // Check if all sub-todos are completed
        const allSubTodosCompleted = updatedSubTodos.length > 0 && 
          updatedSubTodos.every(st => st.completed)
        
        return {
          ...todo,
          subTodos: updatedSubTodos,
          completed: allSubTodosCompleted
        }
      }
      return todo
    })

    saveTodos(updatedTodos)
  }

  const deleteTodo = (todoId: string) => {
    const updatedTodos = todos.filter(t => t.id !== todoId)
    saveTodos(updatedTodos)
    toast.success("Topic deleted")
  }

  const deleteSubTodo = (todoId: string, subTodoId: string) => {
    const updatedTodos = todos.map(todo => {
      if (todo.id === todoId) {
        return {
          ...todo,
          subTodos: todo.subTodos.filter(st => st.id !== subTodoId)
        }
      }
      return todo
    })

    saveTodos(updatedTodos)
  }

  const progress = calculateProgress()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => router.push('/protected/subjects')}>
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back to Subjects
        </Button>
      </div>

      {/* Progress Card */}
      <Card className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl text-white">{subject?.name}</CardTitle>
              <CardDescription className="text-indigo-100">
                Track your exam preparation progress
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold">{progress}%</div>
              <div className="text-sm text-indigo-100">Complete</div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={progress} className="h-3 bg-white/20" />
          <div className="flex items-center gap-6 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              <span>{todos.length} Topics</span>
            </div>
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              <span>{todos.filter(t => t.completed).length} Completed</span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              <span>{progress}% Progress</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Add New Topic */}
      <Card>
        <CardHeader>
          <CardTitle>Add Topic/Chapter</CardTitle>
          <CardDescription>
            Add main topics or chapters you need to study for this subject
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="e.g., Unit 1: Basic Electronics"
              value={newTodo}
              onChange={(e) => setNewTodo(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addTodo()}
            />
            <Button onClick={addTodo}>
              <Plus className="h-4 w-4 mr-2" />
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Topics List */}
      <div className="space-y-4">
        {todos.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <div className="text-4xl mb-4">📚</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No topics added yet
              </h3>
              <p className="text-gray-500">
                Start by adding topics or chapters you need to study
              </p>
            </CardContent>
          </Card>
        ) : (
          todos.map((todo) => (
            <Card key={todo.id} className={todo.completed ? 'border-green-200 bg-green-50/50' : ''}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <Checkbox
                      checked={todo.completed}
                      onCheckedChange={() => toggleTodo(todo.id)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <CardTitle className={`text-lg ${todo.completed ? 'line-through text-gray-500' : ''}`}>
                        {todo.text}
                      </CardTitle>
                      <CardDescription>
                        {todo.subTodos.length} sub-topics • {todo.subTodos.filter(st => st.completed).length} completed
                      </CardDescription>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteTodo(todo.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              
              <CardContent className="pt-0">
                {/* Sub-todos */}
                {todo.subTodos.length > 0 && (
                  <div className="ml-7 space-y-2 mb-4">
                    {todo.subTodos.map((subTodo) => (
                      <div 
                        key={subTodo.id} 
                        className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100"
                      >
                        <Checkbox
                          checked={subTodo.completed}
                          onCheckedChange={() => toggleSubTodo(todo.id, subTodo.id)}
                        />
                        <span className={`flex-1 text-sm ${subTodo.completed ? 'line-through text-gray-500' : ''}`}>
                          {subTodo.text}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => deleteSubTodo(todo.id, subTodo.id)}
                        >
                          <Trash2 className="h-3 w-3 text-gray-400" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Add sub-todo */}
                <div className="ml-7 flex gap-2">
                  <Input
                    placeholder="Add sub-topic..."
                    value={newSubTodo[todo.id] || ""}
                    onChange={(e) => setNewSubTodo({ ...newSubTodo, [todo.id]: e.target.value })}
                    onKeyPress={(e) => e.key === 'Enter' && addSubTodo(todo.id)}
                    className="text-sm"
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => addSubTodo(todo.id)}
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    Add
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
