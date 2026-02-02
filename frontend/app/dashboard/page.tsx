'use client';

import React from 'react';
import DashboardLayout from '@/src/components/dashboard/DashboardLayout';

const DashboardPage = () => {
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Welcome Card */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Welcome back, John!</h1>
          <p className="text-red-600 font-semibold">Exam in 45 days</p>
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
                <p className="text-2xl font-bold">3</p>
              </div>
            </div>
            <a href="#" className="text-blue-600 text-sm mt-2 inline-block">View all</a>
          </div>

          {/* Papers Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600 mr-4">
                📄
              </div>
              <div>
                <p className="text-gray-500">Papers uploaded</p>
                <p className="text-2xl font-bold">12</p>
                <p className="text-gray-500 text-sm">Last: Jan 5, 2025</p>
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
                <p className="text-2xl font-bold">2</p>
                <p className="text-green-600 text-sm">85% accuracy</p>
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
                <p className="text-2xl font-bold">5</p>
                <p className="text-gray-500 text-sm">Avg: 72%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Subjects Grid */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">My Subjects</h2>
            <button className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-700">
              + Add Subject
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Subject Card 1 */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6">
                <h3 className="text-lg font-bold">Linear Algebra</h3>
                <p className="text-gray-500">MA201</p>
                <p className="text-sm text-gray-500">Semester 2</p>
                
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Papers: 5 uploaded</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Predictions: Generated</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Exams: In 45 days</span>
                  </div>
                </div>
                
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-teal-600 h-2 rounded-full" style={{width: '65%'}}></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Predictions readiness: 65%</p>
                </div>
                
                <div className="flex mt-4 space-x-2">
                  <button className="flex-1 bg-gray-100 text-gray-700 py-2 rounded hover:bg-gray-200 text-sm">
                    📤 Upload Paper
                  </button>
                  <button className="flex-1 bg-teal-100 text-teal-700 py-2 rounded hover:bg-teal-200 text-sm">
                    🔮 View Prediction
                  </button>
                  <button className="flex-1 bg-purple-100 text-purple-700 py-2 rounded hover:bg-purple-200 text-sm">
                    🎯 Start Mock Test
                  </button>
                </div>
              </div>
            </div>
            
            {/* Subject Card 2 */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6">
                <h3 className="text-lg font-bold">Data Structures</h3>
                <p className="text-gray-500">CS201</p>
                <p className="text-sm text-gray-500">Semester 2</p>
                
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Papers: 4 uploaded</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Predictions: Generated</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Exams: In 45 days</span>
                  </div>
                </div>
                
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-teal-600 h-2 rounded-full" style={{width: '70%'}}></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Predictions readiness: 70%</p>
                </div>
                
                <div className="flex mt-4 space-x-2">
                  <button className="flex-1 bg-gray-100 text-gray-700 py-2 rounded hover:bg-gray-200 text-sm">
                    📤 Upload Paper
                  </button>
                  <button className="flex-1 bg-teal-100 text-teal-700 py-2 rounded hover:bg-teal-200 text-sm">
                    🔮 View Prediction
                  </button>
                  <button className="flex-1 bg-purple-100 text-purple-700 py-2 rounded hover:bg-purple-200 text-sm">
                    🎯 Start Mock Test
                  </button>
                </div>
              </div>
            </div>
            
            {/* Subject Card 3 */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6">
                <h3 className="text-lg font-bold">Calculus</h3>
                <p className="text-gray-500">MA202</p>
                <p className="text-sm text-gray-500">Semester 2</p>
                
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Papers: 3 uploaded</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Predictions: Not generated</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Exams: In 45 days</span>
                  </div>
                </div>
                
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-teal-600 h-2 rounded-full" style={{width: '40%'}}></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Predictions readiness: 40%</p>
                </div>
                
                <div className="flex mt-4 space-x-2">
                  <button className="flex-1 bg-gray-100 text-gray-700 py-2 rounded hover:bg-gray-200 text-sm">
                    📤 Upload Paper
                  </button>
                  <button className="flex-1 bg-teal-100 text-teal-700 py-2 rounded hover:bg-teal-200 text-sm">
                    🔮 View Prediction
                  </button>
                  <button className="flex-1 bg-purple-100 text-purple-700 py-2 rounded hover:bg-purple-200 text-sm">
                    🎯 Start Mock Test
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Jan 5, 8:30 PM - Generated prediction for Linear Algebra</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Jan 5, 7:45 PM - Uploaded 2025 exam paper</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Jan 4, 3:20 PM - Scored 85/100 in mock test</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Jan 3, 10:15 AM - Started study plan for Data Structures</span>
            </li>
          </ul>
          <button className="text-blue-600 mt-2">Show more</button>
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