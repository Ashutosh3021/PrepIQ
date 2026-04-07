import React, { useState } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';

const recentlyCatalogued = [
  { name: 'Lecture_04_Fluid.pdf', date: '12 Mar', subject: 'Thermodynamics' },
  { name: 'Modernism_Notes.docx', date: '10 Mar', subject: 'Literature' },
  { name: 'Intro_Macro_V2.pdf', date: '08 Mar', subject: 'Economics' },
  { name: 'Psych_Labs.pdf', date: '05 Mar', subject: 'Psychology' },
];

const subjectOptions = [
  'Select a Subject...',
  'Advanced Thermodynamics',
  'Modernist Literature',
  'Cognitive Psychology',
  'Macroeconomics 101',
];

export default function DesktopUpload() {
  const [selectedSubject, setSelectedSubject] = useState('');

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
            <div className="bg-surface-container-highest p-12 flex flex-col border border-dashed border-primary/30 relative">
              <div className="absolute inset-0 border-[3px] border-dashed border-primary/20 pointer-events-none" />
              <div className="flex flex-col items-center justify-center py-20 text-center relative z-10">
                <div className="w-16 h-16 bg-primary text-white flex items-center justify-center mb-6">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold mb-2">
                  Drop your lecture notes or textbooks
                </h2>
                <p className="text-on-surface/60 text-sm mb-8 font-medium">
                  PDF, DOCX, or Image formats supported (Up to 50MB)
                </p>
                <button className="bg-primary text-white px-10 py-4 font-bold uppercase tracking-widest text-xs hover:bg-primary/90 transition-colors">
                  Select Files from Device
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Form Controls */}
              <div className="flex flex-col gap-4">
                <label className="text-xs font-bold uppercase tracking-widest text-on-surface/60">
                  Assign to Subject
                </label>
                <div className="relative group">
                  <select
                    className="w-full bg-surface-container-low border-b-2 border-primary/20 focus:border-primary appearance-none py-4 px-4 text-on-surface text-sm font-medium focus:ring-0 cursor-pointer"
                    value={selectedSubject}
                    onChange={(e) => setSelectedSubject(e.target.value)}
                  >
                    {subjectOptions.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </span>
                </div>
              </div>
              <div className="flex flex-col justify-end">
                <button className="bg-primary text-white w-full py-4 font-bold uppercase tracking-widest text-xs hover:bg-primary/90 transition-colors flex items-center justify-center gap-3">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4" />
                  </svg>
                  Upload &amp; Analyze
                </button>
              </div>
            </div>
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
                <div className="flex flex-start gap-4">
                  <span className="text-primary font-serif italic text-3xl shrink-0">01.</span>
                  <div>
                    <h4 className="font-bold text-sm mb-1 uppercase tracking-wider">
                      Semantic Scanning
                    </h4>
                    <p className="text-sm text-on-surface/70 leading-relaxed">
                      Our AI identifies key definitions, formulas, and critical concepts within the
                      text hierarchy.
                    </p>
                  </div>
                </div>
                <div className="flex flex-start gap-4">
                  <span className="text-primary font-serif italic text-3xl shrink-0">02.</span>
                  <div>
                    <h4 className="font-bold text-sm mb-1 uppercase tracking-wider">
                      Automated Tagging
                    </h4>
                    <p className="text-sm text-on-surface/70 leading-relaxed">
                      Materials are automatically cross-referenced with your existing syllabus and
                      exam board requirements.
                    </p>
                  </div>
                </div>
                <div className="flex flex-start gap-4">
                  <span className="text-primary font-serif italic text-3xl shrink-0">03.</span>
                  <div>
                    <h4 className="font-bold text-sm mb-1 uppercase tracking-wider">
                      Prediction Generation
                    </h4>
                    <p className="text-sm text-on-surface/70 leading-relaxed">
                      Questions are immediately added to your &apos;Predictions&apos; pool based on
                      the new material&apos;s complexity.
                    </p>
                  </div>
                </div>
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

        {/* Secondary Info Row */}
        <div className="mt-20 border-t border-primary/10 pt-12">
          <h3 className="font-serif italic text-2xl mb-8">Recently Catalogued</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {recentlyCatalogued.map((file) => (
              <div key={file.name} className="bg-surface-container p-6 flex flex-col gap-4">
                <div className="flex justify-between items-start">
                  <span className="text-on-surface/60">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </span>
                  <span className="text-[10px] font-bold bg-primary/10 text-primary px-2 py-1 uppercase tracking-tighter">
                    Analyzed
                  </span>
                </div>
                <div>
                  <p className="font-bold text-xs uppercase tracking-wider mb-1">{file.name}</p>
                  <p className="text-[11px] text-on-surface/60">
                    {file.date} &bull; {file.subject}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </DesktopLayout>
    </>
  );
}
