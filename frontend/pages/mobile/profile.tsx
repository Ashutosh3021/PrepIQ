import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { useProfile } from '@/lib/hooks/useProfile';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { deriveSubjectProgress } from '@/lib/types/subject.types';

function formatMemberSince(dateStr?: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function initials(name?: string | null, email?: string | null): string {
  if (name?.trim()) {
    const parts = name.trim().split(/\s+/);
    return parts.length >= 2
      ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      : parts[0].slice(0, 2).toUpperCase();
  }
  return email ? email[0].toUpperCase() : '?';
}

export default function MobileProfile() {
  const { profile, isLoading: profileLoading, error: profileError } = useProfile();
  const { subjects, isLoading: subjectsLoading } = useSubjects();

  const isLoading = profileLoading || subjectsLoading;

  if (isLoading) {
    return (
      <MobileLayout title="Profile" showBack>
        <div className="space-y-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </MobileLayout>
    );
  }

  if (profileError) {
    return (
      <MobileLayout title="Profile" showBack>
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center px-4">
          <h2 className="text-xl font-bold text-on-surface mb-2">Failed to load profile</h2>
          <p className="text-on-surface/60 mb-6 text-sm">{profileError.message || 'An unexpected error occurred'}</p>
          <button onClick={() => window.location.reload()} className="bg-primary text-on-primary px-6 py-3 font-bold uppercase tracking-widest text-sm">
            Try Again
          </button>
        </div>
      </MobileLayout>
    );
  }

  const displayName = profile?.full_name || profile?.email?.split('@')[0] || 'Student';
  const email = profile?.email || '—';
  const college = profile?.college_name || '—';
  const program = profile?.program || '—';
  const year = profile?.year_of_study ? `Year ${profile.year_of_study}` : '—';
  const memberSince = formatMemberSince((profile as any)?.created_at);
  const avatarText = initials(profile?.full_name, profile?.email);

  const avgProgress = subjects.length > 0
    ? Math.round(subjects.reduce((sum, s) => sum + deriveSubjectProgress(s), 0) / subjects.length)
    : 0;

  const streak = (profile as any)?.streak_days ?? '—';
  const testsTaken = (profile as any)?.tests_taken ?? '—';

  return (
    <>
      <Head>
        <title>PrepIQ - Profile</title>
        <meta name="description" content="View and edit your PrepIQ profile" />
      </Head>
      <MobileLayout title="Profile" showBack>
        <div className="space-y-6">
          {/* Page Heading */}
          <section>
            <h2 className="font-serif italic text-2xl leading-none text-on-surface">My Profile</h2>
          </section>

          {/* Profile Hero Card */}
          <section className="relative bg-white border border-outline-variant p-4">
            <div className="flex items-start gap-4">
              {/* Avatar */}
              <div className="flex-shrink-0 w-14 h-14 bg-primary border border-outline-variant flex items-center justify-center">
                <span className="text-on-primary font-bold text-lg tracking-tight">{avatarText}</span>
              </div>
              {/* Info */}
              <div className="flex-grow min-w-0">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-on-surface truncate uppercase tracking-tight">{displayName}</h3>
                    <p className="text-sm text-on-surface-variant font-medium truncate italic">{email}</p>
                  </div>
                  <div className="flex items-center gap-1 border border-outline-variant px-2 py-0.5 flex-shrink-0">
                    <span className="text-[10px] font-bold text-on-surface uppercase tracking-wider">Active</span>
                  </div>
                </div>
                <p className="mt-1.5 text-xs text-on-surface-variant font-medium uppercase tracking-wide">{college}</p>
                <div className="mt-2 flex gap-2">
                  <span className="px-2.5 py-0.5 bg-primary/10 text-on-surface text-[10px] font-semibold border border-outline-variant">{program}</span>
                  <span className="px-2.5 py-0.5 bg-primary/10 text-on-surface text-[10px] font-semibold border border-outline-variant">{year}</span>
                </div>
              </div>
            </div>
            {/* Action Button */}
            <Link href="/mobile/settings">
              <button className="mt-4 w-full py-2 bg-primary text-on-primary text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors active:scale-[0.98] border border-outline-variant">
                Edit Profile
              </button>
            </Link>
          </section>

          {/* Details Card */}
          <section className="border border-outline-variant bg-white p-5 space-y-6">
            {/* Personal Information */}
            <div>
              <h4 className="font-serif italic text-lg text-primary mb-4 border-b border-outline-variant pb-2">Personal Information</h4>
              <div className="space-y-3">
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">Name</span>
                  <span className="text-sm text-on-surface font-medium">{displayName}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">Email</span>
                  <span className="text-sm text-on-surface font-medium">{email}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">College</span>
                  <span className="text-sm text-on-surface font-medium">{college}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">Program</span>
                  <span className="text-sm text-on-surface font-medium">{program}</span>
                </div>
              </div>
            </div>

            {/* Preferences */}
            <div>
              <h4 className="font-serif italic text-lg text-primary mb-4 border-b border-outline-variant pb-2">Preferences</h4>
              <div className="space-y-3">
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">Account Status</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-on-surface font-medium">Premium</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-primary">
                      <path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" />
                      <path d="m9 12 2 2 4-4" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">Member Since</span>
                  <span className="text-sm text-on-surface font-medium">{memberSince}</span>
                </div>
              </div>
            </div>
          </section>

          {/* Learning Progress Card */}
          <section className="border border-outline-variant bg-surface-container p-4">
            <h4 className="font-serif italic text-lg text-primary mb-4 border-b border-outline-variant pb-2">Learning Journey</h4>
            <div className="grid grid-cols-4 gap-2">
              {/* Subjects */}
              <div className="flex flex-col items-center text-center space-y-1.5">
                <div className="w-10 h-10 bg-white flex items-center justify-center border border-outline-variant">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                  </svg>
                </div>
                <div>
                  <p className="text-base font-bold text-on-surface">{subjects.length}</p>
                  <p className="text-[8px] uppercase tracking-widest text-on-surface-variant/60 font-bold leading-tight">Subjects</p>
                </div>
              </div>
              {/* Progress */}
              <div className="flex flex-col items-center text-center space-y-1.5">
                <div className="w-10 h-10 bg-white flex items-center justify-center border border-outline-variant">
                  <span className="text-[11px] font-bold text-on-surface">{avgProgress}%</span>
                </div>
                <div>
                  <p className="text-[8px] uppercase tracking-widest text-on-surface-variant/60 font-bold leading-tight">Overall</p>
                </div>
              </div>
              {/* Tests */}
              <div className="flex flex-col items-center text-center space-y-1.5">
                <div className="w-10 h-10 bg-white flex items-center justify-center border border-outline-variant">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M15.5 2H8.5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z" />
                    <path d="m9 12 2 2 4-4" />
                  </svg>
                </div>
                <div>
                  <p className="text-base font-bold text-on-surface">{testsTaken}</p>
                  <p className="text-[8px] uppercase tracking-widest text-on-surface-variant/60 font-bold leading-tight">Tests</p>
                </div>
              </div>
              {/* Streak */}
              <div className="flex flex-col items-center text-center space-y-1.5">
                <div className="w-10 h-10 bg-white flex items-center justify-center border border-outline-variant">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
                  </svg>
                </div>
                <div>
                  <p className="text-base font-bold text-on-surface">{streak}</p>
                  <p className="text-[8px] uppercase tracking-widest text-on-surface-variant/60 font-bold leading-tight">Streak</p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </MobileLayout>
    </>
  );
}
