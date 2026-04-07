import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';
// Profile data is mostly static in prototype — hook imports added for future use
// import { usePreferredVariant } from '@/lib/hooks';

export default function MobileProfile() {
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
                <span className="text-on-primary font-bold text-lg tracking-tight">RD</span>
              </div>
              {/* Info */}
              <div className="flex-grow min-w-0">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-on-surface truncate uppercase tracking-tight">Rahul Das</h3>
                    <p className="text-sm text-on-surface-variant font-medium truncate italic">rahul.das@college.edu</p>
                  </div>
                  <div className="flex items-center gap-1 border border-outline-variant px-2 py-0.5 flex-shrink-0">
                    <span className="text-[10px] font-bold text-on-surface uppercase tracking-wider">Active</span>
                  </div>
                </div>
                <p className="mt-1.5 text-xs text-on-surface-variant font-medium uppercase tracking-wide">Indian Institute of Technology</p>
                <div className="mt-2 flex gap-2">
                  <span className="px-2.5 py-0.5 bg-primary/10 text-on-surface text-[10px] font-semibold border border-outline-variant">BTech</span>
                  <span className="px-2.5 py-0.5 bg-primary/10 text-on-surface text-[10px] font-semibold border border-outline-variant">3rd Year</span>
                </div>
              </div>
            </div>
            {/* Action Button */}
            <button className="mt-4 w-full py-2 bg-primary text-on-primary text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors active:scale-[0.98] border border-outline-variant">
              Edit Profile
            </button>
          </section>

          {/* Details Card */}
          <section className="border border-outline-variant bg-white p-5 space-y-6">
            {/* Personal Information */}
            <div>
              <h4 className="font-serif italic text-lg text-primary mb-4 border-b border-outline-variant pb-2">Personal Information</h4>
              <div className="space-y-3">
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">Name</span>
                  <span className="text-sm text-on-surface font-medium">Rahul Das</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">Email</span>
                  <span className="text-sm text-on-surface font-medium">rahul.das@college.edu</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">College</span>
                  <span className="text-sm text-on-surface font-medium">IIT Delhi</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-on-surface-variant/60 font-bold uppercase tracking-tighter">Program</span>
                  <span className="text-sm text-on-surface font-medium">Computer Science &amp; Engineering</span>
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
                  <span className="text-sm text-on-surface font-medium">Oct 2023</span>
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
                  <p className="text-base font-bold text-on-surface">12</p>
                  <p className="text-[8px] uppercase tracking-widest text-on-surface-variant/60 font-bold leading-tight">Subjects</p>
                </div>
              </div>
              {/* Progress */}
              <div className="flex flex-col items-center text-center space-y-1.5">
                <div className="w-10 h-10 bg-white flex items-center justify-center border border-outline-variant">
                  <span className="text-[11px] font-bold text-on-surface">88%</span>
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
                  <p className="text-base font-bold text-on-surface">24</p>
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
                  <p className="text-base font-bold text-on-surface">15</p>
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
