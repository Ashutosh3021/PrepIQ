import NextAuth from 'next-auth';

export default NextAuth({
  providers: [
    // TODO: Add auth providers when auth phase begins
  ],
  secret: process.env.NEXTAUTH_SECRET,
  // Session is disabled — no session check anywhere in Phase 3
});
