'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Edit, Trash, Eye } from 'lucide-react';

interface SubjectRowProps {
  subject: {
    id: string;
    name: string;
    code?: string;
    semester?: number;
    total_marks?: number;
    exam_date?: string;
    papers_uploaded: number;
    predictions_generated: number;
    mock_tests_created: number;
  };
}

export default function SubjectRowClient({ subject }: SubjectRowProps) {
  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-bold">{subject.name}</h3>
            <p className="text-gray-500">{subject.code}</p>
            <p className="text-sm text-gray-500">Semester {subject.semester}</p>
          </div>
          
          {/* Dropdown Menu for actions - this component runs entirely on the client */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                className="h-8 w-8 p-0"
              >
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={() => window.location.href = `/protected/upload?subjectId=${subject.id}`}
              >
                <Eye className="mr-2 h-4 w-4" />
                Upload Materials
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => window.location.href = `/protected/predictions?subjectId=${subject.id}`}
              >
                <Edit className="mr-2 h-4 w-4" />
                View Predictions
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => window.location.href = `/protected/tests?subjectId=${subject.id}`}
              >
                <Trash className="mr-2 h-4 w-4" />
                Take Test
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        
        <div className="mt-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span>Total Marks:</span>
            <span className="font-medium">{subject.total_marks}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Exam Date:</span>
            <span className="font-medium">{new Date(subject.exam_date || '').toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Papers Uploaded:</span>
            <span className="font-medium">{subject.papers_uploaded}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Predictions Generated:</span>
            <span className="font-medium">{subject.predictions_generated}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Mock Tests:</span>
            <span className="font-medium">{subject.mock_tests_created}</span>
          </div>
        </div>
        
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-teal-600 h-2 rounded-full" 
              style={{ width: `${Math.min((subject.papers_uploaded / 10) * 100, 100)}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {subject.papers_uploaded} papers uploaded
          </p>
        </div>
        
        <div className="flex mt-4 space-x-2">
          <button 
            onClick={() => window.location.href = `/protected/upload?subjectId=${subject.id}`}
            className="flex-1 bg-gray-100 text-gray-700 py-2 rounded hover:bg-gray-200 text-sm"
          >
            📤 Upload Paper
          </button>
          <button 
            onClick={() => window.location.href = `/protected/predictions?subjectId=${subject.id}`}
            className="flex-1 bg-teal-100 text-teal-700 py-2 rounded hover:bg-teal-200 text-sm"
          >
            🔮 Predictions
          </button>
          <button 
            onClick={() => window.location.href = `/protected/tests?subjectId=${subject.id}`}
            className="flex-1 bg-purple-100 text-purple-700 py-2 rounded hover:bg-purple-200 text-sm"
          >
            🎯 Mock Test
          </button>
        </div>
      </div>
    </div>
  );
}