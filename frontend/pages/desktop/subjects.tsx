import React, { useState } from 'react';
import Head from 'next/head';
import { DesktopLayout, SubjectCard } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { subjectsService } from '@/lib/services/subjects.service';
import { apiFetch } from '@/lib/services/base.service';
import { deriveSubjectProgress } from '@/lib/types/subject.types';

// ── Add Subject modal ─────────────────────────────────────────────────────────

interface AddSubjectModalProps {
  onClose: () => void;
  onCreated: () => void;
}

function AddSubjectModal({ onClose, onCreated }: AddSubjectModalProps) {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [semester, setSemester] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setError('Subject name is required.'); return; }
    setSaving(true);
    setError('');
    try {
      await subjectsService.create({
        name: name.trim(),
        code: code.trim() || undefined,
        semester: semester ? Number(semester) : undefined,
      });
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create subject.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-surface w-full max-w-md p-10 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-on-surface/40 hover:text-on-surface transition-colors"
          aria-label="Close"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <h2 className="font-serif italic text-3xl mb-8 text-on-surface">Add Subject</h2>

        {error && (
          <div className="mb-6 px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
              Subject Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Linear Algebra"
              className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
              required
              autoFocus
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                Subject Code
              </label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="e.g. MA201"
                className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                Semester
              </label>
              <input
                type="number"
                min={1}
                max={8}
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                placeholder="1–8"
                className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
              />
            </div>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-primary text-primary py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary hover:text-on-primary transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 bg-primary text-on-primary py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-all disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {saving && (
                <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
              )}
              {saving ? 'Creating…' : 'Create Subject'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

interface WizardStatus {
  focus_subjects?: string[];
}

export default function DesktopSubjects() {
  const { subjects, isLoading, error, refresh } = useSubjects();
  const [showAddModal, setShowAddModal] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  // ── Delete Subject ──────────────────────────────────────────────────────────
  const handleDeleteSubject = async () => {
    if (!deleteConfirm) return;
    setDeleting(true);
    try {
      await subjectsService.delete(deleteConfirm.id);
      await refresh();
      setDeleteConfirm(null);
    } catch (err: unknown) {
      console.error('Failed to delete subject:', err);
      setDeleteConfirm(null);
    } finally {
      setDeleting(false);
    }
  };

  // ── Sync from Wizard ────────────────────────────────────────────────────────
  const handleSyncFromWizard = async () => {
    setSyncing(true);
    setSyncMessage('');
    try {
      const status = await apiFetch<WizardStatus>('/wizard/status', {});
      const focusSubjects: string[] = status.focus_subjects ?? [];

      if (focusSubjects.length === 0) {
        setSyncMessage('No subjects found in your wizard setup. Complete the wizard first.');
        return;
      }

      // Find which subjects don't already exist (case-insensitive)
      const existingNames = new Set(subjects.map((s) => s.name.toLowerCase()));
      const toCreate = focusSubjects.filter((name) => !existingNames.has(name.toLowerCase()));

      if (toCreate.length === 0) {
        setSyncMessage('All wizard subjects are already in your list.');
        return;
      }

      // Create missing subjects sequentially
      for (const name of toCreate) {
        await subjectsService.create({ name });
      }

      await refresh();
      setSyncMessage(`Synced ${toCreate.length} subject${toCreate.length !== 1 ? 's' : ''} from your wizard.`);
    } catch (err: unknown) {
      setSyncMessage(err instanceof Error ? err.message : 'Sync failed. Please try again.');
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncMessage(''), 4000);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <DesktopLayout>
        <Skeleton className="h-12 w-96 mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </DesktopLayout>
    );
  }

  if (error) {
    return (
      <DesktopLayout>
        <div className="text-red-600">Failed to load subjects</div>
      </DesktopLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Subjects | PrepIQ</title>
        <meta name="description" content="Browse and manage your study subjects" />
      </Head>
      <DesktopLayout>
        {showAddModal && (
          <AddSubjectModal
            onClose={() => setShowAddModal(false)}
            onCreated={() => refresh()}
          />
        )}

        {/* Delete Confirmation Dialog */}
        {deleteConfirm && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
            onClick={(e) => e.target === e.currentTarget && !deleting && setDeleteConfirm(null)}
          >
            <div className="bg-surface w-full max-w-md p-10 relative">
              <h2 className="font-serif italic text-2xl mb-4 text-on-surface">Delete Subject?</h2>
              <p className="text-sm text-on-surface/70 mb-6">
                Are you sure you want to delete <strong>{deleteConfirm.name}</strong>? This will permanently remove the subject and all associated data (papers, questions, predictions, mock tests, study plans, and chat history). This action cannot be undone.
              </p>
              <div className="flex gap-4">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  disabled={deleting}
                  className="flex-1 border border-primary text-primary py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary hover:text-on-primary transition-all disabled:opacity-40"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteSubject}
                  disabled={deleting}
                  className="flex-1 bg-error text-on-error py-3 text-xs font-bold uppercase tracking-widest hover:bg-error/90 transition-all disabled:opacity-40 flex items-center justify-center gap-2"
                >
                  {deleting && (
                    <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                  )}
                  {deleting ? 'Deleting…' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Header Row */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 md:mb-16 gap-4 md:gap-6">
          <div className="flex flex-col">
            <span className="text-xs font-bold uppercase tracking-widest text-primary mb-2">
              Academic Atelier / {new Date().getFullYear()}
            </span>
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-serif italic leading-none">My Subjects</h1>
          </div>
          <div className="flex flex-col items-start md:items-end gap-3 w-full md:w-auto">
            <div className="flex gap-3 w-full md:w-auto">
              <button
                onClick={() => setShowAddModal(true)}
                className="flex-1 md:flex-none bg-primary text-on-primary px-4 md:px-6 py-3 text-sm font-semibold uppercase tracking-wider hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                <span>Add Subject</span>
              </button>
              <button
                onClick={handleSyncFromWizard}
                disabled={syncing}
                className="flex-1 md:flex-none border border-primary text-primary px-4 md:px-6 py-3 text-sm font-semibold uppercase tracking-wider hover:bg-primary hover:text-on-primary transition-all flex items-center justify-center gap-2 disabled:opacity-40"
              >
                {syncing ? (
                  <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="1 4 1 10 7 10" />
                    <polyline points="23 20 23 14 17 14" />
                    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                  </svg>
                )}
                <span className="hidden sm:inline">{syncing ? 'Syncing…' : 'Sync from Wizard'}</span>
                <span className="sm:hidden">{syncing ? '…' : 'Sync'}</span>
              </button>
            </div>
            {syncMessage && (
              <p className="text-xs text-on-surface/60 max-w-xs">{syncMessage}</p>
            )}
          </div>
        </header>

        {/* Subjects Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {subjects.length === 0 ? (
            <div className="col-span-full text-center py-16">
              <p className="text-on-surface/50 text-lg mb-4">No subjects yet.</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="bg-primary text-on-primary px-6 py-3 text-sm font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors"
              >
                Add your first subject
              </button>
            </div>
          ) : (
            subjects.map((subject) => (
              <SubjectCard
                key={subject.id}
                subject={{
                  code: subject.code ?? subject.id.slice(0, 8).toUpperCase(),
                  name: subject.name,
                  description: subject.syllabus_json
                    ? `Semester ${subject.semester ?? '—'} · ${subject.academic_year ?? ''}`
                    : `${subject.papers_uploaded} paper${subject.papers_uploaded !== 1 ? 's' : ''} uploaded`,
                  progress: deriveSubjectProgress(subject),
                }}
                onTrackProgress={() => {}}
                onDelete={() => setDeleteConfirm({ id: subject.id, name: subject.name })}
              />
            ))
          )}
        </div>
      </DesktopLayout>
    </>
  );
}
