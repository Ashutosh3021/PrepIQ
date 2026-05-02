import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/router';
import { getAccessToken } from '@/lib/services/base.service';

interface AuthUser {
  id: string;
  email: string;
  name?: string;
}

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  token: string | null;
  /** Sign in: persist session and update React state */
  signIn: (token: string, user: AuthUser, refreshToken?: string) => void;
  /** Sign out: clear session and redirect to /login */
  signOut: () => void;
  /** FE-02: retrieve the current access token (reads from localStorage) */
  getToken: () => string | null;
}

const SESSION_STORAGE_KEY = 'prepiq-supabase-session';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    /**
     * FE-02: Restore session from localStorage on mount.
     * We read the stored session directly — no extra network call needed
     * because the token is already validated by the backend on every API call.
     * If the token is expired the first protected API call will trigger a
     * refresh (handled in base.service.ts) or redirect to /login.
     */
    const restoreSession = () => {
      try {
        // Primary key written by login.tsx and signIn()
        const stored = localStorage.getItem(SESSION_STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed.access_token && parsed.user) {
            setToken(parsed.access_token);
            setUser(parsed.user as AuthUser);
            setLoading(false);
            return;
          }
        }

        // Fallback: scan for any Supabase-style session keys
        const supabaseKeys = Object.keys(localStorage).filter(
          (key) => key.includes('supabase') || key.includes('sb-')
        );
        for (const key of supabaseKeys) {
          const item = localStorage.getItem(key);
          if (item) {
            const parsed = JSON.parse(item);
            if (parsed.access_token && parsed.user) {
              setToken(parsed.access_token);
              setUser(parsed.user as AuthUser);
              break;
            }
          }
        }
      } catch {
        // Corrupted storage — clear it
        localStorage.removeItem(SESSION_STORAGE_KEY);
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  /**
   * Persist the session so that:
   * 1. React state is updated immediately.
   * 2. base.service.ts can find the token on the next API call (even after a
   *    hard refresh) because it scans localStorage for keys containing 'supabase'.
   */
  const signIn = useCallback(
    (accessToken: string, userData: AuthUser, refreshToken?: string) => {
      const session = {
        access_token: accessToken,
        refresh_token: refreshToken ?? null,
        user: userData,
      };
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
      setToken(accessToken);
      setUser(userData);
    },
    []
  );

  const signOut = useCallback(() => {
    localStorage.removeItem(SESSION_STORAGE_KEY);
    // Also clear any Supabase SDK keys
    Object.keys(localStorage)
      .filter((key) => key.includes('supabase') || key.includes('sb-'))
      .forEach((key) => localStorage.removeItem(key));
    setToken(null);
    setUser(null);
    router.push('/login');
  }, [router]);

  /** FE-02: expose a stable getter so components can read the token without subscribing to state */
  const getToken = useCallback((): string | null => {
    return getAccessToken();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, token, signIn, signOut, getToken }}>
      {children}
    </AuthContext.Provider>
  );
}
