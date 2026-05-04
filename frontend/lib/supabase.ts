import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    // Store session in localStorage so it persists across page reloads
    persistSession: true,
    // Let Supabase detect and handle the OAuth callback automatically
    detectSessionInUrl: true,
    // PKCE is Supabase's default — keep it, do NOT call exchangeCodeForSession manually
    flowType: 'pkce',
  },
});
