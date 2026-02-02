'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import DashboardLayout from '@/components/dashboard/DashboardLayout';

const ProtectedPage = () => {
  const router = useRouter();

  const handleNavigate = (path: string) => {
    router.push(path);
  };

  const [userData, setUserData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  
  React.useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          router.push('/login');
          return;
        }
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setUserData(data);
        } else {
          router.push('/login');
        }
      } catch (error) {
        console.error('Error fetching user data:', error);
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };
    
    fetchUserData();
  }, [router]);
  
  if (loading) {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto p-6 flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-lg text-gray-600">Loading dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }
  
  if (!userData) {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto p-6 text-center py-12">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome to PrepIQ</h2>
          <p className="text-gray-600 mb-8">Get started by adding your first subject or uploading study materials.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={() => handleNavigate('/subjects')}
              className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition"
            >
              Add Your First Subject
            </button>
            <button 
              onClick={() => handleNavigate('/upload')}
              className="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold border border-indigo-600 hover:bg-indigo-50 transition"
            >
              Upload Study Materials
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }
  
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto p-6">
        {/* Hero Banner with Personalized Greeting */}
        <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-xl p-6 text-white mb-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2">Hi {userData.full_name || 'there'}!</h1>
              <p className="text-lg">Your {userData.program || 'program'} studies continue in {userData.college_name || 'your college'}</p>
            </div>
            <div className="mt-4 md:mt-0 bg-white/20 p-4 rounded-lg">
              <div className="text-center">
                <div className="text-3xl font-bold">{userData.days_to_exam || '45'} days</div>
                <div className="text-sm">to your next exam</div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl mb-2 text-indigo-600">📚</div>
            <h3 className="text-lg font-semibold mb-1">Subjects</h3>
            <p className="text-2xl font-bold text-gray-800">{userData.subjects_count || 0}</p>
            <p className="text-sm text-gray-600">Active courses</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl mb-2 text-indigo-600">📊</div>
            <h3 className="text-lg font-semibold mb-1">Progress</h3>
            <p className="text-2xl font-bold text-gray-800">{userData.completion_percentage || 0}%</p>
            <p className="text-sm text-gray-600">Overall completion</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl mb-2 text-indigo-600">🎯</div>
            <h3 className="text-lg font-semibold mb-1">Focus Area</h3>
            <p className="text-lg font-bold text-gray-800">{userData.focus_area || 'N/A'}</p>
            <p className="text-sm text-gray-600">Recommended topic</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl mb-2 text-indigo-600">🔥</div>
            <h3 className="text-lg font-semibold mb-1">Streak</h3>
            <p className="text-2xl font-bold text-gray-800">{userData.study_streak || 0} days</p>
            <p className="text-sm text-gray-600">Active learning</p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <div className="space-y-3">
            <div className="flex items-center p-3 border-b border-gray-100 last:border-0">
              <div className="mr-3 text-indigo-600">•</div>
              <div>
                <p className="font-medium">Started Linear Algebra preparation</p>
                <p className="text-sm text-gray-500">Today, 10:30 AM</p>
              </div>
            </div>
            <div className="flex items-center p-3 border-b border-gray-100 last:border-0">
              <div className="mr-3 text-indigo-600">•</div>
              <div>
                <p className="font-medium">Completed Calculus quiz</p>
                <p className="text-sm text-gray-500">Yesterday, 4:15 PM</p>
              </div>
            </div>
            <div className="flex items-center p-3 border-b border-gray-100 last:border-0">
              <div className="mr-3 text-indigo-600">•</div>
              <div>
                <p className="font-medium">Uploaded Physics notes</p>
                <p className="text-sm text-gray-500">Jan 5, 2026</p>
              </div>
            </div>
          </div>
        </div>

        {/* Today's Focus */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Today's Focus</h2>
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div>
              <p className="text-gray-600 mb-1">Recommended Focus:</p>
              <p className="text-lg font-semibold">{userData.focus_area || 'Unit 3 - Linear Transformations'}</p>
              <p className="text-green-600 text-sm">High probability topic</p>
            </div>
            <button 
              onClick={() => handleNavigate('/subjects')}
              className="mt-4 md:mt-0 bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-indigo-700 transition"
            >
              Start Studying
            </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ProtectedPage;