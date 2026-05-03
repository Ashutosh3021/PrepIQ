import React, { useState, useRef } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { getAccessToken } from '@/lib/services/base.service';

// ── Types ────────────────────────────────────────────────────────────────────

interface UploadResult {
  paper_id: string;
  status: string;
  message: string;
  questions_count: number;
}

// ── Component ────────────────────────────────────────────────────────────────

export default function DesktopUpload() {
  const { subjects, isLoading: subjectsLoading } = useSubjects();

  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    setResult(null);
    setError('');
  };

  const handleSelectClick = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!selectedFile) { setError('Please select a PDF file first.'); return; }
    if (!selectedSubjectId) { setError('Please select a subject first.'); return; }

    const token = getAccessToken();
    if (!token) { setError('You must be logged in to upload files.'); return; }

    setUploading(true);
    setError('');
    setResult(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? '';
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('subject_id', selectedSubjectId);

      const res = await fetch(`${apiUrl}/papers/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail ?? `Upload failed (${res.status})`);
      }

      setResult(data as UploadResult);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

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
              The system will automatically scan, categorize, and extract core concepts from your
              documents.
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
          {/* Upload Section */}
          <section className="lg:col-span-8 flex flex-col gap-8">

            {/* Drop zone */}
            <div
              className="bg-surface-container-highest p-12 flex flex-col border border-dashed border-primary/30 relative cursor-pointer"
              onClick={handleSelectClick}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const file = e.dataTransfer.files?.[0];
                if (file) { setSelectedFile(file); setResult(null); setError(''); }
              }}
            >
              <div className="absolute inset-0 border-[3px] border-dashed border-primary/20 pointer-events-none" />
              <div className="flex flex-col items-center justify-center py-20 text-center relative z-10">
                <div className="w-16 h-16 bg-primary text-white flex items-center justify-center mb-6">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                </div>
                {selectedFile ? (
                  <>
                    <p className="text-lg font-semibold text-primary mb-1">{selectedFile.name}</p>
                    <p className="text-sm text-on-surface/60">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB · Click to change
                    </p>
                  </>
                ) : (
                  <>
                    <h2 className="text-2xl font-semibold mb-2">
                      Drop your question paper here
                    </h2>
                    <p className="text-on-surface/60 text-sm mb-8 font-medium">
                      PDF only · Max 10 MB
                    </p>
                    <button
                      type="button"
                      className="bg-primary text-white px-10 py-4 font-bold uppercase tracking-widest text-xs hover:bg-primary/90 transition-colors"
                      onClick={(e) => { e.stopPropagation(); handleSelectClick(); }}
                    >
                      Select File from Device
                    </button>
                  </>
                )}
              </div>
              {/* Hidden real file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>

            {/* Subject selector + upload button */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="flex flex-col gap-4">
                <label className="text-xs font-bold uppercase tracking-widest text-on-surface/60">
                  Assign to Subject
                </label>
                {subjectsLoading ? (
                  <Skeleton className="h-12" />
                ) : (
                  <div className="relative group">
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
                  disabled={uploading || !selectedFile || !selectedSubjectId}
                  onClick={handleUpload}
                  className="bg-primary text-white w-full py-4 font-bold uppercase tracking-widest text-xs hover:bg-primary/90 transition-colors flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? (
                    <>
                      <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                      </svg>
                      Processing…
                    </>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4" />
                      </svg>
                      Upload &amp; Analyze
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Error / success feedback */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-300 text-red-700 text-sm">
                {error}
              </div>
            )}
            {result && (
              <div className="p-4 bg-green-50 border border-green-300 text-green-800 text-sm">
                <p className="font-bold mb-1">Upload successful!</p>
                <p>{result.message}</p>
                <p className="mt-1 text-xs opacity-70">
                  {result.questions_count} question{result.questions_count !== 1 ? 's' : ''} extracted · Paper ID: {result.paper_id}
                </p>
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
                  { n: '01.', title: 'Semantic Scanning', desc: 'Our AI identifies key definitions, formulas, and critical concepts within the text hierarchy.' },
                  { n: '02.', title: 'Automated Tagging', desc: 'Materials are automatically cross-referenced with your existing syllabus and exam board requirements.' },
                  { n: '03.', title: 'Prediction Generation', desc: "Questions are immediately added to your 'Predictions' pool based on the new material's complexity." },
                ].map(({ n, title, desc }) => (
                  <div key={n} className="flex flex-start gap-4">
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
