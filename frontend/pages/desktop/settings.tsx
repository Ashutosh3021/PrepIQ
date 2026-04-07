import React, { useState } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';

const themeOptions = ['Atelier Cream (Default)', 'Midnight Parchment', 'Academic Slate'];
const typographyOptions = [
  'Standard (14pt Body)',
  'Enlarged (16pt Body)',
  'Compact (12pt Body)',
];

export default function DesktopSettings() {
  const [weeklyDigest, setWeeklyDigest] = useState(true);
  const [aiAlerts, setAiAlerts] = useState(true);
  const [communityInvites, setCommunityInvites] = useState(false);

  return (
    <>
      <Head>
        <title>Settings | PrepIQ</title>
        <meta name="description" content="Manage your academic profile and preferences" />
      </Head>
      <DesktopLayout>
        {/* Header */}
        <header className="mb-16 border-b border-primary/10 pb-8 flex justify-between items-end">
          <div>
            <h1 className="font-serif italic text-6xl text-on-surface">Settings</h1>
            <p className="text-primary mt-4 font-medium uppercase tracking-widest text-xs">
              Manage your academic profile &amp; preferences
            </p>
          </div>
          <div className="flex gap-4">
            <button className="bg-transparent border border-primary text-primary px-8 py-3 font-semibold uppercase text-xs tracking-widest hover:bg-primary hover:text-on-primary transition-all duration-150">
              Discard
            </button>
            <button className="bg-primary text-on-primary px-8 py-3 font-semibold uppercase text-xs tracking-widest hover:bg-primary/90 transition-all duration-150">
              Save Changes
            </button>
          </div>
        </header>

        <div className="grid grid-cols-12 gap-12">
          {/* Side Navigation Links */}
          <aside className="col-span-3">
            <nav className="flex flex-col gap-2">
              <a
                href="#profile"
                className="text-primary border-l-2 border-primary pl-4 py-2 font-bold transition-all duration-150"
              >
                Profile Information
              </a>
              <a
                href="#preferences"
                className="text-on-surface/70 border-l-2 border-transparent hover:border-primary/30 pl-4 py-2 font-medium transition-all duration-150"
              >
                Preferences
              </a>
              <a
                href="#security"
                className="text-on-surface/70 border-l-2 border-transparent hover:border-primary/30 pl-4 py-2 font-medium transition-all duration-150"
              >
                Account Security
              </a>
              <a
                href="#billing"
                className="text-on-surface/70 border-l-2 border-transparent hover:border-primary/30 pl-4 py-2 font-medium transition-all duration-150"
              >
                Billing &amp; Subscription
              </a>
            </nav>
          </aside>

          {/* Settings Content */}
          <div className="col-span-9 space-y-24">
            {/* Section: Profile Information */}
            <section className="space-y-8" id="profile">
              <div className="flex items-center gap-4">
                <span className="text-4xl font-serif italic text-primary">01.</span>
                <h2 className="text-2xl font-semibold text-on-surface">Profile Information</h2>
              </div>
              <div className="bg-surface-container-low p-10 grid grid-cols-2 gap-x-12 gap-y-8">
                <div className="col-span-2 flex items-center gap-8 mb-4">
                  <div className="w-24 h-24 bg-surface-container-high flex items-center justify-center border-2 border-dashed border-primary/20">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                      <circle cx="12" cy="13" r="4" />
                    </svg>
                  </div>
                  <div className="space-y-1">
                    <p className="font-bold text-on-surface">Profile Picture</p>
                    <p className="text-xs text-primary">
                      JPG or PNG, max 2MB. 400x400px recommended.
                    </p>
                    <button className="mt-2 text-primary font-bold text-xs uppercase underline tracking-wider">
                      Change Image
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                    First Name
                  </label>
                  <input
                    className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm transition-all duration-150"
                    type="text"
                    defaultValue="Julian"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                    Last Name
                  </label>
                  <input
                    className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm transition-all duration-150"
                    type="text"
                    defaultValue="Vandervilt"
                  />
                </div>
                <div className="col-span-2 space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                    Academic Biography
                  </label>
                  <textarea
                    className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm transition-all duration-150"
                    rows={4}
                    defaultValue="Ph.D. candidate specializing in classical literature and archival studies. Focus on early 19th-century folio preservation."
                  />
                </div>
              </div>
            </section>

            {/* Section: Preferences */}
            <section className="space-y-8" id="preferences">
              <div className="flex items-center gap-4">
                <span className="text-4xl font-serif italic text-primary">02.</span>
                <h2 className="text-2xl font-semibold text-on-surface">Preferences</h2>
              </div>
              <div className="bg-surface-container-high p-10 space-y-10">
                <div className="grid grid-cols-2 gap-12">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Interface Theme
                    </label>
                    <select className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm appearance-none cursor-pointer">
                      {themeOptions.map((opt) => (
                        <option key={opt}>{opt}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Typographic Scale
                    </label>
                    <select className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm appearance-none cursor-pointer">
                      {typographyOptions.map((opt) => (
                        <option key={opt}>{opt}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="space-y-6">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                    Notification Settings
                  </p>
                  <div className="space-y-4">
                    <label className="flex items-center gap-4 cursor-pointer group">
                      <div className="relative w-5 h-5 border-2 border-primary flex items-center justify-center">
                        <input
                          checked={weeklyDigest}
                          onChange={(e) => setWeeklyDigest(e.target.checked)}
                          className="opacity-0 absolute inset-0 cursor-pointer peer"
                          type="checkbox"
                        />
                        <div className="w-2.5 h-2.5 bg-primary opacity-0 peer-checked:opacity-100 transition-opacity" />
                      </div>
                      <span className="text-sm font-medium text-on-surface">
                        Weekly Performance Digest
                      </span>
                    </label>
                    <label className="flex items-center gap-4 cursor-pointer group">
                      <div className="relative w-5 h-5 border-2 border-primary flex items-center justify-center">
                        <input
                          checked={aiAlerts}
                          onChange={(e) => setAiAlerts(e.target.checked)}
                          className="opacity-0 absolute inset-0 cursor-pointer peer"
                          type="checkbox"
                        />
                        <div className="w-2.5 h-2.5 bg-primary opacity-0 peer-checked:opacity-100 transition-opacity" />
                      </div>
                      <span className="text-sm font-medium text-on-surface">
                        AI Tutor Prediction Alerts
                      </span>
                    </label>
                    <label className="flex items-center gap-4 cursor-pointer group">
                      <div className="relative w-5 h-5 border-2 border-primary flex items-center justify-center">
                        <input
                          checked={communityInvites}
                          onChange={(e) => setCommunityInvites(e.target.checked)}
                          className="opacity-0 absolute inset-0 cursor-pointer peer"
                          type="checkbox"
                        />
                        <div className="w-2.5 h-2.5 bg-primary opacity-0 peer-checked:opacity-100 transition-opacity" />
                      </div>
                      <span className="text-sm font-medium text-on-surface">
                        Community Study Session Invites
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            </section>

            {/* Section: Account Security */}
            <section className="space-y-8" id="security">
              <div className="flex items-center gap-4">
                <span className="text-4xl font-serif italic text-primary">03.</span>
                <h2 className="text-2xl font-semibold text-on-surface">Account Security</h2>
              </div>
              <div className="bg-surface-container-highest p-10 space-y-12">
                <div className="grid grid-cols-1 gap-8 max-w-lg">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Current Password
                    </label>
                    <input
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
                      placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
                      type="password"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      New Password
                    </label>
                    <input
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
                      type="password"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Confirm New Password
                    </label>
                    <input
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
                      type="password"
                    />
                  </div>
                  <button className="w-fit text-primary font-bold text-xs uppercase underline tracking-wider">
                    Update Credentials
                  </button>
                </div>
                <div className="pt-8 border-t border-primary/10">
                  <div className="bg-error/5 p-8">
                    <h3 className="text-error font-bold uppercase tracking-widest text-xs mb-4">
                      Danger Zone
                    </h3>
                    <div className="flex justify-between items-center">
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-on-surface">Archive Account</p>
                        <p className="text-xs text-on-surface/70">
                          This will permanently delete all study data and history.
                        </p>
                      </div>
                      <button className="bg-error text-white px-6 py-2 text-xs font-bold uppercase tracking-widest hover:bg-error/90 transition-all duration-150">
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </DesktopLayout>
    </>
  );
}
