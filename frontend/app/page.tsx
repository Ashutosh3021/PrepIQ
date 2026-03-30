'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { 
  GraduationCap, 
  Brain, 
  Target, 
  FileText, 
  Sparkles, 
  ArrowRight, 
  CheckCircle2,
  Zap,
  BarChart3,
  Users
} from 'lucide-react';

export default function LandingPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsAuthenticated(true);
      router.push('/protected');
    }
  }, [router]);

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Predictions',
      description: 'Get personalized question predictions with 80%+ accuracy using advanced ML models.'
    },
    {
      icon: FileText,
      title: 'Smart Document Analysis',
      description: 'Upload past papers and automatically extract questions, topics, and patterns.'
    },
    {
      icon: Target,
      title: 'Mock Test Generation',
      description: 'Generate unlimited practice tests tailored to your subjects and exam pattern.'
    },
    {
      icon: BarChart3,
      title: 'Progress Analytics',
      description: 'Track your study progress with detailed analytics and performance insights.'
    }
  ];

  const steps = [
    {
      number: '01',
      title: 'Upload Your Papers',
      description: 'Add previous year question papers, notes, and study materials.'
    },
    {
      number: '02',
      title: 'Get AI Predictions',
      description: 'Our AI analyzes patterns and predicts likely exam questions.'
    },
    {
      number: '03',
      title: 'Practice & Improve',
      description: 'Take mock tests and track your progress to ace your exams.'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-slate-50">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <GraduationCap className="h-8 w-8 text-indigo-600" />
              <span className="text-xl font-bold text-gray-900">PrepIQ</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/login">
                <Button variant="ghost">Sign In</Button>
              </Link>
              <Link href="/signup">
                <Button className="bg-indigo-600 hover:bg-indigo-700">Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-100 text-indigo-700 text-sm font-medium mb-6">
              <Sparkles className="h-4 w-4" />
              AI-Powered Exam Preparation
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Predict Your Exam Questions
              <span className="block text-indigo-600">Before They Appear</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
              PrepIQ uses advanced AI to analyze your study materials and predict 
              questions with 80%+ accuracy. Upload papers, get predictions, and ace your exams.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/signup">
                <Button size="lg" className="bg-indigo-600 hover:bg-indigo-700 text-lg px-8">
                  Start Free <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="text-lg px-8">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-slate-50 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Ace Your Exams
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Powerful AI tools designed to make your preparation smarter and more effective.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
                <CardContent className="p-6">
                  <div className="w-12 h-12 rounded-lg bg-indigo-100 flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-indigo-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600">
              Three simple steps to smarter exam preparation
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-600 text-white text-2xl font-bold mb-6">
                  {step.number}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-gray-600">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-indigo-600 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Exam Prep?
          </h2>
          <p className="text-xl text-indigo-100 mb-8">
            Join thousands of students already using PrepIQ to ace their exams.
          </p>
          <Link href="/signup">
            <Button size="lg" className="bg-white text-indigo-600 hover:bg-indigo-50 text-lg px-8">
              Get Started for Free <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-gray-900 text-gray-400 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <GraduationCap className="h-6 w-6 text-indigo-400" />
              <span className="text-lg font-bold text-white">PrepIQ</span>
            </div>
            <p className="text-sm">
              © 2025 PrepIQ. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
