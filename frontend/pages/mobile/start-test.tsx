import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MobileLayout } from '@/components/mobile';

export default function MobileStartTest() {
  return (
    <>
      <Head>
        <title>PrepIQ - Start Test</title>
        <meta name="description" content="Begin your test session" />
      </Head>
      <MobileLayout title="Start Test">
        {/* Modal Overlay */}
        <div className="fixed inset-0 z-50 bg-on-surface/40 backdrop-blur-sm flex items-end md:items-center justify-center">
          {/* The Academic Atelier Modal */}
          <div className="bg-surface w-full max-w-md mx-auto border-t-4 border-primary shadow-2xl">
            <div className="p-6">
              {/* Header */}
              <div className="mb-8">
                <span className="text-[10px] uppercase tracking-[0.2em] text-primary font-extrabold block mb-2">Examination Protocol</span>
                <h2 className="font-serif italic text-3xl text-on-surface leading-none">PrepIQ Advanced Certification</h2>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-px bg-outline-variant/20 mb-8">
                <div className="bg-surface-container-low p-4 flex flex-col justify-between h-24">
                  <span className="text-[10px] uppercase tracking-widest font-bold opacity-60">Duration</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-light">45</span>
                    <span className="text-sm font-bold tracking-tighter italic">mins</span>
                  </div>
                </div>
                <div className="bg-surface-container-low p-4 flex flex-col justify-between h-24">
                  <span className="text-[10px] uppercase tracking-widest font-bold opacity-60">Quantities</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-light">30</span>
                    <span className="text-sm font-bold tracking-tighter italic">items</span>
                  </div>
                </div>
                <div className="bg-surface-container-high col-span-2 p-4">
                  <div className="flex items-center gap-3">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                    </svg>
                    <span className="text-sm font-medium tracking-tight">Proctored Session: Continuous focus required.</span>
                  </div>
                </div>
              </div>

              {/* Rules List */}
              <div className="space-y-4 mb-8">
                <div className="flex gap-3 items-start">
                  <span className="font-serif italic text-lg text-primary mt-[-2px]">01</span>
                  <p className="text-sm leading-relaxed text-on-surface/80">Navigation is locked once the timer commences. All responses are final upon submission.</p>
                </div>
                <div className="flex gap-3 items-start">
                  <span className="font-serif italic text-lg text-primary mt-[-2px]">02</span>
                  <p className="text-sm leading-relaxed text-on-surface/80">External resources, tabs, or collaborative software will result in immediate termination.</p>
                </div>
              </div>

              {/* Primary Action */}
              <button className="w-full bg-primary hover:bg-on-primary-fixed-variant text-white py-5 flex items-center justify-center gap-4 transition-colors group active:scale-[0.98]">
                <span className="text-[11px] uppercase tracking-[0.3em] font-black">Begin Test</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="transition-transform group-hover:translate-x-1">
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </button>
              <Link href="/mobile/tests" className="w-full py-3 mt-2 text-[10px] uppercase tracking-widest font-bold text-on-surface/40 hover:text-on-surface transition-colors flex items-center justify-center">
                Return to Library
              </Link>
            </div>
          </div>
        </div>
      </MobileLayout>
    </>
  );
}
