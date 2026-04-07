import React, { useState } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';
// Profile data is mostly static in prototype — hook imports added for future use
// import { usePreferredVariant } from '@/lib/hooks';

const recentActivity = [
  { text: 'Completed "Cognitive Bias" module', time: '2h ago' },
  { text: "Achieved 'High Distinction' in Logic II", time: 'Yesterday' },
];

export default function DesktopProfile() {
  const [focusedMode, setFocusedMode] = useState(true);
  const [paperTexture, setPaperTexture] = useState(false);
  const [dailyGoal, setDailyGoal] = useState(true);

  return (
    <>
      <Head>
        <title>User Profile | PrepIQ</title>
        <meta name="description" content="Your PrepIQ student profile and learning journey" />
      </Head>
      <DesktopLayout>
        {/* Hero Section / Header */}
        <section className="grid grid-cols-1 md:grid-cols-12 gap-0 bg-surface-container-high mb-12">
          <div className="md:col-span-4 aspect-square md:aspect-auto bg-primary flex items-center justify-center text-[120px] font-serif italic text-on-primary select-none">
            JD
          </div>
          <div className="md:col-span-8 p-12 flex flex-col justify-between">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-[0.2em] mb-4 text-primary">
                Student Profile
              </h2>
              <h1 className="font-serif italic text-7xl mb-2 text-on-surface">
                James Davenport
              </h1>
              <p className="text-xl opacity-70">j.davenport@atelier.edu</p>
            </div>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-tertiary mb-1">
                  Current Track
                </p>
                <p className="font-semibold text-lg">
                  Advanced Psychometrics &amp; Logic
                </p>
              </div>
              <button className="bg-primary text-on-primary px-8 py-4 font-bold text-sm tracking-wider hover:bg-primary/90 transition-opacity">
                EDIT ARCHIVE
              </button>
            </div>
          </div>
        </section>

        {/* Two Column Content Grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-px bg-on-surface/5 mb-12">
          {/* Left: Personal Information */}
          <div className="bg-surface-container-low p-12">
            <div className="flex items-center gap-3 mb-10">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                <path d="M12 11c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3z" />
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              </svg>
              <h3 className="font-serif italic text-3xl">Personal Archive</h3>
            </div>
            <div className="space-y-8">
              <div className="flex justify-between items-end border-b border-on-surface/10 pb-4">
                <span className="text-xs font-bold uppercase text-tertiary">
                  Institutional ID
                </span>
                <span className="font-medium">PIQ-8829-X</span>
              </div>
              <div className="flex justify-between items-end border-b border-on-surface/10 pb-4">
                <span className="text-xs font-bold uppercase text-tertiary">
                  Enrollment Date
                </span>
                <span className="font-medium">September 12, 2023</span>
              </div>
              <div className="flex justify-between items-end border-b border-on-surface/10 pb-4">
                <span className="text-xs font-bold uppercase text-tertiary">Timezone</span>
                <span className="font-medium">GMT-5 (Eastern Standard)</span>
              </div>
              <div className="flex justify-between items-end border-b border-on-surface/10 pb-4">
                <span className="text-xs font-bold uppercase text-tertiary">
                  Preferred Language
                </span>
                <span className="font-medium">English (Oxford Academic)</span>
              </div>
            </div>
          </div>

          {/* Right: Preferences & Settings */}
          <div className="bg-surface-container p-12">
            <div className="flex items-center gap-3 mb-10">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                <line x1="4" y1="21" x2="4" y2="14" />
                <line x1="4" y1="10" x2="4" y2="3" />
                <line x1="12" y1="21" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12" y2="3" />
                <line x1="20" y1="21" x2="20" y2="16" />
                <line x1="20" y1="12" x2="20" y2="3" />
                <line x1="1" y1="14" x2="7" y2="14" />
                <line x1="9" y1="8" x2="15" y2="8" />
                <line x1="17" y1="16" x2="23" y2="16" />
              </svg>
              <h3 className="font-serif italic text-3xl">Atelier Settings</h3>
            </div>
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 bg-surface-container-highest">
                <div>
                  <p className="font-bold text-sm">Focused Study Mode</p>
                  <p className="text-[10px] text-tertiary">
                    Disables non-academic notifications during sessions
                  </p>
                </div>
                <button
                  className={`w-12 h-6 p-1 flex ${focusedMode ? 'bg-primary justify-end' : 'bg-secondary-container justify-start'} transition-colors`}
                  onClick={() => setFocusedMode(!focusedMode)}
                >
                  <div className="w-4 h-4 bg-white" />
                </button>
              </div>
              <div
                className={`flex items-center justify-between p-4 bg-surface-container-highest ${!paperTexture ? 'opacity-60' : ''}`}
              >
                <div>
                  <p className="font-bold text-sm">Paper Texture Overlay</p>
                  <p className="text-[10px] text-tertiary">
                    Subtle grain for reduced digital fatigue
                  </p>
                </div>
                <button
                  className={`w-12 h-6 p-1 flex ${paperTexture ? 'bg-primary justify-end' : 'bg-secondary-container justify-start'} transition-colors`}
                  onClick={() => setPaperTexture(!paperTexture)}
                >
                  <div className="w-4 h-4 bg-white" />
                </button>
              </div>
              <div className="flex items-center justify-between p-4 bg-surface-container-highest">
                <div>
                  <p className="font-bold text-sm">Daily Goal Tracking</p>
                  <p className="text-[10px] text-tertiary">
                    Receive summaries at 21:00 daily
                  </p>
                </div>
                <button
                  className={`w-12 h-6 p-1 flex ${dailyGoal ? 'bg-primary justify-end' : 'bg-secondary-container justify-start'} transition-colors`}
                  onClick={() => setDailyGoal(!dailyGoal)}
                >
                  <div className="w-4 h-4 bg-white" />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Learning Journey Stats */}
        <section className="space-y-6 mb-12">
          <h3 className="font-serif italic text-4xl">Learning Journey</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Stat 1: Subjects */}
            <div className="bg-surface-container-high p-8 flex flex-col justify-between aspect-video">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
              <div>
                <p className="text-4xl font-serif italic">08</p>
                <p className="text-[10px] font-bold uppercase tracking-widest text-tertiary">
                  Active Subjects
                </p>
              </div>
            </div>
            {/* Stat 2: Progress */}
            <div className="bg-surface-container-high p-8 flex flex-col justify-between aspect-video">
              <div className="relative w-12 h-12">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    className="text-secondary-container"
                    cx="24"
                    cy="24"
                    fill="transparent"
                    r="20"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <circle
                    className="text-primary"
                    cx="24"
                    cy="24"
                    fill="transparent"
                    r="20"
                    stroke="currentColor"
                    strokeDasharray="125.6"
                    strokeDashoffset="31.4"
                    strokeWidth="4"
                  />
                </svg>
              </div>
              <div>
                <p className="text-4xl font-serif italic">75%</p>
                <p className="text-[10px] font-bold uppercase tracking-widest text-tertiary">
                  Overall Progress
                </p>
              </div>
            </div>
            {/* Stat 3: Tests */}
            <div className="bg-surface-container-high p-8 flex flex-col justify-between aspect-video">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                <path d="M9 11l3 3L22 4" />
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
              </svg>
              <div>
                <p className="text-4xl font-serif italic">142</p>
                <p className="text-[10px] font-bold uppercase tracking-widest text-tertiary">
                  Tests Conducted
                </p>
              </div>
            </div>
            {/* Stat 4: Streak */}
            <div className="bg-primary p-8 flex flex-col justify-between aspect-video text-on-primary">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-white">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              <div>
                <p className="text-4xl font-serif italic">24</p>
                <p className="text-[10px] font-bold uppercase tracking-widest text-on-primary opacity-60">
                  Day Streak
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Bento Grid Footer / Additional Info */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-12 border-t border-on-surface/5">
          <div className="space-y-4">
            <h4 className="text-[10px] font-bold uppercase tracking-[0.2em] text-tertiary">
              Recent Scholarly Activity
            </h4>
            <div className="space-y-3">
              {recentActivity.map((item) => (
                <div
                  key={item.text}
                  className="flex items-center gap-3 p-3 bg-surface-container-low border-l-2 border-primary"
                >
                  <div className="w-1.5 h-1.5 bg-primary shrink-0" />
                  <span className="text-xs">{item.text}</span>
                  <span className="ml-auto text-[10px] opacity-40">{item.time}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="md:col-span-2 bg-surface-container-low p-12 flex items-center justify-between overflow-hidden relative group">
            <div className="z-10 relative">
              <h4 className="font-serif italic text-4xl mb-4 max-w-xs">
                &ldquo;The beautiful thing about learning is that no one can take it away from
                you.&rdquo;
              </h4>
              <p className="text-xs font-bold uppercase tracking-widest text-tertiary">
                &mdash; B.B. KING
              </p>
            </div>
            <div className="absolute -right-12 -bottom-12 opacity-[0.03] scale-150 select-none pointer-events-none group-hover:rotate-12 transition-transform duration-700">
              <svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </div>
          </div>
        </section>
      </DesktopLayout>
    </>
  );
}
