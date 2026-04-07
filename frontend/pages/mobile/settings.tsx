import React, { useState } from 'react';
import Head from 'next/head';
import { MobileLayout } from '@/components/mobile';

export default function MobileSettings() {
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [studyReminders, setStudyReminders] = useState(true);
  const [predictionUpdates, setPredictionUpdates] = useState(false);

  return (
    <>
      <Head>
        <title>PrepIQ - Settings</title>
        <meta name="description" content="Manage your PrepIQ settings" />
      </Head>
      <MobileLayout title="Settings">
        <div className="space-y-8">
          {/* Page Title */}
          <h1 className="text-2xl font-serif italic text-on-surface uppercase tracking-tight">Settings</h1>

          {/* Section 1: Profile Information */}
          <section className="border border-outline-variant p-5 space-y-4">
            <div className="flex items-center gap-3 border-l-2 border-outline-variant pl-3">
              <h2 className="text-sm font-semibold uppercase tracking-widest">Profile Information</h2>
            </div>
            <div className="space-y-3">
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Full Name</label>
                <input
                  className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                  type="text"
                  defaultValue="Julian Alexander"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">College Name</label>
                <input
                  className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                  type="text"
                  defaultValue="Stanford University"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Program</label>
                  <select className="w-full h-11 px-3 text-on-surface appearance-none border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary">
                    <option>CS Masters</option>
                    <option>MBA</option>
                    <option>Medicine</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Year</label>
                  <select className="w-full h-11 px-3 text-on-surface appearance-none border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary">
                    <option>Final Year</option>
                    <option>3rd Year</option>
                    <option>2nd Year</option>
                  </select>
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Exam Date</label>
                <input
                  className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                  type="date"
                  defaultValue="2024-12-15"
                />
              </div>
              <div className="flex flex-col gap-1 opacity-60">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Email Address</label>
                <div className="relative">
                  <input
                    className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent cursor-not-allowed pr-10"
                    readOnly
                    type="email"
                    defaultValue="julian.a@stanford.edu"
                  />
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
                    <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="flex justify-end">
              <button className="bg-primary hover:bg-on-primary-fixed-variant text-on-primary px-5 h-10 font-medium text-sm transition-all border border-outline-variant">
                SAVE CHANGES
              </button>
            </div>
          </section>

          {/* Section 2: Preferences */}
          <section className="border border-outline-variant p-5 space-y-4">
            <div className="flex items-center gap-3 border-l-2 border-outline-variant pl-3">
              <h2 className="text-sm font-semibold uppercase tracking-widest">Preferences</h2>
            </div>
            <div className="space-y-4">
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Language</label>
                <select className="w-full h-11 px-3 text-on-surface appearance-none border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary">
                  <option>English (US)</option>
                  <option>Spanish</option>
                  <option>French</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Notifications</label>
                <div className="space-y-2">
                  {/* Email notifications */}
                  <label className="flex items-center justify-between group cursor-pointer border border-outline-variant/20 p-3">
                    <span className="text-sm text-on-surface uppercase tracking-tight">Email notifications</span>
                    <div className="relative inline-flex items-center cursor-pointer">
                      <input
                        checked={emailNotifs}
                        onChange={(e) => setEmailNotifs(e.target.checked)}
                        className="sr-only peer"
                        type="checkbox"
                      />
                      <div className="w-10 h-5 bg-outline-variant/10 border border-outline-variant peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[1px] after:left-[1px] after:bg-on-surface after:h-4 after:w-4 after:transition-all" />
                    </div>
                  </label>
                  {/* Study reminders */}
                  <label className="flex items-center justify-between group cursor-pointer border border-outline-variant/20 p-3">
                    <span className="text-sm text-on-surface uppercase tracking-tight">Study reminders</span>
                    <div className="relative inline-flex items-center cursor-pointer">
                      <input
                        checked={studyReminders}
                        onChange={(e) => setStudyReminders(e.target.checked)}
                        className="sr-only peer"
                        type="checkbox"
                      />
                      <div className="w-10 h-5 bg-outline-variant/10 border border-outline-variant peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[1px] after:left-[1px] after:bg-on-surface after:h-4 after:w-4 after:transition-all" />
                    </div>
                  </label>
                  {/* Prediction updates */}
                  <label className="flex items-center justify-between group cursor-pointer border border-outline-variant/20 p-3">
                    <span className="text-sm text-on-surface uppercase tracking-tight">Prediction updates</span>
                    <div className="relative inline-flex items-center cursor-pointer">
                      <input
                        checked={predictionUpdates}
                        onChange={(e) => setPredictionUpdates(e.target.checked)}
                        className="sr-only peer"
                        type="checkbox"
                      />
                      <div className="w-10 h-5 bg-outline-variant/10 border border-outline-variant peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[1px] after:left-[1px] after:bg-on-surface after:h-4 after:w-4 after:transition-all" />
                    </div>
                  </label>
                </div>
              </div>
            </div>
            <div className="flex justify-end pt-3">
              <button className="bg-primary hover:bg-on-primary-fixed-variant text-on-primary px-5 h-10 font-medium text-sm transition-all border border-outline-variant">
                SAVE PREFERENCES
              </button>
            </div>
          </section>

          {/* Section 3: Account Security */}
          <section className="border border-outline-variant p-5 space-y-4">
            <div className="flex items-center gap-3 border-l-2 border-outline-variant pl-3">
              <h2 className="text-sm font-semibold uppercase tracking-widest">Account Security</h2>
            </div>
            <div className="space-y-3">
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Current Password</label>
                <input
                  className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                  type="password"
                  defaultValue="........"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">New Password</label>
                <div className="relative">
                  <input
                    className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary pr-10"
                    placeholder="Min 8 characters"
                    type="password"
                  />
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant cursor-pointer">
                    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </div>
                {/* Password Strength Bar */}
                <div className="w-full h-1.5 border border-outline-variant mt-2 overflow-hidden">
                  <div className="h-full w-[65%] bg-primary" />
                </div>
                <p className="text-[10px] text-on-surface-variant uppercase tracking-wider">Strength: Moderate</p>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Confirm Password</label>
                <input
                  className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                  placeholder="Confirm your new password"
                  type="password"
                />
              </div>
            </div>
            <div className="flex flex-col gap-6 pt-3">
              <div className="flex justify-end">
                <button className="bg-primary hover:bg-on-primary-fixed-variant text-on-primary px-5 h-10 font-medium text-sm transition-all border border-outline-variant">
                  CHANGE PASSWORD
                </button>
              </div>
              <div className="pt-4 border-t border-outline-variant/20 space-y-3">
                <p className="text-[10px] text-on-surface-variant uppercase tracking-wider">Careful! This action cannot be undone.</p>
                <button className="w-full h-10 border border-outline-variant text-on-surface-variant font-medium text-sm hover:bg-outline-variant/5 transition-colors uppercase tracking-widest">
                  DELETE ACCOUNT
                </button>
              </div>
            </div>
          </section>
        </div>
      </MobileLayout>
    </>
  );
}
