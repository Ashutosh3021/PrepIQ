/**
 * DEPRECATED — OAuth / Supabase auth removed.
 * Classic email+password auth lives in `@/lib/auth`.
 * This stub exists only so accidental imports do not crash the build.
 */
export const supabase = {
  auth: {
    getSession: async () => ({ data: { session: null }, error: null }),
    signOut: async () => ({ error: null }),
    onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
    signInWithOAuth: async () => ({
      data: null,
      error: { message: 'OAuth is disabled. Use email and password on /auth.' },
    }),
  },
};
