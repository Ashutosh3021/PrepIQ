import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import {
  AuthUser,
  clearSession,
  fetchMe,
  getStoredToken,
  getStoredUser,
  loginWithEmail,
  signupWithEmail,
} from '@/lib/auth';

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName?: string) => Promise<{ needsConfirmation: boolean }>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  signIn: async () => {},
  signUp: async () => ({ needsConfirmation: false }),
  signOut: async () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    const cached = getStoredUser();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    if (cached) setUser(cached);
    fetchMe(token)
      .then((u) => setUser(u))
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const u = await loginWithEmail(email, password);
    try {
      const me = await fetchMe();
      setUser(me);
    } catch {
      setUser(u);
    }
  }, []);

  const signUp = useCallback(async (email: string, password: string, fullName?: string) => {
    const { user: u, needsConfirmation } = await signupWithEmail({
      email,
      password,
      full_name: fullName,
    });
    if (!needsConfirmation) {
      try {
        const me = await fetchMe();
        setUser(me);
      } catch {
        setUser(u);
      }
    }
    return { needsConfirmation };
  }, []);

  const signOut = useCallback(async () => {
    clearSession();
    setUser(null);
    try {
      const token = getStoredToken();
      // best-effort server logout (token already cleared)
      void token;
    } catch {
      /* ignore */
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const me = await fetchMe();
    setUser(me);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
