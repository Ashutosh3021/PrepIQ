'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/src/lib/api';
import type { WizardStatus, WizardStep1Data, WizardStep2Data, WizardStep3Data } from '@/src/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';

interface WizardFormProps {
  onComplete?: () => void;
}

const WizardForm: React.FC<WizardFormProps> = ({ onComplete }) => {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [wizardData, setWizardData] = useState<WizardStatus>({
    completed: false,
    exam_name: '',
    days_until_exam: 30,
    focus_subjects: [],
    study_hours_per_day: 2,
    target_score: 80,
    preparation_level: 'intermediate'
  });

  // Common subjects for selection
  const commonSubjects = [
    'Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science',
    'English', 'History', 'Geography', 'Economics', 'Political Science',
    'Business Studies', 'Accountancy', 'Statistics', 'Psychology',
    'Sociology', 'Philosophy', 'Languages', 'Engineering'
  ];

  useEffect(() => {
    // Check if wizard is already completed
    const checkWizardStatus = async () => {
      try {
        const status = await authService.getWizardStatus();
        if (status.completed) {
          // If already completed, redirect to dashboard
          router.push('/protected');
        } else {
          // Load existing partial data
          setWizardData({
            ...wizardData,
            ...status
          });
        }
      } catch (error) {
        console.error('Error checking wizard status:', error);
        toast.error('Failed to load wizard status');
      }
    };

    checkWizardStatus();
  }, []);

  const handleNext = async () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    } else {
      // Complete the wizard
      await completeWizard();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const completeWizard = async () => {
    try {
      setLoading(true);
      
      // Complete the wizard
      await authService.completeWizard();
      
      toast.success('Setup completed successfully! Welcome to PrepIQ.');
      
      // Call onComplete callback if provided
      if (onComplete) {
        onComplete();
      } else {
        // Redirect to dashboard
        router.push('/protected');
      }
    } catch (error) {
      console.error('Error completing wizard:', error);
      toast.error('Failed to complete setup. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleStep1Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const step1Data: WizardStep1Data = {
        exam_name: wizardData.exam_name || '',
        days_until_exam: wizardData.days_until_exam || 30
      };
      
      await authService.completeWizardStep1(step1Data);
      handleNext();
    } catch (error) {
      console.error('Error in step 1:', error);
      toast.error('Failed to save step 1 data');
    } finally {
      setLoading(false);
    }
  };

  const handleStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const step2Data: WizardStep2Data = {
        focus_subjects: wizardData.focus_subjects || [],
        study_hours_per_day: wizardData.study_hours_per_day || 2
      };
      
      await authService.completeWizardStep2(step2Data);
      handleNext();
    } catch (error) {
      console.error('Error in step 2:', error);
      toast.error('Failed to save step 2 data');
    } finally {
      setLoading(false);
    }
  };

  const handleStep3Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const step3Data: WizardStep3Data = {
        target_score: wizardData.target_score || 80,
        preparation_level: wizardData.preparation_level || 'intermediate'
      };
      
      await authService.completeWizardStep3(step3Data);
      handleNext();
    } catch (error) {
      console.error('Error in step 3:', error);
      toast.error('Failed to save step 3 data');
    } finally {
      setLoading(false);
    }
  };

  const toggleSubject = (subject: string) => {
    setWizardData(prev => {
      const currentSubjects = prev.focus_subjects || [];
      const newSubjects = currentSubjects.includes(subject)
        ? currentSubjects.filter(s => s !== subject)
        : [...currentSubjects, subject];
      
      return {
        ...prev,
        focus_subjects: newSubjects
      };
    });
  };

  const renderStep1 = () => (
    <form onSubmit={handleStep1Submit} className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Welcome to PrepIQ!</h2>
        <p className="text-gray-600 mt-2">Let's customize your study experience</p>
      </div>
      
      <div className="space-y-4">
        <div>
          <Label htmlFor="exam_name" className="text-sm font-medium">
            What exam are you preparing for?
          </Label>
          <Input
            id="exam_name"
            value={wizardData.exam_name || ''}
            onChange={(e) => setWizardData({...wizardData, exam_name: e.target.value})}
            placeholder="e.g., JEE Main, GATE, NEET, etc."
            required
            className="mt-1"
          />
        </div>
        
        <div>
          <Label htmlFor="days_until_exam" className="text-sm font-medium">
            How many days until your exam?
          </Label>
          <Input
            id="days_until_exam"
            type="number"
            min="1"
            max="365"
            value={wizardData.days_until_exam || ''}
            onChange={(e) => setWizardData({...wizardData, days_until_exam: parseInt(e.target.value) || 30})}
            required
            className="mt-1"
          />
        </div>
      </div>
      
      <div className="flex justify-between pt-6">
        <div></div> {/* Empty div for spacing */}
        <Button type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Next'}
        </Button>
      </div>
    </form>
  );

  const renderStep2 = () => (
    <form onSubmit={handleStep2Submit} className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Your Study Focus</h2>
        <p className="text-gray-600 mt-2">Select the subjects you want to focus on</p>
      </div>
      
      <div className="space-y-4">
        <div>
          <Label className="text-sm font-medium mb-3 block">
            Select your subjects (choose 1-10):
          </Label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto p-2 border rounded">
            {commonSubjects.map((subject) => (
              <div key={subject} className="flex items-center space-x-2">
                <Checkbox
                  id={subject}
                  checked={wizardData.focus_subjects?.includes(subject) || false}
                  onCheckedChange={() => toggleSubject(subject)}
                />
                <label
                  htmlFor={subject}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {subject}
                </label>
              </div>
            ))}
          </div>
          {wizardData.focus_subjects && wizardData.focus_subjects.length > 0 && (
            <p className="text-sm text-gray-500 mt-2">
              Selected: {wizardData.focus_subjects.length} subject(s)
            </p>
          )}
        </div>
        
        <div>
          <Label htmlFor="study_hours" className="text-sm font-medium">
            How many hours per day can you study?
          </Label>
          <Select
            value={wizardData.study_hours_per_day?.toString() || '2'}
            onValueChange={(value) => setWizardData({...wizardData, study_hours_per_day: parseInt(value)})}
          >
            <SelectTrigger className="mt-1">
              <SelectValue placeholder="Select hours per day" />
            </SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((hours) => (
                <SelectItem key={hours} value={hours.toString()}>
                  {hours} hour{hours > 1 ? 's' : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="flex justify-between pt-6">
        <Button variant="outline" onClick={handlePrevious} disabled={loading}>
          Previous
        </Button>
        <Button type="submit" disabled={loading || !wizardData.focus_subjects || wizardData.focus_subjects.length === 0}>
          {loading ? 'Saving...' : 'Next'}
        </Button>
      </div>
    </form>
  );

  const renderStep3 = () => (
    <form onSubmit={handleStep3Submit} className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Your Goals</h2>
        <p className="text-gray-600 mt-2">Set your target score and preparation level</p>
      </div>
      
      <div className="space-y-4">
        <div>
          <Label htmlFor="target_score" className="text-sm font-medium">
            What's your target score? (%)
          </Label>
          <Input
            id="target_score"
            type="number"
            min="1"
            max="100"
            value={wizardData.target_score || ''}
            onChange={(e) => setWizardData({...wizardData, target_score: parseInt(e.target.value) || 80})}
            required
            className="mt-1"
          />
        </div>
        
        <div>
          <Label htmlFor="preparation_level" className="text-sm font-medium">
            What's your current preparation level?
          </Label>
          <Select
            value={wizardData.preparation_level || 'intermediate'}
            onValueChange={(value) => setWizardData({...wizardData, preparation_level: value})}
          >
            <SelectTrigger className="mt-1">
              <SelectValue placeholder="Select preparation level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="beginner">Beginner</SelectItem>
              <SelectItem value="intermediate">Intermediate</SelectItem>
              <SelectItem value="advanced">Advanced</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
        <h3 className="font-medium text-blue-800">What's next?</h3>
        <p className="text-blue-700 text-sm mt-1">
          After completing setup, you'll be able to:
        </p>
        <ul className="text-blue-700 text-sm mt-2 list-disc list-inside space-y-1">
          <li>Get personalized study recommendations</li>
          <li>See predicted question patterns</li>
          <li>Track your progress with analytics</li>
          <li>Take mock tests tailored to your goals</li>
        </ul>
      </div>
      
      <div className="flex justify-between pt-6">
        <Button variant="outline" onClick={handlePrevious} disabled={loading}>
          Previous
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Complete Setup'}
        </Button>
      </div>
    </form>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return renderStep1();
      case 2: return renderStep2();
      case 3: return renderStep3();
      default: return renderStep1();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl shadow-xl">
        <CardHeader className="text-center pb-2">
          <div className="flex justify-center mb-4">
            <div className="flex space-x-2">
              {[1, 2, 3].map((step) => (
                <div
                  key={step}
                  className={`w-3 h-3 rounded-full ${
                    currentStep >= step 
                      ? 'bg-indigo-600' 
                      : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
          <CardTitle className="text-xl">
            Step {currentStep} of 3
          </CardTitle>
        </CardHeader>
        <CardContent>
          {renderCurrentStep()}
        </CardContent>
      </Card>
    </div>
  );
};

export default WizardForm;