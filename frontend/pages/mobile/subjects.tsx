import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { subjectsService } from '@/lib/services/subjects.service';
import { apiFetch } from '@/lib/services/base.service';
import { deriveSubjectProgress } from '@/lib/types/subject.types';
import type { Subject } from '@/lib/types/subject.types';

interface SubjectCardProps {
  code: string;
  name: string;
  progress: number;
  onEdit: () => void;
  onDelete: () => void;
}

function SubjectCard({ code, name, progress, onEdit, onDelete }: SubjectCardProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant/30 border-t-4 border-t-primary">
      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div>
            <p className="text-[10px] uppercase tracking-widest text-secondary mb-1">CODE: {code}</p>
            <h2 className="text-lg font-bold text-on-surface">{name}</h2>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onEdit}
              className="text-on-surface-variant p-1 active:opacity-60"
              aria-label={`Edit ${name}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                <path d="m15 5 4 4" />
              </svg>
            </button>
            <button
              type="button"
              onClick={onDelete}
              className="text-error p-1 active:opacity-60"
              aria-label={`Delete ${name}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h5l2 13h4L16 6h5" />
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                <line x1="10" y1="11" x2="10" y2="17" />
                <line x1="14" y1="11" x2="14" y2="17" />
              </svg>
            </button>
          </div>
        </div>
        <div className="mb-4">
          <div className="flex justify-between items-end mb-1">
            <span className="text-xs font-bold text-secondary">PROGRESS</span>
            <span className="text-xs font-bold text-primary">{progress}%</span>
          </div>
          <div className="w-full h-2 bg-secondary-container">
            <div className="bg-primary h-full" style={{ width: `${progress}%` }} />
          </div>
        </div>
        <Link href="/mobile/progress" className="w-full py-2 border border-primary text-primary font-bold flex items-center justify-center gap-2 hover:bg-surface-container-high transition-colors">
          <span>Track Progress</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
        </Link>
      </div>
    </div>
  );
}

// ── Add / Edit subject modal ──────────────────────────────────────────────────

interface SubjectFormModalProps {
  initial?: Subject;
  onClose: () => void;
  onSaved: () => void;
}

function SubjectFormModal({ initial, onClose, onSaved }: SubjectFormModalProps) {
  const [name, setName] = useState(initial?.name ?? '');
  const [code, setCode] = useState(initial?.code ?? '');
  const [semester, setSemester] = useState(initial?.semester ? String(initial.semester) : '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Subject name is required.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const payload = {
        name: name.trim(),
        code: code.trim() || undefined,
        semester: semester ? Number(semester) : undefined,
      };
      if (initial) {
        await subjectsService.update(initial.id, payload);
      } else {
        await subjectsService.create(payload);
      }
      onSaved();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save subject.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40"
      onClick={(e) => e.target === e.currentTarget && !saving && onClose()}
    >
      <div className="bg-surface w-full sm:max-w-md p-6 sm:p-8 relative max-h-[90vh] overflow-y-auto">
        <button
          type="button"
          onClick={onClose}
          disabled={saving}
          className="absolute top-4 right-4 text-on-surface/40 hover:text-on-surface transition-colors"
          aria-label="Close"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <h2 className="font-serif italic text-2xl mb-6 text-on-surface">
          {initial ? 'Edit Subject' : 'Add Subject'}
        </h2>

        {error && (
          <div className="mb-4 px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary" htmlFor="subject-name">
              Subject Name *
            </label>
            <input
              id="subject-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Linear Algebra"
              className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
              required
              autoFocus
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary" htmlFor="subject-code">
                Subject Code
              </label>
              <input
                id="subject-code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="e.g. MA201"
                className="w-full bg-surface border-none border-b-2 border-outline-variant/40 focus:border-primary focus:ring-0 p-3 text-sm"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary" htmlFor="subject-semester">
                Semester
              </label>
              <input
                id="subject-semester"
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

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="flex-1 border border-primary text-primary py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary hover:text-on-primary transition-all disabled:opacity-40"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 bg-primary text-on-primary py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-all disabled:opacity-40"
            >
              {saving ? 'Saving…' : initial ? 'Save' : 'Add Subject'}
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

export default function MobileSubjects() {
  const { subjects, isLoading, error, refresh } = useSubjects();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Subject | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Subject | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleting(true);
    try {
      await subjectsService.delete(deleteConfirm.id);
      await refresh();
      setDeleteConfirm(null);
    } catch (err: unknown) {
      setSyncMessage(err instanceof Error ? err.message : 'Failed to delete subject.');
      setDeleteConfirm(null);
    } finally {
      setDeleting(false);
    }
  };

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

      const existingNames = new Set(subjects.map((s) => s.name.toLowerCase()));
      const toCreate = focusSubjects.filter((name) => !existingNames.has(name.toLowerCase()));

      if (toCreate.length === 0) {
        setSyncMessage('All wizard subjects are already in your list.');
        return;
      }

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

  if (isLoading) {
    return (
      <MobileLayout title="My Subjects">
        <div className="space-y-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </MobileLayout>
    );
  }

  if (error) {
    return (
      <MobileLayout title="My Subjects">
        <div className="text-red-600 p-4">
          {error instanceof Error ? error.message : 'Failed to load subjects'}
        </div>
      </MobileLayout>
    );
  }

  return (
    <>
      <Head>
        <title>PrepIQ - My Subjects</title>
        <meta name="description" content="Manage your subjects on PrepIQ" />
      </Head>
      <MobileLayout title="My Subjects">
        {showForm && (
          <SubjectFormModal
            onClose={() => setShowForm(false)}
            onSaved={() => refresh()}
          />
        )}
        {editing && (
          <SubjectFormModal
            initial={editing}
            onClose={() => setEditing(null)}
            onSaved={() => refresh()}
          />
        )}
        {deleteConfirm && (
          <div
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40"
            onClick={(e) => e.target === e.currentTarget && !deleting && setDeleteConfirm(null)}
          >
            <div className="bg-surface w-full sm:max-w-md p-6 sm:p-8 relative">
              <h2 className="font-serif italic text-2xl mb-3 text-on-surface">Delete Subject?</h2>
              <p className="text-sm text-on-surface/70 mb-6">
                Delete <strong>{deleteConfirm.name}</strong> and all of its data? This cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setDeleteConfirm(null)}
                  disabled={deleting}
                  className="flex-1 border border-primary text-primary py-3 text-xs font-bold uppercase tracking-widest hover:bg-primary hover:text-on-primary transition-all disabled:opacity-40"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={deleting}
                  className="flex-1 bg-error text-on-error py-3 text-xs font-bold uppercase tracking-widest hover:bg-error/90 transition-all disabled:opacity-40"
                >
                  {deleting ? 'Deleting…' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-8">
          {/* Action Buttons */}
          <div className="flex flex-col gap-3">
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="w-full bg-primary text-on-primary py-3 px-4 font-bold flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5v14" />
                <path d="M5 12h14" />
              </svg>
              <span>Add Subject</span>
            </button>
            <button
              type="button"
              onClick={handleSyncFromWizard}
              disabled={syncing}
              className="w-full bg-transparent border border-outline-variant text-on-surface-variant py-3 px-4 font-bold flex items-center justify-center gap-2 active:scale-[0.98] transition-transform disabled:opacity-40"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.5 2v6h-6" />
                <path d="M2.5 22v-6h6" />
                <path d="M2 11.5a10 10 0 0 1 18.8-4.3" />
                <path d="M22 12.5a10 10 0 0 1-18.8 4.2" />
              </svg>
              <span>{syncing ? 'Syncing…' : 'Sync from Wizard'}</span>
            </button>
            {syncMessage && (
              <p className="text-xs text-on-surface/60 text-center">{syncMessage}</p>
            )}
          </div>

          {/* Subject List */}
          <div className="space-y-4">
            {subjects.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-on-surface-variant/50 text-sm">No subjects yet.</p>
              </div>
            ) : (
              subjects.map((subject) => (
                <SubjectCard
                  key={subject.id}
                  // H-19: use code from backend, derive progress from activity counts
                  code={subject.code ?? subject.id.slice(0, 8).toUpperCase()}
                  name={subject.name}
                  progress={deriveSubjectProgress(subject)}
                  onEdit={() => setEditing(subject)}
                  onDelete={() => setDeleteConfirm(subject)}
                />
              ))
            )}

            {/* Empty State Hint */}
            <div className="border-2 border-dashed border-outline-variant p-8 flex flex-col items-center justify-center text-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-outline-variant mb-3">
                <path d="m16 6 4 14" />
                <path d="M12 6v14" />
                <path d="M8 8v12" />
                <path d="M4 4v16" />
              </svg>
              <p className="font-serif italic text-xl text-on-surface mb-2">New semester?</p>
              <p className="text-secondary text-sm max-w-[200px]">Import your syllabus using the PrepIQ Study Wizard.</p>
            </div>
          </div>
        </div>
      </MobileLayout>
    </>
  );
}
