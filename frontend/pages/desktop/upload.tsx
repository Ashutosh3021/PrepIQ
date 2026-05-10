import React, { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { getAccessToken } from '@/lib/services/base.service';

// ── Types ─────────────────────────────────────────────────────────────────────

interface UploadResult {
  success: boolean;
  upload_id: string;
  message: string;
  extracted_data?: {
    questions_count: number;
    questions?: unknown[];
  };
}

interface UploadProgress {
  upload_id: string;
  status: string;
  overall_progress: number;
  current_file: string;
  current_step: string;
  files_processed: number;
  total_files: number;
  questions_extracted: number;
  errors: string[];
  start_time: string;
  end_time?: string;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const ACCEPTED = '.pdf,.doc,.docx,.ppt,.pptx';
const ACCEPTED_MIME = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
];
const MAX_MB = 20;

// ── Helpers ───────────────────────────────────────────────────────────────────

function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? '';
  if (ext === 'pdf') return '📄';
  if (['doc', 'docx'].includes(ext)) return '📝';
  if (['ppt', 'pptx'].includes(ext)) return '📊';
  return '📎';
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function DesktopUpload() {
  const { subjects, isLoading: subjectsLoading } = useSubjects();

  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const validateAndSetFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const valid: File[] = [];
    const rejected: string[] = [];

    Array.from(incoming).forEach((f) => {
      const ext = '.' + (f.name.split('.').pop()?.toLowerCase() ?? '');
      if (!ACCEPTED.split(',').includes(ext)) {
        rejected.push(`${f.name} (unsupported type)`);
      } else if (f.size > MAX_MB * 1024 * 1024) {
        rejected.push(`${f.name} (exceeds ${MAX_MB} MB)`);
      } else {
        valid.push(f);
      }
    });

    if (rejected.length) {
      setError(`Skipped: ${rejected.join(', ')}`);
    } else {
      setError('');
    }

    setSelectedFiles((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...valid.filter((f) => !names.has(f.name))];
    });
    setResults([]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    validateAndSetFiles(e.target.files);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (name: string) => {
    setSelectedFiles((prev) => prev.filter((f) => f.name !== name));
  };

  const pollProgress = async (uploadId: string, token: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? '';
      const res = await fetch(`${apiUrl}/upload/status/${uploadId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (res.ok) {
        const data = await res.json();
        setUploadProgress(data);
        
        // Stop polling when complete or failed
        if (data.status === 'completed' || data.status === 'failed') {
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
          }
          
          if (data.status === 'completed') {
            setUploading(false);
            setSelectedFiles([]);
          }
        }
      }
    } catch (err) {
      console.error('Failed to poll progress:', err);
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) { setError('Please select at least one file.'); return; }
    if (!selectedSubjectId) { setError('Please select a subject first.'); return; }

    const token = getAccessToken();
    if (!token) { setError('You must be logged in to upload files.'); return; }

    setUploading(true);
    setError('');
    setResults([]);
    setUploadProgress(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? '';
      const formData = new FormData();
      selectedFiles.forEach((f) => formData.append('files', f));
      formData.append('subject_id', selectedSubjectId);

      const res = await fetch(`${apiUrl}/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail ?? `Upload failed (${res.status})`);
      }

      // Start polling progress
      if (data.upload_id) {
        setUploadProgress({
          upload_id: data.upload_id,
          status: 'processing',
          overall_progress: 0,
          current_file: '',
          current_step: 'Starting...',
          files_processed: 0,
          total_files: selectedFiles.length,
          questions_extracted: 0,
          errors: [],
          start_time: new Date().toISOString(),
        });

        // Poll every 500ms
        progressIntervalRef.current = setInterval(() => {
          pollProgress(data.upload_id, token);
        }, 500);
      }

      setResults(Array.isArray(data) ? data : [data]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
      setUploading(false);
    }
  };

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      <Head>
        <title>Upload Materials | PrepIQ</title>
        <meta name="description" content="Upload and enrich your study library" />
      </Head>
      <DesktopLayout>
        {/* Header */}
        <div className="mb-12 flex flex-col md:flex-row md:items-end md:justify-between gap-6">
          <div className="max-w-2xl">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-primary mb-4 block">
              Archive Management
            </span>
            <h1 className="text-5xl md:text-6xl font-serif italic leading-tight">
              Enrich your library with
              <br />
              new study materials.
            </h1>
          </div>
          <div className="text-right flex flex-col items-end">
            <p className="text-sm text-on-surface/60 max-w-[240px] mb-4 italic">
              Upload PDFs, Word documents, or PowerPoint files. Multiple files supported.
            </p>
            <div className="flex items-center gap-2 text-primary font-bold">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span className="text-xs uppercase tracking-wider">AI Analysis Ready</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <section className="lg:col-span-8 flex flex-col gap-8">

            {/* Drop zone */}
            <div
              className="bg-surface-container-highest p-12 flex flex-col border border-dashed border-primary/30 relative cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                validateAndSetFiles(e.dataTransfer.files);
              }}
            >
              <div className="absolute inset-0 border-[3px] border-dashed border-primary/20 pointer-events-none" />
              <div className="flex flex-col items-center justify-center py-16 text-center relative z-10">
                <div className="w-16 h-16 bg-primary text-white flex items-center justify-center mb-6">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold mb-2">
                  Drop files here or click to browse
                </h2>
                <p className="text-on-surface/60 text-sm mb-2 font-medium">
                  PDF · DOCX · DOC · PPTX · PPT
                </p>
                <p className="text-on-surface/40 text-xs mb-8">
                  Multiple files supported · Max {MAX_MB} MB each
                </p>
                <button
                  type="button"
                  className="bg-primary text-white px-10 py-4 font-bold uppercase tracking-widest text-xs hover:bg-primary/90 transition-colors"
                  onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                >
                  Select Files from Device
                </button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED}
                multiple
                className="hidden"
                onChange={handleFileChange}
              />
            </div>

            {/* Selected files list */}
            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-bold uppercase tracking-widest text-on-surface/60">
                  {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
                </p>
                {selectedFiles.map((f) => (
                  <div
                    key={f.name}
                    className="flex items-center justify-between px-4 py-3 bg-surface-container border border-outline-variant/20"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-lg shrink-0">{fileIcon(f.name)}</span>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{f.name}</p>
                        <p className="text-xs text-on-surface/40">
                          {(f.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(f.name)}
                      className="text-on-surface/30 hover:text-error transition-colors ml-4 shrink-0"
                      aria-label={`Remove ${f.name}`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Subject selector + upload button */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="flex flex-col gap-4">
                <label className="text-xs font-bold uppercase tracking-widest text-on-surface/60">
                  Assign to Subject
                </label>
                {subjectsLoading ? (
                  <Skeleton className="h-12" />
                ) : (
                  <div className="relative">
                    <select
                      className="w-full bg-surface-container-low border-b-2 border-primary/20 focus:border-primary appearance-none py-4 px-4 text-on-surface text-sm font-medium focus:ring-0 cursor-pointer"
                      value={selectedSubjectId}
                      onChange={(e) => setSelectedSubjectId(e.target.value)}
                    >
                      <option value="">Select a Subject…</option>
                      {subjects.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-primary">
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="6 9 12 15 18 9" />
                      </svg>
                    </span>
                  </div>
                )}
              </div>
              <div className="flex flex-col justify-end">
                <button
                  type="button"
                  disabled={uploading || selectedFiles.length === 0 || !selectedSubjectId}
                  onClick={handleUpload}
                  className="bg-primary text-white w-full py-4 font-bold uppercase tracking-widest text-xs hover:bg-primary/90 transition-colors flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? (
                    <>
                      <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                      </svg>
                      Processing {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}…
                    </>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4" />
                      </svg>
                      Upload &amp; Analyze
                      {selectedFiles.length > 0 && ` (${selectedFiles.length})`}
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-300 text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Real-time Progress Display */}
            {uploadProgress && (
              <div className="space-y-4 p-6 bg-blue-50 border border-blue-300 rounded">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-blue-900">Upload Progress</h3>
                  <span className="text-sm font-semibold text-blue-700">{uploadProgress.overall_progress}%</span>
                </div>

                {/* Main Progress Bar */}
                <div className="w-full bg-blue-200 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-blue-600 h-full transition-all duration-300"
                    style={{ width: `${uploadProgress.overall_progress}%` }}
                  />
                </div>

                {/* Status Info */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-blue-700 uppercase font-bold">Status</p>
                    <p className="font-semibold text-blue-900 capitalize">{uploadProgress.status}</p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-700 uppercase font-bold">Files</p>
                    <p className="font-semibold text-blue-900">{uploadProgress.files_processed}/{uploadProgress.total_files}</p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-700 uppercase font-bold">Questions</p>
                    <p className="font-semibold text-blue-900">{uploadProgress.questions_extracted}</p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-700 uppercase font-bold">Current Step</p>
                    <p className="font-semibold text-blue-900 truncate">{uploadProgress.current_step}</p>
                  </div>
                </div>

                {/* Current File */}
                {uploadProgress.current_file && (
                  <div className="text-sm">
                    <p className="text-xs text-blue-700 uppercase font-bold mb-1">Processing</p>
                    <p className="text-blue-900 truncate">{uploadProgress.current_file}</p>
                  </div>
                )}

                {/* Errors */}
                {uploadProgress.errors.length > 0 && (
                  <div className="text-sm">
                    <p className="text-xs text-red-700 uppercase font-bold mb-1">Errors</p>
                    {uploadProgress.errors.map((err, idx) => (
                      <p key={idx} className="text-red-700 text-xs">{err}</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Per-file results */}
            {results.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-bold uppercase tracking-widest text-on-surface/60">
                  Upload Results
                </p>
                {results.map((r, idx) => {
                  const succeeded = r.success === true;
                  const questionsCount = r.extracted_data?.questions_count ?? 0;
                  return (
                    <div
                      key={r.upload_id ?? idx}
                      className={`p-4 text-sm border-l-2 ${
                        succeeded
                          ? 'bg-green-50 border-green-500 text-green-800'
                          : 'bg-red-50 border-red-400 text-red-700'
                      }`}
                    >
                      <p className="font-bold mb-0.5">
                        {succeeded ? '✓' : '✗'} {r.message}
                      </p>
                      {succeeded && (
                        <p className="text-xs opacity-70">
                          {questionsCount} question{questionsCount !== 1 ? 's' : ''} extracted
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* Topic Extraction Info */}
          <aside className="lg:col-span-4 flex flex-col gap-6">
            <div className="bg-surface-container-low p-8 h-full flex flex-col">
              <div className="flex items-center gap-3 mb-8">
                <span className="text-primary">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a10 10 0 1 0 10 10H12V2z" />
                    <path d="M20 12a8 8 0 0 0-8-8v8h8z" />
                  </svg>
                </span>
                <h3 className="font-bold uppercase tracking-[0.15em] text-xs">
                  Topic Extraction Engine
                </h3>
              </div>
              <div className="flex flex-col gap-8">
                {[
                  { n: '01.', title: 'Multi-Format Support', desc: 'Upload PDFs, Word documents, and PowerPoint presentations. All formats are parsed for questions and key concepts.' },
                  { n: '02.', title: 'Semantic Scanning', desc: 'AI identifies key definitions, formulas, and critical concepts within the text hierarchy.' },
                  { n: '03.', title: 'Prediction Generation', desc: "Questions are added to your 'Predictions' pool based on the material's complexity and frequency." },
                ].map(({ n, title, desc }) => (
                  <div key={n} className="flex gap-4">
                    <span className="text-primary font-serif italic text-3xl shrink-0">{n}</span>
                    <div>
                      <h4 className="font-bold text-sm mb-1 uppercase tracking-wider">{title}</h4>
                      <p className="text-sm text-on-surface/70 leading-relaxed">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-auto pt-12">
                <div className="bg-primary/5 p-6 border-l-4 border-primary">
                  <p className="text-xs italic text-on-surface/70 leading-relaxed">
                    &quot;The quietest library is the one where the archive thinks for you.&quot;
                  </p>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-primary mt-2 block">
                    &mdash; Folio System Note
                  </span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </DesktopLayout>
    </>
  );
}
