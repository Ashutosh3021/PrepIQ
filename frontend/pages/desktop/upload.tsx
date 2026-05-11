import React, { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { getAccessToken } from '@/lib/services/base.service';

// ── Types ─────────────────────────────────────────────────────────────────────

type MaterialType = 'question_paper' | 'study_material';

interface UploadResult {
  success: boolean;
  upload_id: string;
  message: string;
  material_type?: MaterialType;
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
const MAX_MB = 20;

const MATERIAL_TYPES: { value: MaterialType; label: string; desc: string }[] = [
  {
    value: 'question_paper',
    label: 'Question Paper / PYQ',
    desc: 'Previous year papers, mock tests, exam questions',
  },
  {
    value: 'study_material',
    label: 'Book / Notes / Concepts',
    desc: 'Textbooks, lecture notes, reference material',
  },
];

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
  const [materialType, setMaterialType] = useState<MaterialType>('question_paper');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
        if (data.status === 'completed' || data.status === 'failed') {
          if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
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
      formData.append('material_type', materialType);

      const res = await fetch(`${apiUrl}/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `Upload failed (${res.status})`);

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

  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    };
  }, []);

  const isQuestionPaper = materialType === 'question_paper';

  const sidebarSteps = isQuestionPaper
    ? [
        { n: '01.', title: 'Question Detection', desc: 'AI identifies every question — numbered, lettered, roman-numeral, and sub-parts — from the paper.' },
        { n: '02.', title: 'Marks & Type Analysis', desc: 'Each question is classified by type (theory, numerical, proof) and marks are extracted automatically.' },
        { n: '03.', title: 'Prediction Pool', desc: 'Extracted questions are added to your Predictions pool and weighted by frequency across papers.' },
      ]
    : [
        { n: '01.', title: 'Concept Extraction', desc: 'AI identifies key definitions, theorems, formulas, and important concepts from the material.' },
        { n: '02.', title: 'Topic Mapping', desc: 'Concepts are mapped to syllabus units and tagged by difficulty and importance.' },
        { n: '03.', title: 'Study Context', desc: 'Extracted concepts enrich your AI Tutor and help generate better study plans and predictions.' },
      ];

  return (
    <>
      <Head>
        <title>Upload Materials | PrepIQ</title>
        <meta name="description" content="Upload and enrich your study library" />
      </Head>
      <DesktopLayout>
        {/* Header */}
        <div className="mb-8 md:mb-12 flex flex-col md:flex-row md:items-end md:justify-between gap-4 md:gap-6">
          <div className="max-w-2xl">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-primary mb-3 block">
              Archive Management
            </span>
            <h1 className="text-3xl md:text-5xl lg:text-6xl font-serif italic leading-tight">
              Enrich your library with
              <br />
              new study materials.
            </h1>
          </div>
          <div className="flex flex-col items-start md:items-end">
            <p className="text-sm text-on-surface/60 max-w-[240px] mb-3 italic">
              Upload PDFs, Word documents, or PowerPoint files.
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

            {/* Material Type Selector */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-widest text-on-surface/60">
                What are you uploading?
              </p>
              <div className="grid grid-cols-2 gap-4">
                {MATERIAL_TYPES.map((mt) => (
                  <button
                    key={mt.value}
                    type="button"
                    onClick={() => setMaterialType(mt.value)}
                    className={`flex items-start gap-4 p-5 border-2 text-left transition-all ${
                      materialType === mt.value
                        ? 'border-primary bg-primary/5'
                        : 'border-outline-variant/30 bg-surface hover:border-primary/40'
                    }`}
                  >
                    <div>
                      <p className={`text-sm font-bold ${materialType === mt.value ? 'text-primary' : 'text-on-surface'}`}>
                        {mt.label}
                      </p>
                      <p className="text-xs text-on-surface/60 mt-1 leading-relaxed">{mt.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Drop zone */}
            <div
              className="bg-surface-container-highest p-4 md:p-12 flex flex-col border border-dashed border-primary/30 relative cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); validateAndSetFiles(e.dataTransfer.files); }}
            >
              <div className="absolute inset-0 border-[3px] border-dashed border-primary/20 pointer-events-none" />
              <div className="flex flex-col items-center justify-center py-8 md:py-16 text-center relative z-10">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-primary text-white flex items-center justify-center mb-4 md:mb-6">
                  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                </div>
                <h2 className="text-lg md:text-2xl font-semibold mb-2">Drop files here or click to browse</h2>
                <p className="text-on-surface/60 text-sm mb-2 font-medium">PDF · DOCX · DOC · PPTX · PPT</p>
                <p className="text-on-surface/40 text-xs mb-6 md:mb-8">Multiple files supported · Max {MAX_MB} MB each</p>
                <button
                  type="button"
                  className="bg-primary text-white px-6 md:px-10 py-3 md:py-4 font-bold uppercase tracking-widest text-xs hover:bg-primary/90 transition-colors"
                  onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                >
                  Select Files from Device
                </button>
              </div>
              <input ref={fileInputRef} type="file" accept={ACCEPTED} multiple className="hidden" onChange={handleFileChange} />
            </div>

            {/* Selected files */}
            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-bold uppercase tracking-widest text-on-surface/60">
                  {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
                </p>
                {selectedFiles.map((f) => (
                  <div key={f.name} className="flex items-center justify-between px-4 py-3 bg-surface-container border border-outline-variant/20">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-lg shrink-0">{fileIcon(f.name)}</span>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{f.name}</p>
                        <p className="text-xs text-on-surface/40">{(f.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(f.name)}
                      className="text-on-surface/30 hover:text-error transition-colors ml-4 shrink-0"
                      aria-label={`Remove ${f.name}`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Subject + Upload */}
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
                      Upload &amp; Analyze{selectedFiles.length > 0 && ` (${selectedFiles.length})`}
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="p-4 bg-error/5 border border-error/30 text-error text-sm">{error}</div>
            )}

            {/* Progress */}
            {uploadProgress && (
              <div className="space-y-4 p-6 bg-surface-container-low border border-outline-variant/20">
                <div className="flex justify-between items-center">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-secondary">Processing</h3>
                  <span className="text-sm font-semibold text-primary">{uploadProgress.overall_progress}%</span>
                </div>
                <div className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden" role="progressbar" aria-valuenow={uploadProgress.overall_progress} aria-valuemin={0} aria-valuemax={100}>
                  <div className="bg-primary h-full transition-all duration-300" style={{ width: `${uploadProgress.overall_progress}%` }} />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest text-secondary mb-1">Status</p>
                    <p className="text-sm font-semibold text-on-surface capitalize">{uploadProgress.status}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest text-secondary mb-1">Files</p>
                    <p className="text-sm font-semibold text-on-surface">{uploadProgress.files_processed}/{uploadProgress.total_files}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest text-secondary mb-1">
                      {isQuestionPaper ? 'Questions' : 'Concepts'}
                    </p>
                    <p className="text-sm font-semibold text-on-surface">{uploadProgress.questions_extracted}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest text-secondary mb-1">Step</p>
                    <p className="text-sm font-semibold text-on-surface truncate">{uploadProgress.current_step}</p>
                  </div>
                </div>
                {uploadProgress.current_file && (
                  <p className="text-xs text-on-surface/60 truncate">Processing: {uploadProgress.current_file}</p>
                )}
                {uploadProgress.errors.length > 0 && (
                  <div className="space-y-1">
                    {uploadProgress.errors.map((err, idx) => (
                      <p key={idx} className="text-xs text-error">{err}</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Results */}
            {results.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-bold uppercase tracking-widest text-on-surface/60">Upload Results</p>
                {results.map((r, idx) => {
                  const succeeded = r.success === true;
                  const count = r.extracted_data?.questions_count ?? 0;
                  const label = r.material_type === 'study_material' ? 'concept' : 'question';
                  return (
                    <div
                      key={r.upload_id ?? idx}
                      className={`p-4 text-sm border-l-2 ${succeeded ? 'bg-green-50 border-green-500 text-green-800' : 'bg-error/5 border-error text-error'}`}
                    >
                      <p className="font-bold mb-0.5">{succeeded ? '✓' : '✗'} {r.message}</p>
                      {succeeded && (
                        <p className="text-xs opacity-70">{count} {label}{count !== 1 ? 's' : ''} extracted</p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* Sidebar */}
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
                  {isQuestionPaper ? 'Question Extraction Engine' : 'Concept Extraction Engine'}
                </h3>
              </div>
              <div className="flex flex-col gap-8">
                {sidebarSteps.map(({ n, title, desc }) => (
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
                    {isQuestionPaper
                      ? '"The pattern of past questions is the map to future answers."'
                      : '"The quietest library is the one where the archive thinks for you."'}
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
