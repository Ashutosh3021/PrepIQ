'use client';

import React, { useState } from 'react';
import DashboardLayout from '@/src/components/dashboard/DashboardLayout';

const UploadPage = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: number}>({});
  const [uploadStatus, setUploadStatus] = useState<{[key: string]: string}>({});
  const [dragActive, setDragActive] = useState(false);

  const handleFiles = (newFiles: FileList) => {
    const newFileArray = Array.from(newFiles);
    setFiles(prev => [...prev, ...newFileArray]);
    
    // Initialize upload status for new files
    newFileArray.forEach(file => {
      setUploadStatus(prev => ({ ...prev, [file.name]: 'pending' }));
    });
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (fileName: string) => {
    setFiles(prev => prev.filter(file => file.name !== fileName));
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[fileName];
      return newProgress;
    });
    setUploadStatus(prev => {
      const newStatus = { ...prev };
      delete newStatus[fileName];
      return newStatus;
    });
  };

  const uploadFile = (file: File) => {
    setUploadStatus(prev => ({ ...prev, [file.name]: 'processing' }));
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        const currentProgress = prev[file.name] || 0;
        const newProgress = currentProgress + 10;
        
        if (newProgress >= 100) {
          clearInterval(interval);
          setUploadStatus(prev => ({ ...prev, [file.name]: 'completed' }));
          return { ...prev, [file.name]: 100 };
        }
        
        return { ...prev, [file.name]: newProgress };
      });
    }, 200);
  };

  const processAllFiles = () => {
    files.forEach(file => {
      if (uploadStatus[file.name] !== 'completed') {
        uploadFile(file);
      }
    });
  };

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Linear Algebra - Upload Question Papers</h1>
          <p className="text-gray-600">Upload 3-5 previous year papers for accurate predictions</p>
          <p className="text-sm text-gray-500">Supported formats: PDF (max 10MB per file)</p>
        </div>

        {/* Upload Area */}
        <div className="bg-white rounded-lg shadow p-8 mb-6">
          <div 
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              dragActive ? 'border-teal-500 bg-teal-50' : 'border-gray-300 hover:border-teal-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-upload')?.click()}
          >
            <div className="text-6xl mb-4">📁</div>
            <h3 className="text-xl font-semibold mb-2">Drag & drop PDF files here</h3>
            <p className="text-gray-600 mb-4">or click to select from computer</p>
            <p className="text-gray-500 text-sm">PDF files, 10MB max each</p>
            
            <input
              id="file-upload"
              type="file"
              multiple
              accept=".pdf"
              onChange={handleChange}
              className="hidden"
            />
          </div>
          
          <div className="mt-4 text-center">
            <button 
              onClick={() => document.getElementById('file-upload')?.click()}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
            >
              Or select multiple files
            </button>
          </div>
        </div>

        {/* Uploaded Files List */}
        {files.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Uploaded Papers ({files.length})</h2>
            
            <div className="space-y-4">
              {files.map((file, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <div className="text-2xl mr-3">📄</div>
                      <div>
                        <p className="font-medium truncate max-w-xs">{file.name}</p>
                        <p className="text-sm text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        uploadStatus[file.name] === 'pending' ? 'bg-gray-200 text-gray-800' :
                        uploadStatus[file.name] === 'processing' ? 'bg-yellow-200 text-yellow-800' :
                        uploadStatus[file.name] === 'completed' ? 'bg-green-200 text-green-800' :
                        'bg-red-200 text-red-800'
                      }`}>
                        {uploadStatus[file.name]}
                      </span>
                      
                      <button 
                        onClick={() => removeFile(file.name)}
                        className="text-red-500 hover:text-red-700"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  
                  {uploadStatus[file.name] === 'processing' && (
                    <div className="mt-3">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-teal-600 h-2 rounded-full" 
                          style={{ width: `${uploadProgress[file.name] || 0}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Processing... {(uploadProgress[file.name] || 0)}%</p>
                    </div>
                  )}
                  
                  {uploadStatus[file.name] === 'completed' && (
                    <div className="mt-2 text-sm text-green-600">
                      <p>✅ Extracted 25 questions</p>
                    </div>
                  )}
                  
                  <div className="flex mt-3 space-x-2">
                    <button className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">
                      Preview
                    </button>
                    {uploadStatus[file.name] === 'completed' && (
                      <button className="text-sm bg-blue-100 hover:bg-blue-200 px-3 py-1 rounded">
                        View Questions
                      </button>
                    )}
                    {uploadStatus[file.name] !== 'completed' && (
                      <button 
                        onClick={() => uploadFile(file)}
                        className="text-sm bg-teal-100 hover:bg-teal-200 px-3 py-1 rounded"
                      >
                        Process
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Statistics Section */}
        {files.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold">Total Papers Uploaded</h3>
                <p className="text-2xl font-bold">{files.length}</p>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold">Total Questions Extracted</h3>
                <p className="text-2xl font-bold">{files.length * 25}</p>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold">Questions by Marks</h3>
                <p>2-mark: {files.length * 10}</p>
                <p>5-mark: {files.length * 10}</p>
                <p>10-mark: {files.length * 5}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-4">
          <button 
            onClick={processAllFiles}
            disabled={files.length === 0}
            className={`px-6 py-3 rounded font-medium ${
              files.length === 0 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-teal-600 text-white hover:bg-teal-700'
            }`}
          >
            Generate Prediction
          </button>
          <button 
            disabled={files.length === 0}
            className={`px-6 py-3 rounded font-medium ${
              files.length === 0 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            View Extracted Questions
          </button>
          <button className="px-6 py-3 rounded font-medium bg-gray-200 text-gray-700 hover:bg-gray-300">
            Back to Subject
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default UploadPage;