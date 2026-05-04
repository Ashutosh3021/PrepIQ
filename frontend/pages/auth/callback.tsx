import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { supabase } from '@/lib/supabase';
import { apiFetch } from '@/lib/services/base.service';
import { getWizardPath, getDashboardPath } from '@/lib/utils/device';

interface WizardStatus {
  completed: boolean;
}

/**
 * Supabase redirects here after OAuth.
 * With PKCE flow (Supabase default), the SDK automatically exchanges the
 * code for a session when it detects the `code` param in the URL — we must
 * NOT call exchangeCodeForSession manually. Just wait for onAuthStateChange
 * to fire with the new session, then route based on wizard status.
 */
export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    let unsubscribed = false;

    const redirect = async (session: import('@supabase/supabase-js').Session) => {
      try {
        const status = await apiFetch<WizardStatus>('/wizard/status', { completed: false });
        // Route to the device-appropriate path
        router.replace(status.completed ? getDashboardPath() : getWizardPath());
      } catch {
        router.replace(getWizardPath());
      }
    };

    const run = async () => {
      // 1. Supabase may have already exchanged the code synchronously —
      //    check for an existing session before setting up any listener.
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        redirect(session);
        return;
      }

      // 2. Not ready yet — wait for the SDK to finish the PKCE exchange.
      const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, newSession) => {
        if (unsubscribed) return;
        if ((event === 'SIGNED_IN' || event === 'INITIAL_SESSION') && newSession) {
          unsubscribed = true;
          subscription.unsubscribe();
          redirect(newSession);
        }
      });

      // 3. Race condition guard — poll once more after 500ms in case the
      //    event already fired before the listener attached.
      setTimeout(async () => {
        if (unsubscribed) return;
        const { data: { session: retrySession } } = await supabase.auth.getSession();
        if (retrySession) {
          unsubscribed = true;
          subscription.unsubscribe();
          redirect(retrySession);
        }
      }, 500);

      // 4. Hard timeout — only reached if OAuth genuinely failed.
      setTimeout(() => {
        if (unsubscribed) return;
        unsubscribed = true;
        subscription.unsubscribe();
        router.replace('/auth?error=callback_timeout');
      }, 10000);
    };

    run();

    return () => { unsubscribed = true; };
  }, [router]);

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-4"
      style={{ backgroundColor: 'var(--color-background)' }}
    >
      <svg
        className="animate-spin"
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        style={{ color: 'var(--color-primary)' }}
      >
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
      </svg>
      <span
        className="text-xs font-bold uppercase tracking-[0.2em]"
        style={{ color: 'var(--color-primary)' }}
      >
        Signing you in…
      </span>
    </div>
  );
}
