import React, { useState } from 'react';
import Head from 'next/head';
import { MobileLayout } from '@/components/mobile';

const subjects = [
  'Mathematics Analysis',
  'Quantum Physics',
  'Organic Chemistry',
  'Macroeconomics',
];

export default function MobileUpload() {
  const [selectedFile, setSelectedFile] = useState<string | null>('advanced_calculus_finals.pdf');
  const [selectedSubject, setSelectedSubject] = useState(subjects[0]);

  return (
    <>
      <Head>
        <title>PrepIQ - Upload Materials</title>
        <meta name="description" content="Upload study materials for AI analysis" />
      </Head>
      <MobileLayout title="Upload">
        <div className="space-y-8">
          {/* Header */}
          <section className="mb-8">
            <h1 className="font-serif italic text-3xl leading-tight text-on-surface mb-2">Upload Materials</h1>
            <p className="text-on-surface-variant text-sm border-l-2 border-outline-variant pl-3">Archives and notes for computational analysis</p>
          </section>

          {/* Upload Area */}
          <div className="space-y-4">
            <div className="border border-dashed border-outline-variant p-8 flex flex-col items-center text-center transition-colors hover:bg-surface-container">
              <div className="w-12 h-12 border border-outline flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-on-surface">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <h3 className="text-sm font-medium uppercase tracking-widest text-on-surface mb-1">Transfer Files</h3>
              <p className="text-on-surface-variant text-xs mb-6">PDF, DOCX, PPTX (MAX 20MB)</p>
              <button className="bg-primary text-white px-6 py-2 font-medium text-xs tracking-widest uppercase transition-colors hover:bg-on-surface">
                Select Archive
              </button>
            </div>

            {/* Selected File State */}
            {selectedFile && (
              <div className="bg-transparent p-3 flex items-center justify-between border border-outline-variant">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 border border-outline-variant flex items-center justify-center flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-on-surface">
                      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
                      <path d="M14 2v4a2 2 0 0 0 2 2h4" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-on-surface truncate max-w-[180px] uppercase tracking-tighter">{selectedFile}</p>
                    <p className="text-[10px] text-on-surface-variant uppercase">2.4 MB &bull; PDF</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="w-8 h-8 flex items-center justify-center text-on-surface hover:text-error transition-colors"
                  aria-label="Remove file"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 6 6 18" />
                    <path d="m6 6 12 12" />
                  </svg>
                </button>
              </div>
            )}

            {/* Subject Selection */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-on-surface-variant ml-1 uppercase tracking-[0.2em]">Catalogue Subject</label>
              <div className="relative">
                <select
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="w-full bg-transparent border border-outline-variant h-12 px-4 text-on-surface text-sm appearance-none focus:ring-1 focus:ring-on-surface focus:border-on-surface transition-all cursor-pointer"
                >
                  {subjects.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-on-surface-variant">
                    <path d="m6 9 6 6 6-6" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Primary Action */}
            <button className="w-full bg-primary hover:bg-on-surface text-white h-12 font-bold uppercase tracking-[0.2em] text-xs transition-colors">
              Execute Analysis
            </button>
          </div>

          {/* AI Insights Preview */}
          <section className="mt-12 pb-8 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-[0.3em] text-on-surface-variant border-b border-outline-variant pb-2">Systems &amp; Logic</h2>
            <div className="space-y-4">
              {/* Topic Extraction */}
              <div className="bg-transparent p-5 border border-outline-variant flex gap-4 items-start">
                <div className="p-2 border border-outline-variant flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-on-surface">
                    <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z" />
                    <path d="M9 21h6" />
                    <path d="M10 24h4" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-bold text-sm text-on-surface mb-1 uppercase tracking-tight">Topic Extraction</h4>
                  <p className="text-xs text-on-surface-variant leading-relaxed">Structural identification of core concepts, axioms, and notations within the dataset.</p>
                </div>
              </div>

              {/* Probability Mapping */}
              <div className="bg-transparent p-5 border border-outline-variant flex gap-4 items-start">
                <div className="p-2 border border-outline-variant flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-on-surface">
                    <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" />
                    <path d="M3 5v14a2 2 0 0 0 2 2h16v-5" />
                    <path d="M18 12a2 2 0 0 0 0 4h4v-4Z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-bold text-sm text-on-surface mb-1 uppercase tracking-tight">Probability Mapping</h4>
                  <p className="text-xs text-on-surface-variant leading-relaxed">Calculated probability indices for thematic recurrence based on archival trends.</p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </MobileLayout>
    </>
  );
}
