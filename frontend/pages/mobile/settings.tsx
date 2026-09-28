import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { useProfile } from '@/lib/hooks/useProfile';
import { userService } from '@/lib/services/user.service';
import { getWizardPath } from '@/lib/utils/device';

// Same key the desktop settings page uses — prefs stay in sync across screens.
const NOTIF_KEY = 'prepiq-notification-settings';

export default function MobileSettings() {
  const { profile, isLoading, updateProfile } = useProfile();
  const router = useRouter();
  const [changingExam, setChangingExam] = useState(false);
  const [changeExamError, setChangeExamError] = useState('');

  const [emailNotifs, setEmailNotifs] = useState(true);
  const [studyReminders, setStudyReminders] = useState(true);
  const [predictionUpdates, setPredictionUpdates] = useState(false);
  const [prefSaving, setPrefSaving] = useState(false);
  const [prefSaved, setPrefSaved] = useState(false);

  // Form state — seeded from profile once loaded
  const [fullName, setFullName] = useState('');
  const [collegeName, setCollegeName] = useState('');
  const [program, setProgram] = useState('');
  const [yearOfStudy, setYearOfStudy] = useState('');
  const [examDate, setExamDate] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name ?? '');
      setCollegeName(profile.college_name ?? '');
      setProgram(profile.program ?? '');
      setYearOfStudy(profile.year_of_study ? String(profile.year_of_study) : '');
      if (profile.exam_date) {
        // Format as YYYY-MM-DD for the date input
        setExamDate(profile.exam_date.split('T')[0]);
      }
    }
  }, [profile]);

  // Restore device-local notification preferences on mount
  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(NOTIF_KEY) ?? '{}');
      if (typeof stored.emailNotifs === 'boolean') setEmailNotifs(stored.emailNotifs);
      if (typeof stored.studyReminders === 'boolean') setStudyReminders(stored.studyReminders);
      if (typeof stored.predictionUpdates === 'boolean') setPredictionUpdates(stored.predictionUpdates);
    } catch {
      // keep defaults
    }
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaveError('');
    try {
      await updateProfile({
        full_name: fullName.trim() || undefined,
        college_name: collegeName.trim() || undefined,
        program: program || undefined,
        year_of_study: yearOfStudy ? Number(yearOfStudy) : undefined,
        exam_date: examDate || undefined,
      });
      setSavedFlash(true);
      setTimeout(() => setSavedFlash(false), 2500);
    } catch (err: unknown) {
      setSaveError(err instanceof Error && err.message ? err.message : 'Save failed. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleSavePreferences = () => {
    setPrefSaving(true);
    try {
      const existing = JSON.parse(localStorage.getItem(NOTIF_KEY) ?? '{}');
      localStorage.setItem(NOTIF_KEY, JSON.stringify({
        ...existing,
        emailNotifs,
        studyReminders,
        predictionUpdates,
      }));
      setPrefSaved(true);
      setTimeout(() => setPrefSaved(false), 2500);
    } finally {
      setPrefSaving(false);
    }
  };

  const handleChangeExam = async () => {
    if (!window.confirm(
      'Change your exam? This will erase your current targeting settings and subjects, then restart the setup wizard.'
    )) {
      return;
    }
    setChangingExam(true);
    setChangeExamError('');
    try {
      await userService.resetTargeting();
      router.replace(getWizardPath());
    } catch (err: unknown) {
      setChangeExamError(err instanceof Error ? err.message : 'Could not reset exam. Please try again.');
      setChangingExam(false);
    }
  };

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

            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-11 w-full" />
                <Skeleton className="h-11 w-full" />
                <Skeleton className="h-11 w-full" />
                <Skeleton className="h-11 w-full" />
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Full Name</label>
                  <input
                    className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">College Name</label>
                  <input
                    className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                    type="text"
                    value={collegeName}
                    onChange={(e) => setCollegeName(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase" htmlFor="settings-program">Program</label>
                    <select
                      id="settings-program"
                      className="w-full h-11 px-3 text-on-surface appearance-none border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                      value={program}
                      onChange={(e) => setProgram(e.target.value)}
                    >
                      <option value="">Select</option>
                      <option>BTech</option>
                      <option>BE</option>
                      <option>BSc</option>
                      <option>MBA</option>
                      <option>MTech</option>
                      <option>MSc</option>
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase" htmlFor="settings-year">Year</label>
                    <select
                      id="settings-year"
                      className="w-full h-11 px-3 text-on-surface appearance-none border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                      value={yearOfStudy}
                      onChange={(e) => setYearOfStudy(e.target.value)}
                    >
                      <option value="">Select</option>
                      {[1, 2, 3, 4, 5, 6].map((y) => (
                        <option key={y} value={y}>Year {y}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Exam Date</label>
                  <input
                    className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent focus:ring-1 focus:ring-primary focus:border-primary"
                    type="date"
                    value={examDate}
                    onChange={(e) => setExamDate(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-1 opacity-60">
                  <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Email Address</label>
                  <div className="relative">
                    <input
                      className="w-full h-11 px-3 text-on-surface border border-outline-variant bg-transparent cursor-not-allowed pr-10"
                      readOnly
                      type="email"
                      value={profile?.email ?? ''}
                    />
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
                      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                  </div>
                </div>
              </div>
            )}

            <div className="flex flex-col items-end gap-2">
              <button
                onClick={handleSave}
                disabled={saving || isLoading}
                className="bg-primary hover:bg-on-primary-fixed-variant text-on-primary px-5 h-10 font-medium text-sm transition-all border border-outline-variant disabled:opacity-40"
              >
                {saving ? 'SAVING…' : savedFlash ? 'SAVED ✓' : 'SAVE CHANGES'}
              </button>
              {saveError && (
                <p className="text-[10px] text-error uppercase tracking-wider text-right">{saveError}</p>
              )}
            </div>
          </section>

          {/* Section 2: Preferences */}
          <section className="border border-outline-variant p-5 space-y-4">
            <div className="flex items-center gap-3 border-l-2 border-outline-variant pl-3">
              <h2 className="text-sm font-semibold uppercase tracking-widest">Preferences</h2>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-medium tracking-wider text-on-surface-variant uppercase">Notifications</label>
                <div className="space-y-2">
                  <label className="flex items-center justify-between group cursor-pointer border border-outline-variant/20 p-3">
                    <span className="text-sm text-on-surface uppercase tracking-tight">Email notifications</span>
                    <div className="relative inline-flex items-center cursor-pointer">
                      <input checked={emailNotifs} onChange={(e) => setEmailNotifs(e.target.checked)} className="sr-only peer" type="checkbox" />
                      <div className="w-10 h-5 bg-outline-variant/10 border border-outline-variant peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[1px] after:left-[1px] after:bg-on-surface after:h-4 after:w-4 after:transition-all" />
                    </div>
                  </label>
                  <label className="flex items-center justify-between group cursor-pointer border border-outline-variant/20 p-3">
                    <span className="text-sm text-on-surface uppercase tracking-tight">Study reminders</span>
                    <div className="relative inline-flex items-center cursor-pointer">
                      <input checked={studyReminders} onChange={(e) => setStudyReminders(e.target.checked)} className="sr-only peer" type="checkbox" />
                      <div className="w-10 h-5 bg-outline-variant/10 border border-outline-variant peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[1px] after:left-[1px] after:bg-on-surface after:h-4 after:w-4 after:transition-all" />
                    </div>
                  </label>
                  <label className="flex items-center justify-between group cursor-pointer border border-outline-variant/20 p-3">
                    <span className="text-sm text-on-surface uppercase tracking-tight">Prediction updates</span>
                    <div className="relative inline-flex items-center cursor-pointer">
                      <input checked={predictionUpdates} onChange={(e) => setPredictionUpdates(e.target.checked)} className="sr-only peer" type="checkbox" />
                      <div className="w-10 h-5 bg-outline-variant/10 border border-outline-variant peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[1px] after:left-[1px] after:bg-on-surface after:h-4 after:w-4 after:transition-all" />
                    </div>
                  </label>
                </div>
              </div>
            </div>
            <div className="flex justify-end pt-3">
              <button
                type="button"
                onClick={handleSavePreferences}
                disabled={prefSaving}
                className="bg-primary hover:bg-on-primary-fixed-variant text-on-primary px-5 h-10 font-medium text-sm transition-all border border-outline-variant disabled:opacity-40"
              >
                {prefSaving ? 'SAVING…' : prefSaved ? 'SAVED ✓' : 'SAVE PREFERENCES'}
              </button>
            </div>
          </section>

          {/* Section 3: Exam Targeting */}
          <section className="border border-outline-variant p-5 space-y-4">
            <div className="flex items-center gap-3 border-l-2 border-outline-variant pl-3">
              <h2 className="text-sm font-semibold uppercase tracking-widest">Exam Targeting</h2>
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Re-run the setup wizard to target a different exam. This completely clears your
              previously saved targeting information and the subjects from your last setup, so the new
              configuration starts clean and cannot conflict with the old one.
            </p>
            <button
              onClick={handleChangeExam}
              disabled={changingExam}
              className="w-full h-11 bg-primary text-on-primary font-medium text-sm transition-all border border-outline-variant disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {changingExam ? 'RESETTING…' : 'CHANGE EXAM'}
            </button>
            {changeExamError && (
              <p className="text-[10px] text-error uppercase tracking-wider">{changeExamError}</p>
            )}
          </section>

          {/* Section 4: Account Security */}
          <section className="border border-outline-variant p-5 space-y-4">
            <div className="flex items-center gap-3 border-l-2 border-outline-variant pl-3">
              <h2 className="text-sm font-semibold uppercase tracking-widest">Account Security</h2>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-semibold text-on-surface">Password Management</p>
              <p className="text-xs text-on-surface/60 leading-relaxed">
                Password changes aren&apos;t supported yet. Contact support to reset your
                password.
              </p>
            </div>
            <div className="flex flex-col gap-6 pt-3">
              <div className="pt-4 border-t border-outline-variant/20 space-y-3">
                <p className="text-[10px] text-on-surface-variant uppercase tracking-wider">Careful! This action cannot be undone.</p>
                <button
                  type="button"
                  onClick={() => alert('Account deletion is not yet available. Please contact support.')}
                  className="w-full h-10 border border-outline-variant text-on-surface-variant font-medium text-sm hover:bg-outline-variant/5 transition-colors uppercase tracking-widest"
                >
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
