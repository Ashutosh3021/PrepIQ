'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authService, dashboardService } from '@/src/lib/api';
import type { UserProfile, DashboardStats } from '@/src/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Calendar, BookOpen, Target, Flame, TrendingUp, ArrowRight, Sparkles } from 'lucide-react';

const ProtectedPage = () => {
  const router = useRouter();

  const handleNavigate = (path: string) => {
    router.push(path);
  };

  const [userData, setUserData] = React.useState<UserProfile | null>(null);
  const [dashboardStats, setDashboardStats] = React.useState<DashboardStats | null>(null);
  const [loading, setLoading] = React.useState(true);
  
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch user profile
        const user = await authService.getCurrentUser();
        setUserData(user);
        
        // Fetch dashboard stats
        const stats = await dashboardService.getStats();
        setDashboardStats(stats);
        
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to load dashboard data';
        toast.error(errorMessage);
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [router]);
  
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        {/* Hero Skeleton */}
        <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-xl p-6 mb-8">
          <Skeleton className="h-8 w-64 bg-white/20 mb-2" />
          <Skeleton className="h-4 w-96 bg-white/20" />
        </div>
        
        {/* Stats Grid Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-8 w-8 mb-4" />
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }
  
  if (!userData) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Card className="text-center py-12">
          <CardContent>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome to PrepIQ</h2>
            <p className="text-gray-600 mb-8">Get started by completing your setup or adding your first subject.</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                onClick={() => handleNavigate('/wizard')}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                Complete Setup Wizard
              </Button>
              <Button 
                variant="outline"
                onClick={() => handleNavigate('/subjects')}
              >
                Add Your First Subject
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const hasExamData = dashboardStats?.days_to_exam !== null && dashboardStats?.days_to_exam !== undefined;
  
  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Hero Banner with Personalized Greeting */}
      <Card className="bg-gradient-to-r from-indigo-500 to-indigo-600 border-0 text-white overflow-hidden">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-5 w-5 text-yellow-300" />
                <h1 className="text-2xl md:text-3xl font-bold">
                  Hi {userData.full_name || 'there'}!
                </h1>
              </div>
              <p className="text-indigo-100">
                Your {userData.program || 'program'} studies continue in {userData.college_name || 'your college'}
              </p>
            </div>
            
            {hasExamData ? (
              <div className="bg-white/20 backdrop-blur-sm p-4 rounded-lg text-center">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <Calendar className="h-5 w-5" />
                  <span className="text-3xl font-bold">{dashboardStats?.days_to_exam}</span>
                </div>
                <div className="text-sm text-indigo-100">
                  {dashboardStats?.days_to_exam === 1 ? 'day' : 'days'} to your exam
                </div>
              </div>
            ) : (
              <div className="bg-white/20 backdrop-blur-sm p-4 rounded-lg">
                <p className="text-sm mb-2">No exam date set</p>
                <Link href="/wizard">
                  <Button 
                    variant="secondary" 
                    size="sm"
                    className="bg-white text-indigo-600 hover:bg-indigo-50"
                  >
                    Set Exam Date <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Subjects Card */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-lg bg-blue-100">
                <BookOpen className="h-6 w-6 text-blue-600" />
              </div>
              <span className="text-3xl font-bold text-gray-800">
                {dashboardStats?.subjects_count || 0}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-700">Subjects</h3>
            <p className="text-sm text-gray-500">Active courses</p>
          </CardContent>
        </Card>
        
        {/* Progress Card */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-lg bg-green-100">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <span className="text-3xl font-bold text-gray-800">
                {dashboardStats?.completion_percentage || 0}%
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-700">Progress</h3>
            <p className="text-sm text-gray-500">Overall completion</p>
          </CardContent>
        </Card>
        
        {/* Focus Area Card */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-lg bg-purple-100">
                <Target className="h-6 w-6 text-purple-600" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-gray-700 mb-1">Focus Area</h3>
            <p className="text-lg font-medium text-gray-800 truncate">
              {dashboardStats?.focus_area || 'No subjects yet'}
            </p>
            <p className="text-sm text-gray-500">Recommended topic</p>
          </CardContent>
        </Card>
        
        {/* Streak Card */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-lg bg-orange-100">
                <Flame className="h-6 w-6 text-orange-600" />
              </div>
              <span className="text-3xl font-bold text-gray-800">
                {dashboardStats?.study_streak || 0}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-700">Streak</h3>
            <p className="text-sm text-gray-500">
              {dashboardStats?.study_streak === 1 ? 'day' : 'days'} of active learning
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          {dashboardStats?.recent_activity && dashboardStats.recent_activity.length > 0 ? (
            <div className="space-y-3">
              {dashboardStats.recent_activity.map((activity, index) => (
                <div 
                  key={index} 
                  className="flex items-center p-3 border-b border-gray-100 last:border-0 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <div className="mr-3 h-2 w-2 rounded-full bg-indigo-600"></div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-800">{activity.action}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📚</div>
              <h3 className="text-lg font-medium text-gray-800 mb-2">Ready to Start Your Journey?</h3>
              <p className="text-gray-500 mb-4">Set up your subjects, upload your resources, and start studying smart with AI-powered insights!</p>
              <p className="text-sm text-indigo-600 font-medium">
                💡 Tip: Upload previous year papers to get personalized predictions and study recommendations
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Today's Focus */}
      <Card>
        <CardHeader>
          <CardTitle>Today&apos;s Focus</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <p className="text-gray-600 mb-1">Recommended Focus:</p>
              <p className="text-lg font-semibold text-gray-800">
                {dashboardStats?.focus_area || 'Complete your setup to get recommendations'}
              </p>
              {dashboardStats?.focus_area && (
                <p className="text-green-600 text-sm flex items-center gap-1 mt-1">
                  <TrendingUp className="h-4 w-4" />
                  High probability topic
                </p>
              )}
            </div>
            <Button 
              onClick={() => handleNavigate('/subjects')}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Start Studying <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProtectedPage;
