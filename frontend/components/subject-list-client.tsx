'use client';

import React, { useState } from 'react';
import { subjectService } from '@/src/lib/api';
import { toast } from 'sonner';
import { useApi } from '@/hooks/use-api';
import { InlineLoader } from '@/components/ui/loading-spinner';
import SubjectRowClient from './subject-row-client';

interface Subject {
  id: string;
  name: string;
  code?: string;
  semester?: number;
  total_marks?: number;
  exam_date?: string;
  exam_duration_minutes?: number;
  syllabus_json?: any;
  papers_uploaded: number;
  predictions_generated: number;
  mock_tests_created: number;
  created_at: string;
}

interface SubjectListClientProps {
  initialSearchTerm?: string;
}

export default function SubjectListClient({ initialSearchTerm = '' }: SubjectListClientProps) {
  const [searchTerm, setSearchTerm] = useState(initialSearchTerm);
  
  // Use the custom hook for data fetching
  const { 
    data: subjects, 
    loading, 
    error, 
    execute: refreshSubjects 
  } = useApi(
    () => subjectService.getAll({ search: searchTerm || undefined }),
    {
      immediate: true,
      loadingMessage: 'Loading your subjects...',
      errorMessage: 'Failed to load subjects'
    }
  );

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold">My Subjects</h1>
          <div className="mt-2 relative">
            <input
              type="text"
              placeholder="Search subjects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full md:w-64 p-2 pl-10 border rounded"
            />
            <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
          </div>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {(error as Error).message}
        </div>
      )}

      {/* Loading indicator */}
      {loading && <InlineLoader message="Loading your subjects..." />}

      {/* Subjects List */}
      {!loading && subjects && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {subjects.map((subject) => (
            <SubjectRowClient key={subject.id} subject={subject} />
          ))}
          {subjects.length === 0 && !loading && (
            <div className="col-span-full text-center py-12">
              <p className="text-gray-500">No subjects found. Create your first subject to get started.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}