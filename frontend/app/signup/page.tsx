'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function SignupPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    college_name: '',
    program: '',
    year_of_study: 1
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      // Get API URL with fallback to default
      let apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      // Remove trailing slash if present to avoid double slashes
      apiUrl = apiUrl.replace(/\/$/, '');
      const fullUrl = `${apiUrl}/auth/signup`;
      
      console.log('🚀 Attempting to connect to:', fullUrl);
      console.log('📦 Form data:', formData);
      
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      console.log('✅ Response received:', response.status);
      const data = await response.json();
      console.log('📄 Response data:', data);

      if (response.ok) {
        setSuccess(true);
        // Show success message and redirect to login after a delay
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      } else {
        // Handle both string and object error responses
        let errorMessage = 'Signup failed';
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            // Handle validation errors array
            errorMessage = data.detail.map((err: any) => err.msg).join(', ');
          } else if (typeof data.detail === 'object' && data.detail.msg) {
            // Handle single validation error object
            errorMessage = data.detail.msg;
          } else {
            errorMessage = JSON.stringify(data.detail);
          }
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.error) {
          errorMessage = data.error;
        }
        setError(errorMessage);
      }
    } catch (err) {
      // Handle network errors and other exceptions
      console.error('❌ Signup error details:', err);
      const error = err as Error;
      console.error('Error name:', error.name);
      console.error('Error message:', error.message);
      
      if (error.name === 'TypeError' && error.message?.includes('fetch')) {
        setError(`Failed to connect to the server at ${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}. Please check:
1. Backend server is running (python start_server.py)
2. No firewall/antivirus blocking the connection
3. Correct API URL in .env.local file`);
      } else {
        setError(`Error: ${error.message || 'An unexpected error occurred'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your PrepIQ account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Study Smart. Score High.
          </p>
        </div>
        
        {success && (
          <div className="rounded-md bg-green-50 p-4">
            <div className="text-sm text-green-700">
              Signup successful! Redirecting to login page...
            </div>
          </div>
        )}
        
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
        )}
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="full-name" className="sr-only">
                Full Name
              </label>
              <input
                id="full-name"
                name="full_name"
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Full Name"
                value={formData.full_name}
                onChange={handleChange}
                disabled={loading || success}
              />
            </div>
            <div>
              <label htmlFor="email-address" className="sr-only">
                Email address
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={formData.email}
                onChange={handleChange}
                disabled={loading || success}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                minLength={6}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password (minimum 6 characters)"
                value={formData.password}
                onChange={handleChange}
                disabled={loading || success}
              />
            </div>
            <div>
              <label htmlFor="college-name" className="sr-only">
                College Name
              </label>
              <input
                id="college-name"
                name="college_name"
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="College Name"
                value={formData.college_name}
                onChange={handleChange}
                disabled={loading || success}
              />
            </div>
            <div>
              <label htmlFor="program" className="sr-only">
                Program
              </label>
              <select
                id="program"
                name="program"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                value={formData.program}
                onChange={handleChange}
                disabled={loading || success}
              >
                <option value="">Select Program</option>
                <option value="BTech">BTech</option>
                <option value="BSc">BSc</option>
                <option value="MSc">MSc</option>
                <option value="BE">BE</option>
                <option value="BCA">BCA</option>
                <option value="MCA">MCA</option>
              </select>
            </div>
            <div>
              <label htmlFor="year" className="sr-only">
                Year of Study
              </label>
              <select
                id="year"
                name="year_of_study"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                value={formData.year_of_study}
                onChange={handleChange}
                disabled={loading || success}
              >
                <option value={1}>1st Year</option>
                <option value={2}>2nd Year</option>
                <option value={3}>3rd Year</option>
                <option value={4}>4th Year</option>
              </select>
            </div>
          </div>

          <div className="flex items-center">
            <input
              id="terms"
              name="terms"
              type="checkbox"
              required
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              disabled={loading || success}
            />
            <label htmlFor="terms" className="ml-2 block text-sm text-gray-900">
              I agree to the <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500">Terms and Conditions</a>
            </label>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading || success}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {success ? 'Redirecting...' : (loading ? 'Creating account...' : 'Sign up')}
            </button>
          </div>
        </form>
        
        <div className="text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}