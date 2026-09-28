import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { MobileLayout } from '@/components/mobile';
import { Skeleton } from '@/components/common';
import { testsService, BackendTest } from '@/lib/services/tests.service';

// Pre-test briefing. The actual test runner lives at /desktop/start-test —
// Begin Test hands off to it with the selected testId.
export default function MobileStartTest() {
  const router = useRouter();
  const { testId } = router.query;

  const [test, setTest] = useState<BackendTest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!router.isReady) return;
    if (!testId) {
      // Nothing to brief on — the old page showed a static mock modal forever.
      router.replace('/mobile/tests');
      return;
    }

    let cancelled = false;
    const load = async () => {
      try {
        const tests = await testsService.getAll();
        const found = tests.find((t) => t.test_id === testId);
        if (cancelled) return;
        if (!found) {
          setError('Test not found.');
        } else {
          setTest(found);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error && err.message ? err.message : 'Failed to load test.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [router.isReady, testId, router]);

  const duration = test?.time_limit_minutes ?? 0;
  const itemCount = test?.total_questions ?? 0;

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
                <h2 className="font-serif italic text-3xl text-on-surface leading-none">
                  {loading ? 'Loading…' : test ? `Mock Test · ${itemCount} Questions` : 'Test unavailable'}
                </h2>
              </div>

              {loading ? (
                <div className="space-y-4 mb-8">
                  <Skeleton className="h-24" />
                  <Skeleton className="h-24" />
                </div>
              ) : error ? (
                <div className="mb-8 px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
                  {error}
                </div>
              ) : (
                <>
                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-px bg-outline-variant/20 mb-8">
                    <div className="bg-surface-container-low p-4 flex flex-col justify-between h-24">
                      <span className="text-[10px] uppercase tracking-widest font-bold opacity-60">Duration</span>
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-light">{duration || '—'}</span>
                        <span className="text-sm font-bold tracking-tighter italic">mins</span>
                      </div>
                    </div>
                    <div className="bg-surface-container-low p-4 flex flex-col justify-between h-24">
                      <span className="text-[10px] uppercase tracking-widest font-bold opacity-60">Questions</span>
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-light">{itemCount || '—'}</span>
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
                </>
              )}

              {/* Primary Action */}
              <button
                type="button"
                disabled={loading || !!error || !test}
                onClick={() => router.push(`/desktop/start-test?testId=${testId}`)}
                className="w-full bg-primary hover:bg-on-primary-fixed-variant text-white py-5 flex items-center justify-center gap-4 transition-colors group active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
              >
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
