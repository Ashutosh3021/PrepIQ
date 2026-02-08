'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Mail, 
  Building, 
  Calendar, 
  GraduationCap, 
  Clock, 
  Award,
  Edit3
} from 'lucide-react';

export default function ProfilePage() {
  const [userData, setUserData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const token = localStorage.getItem('access_token');
        if (!token) {
          setError('No authentication token found. Please log in again.');
          setLoading(false);
          return;
        }

        // Get API URL with fallback to default
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        const response = await fetch(`${apiUrl}/auth/profile`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setUserData(data);
        } else {
          const errorData = await response.json().catch(() => ({}));
          setError(errorData.detail || 'Failed to fetch user data');
        }
      } catch (error) {
        console.error('Error fetching user data:', error);
        setError('Network error occurred while fetching user data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchUserData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error || !userData) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">My Profile</h1>
          <p className="text-muted-foreground">View and manage your profile information</p>
        </div>
        <Card>
          <CardContent className="p-6">
            <p className="text-red-500">{error || 'Unable to load profile data'}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">My Profile</h1>
          <p className="text-muted-foreground">View and manage your profile information</p>
        </div>
        <Button>
          <Edit3 className="h-4 w-4 mr-2" />
          Edit Profile
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Profile Card */}
        <Card className="md:col-span-1">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4">
              <Avatar className="h-24 w-24 mx-auto">
                <AvatarImage src="/placeholder-user.jpg" alt={userData.full_name} />
                <AvatarFallback className="text-2xl">
                  {getInitials(userData.full_name)}
                </AvatarFallback>
              </Avatar>
            </div>
            <CardTitle className="text-xl">{userData.full_name}</CardTitle>
            <CardDescription className="text-base">{userData.email}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Separator />
            <div className="space-y-3">
              <div className="flex items-center text-sm">
                <Building className="h-4 w-4 mr-2 text-muted-foreground" />
                <span className="text-muted-foreground">College:</span>
                <span className="ml-auto font-medium">{userData.college_name || 'Not specified'}</span>
              </div>
              <div className="flex items-center text-sm">
                <GraduationCap className="h-4 w-4 mr-2 text-muted-foreground" />
                <span className="text-muted-foreground">Program:</span>
                <span className="ml-auto font-medium">{userData.program || 'Not specified'}</span>
              </div>
              <div className="flex items-center text-sm">
                <Calendar className="h-4 w-4 mr-2 text-muted-foreground" />
                <span className="text-muted-foreground">Year:</span>
                <span className="ml-auto font-medium">{userData.year_of_study || 'Not specified'}</span>
              </div>
              <div className="flex items-center text-sm">
                <Award className="h-4 w-4 mr-2 text-muted-foreground" />
                <span className="text-muted-foreground">Status:</span>
                <Badge className="ml-auto">Active</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Details Card */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Account Details</CardTitle>
            <CardDescription>Your profile information and preferences</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Personal Information</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Full Name</span>
                    <span className="font-medium">{userData.full_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Email</span>
                    <span className="font-medium">{userData.email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">College</span>
                    <span className="font-medium">{userData.college_name || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Program</span>
                    <span className="font-medium">{userData.program || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Year of Study</span>
                    <span className="font-medium">{userData.year_of_study || 'Not specified'}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Preferences</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Theme</span>
                    <span className="font-medium capitalize">{userData.theme_preference || 'system'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Language</span>
                    <span className="font-medium uppercase">{userData.language || 'en'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Account Status</span>
                    <Badge variant="secondary">Verified</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Member Since</span>
                    <span className="font-medium">
                      {userData.created_at 
                        ? new Date(userData.created_at).toLocaleDateString() 
                        : 'Not available'
                      }
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Updated</span>
                    <span className="font-medium">
                      {userData.updated_at 
                        ? new Date(userData.updated_at).toLocaleDateString() 
                        : 'Not available'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stats Card */}
      <Card>
        <CardHeader>
          <CardTitle>Learning Progress</CardTitle>
          <CardDescription>Your academic journey statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-muted/30 rounded-lg">
              <div className="text-2xl font-bold text-primary">0</div>
              <div className="text-sm text-muted-foreground">Subjects</div>
            </div>
            <div className="text-center p-4 bg-muted/30 rounded-lg">
              <div className="text-2xl font-bold text-primary">0%</div>
              <div className="text-sm text-muted-foreground">Progress</div>
            </div>
            <div className="text-center p-4 bg-muted/30 rounded-lg">
              <div className="text-2xl font-bold text-primary">0</div>
              <div className="text-sm text-muted-foreground">Tests Taken</div>
            </div>
            <div className="text-center p-4 bg-muted/30 rounded-lg">
              <div className="text-2xl font-bold text-primary">0 days</div>
              <div className="text-sm text-muted-foreground">Study Streak</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}