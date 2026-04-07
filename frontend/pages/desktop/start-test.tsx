import React, { useState } from 'react';
import Head from 'next/head';
import { DesktopLayout } from '@/components/desktop';

export default function DesktopStartTest() {
  const [agreed, setAgreed] = useState(false);

  return (
    <>
      <Head>
        <title>Start Test | PrepIQ</title>
        <meta name="description" content="Begin your PrepIQ certification assessment" />
      </Head>
      <DesktopLayout className="!px-12 !py-20">
        {/* Header Section */}
        <header className="grid grid-cols-1 md:grid-cols-12 gap-8 mb-24 items-end">
          <div className="md:col-span-8">
            <span className="uppercase text-[10px] tracking-[0.2em] font-bold text-primary mb-4 block">
              Assessment Portal
            </span>
            <h1 className="font-serif italic text-7xl md:text-8xl leading-none text-on-surface">
              PrepIQ Advanced <br /> Certification
            </h1>
          </div>
          <div className="md:col-span-4 flex flex-col items-end gap-2 text-right">
            <div className="flex items-center gap-4 border-b border-primary/20 pb-2 w-full justify-end">
              <span className="uppercase text-[10px] tracking-widest font-semibold opacity-60">
                Session Duration
              </span>
              <span className="text-xl font-medium">45 mins</span>
            </div>
            <div className="flex items-center gap-4 border-b border-primary/20 pb-2 w-full justify-end">
              <span className="uppercase text-[10px] tracking-widest font-semibold opacity-60">
                Total Questions
              </span>
              <span className="text-xl font-medium">30 items</span>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-16">
          {/* Left: Hero/Visual element */}
          <div className="md:col-span-5">
            <div className="bg-surface-container-high aspect-[4/5] relative flex items-center justify-center p-12">
              <div className="w-full h-full bg-surface-container-highest flex items-center justify-center">
                <span className="text-on-surface/20 text-sm uppercase tracking-widest">
                  Academic Study
                </span>
              </div>
              <div className="absolute inset-0 border border-primary/10 m-4" />
            </div>
          </div>

          {/* Right: Rules and CTA */}
          <div className="md:col-span-7 flex flex-col justify-between">
            <section>
              <h2 className="font-bold text-xs uppercase tracking-[0.3em] mb-8 border-l-4 border-primary pl-4">
                Examination Protocol
              </h2>
              <div className="space-y-10">
                <div className="group">
                  <span className="font-serif italic text-3xl block mb-2 text-primary opacity-40 group-hover:opacity-100 transition-opacity">
                    01.
                  </span>
                  <p className="text-base leading-relaxed max-w-md">
                    Candidates must complete the assessment within the 45-minute limit. The timer
                    will start immediately upon clicking{' '}
                    <span className="font-bold">Begin Test</span>.
                  </p>
                </div>
                <div className="group">
                  <span className="font-serif italic text-3xl block mb-2 text-primary opacity-40 group-hover:opacity-100 transition-opacity">
                    02.
                  </span>
                  <p className="text-base leading-relaxed max-w-md">
                    Navigating away from this tab or minimizing the window will trigger an automatic
                    security pause. Repeated violations will void the attempt.
                  </p>
                </div>
                <div className="group">
                  <span className="font-serif italic text-3xl block mb-2 text-primary opacity-40 group-hover:opacity-100 transition-opacity">
                    03.
                  </span>
                  <p className="text-base leading-relaxed max-w-md">
                    Each question has a single correct answer. You may flag questions for review and
                    return to them if time permits.
                  </p>
                </div>
              </div>
            </section>

            <div className="mt-16 flex flex-col gap-6 items-start">
              <label className="flex items-center gap-4 cursor-pointer">
                <input
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  className="w-5 h-5 border-2 border-primary text-primary focus:ring-0 bg-transparent"
                />
                <span className="text-sm font-medium">
                  I have read and agree to the PrepIQ examination terms and conditions.
                </span>
              </label>
              <button
                className={`font-bold uppercase tracking-[0.2em] px-12 py-5 flex items-center gap-4 group transition-all ${
                  agreed
                    ? 'bg-primary text-on-primary hover:bg-primary/90'
                    : 'bg-primary/50 text-on-primary/50 cursor-not-allowed'
                }`}
                disabled={!agreed}
              >
                Begin Test
                <span className="group-hover:translate-x-1 transition-transform">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer Metric / Archive info */}
        <footer className="mt-32 pt-8 border-t border-primary/10 flex justify-between items-center text-[10px] tracking-widest uppercase font-semibold text-tertiary">
          <div className="flex gap-12">
            <span>Assessment ID: PQ-CERT-2024-X1</span>
            <span>Minimum Passing Score: 85%</span>
          </div>
          <span>Folio Archive System &copy; 2024</span>
        </footer>
      </DesktopLayout>
    </>
  );
}
