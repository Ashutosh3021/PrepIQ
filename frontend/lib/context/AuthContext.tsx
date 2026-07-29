"use client";
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  AuthSession,
  AuthUser,
  clearSession,
  getStoredToken,
  getStoredUser,
  loginWithEmail,
  signupWithEmail,
} from "../auth";

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  /** Alias kept so existing callers using `signOut` still work */
  signOut: () => void;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Hydrate from localStorage on first render
  useEffect(() => {
    const t = getStoredToken();
    const u = getStoredUser();
    setToken(t);
    setUser(u);
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const session: AuthSession = await loginWithEmail(email, password);
    setToken(session.access_token);
    setUser(session.user);
  }, []);

  const signup = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const session: AuthSession = await signupWithEmail(
        email,
        password,
        fullName
      );
      setToken(session.access_token);
      setUser(session.user);
    },
    []
  );

  const logout = useCallback(() => {
    clearSession();
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      login,
      signup,
      logout,
      /** Alias so existing `signOut()` call-sites keep working */
      signOut: logout,
      isAuthenticated: !!token && !!user,
    }),
    [user, token, loading, login, signup, logout]
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
