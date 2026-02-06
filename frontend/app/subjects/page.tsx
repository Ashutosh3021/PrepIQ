'use client';

import React, { useState } from 'react';
import DashboardLayout from '@/src/components/dashboard/DashboardLayout';
import { subjectService } from '@/src/lib/api';
import { toast } from 'sonner';
import { useApi } from '@/hooks/use-api';
import { LoadingSpinner, InlineLoader } from '@/components/ui/loading-spinner';

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

interface SubjectCreate {
  name: string;
  code?: string;
  semester?: number;
  total_marks?: number;
  exam_date?: string;
  exam_duration_minutes?: number;
  syllabus_json?: any;
}

// Subject Row Component - extracted to handle client-side interactions
const SubjectRow = ({ subject }: { subject: Subject }) => {
  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-bold">{subject.name}</h3>
            <p className="text-gray-500">{subject.code}</p>
            <p className="text-sm text-gray-500">Semester {subject.semester}</p>
          </div>
          {/* Using a simple button instead of dropdown to avoid hydration issues */}
          <div className="relative">
            <button className="text-gray-400 hover:text-gray-600">
              ⋯
            </button>
          </div>
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
};

const SubjectsPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<SubjectCreate>({
    name: '',
    code: '',
    semester: 2,
    total_marks: 100,
    exam_date: '',
    exam_duration_minutes: 180,
  });

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

  // Use custom hook for mutations
  const { 
    loading: creatingSubject, 
    error: createError, 
    execute: createSubject 
  } = useApi(
    () => subjectService.create(formData),
    {
      immediate: false,
      onSuccess: (newSubject) => {
        toast.success('Subject created successfully!');
        setShowForm(false);
        setFormData({
          name: '',
          code: '',
          semester: 2,
          total_marks: 100,
          exam_date: '',
          exam_duration_minutes: 180,
        });
        refreshSubjects(); // Refresh the list
      },
      errorMessage: 'Failed to create subject'
    }
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'semester' || name === 'total_marks' || name === 'exam_duration_minutes' ? Number(value) : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createSubject();
  };

  return (
    <DashboardLayout>
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
          <button 
            onClick={() => setShowForm(!showForm)}
            className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-700"
          >
            + Add Subject
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error.message}
          </div>
        )}

        {/* Loading indicator */}
        {loading && <InlineLoader message="Loading your subjects..." />}

        {/* Add Subject Form */}
        {showForm && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Add New Subject</h2>
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 mb-2">Subject Name</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full p-2 border rounded"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-700 mb-2">Subject Code</label>
                  <input
                    type="text"
                    name="code"
                    value={formData.code}
                    onChange={handleInputChange}
                    className="w-full p-2 border rounded"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-700 mb-2">Semester</label>
                  <select
                    name="semester"
                    value={formData.semester}
                    onChange={handleInputChange}
                    className="w-full p-2 border rounded"
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8].map(num => (
                      <option key={num} value={num}>{num}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-700 mb-2">Total Marks</label>
                  <input
                    type="number"
                    name="total_marks"
                    value={formData.total_marks}
                    onChange={handleInputChange}
                    className="w-full p-2 border rounded"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-700 mb-2">Exam Date</label>
                  <input
                    type="date"
                    name="exam_date"
                    value={formData.exam_date}
                    onChange={handleInputChange}
                    className="w-full p2 border rounded"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-700 mb-2">Exam Duration (minutes)</label>
                  <input
                    type="number"
                    name="exam_duration_minutes"
                    value={formData.exam_duration_minutes}
                    onChange={handleInputChange}
                    className="w-full p-2 border rounded"
                    required
                  />
                </div>
              </div>
              <div className="flex mt-4 space-x-2">
                <button 
                  type="submit" 
                  disabled={creatingSubject}
                  className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {creatingSubject ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Creating...
                    </>
                  ) : 'Add Subject'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setShowForm(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Subjects List */}
        {!loading && subjects && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {subjects.map((subject) => (
              <SubjectRow key={subject.id} subject={subject} />
            ))}
            {subjects.length === 0 && !loading && (
              <div className="col-span-full text-center py-12">
                <p className="text-gray-500">No subjects found. Create your first subject to get started.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default SubjectsPage;