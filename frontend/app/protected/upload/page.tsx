"use client"

import { useState } from "react"
import { Upload, FileText, CheckCircle2, AlertCircle, X } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"

export default function UploadPage() {
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [file, setFile] = useState<File | null>(null)

  const handleUpload = () => {
    if (!file) return
    setIsUploading(true)
    let p = 0
    const interval = setInterval(() => {
      p += 10
      setProgress(p)
      if (p >= 100) {
        clearInterval(interval)
        setTimeout(() => setIsUploading(false), 500)
      }
    }, 200)
  }

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload Material</h1>
        <p className="text-muted-foreground">Upload your syllabus, past exams, or lecture notes for AI analysis.</p>
      </div>

      <Card className="border-dashed border-2">
        <CardContent className="pt-12 pb-12 flex flex-col items-center justify-center text-center gap-4">
          <div className="p-4 rounded-full bg-primary/10">
            <Upload className="h-8 w-8 text-primary" />
          </div>
          <div>
            <p className="text-lg font-medium">Click to upload or drag and drop</p>
            <p className="text-sm text-muted-foreground">PDF, DOCX, or PPTX (Max 20MB)</p>
          </div>
          <input
            type="file"
            className="hidden"
            id="file-upload"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <Button variant="outline" asChild>
            <label htmlFor="file-upload" className="cursor-pointer">
              Select File
            </label>
          </Button>

          {file && (
            <div className="mt-4 p-4 border rounded-lg bg-background flex items-center gap-4 w-full max-w-md">
              <FileText className="h-6 w-6 text-primary" />
              <div className="flex-1 text-left">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setFile(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Analysis Settings</CardTitle>
          <CardDescription>Configure how the AI should analyze your documents.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6">
          <div className="grid gap-2">
            <label className="text-sm font-medium">Assign to Subject</label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Select subject" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="calc3">Calculus III</SelectItem>
                <SelectItem value="chem202">Organic Chemistry</SelectItem>
                <SelectItem value="hist101">Modern History</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {isUploading ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span>Analyzing document...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
          ) : (
            <Button onClick={handleUpload} disabled={!file} className="w-full">
              Start AI Analysis
            </Button>
          )}
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            <CardTitle className="text-base">Topic Extraction</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Automatically identifies key exam topics and learning objectives from your files.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center gap-2">
            <AlertCircle className="h-5 w-5 text-blue-500" />
            <CardTitle className="text-base">Weightage Prediction</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Predicts which topics are most likely to appear on your upcoming exams based on analysis.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
