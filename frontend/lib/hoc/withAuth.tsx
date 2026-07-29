import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/lib/context/AuthContext';
import { apiFetch } from '@/lib/services/base.service';
import { getWizardPath } from '@/lib/utils/device';

interface WizardStatus {
  completed: boolean;
}

export default function withAuth<P extends object>(WrappedComponent: React.ComponentType<P>) {
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

      apiFetch<WizardStatus>('/wizard/status', { completed: false })
        .then((status) => {
          if (!status.completed) {
            router.replace(getWizardPath());
          } else {
            setChecking(false);
          }
        })
        .catch(() => {
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
