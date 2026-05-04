import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/lib/context/AuthContext';
import { apiFetch } from '@/lib/services/base.service';
import { getWizardPath } from '@/lib/utils/device';

interface WizardStatus {
  completed: boolean;
}

/**
 * Wrap any page that requires authentication.
 *
 * Behaviour:
 *  - Not logged in          → redirect to /auth
 *  - Logged in, wizard done → render children
 *  - Logged in, no wizard   → redirect to /wizard
 */
export default function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return function AuthGuard(props: P) {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [checking, setChecking] = useState(true);

    useEffect(() => {
      if (loading) return;

      if (!user) {
        router.replace('/auth');
        return;
      }

      // User is authenticated — check wizard status
      apiFetch<WizardStatus>('/wizard/status', { completed: false })
        .then((status) => {
          if (!status.completed) {
            router.replace(getWizardPath());
          } else {
            setChecking(false);
          }
        })
        .catch(() => {
          // If the check fails, let them through rather than blocking forever
          setChecking(false);
        });
    }, [user, loading, router]);

    if (loading || checking) {
      return (
        <div
          className="min-h-screen flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-background)' }}
        >
          <span
            className="text-xs font-bold uppercase tracking-[0.2em]"
            style={{ color: 'var(--color-primary)' }}
          >
            Loading…
          </span>
        </div>
      );
    }

    return <WrappedComponent {...props} />;
  };
}