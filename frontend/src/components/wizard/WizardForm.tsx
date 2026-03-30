'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { wizardService } from '@/src/lib/api';
import { ArrowRight, ArrowLeft, Check, GraduationCap, Target, Calendar } from 'lucide-react';

interface WizardFormProps {
  onComplete?: () => void;
}

const WizardForm: React.FC<WizardFormProps> = ({ onComplete }) => {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    examName: '',
    examDate: '',
    program: 'BTech',
    yearOfStudy: 1,
    focusSubjects: [] as string[],
    studyHoursPerDay: 2,
    targetScore: 75,
    preparationLevel: 'intermediate',
  });

  const subjects = [
    'Mathematics', 'Physics', 'Chemistry', 'Computer Science', 
    'Electrical Engineering', 'Mechanical Engineering', 'Data Structures',
    'Algorithms', 'Database Systems', 'Operating Systems', 'Computer Networks'
  ];

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubjectToggle = (subject: string) => {
    setFormData(prev => {
      const newSubjects = prev.focusSubjects.includes(subject)
        ? prev.focusSubjects.filter(s => s !== subject)
        : [...prev.focusSubjects, subject];
      return { ...prev, focusSubjects: newSubjects };
    });
  };

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await wizardService.completeWizard({
        exam_name: formData.examName,
        exam_date: formData.examDate,
        program: formData.program,
        year_of_study: formData.yearOfStudy,
        focus_subjects: formData.focusSubjects,
        study_hours_per_day: formData.studyHoursPerDay,
        target_score: formData.targetScore,
        preparation_level: formData.preparationLevel,
      });
      
      toast.success('Setup completed successfully!');
      onComplete?.();
      router.push('/protected');
    } catch (error) {
      toast.error('Failed to complete setup. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
          <GraduationCap className="h-5 w-5 text-indigo-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Basic Information</h3>
          <p className="text-sm text-gray-500">Tell us about your exam</p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="examName">Exam Name</Label>
          <Input
            id="examName"
            placeholder="e.g., Semester End Exams"
            value={formData.examName}
            onChange={(e) => handleInputChange('examName', e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor="examDate">Exam Date</Label>
          <Input
            id="examDate"
            type="date"
            value={formData.examDate}
            onChange={(e) => handleInputChange('examDate', e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="program">Program</Label>
            <Select 
              value={formData.program} 
              onValueChange={(value) => handleInputChange('program', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select program" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BTech">B.Tech</SelectItem>
                <SelectItem value="BSc">B.Sc</SelectItem>
                <SelectItem value="MSc">M.Sc</SelectItem>
                <SelectItem value="MTech">M.Tech</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="year">Year of Study</Label>
            <Select 
              value={String(formData.yearOfStudy)} 
              onValueChange={(value) => handleInputChange('yearOfStudy', parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select year" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1st Year</SelectItem>
                <SelectItem value="2">2nd Year</SelectItem>
                <SelectItem value="3">3rd Year</SelectItem>
                <SelectItem value="4">4th Year</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
          <Target className="h-5 w-5 text-indigo-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Focus Subjects</h3>
          <p className="text-sm text-gray-500">Select subjects to focus on</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {subjects.map((subject) => (
          <button
            key={subject}
            onClick={() => handleSubjectToggle(subject)}
            className={`p-3 rounded-lg border text-sm transition-all ${
              formData.focusSubjects.includes(subject)
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            {subject}
          </button>
        ))}
      </div>

      {formData.focusSubjects.length === 0 && (
        <p className="text-sm text-amber-600">Please select at least one subject</p>
      )}
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
          <Calendar className="h-5 w-5 text-indigo-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Study Goals</h3>
          <p className="text-sm text-gray-500">Set your preparation goals</p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="hours">Study Hours Per Day</Label>
          <div className="flex items-center gap-4 mt-2">
            <Input
              id="hours"
              type="range"
              min="1"
              max="12"
              value={formData.studyHoursPerDay}
              onChange={(e) => handleInputChange('studyHoursPerDay', parseInt(e.target.value))}
              className="flex-1"
            />
            <span className="text-lg font-semibold w-16">{formData.studyHoursPerDay} hrs</span>
          </div>
        </div>

        <div>
          <Label htmlFor="target">Target Score (%)</Label>
          <div className="flex items-center gap-4 mt-2">
            <Input
              id="target"
              type="range"
              min="50"
              max="100"
              value={formData.targetScore}
              onChange={(e) => handleInputChange('targetScore', parseInt(e.target.value))}
              className="flex-1"
            />
            <span className="text-lg font-semibold w-16">{formData.targetScore}%</span>
          </div>
        </div>

        <div>
          <Label htmlFor="level">Current Preparation Level</Label>
          <Select 
            value={formData.preparationLevel} 
            onValueChange={(value) => handleInputChange('preparationLevel', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="beginner">Beginner</SelectItem>
              <SelectItem value="intermediate">Intermediate</SelectItem>
              <SelectItem value="advanced">Advanced</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 to-white flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Setup Your Exam Prep</CardTitle>
          <p className="text-gray-500">Step {step} of 3</p>
        </CardHeader>
        <CardContent>
          {/* Progress Bar */}
          <div className="flex gap-2 mb-8">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-2 flex-1 rounded-full transition-all ${
                  s <= step ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
              />
            ))}
          </div>

          {/* Step Content */}
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={step === 1}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>

            {step < 3 ? (
              <Button onClick={handleNext}>
                Next
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button onClick={handleSubmit} disabled={loading}>
                {loading ? 'Saving...' : 'Complete Setup'}
                <Check className="h-4 w-4 ml-2" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WizardForm;
