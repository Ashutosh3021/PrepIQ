"use client";

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, Image, FileText, X, Loader2, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { api } from '@/lib/api';

interface UploadInterfaceProps {
  subjects: Array<{ id: string; name: string }>;
  onAnalysisComplete?: (data: any) => void;
}

export default function UploadInterface({ subjects, onAnalysisComplete }: UploadInterfaceProps) {
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisStage, setAnalysisStage] = useState<string>('');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prev => [...prev, ...acceptedFiles]);
    setError('');
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <Image className="w-5 h-5" />;
    if (file.type.includes('pdf')) return <FileText className="w-5 h-5" />;
    return <File className="w-5 h-5" />;
  };

  const handleUpload = async () => {
    if (!selectedSubject) {
      setError('Please select a subject first');
      return;
    }
    if (files.length === 0) {
      setError('Please upload at least one file');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setError('');

    try {
      const formData = new FormData();
      formData.append('subject_id', selectedSubject);
      formData.append('material_type', 'pyq');
      files.forEach(file => formData.append('files', file));

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      // Analysis stages
      setAnalysisStage('Extracting text with EasyOCR...');
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setAnalysisStage('Detecting objects with YOLOv8...');
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setAnalysisStage('Checking for circuit diagrams...');
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setAnalysisStage('Analyzing patterns and generating insights...');

      const response = await api.post('/analysis/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      setResult(response.data);
      
      if (onAnalysisComplete) {
        onAnalysisComplete(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setAnalysisStage('');
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl flex items-center gap-2">
          <Upload className="w-6 h-6" />
          Upload Study Materials
        </CardTitle>
        <CardDescription>
          Upload your previous year papers, notes, or diagrams. Our AI will analyze them to predict exam patterns.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Subject Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Select Subject</label>
          <Select value={selectedSubject} onValueChange={setSelectedSubject}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Choose a subject..." />
            </SelectTrigger>
            <SelectContent>
              {subjects.map((subject) => (
                <SelectItem key={subject.id} value={subject.id}>
                  {subject.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-colors duration-200
            ${isDragActive ? 'border-teal-500 bg-teal-50' : 'border-gray-300 hover:border-gray-400'}
            ${files.length > 0 ? 'bg-gray-50' : ''}
          `}
        >
          <input {...getInputProps()} />
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          {isDragActive ? (
            <p className="text-teal-600 font-medium">Drop the files here...</p>
          ) : (
            <>
              <p className="text-gray-600 mb-2">
                Drag & drop files here, or click to select
              </p>
              <p className="text-sm text-gray-400">
                Supports: Images (PNG, JPG), PDF, Text files (Max 10MB)
              </p>
            </>
          )}
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">
              Selected Files ({files.length})
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getFileIcon(file)}
                    <div>
                      <p className="text-sm font-medium truncate max-w-xs">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="p-1 hover:bg-gray-200 rounded"
                    disabled={uploading}
                  >
                    <X className="w-4 h-4 text-gray-500" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Upload Progress */}
        {uploading && (
          <div className="space-y-3">
            <Progress value={uploadProgress} className="w-full" />
            <div className="flex items-center justify-center gap-2 text-sm text-teal-600">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{analysisStage || 'Uploading...'}</span>
            </div>
          </div>
        )}

        {/* Success Message */}
        {result && !uploading && (
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle2 className="w-4 h-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Analysis complete! Found {result.extracted_data.questions.length} questions.
            </AlertDescription>
          </Alert>
        )}

        {/* Upload Button */}
        <Button
          onClick={handleUpload}
          disabled={uploading || files.length === 0 || !selectedSubject}
          className="w-full"
          size="lg"
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4 mr-2" />
              Start Analysis
            </>
          )}
        </Button>

        {/* Processing Pipeline Info */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium mb-3">Processing Pipeline:</h4>
          <div className="flex items-center justify-between text-xs text-gray-600">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center mb-1">
                <span className="text-teal-600 font-bold">1</span>
              </div>
              <span>EasyOCR</span>
              <span className="text-gray-400">Text Extraction</span>
            </div>
            <div className="flex-1 h-0.5 bg-gray-300 mx-2" />
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center mb-1">
                <span className="text-teal-600 font-bold">2</span>
              </div>
              <span>YOLOv8</span>
              <span className="text-gray-400">Object Detection</span>
            </div>
            <div className="flex-1 h-0.5 bg-gray-300 mx-2" />
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center mb-1">
                <span className="text-teal-600 font-bold">3</span>
              </div>
              <span>GroundingDINO</span>
              <span className="text-gray-400">Circuit Detection</span>
            </div>
            <div className="flex-1 h-0.5 bg-gray-300 mx-2" />
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center mb-1">
                <span className="text-teal-600 font-bold">4</span>
              </div>
              <span>AI Analysis</span>
              <span className="text-gray-400">Pattern Recognition</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
