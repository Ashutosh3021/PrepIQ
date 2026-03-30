'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('Processing authentication...');

  useEffect(() => {
    const handleCallback = async () => {
      const error = searchParams.get('error');
      const code = searchParams.get('code');
      
      if (error) {
        setStatus('Authentication failed. Redirecting to login...');
        setTimeout(() => router.push('/login'), 2000);
        return;
      }

      // For hash-based auth (Supabase default)
      const hash = window.location.hash;
      if (hash && hash.includes('access_token')) {
        const params = new URLSearchParams(hash.substring(1));
        const accessToken = params.get('access_token');
        const refreshToken = params.get('refresh_token');
        
        if (accessToken) {
          localStorage.setItem('access_token', accessToken);
          if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
          }
          setStatus('Authentication successful! Redirecting...');
          setTimeout(() => router.push('/protected'), 1000);
          return;
        }
      }

      // If we have a code but no hash, exchange it for tokens
      if (code) {
        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/oauth/callback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code }),
          });
          
          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            if (data.refresh_token) {
              localStorage.setItem('refresh_token', data.refresh_token);
            }
            setStatus('Authentication successful! Redirecting...');
            setTimeout(() => router.push('/protected'), 1000);
          } else {
            throw new Error('Token exchange failed');
          }
        } catch (err) {
          setStatus('Authentication failed. Redirecting to login...');
          setTimeout(() => router.push('/login'), 2000);
        }
        return;
      }

      // No valid auth data found
      setStatus('Authentication failed. Redirecting to login...');
      setTimeout(() => router.push('/login'), 2000);
    };

    handleCallback();
  }, [router, searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
        <p className="text-gray-600">{status}</p>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  );
}
