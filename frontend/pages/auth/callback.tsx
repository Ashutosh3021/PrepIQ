/**
 * /auth/callback is no longer used (OAuth removed).
 * Redirect anyone landing here to /auth so they can log in with email/password.
 */
import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/auth');
  }, [router]);

  return null;
}
