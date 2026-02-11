'use client';

import React from 'react';
import DashboardLayout from '@/src/components/dashboard/DashboardLayout';

const DashboardPage = () => {
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Welcome Card */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Welcome back!</h1>
          <p className="text-red-600 font-semibold">Track your exam preparation progress</p>
          <div className="flex mt-4 space-x-4">
            <button className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-700">
              + Upload Papers
            </button>
            <button className="bg-teal-100 text-teal-700 px-4 py-2 rounded hover:bg-teal-200">
              Generate Prediction
            </button>
          </div>
        </div>

        {/* Quick Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {/* Subjects Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100 text-blue-600 mr-4">
                📚
              </div>
              <div>
                <p className="text-gray-500">Subjects</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
            <a href="/subjects" className="text-blue-600 text-sm mt-2 inline-block">View all</a>
          </div>

          {/* Papers Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600 mr-4">
                📄
              </div>
              <div>
                <p className="text-gray-500">Papers uploaded</p>
                <p className="text-2xl font-bold">0</p>
                <p className="text-gray-500 text-sm">Upload your first paper</p>
              </div>
            </div>
          </div>

          {/* Predictions Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100 text-yellow-600 mr-4">
                🔮
              </div>
              <div>
                <p className="text-gray-500">Predictions</p>
                <p className="text-2xl font-bold">0</p>
                <p className="text-green-600 text-sm">Generate predictions</p>
              </div>
            </div>
          </div>

          {/* Mock Tests Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100 text-purple-600 mr-4">
                📝
              </div>
              <div>
                <p className="text-gray-500">Mock tests</p>
                <p className="text-2xl font-bold">0</p>
                <p className="text-gray-500 text-sm">Start practicing</p>
              </div>
            </div>
          </div>
        </div>

        {/* Subjects Grid */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">My Subjects</h2>
            <a href="/subjects" className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-700">
              + Add Subject
            </a>
          </div>
          
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-4xl mb-4">📚</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">No subjects yet</h3>
            <p className="text-gray-600 mb-4">Add your first subject to start tracking your exam preparation</p>
            <a href="/subjects" className="bg-teal-600 text-white px-6 py-2 rounded hover:bg-teal-700 inline-block">
              Add Your First Subject
            </a>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <div className="text-center py-8 text-gray-500">
            <p>No recent activity yet.</p>
            <p className="text-sm mt-1">Start by adding a subject or uploading study materials!</p>
          </div>
        </div>

        {/* Help Section */}
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-xl font-semibold mb-4">Getting Started?</h2>
          <div className="space-y-2">
            <p>1. Upload 3-5 previous year papers</p>
            <p>2. Run prediction to see high-probability questions</p>
            <p>3. Take mock tests to practice</p>
          </div>
          <button className="text-blue-600 mt-2">Watch tutorial video</button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DashboardPage;