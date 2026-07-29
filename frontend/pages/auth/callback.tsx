import { useEffect } from 'react';
import { useRouter } from 'next/router';

/** OAuth removed — redirect any leftover callback hits to classic auth. */
export default function AuthCallbackPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/auth');
  }, [router]);

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-4"
      style={{ backgroundColor: 'var(--color-background)' }}
    >
      <span
        className="text-xs font-bold uppercase tracking-[0.2em]"
        style={{ color: 'var(--color-primary)' }}
      >
        Redirecting…
      </span>
    </div>
  );
}
