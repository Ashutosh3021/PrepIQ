import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { userService } from '@/lib/services/user.service';
import { apiFetch } from '@/lib/services/base.service';
import type { User } from '@/lib/types/user.types';

// ── Constants ─────────────────────────────────────────────────────────────────

const NOTIF_KEY = 'prepiq-notification-settings';
const THEME_KEY = 'prepiq-theme-settings';

const themeOptions = ['Atelier Cream (Default)', 'Midnight Parchment', 'Academic Slate'];
const typographyOptions = [
  'Standard (14pt Body)',
  'Enlarged (16pt Body)',
  'Compact (12pt Body)',
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function readNotifSettings() {
  if (typeof window === 'undefined') return { weeklyDigest: true, aiAlerts: true, communityInvites: false };
  try { return { weeklyDigest: true, aiAlerts: true, communityInvites: false, ...JSON.parse(localStorage.getItem(NOTIF_KEY) ?? '{}') }; }
  catch { return { weeklyDigest: true, aiAlerts: true, communityInvites: false }; }
}

function readThemeSettings() {
  if (typeof window === 'undefined') return { theme: 0, typography: 0 };
  try { return { theme: 0, typography: 0, ...JSON.parse(localStorage.getItem(THEME_KEY) ?? '{}') }; }
  catch { return { theme: 0, typography: 0 }; }
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function DesktopSettings() {
  // ── Profile state ──────────────────────────────────────────────────────────
  const [profile, setProfile] = useState<User | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [fullName, setFullName] = useState('');
  const [collegeName, setCollegeName] = useState('');
  const [program, setProgram] = useState('');
  const [yearOfStudy, setYearOfStudy] = useState('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [saveError, setSaveError] = useState('');

  // ── Notification / theme state (localStorage) ──────────────────────────────
  const [weeklyDigest, setWeeklyDigest] = useState(true);
  const [aiAlerts, setAiAlerts] = useState(true);
  const [communityInvites, setCommunityInvites] = useState(false);
  const [themeIdx, setThemeIdx] = useState(0);
  const [typographyIdx, setTypographyIdx] = useState(0);

  // ── Load profile on mount ──────────────────────────────────────────────────
  useEffect(() => {
    userService.getProfile().then((data) => {
      setProfile(data);
      setFullName(data.full_name ?? '');
      setCollegeName(data.college_name ?? '');
      setProgram(data.program ?? '');
      setYearOfStudy(String(data.year_of_study ?? ''));
    }).catch(() => {
      // Non-fatal — form stays empty
    }).finally(() => setProfileLoading(false));

    // Restore localStorage preferences
    const notif = readNotifSettings();
    setWeeklyDigest(notif.weeklyDigest);
    setAiAlerts(notif.aiAlerts);
    setCommunityInvites(notif.communityInvites);

    const theme = readThemeSettings();
    setThemeIdx(theme.theme);
    setTypographyIdx(theme.typography);
  }, []);

  // ── Save profile ───────────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaveStatus('saving');
    setSaveError('');
    try {
      await apiFetch('/wizard/update', {}, {
        method: 'PUT',
        body: JSON.stringify({
          full_name: fullName.trim() || undefined,
          college_name: collegeName.trim() || undefined,
          program: program.trim() || undefined,
          year_of_study: yearOfStudy ? Number(yearOfStudy) : undefined,
        }),
      });

      // Persist notification + theme preferences to localStorage
      localStorage.setItem(NOTIF_KEY, JSON.stringify({ weeklyDigest, aiAlerts, communityInvites }));
      localStorage.setItem(THEME_KEY, JSON.stringify({ theme: themeIdx, typography: typographyIdx }));

      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2500);
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : 'Save failed. Please try again.');
      setSaveStatus('error');
    }
  };

  const handleDiscard = () => {
    if (!profile) return;
    setFullName(profile.full_name ?? '');
    setCollegeName(profile.college_name ?? '');
    setProgram(profile.program ?? '');
    setYearOfStudy(String(profile.year_of_study ?? ''));
    setSaveStatus('idle');
    setSaveError('');
  };

  // ── Render ─────────────────────────────────────────────────────────────────

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
            <button
              onClick={handleDiscard}
              disabled={saveStatus === 'saving'}
              className="bg-transparent border border-primary text-primary px-8 py-3 font-semibold uppercase text-xs tracking-widest hover:bg-primary hover:text-on-primary transition-all duration-150 disabled:opacity-40"
            >
              Discard
            </button>
            <button
              onClick={handleSave}
              disabled={saveStatus === 'saving'}
              className="bg-primary text-on-primary px-8 py-3 font-semibold uppercase text-xs tracking-widest hover:bg-primary/90 transition-all duration-150 disabled:opacity-40 flex items-center gap-2"
            >
              {saveStatus === 'saving' && (
                <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
              )}
              {saveStatus === 'saved' ? 'Saved ✓' : 'Save Changes'}
            </button>
          </div>
        </header>

        {saveError && (
          <div className="mb-8 px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
            {saveError}
          </div>
        )}

        <div className="grid grid-cols-12 gap-12">
          {/* Side Navigation */}
          <aside className="col-span-3">
            <nav className="flex flex-col gap-2">
              {[
                { href: '#profile', label: 'Profile Information' },
                { href: '#preferences', label: 'Preferences' },
                { href: '#security', label: 'Account Security' },
              ].map(({ href, label }) => (
                <a key={href} href={href}
                  className="text-on-surface/70 border-l-2 border-transparent hover:border-primary/30 pl-4 py-2 font-medium transition-all duration-150 first:text-primary first:border-primary first:font-bold">
                  {label}
                </a>
              ))}
            </nav>
          </aside>

          {/* Settings Content */}
          <div className="col-span-9 space-y-24">

            {/* ── 01. Profile Information ── */}
            <section className="space-y-8" id="profile">
              <div className="flex items-center gap-4">
                <span className="text-4xl font-serif italic text-primary">01.</span>
                <h2 className="text-2xl font-semibold text-on-surface">Profile Information</h2>
              </div>

              {profileLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : (
                <div className="bg-surface-container-low p-10 grid grid-cols-2 gap-x-12 gap-y-8">
                  {/* Email — read-only, managed by Supabase OAuth */}
                  <div className="col-span-2 space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Email Address
                    </label>
                    <input
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/20 p-3 text-sm text-on-surface/50 cursor-not-allowed"
                      type="email"
                      value={profile?.email ?? ''}
                      disabled
                      title="Email is managed by your OAuth provider and cannot be changed here."
                    />
                    <p className="text-[10px] text-on-surface/40">
                      Managed by your Google / GitHub account — cannot be changed here.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Full Name
                    </label>
                    <input
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm transition-all duration-150"
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Your full name"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      College / University
                    </label>
                    <input
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm transition-all duration-150"
                      type="text"
                      value={collegeName}
                      onChange={(e) => setCollegeName(e.target.value)}
                      placeholder="Your institution"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Program
                    </label>
                    <input
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm transition-all duration-150"
                      type="text"
                      value={program}
                      onChange={(e) => setProgram(e.target.value)}
                      placeholder="e.g. B.Tech, B.Sc"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Year of Study
                    </label>
                    <input
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm transition-all duration-150"
                      type="number"
                      min={1}
                      max={6}
                      value={yearOfStudy}
                      onChange={(e) => setYearOfStudy(e.target.value)}
                      placeholder="1–6"
                    />
                  </div>
                </div>
              )}
            </section>

            {/* ── 02. Preferences (localStorage) ── */}
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
                    <select
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm appearance-none cursor-pointer"
                      value={themeIdx}
                      onChange={(e) => setThemeIdx(Number(e.target.value))}
                    >
                      {themeOptions.map((opt, i) => (
                        <option key={opt} value={i}>{opt}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                      Typographic Scale
                    </label>
                    <select
                      className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm appearance-none cursor-pointer"
                      value={typographyIdx}
                      onChange={(e) => setTypographyIdx(Number(e.target.value))}
                    >
                      {typographyOptions.map((opt, i) => (
                        <option key={opt} value={i}>{opt}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-6">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                    Notification Settings
                  </p>
                  <p className="text-xs text-on-surface/40 -mt-4">
                    Saved locally in your browser.
                  </p>
                  <div className="space-y-4">
                    {[
                      { label: 'Weekly Performance Digest', value: weeklyDigest, set: setWeeklyDigest },
                      { label: 'AI Tutor Prediction Alerts', value: aiAlerts, set: setAiAlerts },
                      { label: 'Community Study Session Invites', value: communityInvites, set: setCommunityInvites },
                    ].map(({ label, value, set }) => (
                      <label key={label} className="flex items-center gap-4 cursor-pointer group">
                        <div className="relative w-5 h-5 border-2 border-primary flex items-center justify-center">
                          <input
                            checked={value}
                            onChange={(e) => set(e.target.checked)}
                            className="opacity-0 absolute inset-0 cursor-pointer peer"
                            type="checkbox"
                          />
                          <div className="w-2.5 h-2.5 bg-primary opacity-0 peer-checked:opacity-100 transition-opacity" />
                        </div>
                        <span className="text-sm font-medium text-on-surface">{label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* ── 03. Account Security ── */}
            <section className="space-y-8" id="security">
              <div className="flex items-center gap-4">
                <span className="text-4xl font-serif italic text-primary">03.</span>
                <h2 className="text-2xl font-semibold text-on-surface">Account Security</h2>
              </div>
              <div className="bg-surface-container-highest p-10 space-y-12">
                {/* Password change — OAuth users don't have a password */}
                <div className="p-6 border border-outline-variant/30 bg-surface-container-low">
                  <p className="text-sm font-semibold text-on-surface mb-2">Password Management</p>
                  <p className="text-xs text-on-surface/60 leading-relaxed">
                    Your account uses Google or GitHub OAuth — there is no password to change here.
                    To update your password, visit your provider&apos;s account settings directly.
                  </p>
                  <div className="flex gap-3 mt-4">
                    <a
                      href="https://myaccount.google.com/security"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-bold uppercase tracking-wider text-primary underline underline-offset-4"
                    >
                      Google Account →
                    </a>
                    <a
                      href="https://github.com/settings/security"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-bold uppercase tracking-wider text-primary underline underline-offset-4"
                    >
                      GitHub Security →
                    </a>
                  </div>
                </div>

                {/* Danger zone */}
                <div className="pt-8 border-t border-primary/10">
                  <div className="bg-error/5 p-8">
                    <h3 className="text-error font-bold uppercase tracking-widest text-xs mb-4">
                      Danger Zone
                    </h3>
                    <div className="flex justify-between items-center">
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-on-surface">Delete Account</p>
                        <p className="text-xs text-on-surface/70">
                          This will permanently delete all study data and history.
                        </p>
                      </div>
                      <button
                        onClick={() => alert('Account deletion is not yet available. Please contact support.')}
                        className="bg-error text-white px-6 py-2 text-xs font-bold uppercase tracking-widest hover:bg-error/90 transition-all duration-150"
                      >
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
