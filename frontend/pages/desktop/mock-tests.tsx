import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { DesktopLayout } from '@/components/desktop';
import { Skeleton } from '@/components/common';
import { useSubjects } from '@/lib/hooks/useSubjects';
import { useMockTests } from '@/lib/hooks/useMockTests';
import { mockTestsService } from '@/lib/services/mock-tests.service';
import type {
  Difficulty,
  TestSource,
  MockTestCreate,
  BlueprintPreset,
  BlueprintSectionSpec,
  BlueprintView,
} from '@/lib/services/mock-tests.service';
import { cn } from '@/lib/utils/cn';

// ── Config check ──────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}

function StatusBadge({ status }: { status: 'pending' | 'completed' }) {
  return (
    <span
      className={cn(
        'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5',
        status === 'completed'
          ? 'bg-green-100 text-green-700'
          : 'bg-surface-container-high text-on-surface/50'
      )}
    >
      {status === 'completed' ? 'Completed' : 'Pending'}
    </span>
  );
}

const BLOOM_OPTIONS = ['recall', 'understand', 'apply', 'analyze'] as const;
const MAX_SECTIONS = 4;

// ── Blueprint section editor row ──────────────────────────────────────────────

function BlueprintSectionEditor({
  section,
  index,
  onChange,
  onRemove,
  canRemove,
}: {
  section: BlueprintSectionSpec;
  index: number;
  onChange: (next: BlueprintSectionSpec) => void;
  onRemove: () => void;
  canRemove: boolean;
}) {
  const bloom = section.bloom ?? [];
  const toggleBloom = (level: string) => {
    const has = bloom.includes(level as (typeof BLOOM_OPTIONS)[number]);
    onChange({
      ...section,
      bloom: has ? bloom.filter((b) => b !== level) : [...bloom, level as (typeof BLOOM_OPTIONS)[number]],
    });
  };

  const numCls =
    'w-full bg-surface border border-outline-variant/30 focus:border-primary focus:ring-0 px-3 py-2 text-sm text-on-surface';

  return (
    <div className="border border-outline-variant/20 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-widest text-primary shrink-0">
          Section {index + 1}
        </span>
        <input
          type="text"
          value={section.name ?? ''}
          onChange={(e) => onChange({ ...section, name: e.target.value })}
          placeholder="Section name"
          aria-label={`Section ${index + 1} name`}
          className="flex-1 min-w-0 bg-surface border border-outline-variant/30 focus:border-primary focus:ring-0 px-3 py-1.5 text-sm text-on-surface"
        />
        {canRemove && (
          <button
            type="button"
            onClick={onRemove}
            aria-label={`Remove section ${index + 1}`}
            className="text-on-surface/40 hover:text-error text-lg leading-none px-1"
          >
            ×
          </button>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2">
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
            Questions
          </span>
          <input
            type="number"
            min={1}
            max={30}
            value={section.count}
            onChange={(e) => onChange({ ...section, count: Number(e.target.value) })}
            className={numCls}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
            Marks each
          </span>
          <input
            type="number"
            min={1}
            max={100}
            value={section.marks}
            onChange={(e) => onChange({ ...section, marks: Number(e.target.value) })}
            className={numCls}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
            Choice (opt.)
          </span>
          <input
            type="number"
            min={1}
            max={section.count}
            value={section.attempt ?? ''}
            placeholder="all"
            onChange={(e) =>
              onChange({
                ...section,
                attempt: e.target.value === '' ? null : Number(e.target.value),
              })
            }
            className={numCls}
          />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
            Difficulty
          </span>
          <select
            value={section.difficulty}
            onChange={(e) => onChange({ ...section, difficulty: e.target.value as Difficulty })}
            className="w-full bg-surface border border-outline-variant/30 focus:border-primary focus:ring-0 px-3 py-2 text-sm text-on-surface cursor-pointer"
          >
            {(['easy', 'medium', 'hard', 'mixed'] as Difficulty[]).map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
            Question type
          </span>
          <select
            value={section.qtype}
            onChange={(e) =>
              onChange({ ...section, qtype: e.target.value as BlueprintSectionSpec['qtype'] })
            }
            className="w-full bg-surface border border-outline-variant/30 focus:border-primary focus:ring-0 px-3 py-2 text-sm text-on-surface cursor-pointer"
          >
            <option value="any">any</option>
            <option value="mcq">mcq</option>
            <option value="descriptive">descriptive</option>
          </select>
        </label>
      </div>

      {/* Cognitive (Bloom) mix */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50 mr-1">
          Cognitive mix
        </span>
        {BLOOM_OPTIONS.map((level) => (
          <button
            key={level}
            type="button"
            onClick={() => toggleBloom(level)}
            aria-pressed={bloom.includes(level)}
            className={cn(
              'px-2 py-1 text-[10px] font-bold uppercase tracking-wider border transition-colors',
              bloom.includes(level)
                ? 'bg-primary text-on-primary border-primary'
                : 'border-outline-variant/30 text-on-surface/50 hover:border-primary/40'
            )}
          >
            {level}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Blueprint drawer ──────────────────────────────────────────────────────────

function BlueprintDrawer({
  subjectId,
  presets,
  view,
  loading,
  error,
  onSavePreset,
  onSaveSections,
  saving,
}: {
  subjectId: string;
  presets: BlueprintPreset[];
  view: BlueprintView | null;
  loading: boolean;
  error: string;
  saving: boolean;
  onSavePreset: (presetId: string) => void;
  onSaveSections: (duration: number, sections: BlueprintSectionSpec[]) => void;
}) {
  const [sections, setSections] = useState<BlueprintSectionSpec[] | null>(null);
  const [duration, setDuration] = useState<number>(60);
  const [localError, setLocalError] = useState('');

  // Re-sync local edits whenever the server view changes (load or after save).
  useEffect(() => {
    const bp = view?.blueprint;
    if (!bp || !Array.isArray(bp.sections) || bp.sections.length === 0) return;
    setSections(bp.sections.map((s) => ({ ...s, bloom: s.bloom ?? [] })));
    setDuration(bp.duration_minutes ?? 60);
    setLocalError('');
  }, [view]);

  const effective = sections ?? view?.blueprint?.sections ?? [];
  const totalQ = effective.reduce((sum, s) => sum + (Number(s.count) || 0), 0);
  const totalM = effective.reduce(
    (sum, s) => sum + (Number(s.count) || 0) * (Number(s.marks) || 0),
    0
  );

  const updateSection = (i: number, next: BlueprintSectionSpec) => {
    setSections((prev) => {
      const base = prev ?? (view?.blueprint?.sections ?? []).map((s) => ({ ...s }));
      return base.map((s, idx) => (idx === i ? next : s));
    });
  };

  const removeSection = (i: number) => {
    setSections((prev) => {
      const base = prev ?? (view?.blueprint?.sections ?? []).map((s) => ({ ...s }));
      return base.filter((_, idx) => idx !== i);
    });
  };

  const addSection = () => {
    setSections((prev) => {
      const base = prev ?? (view?.blueprint?.sections ?? []).map((s) => ({ ...s }));
      if (base.length >= MAX_SECTIONS) return base;
      return [
        ...base,
        {
          name: `Section ${String.fromCharCode(65 + base.length)}`,
          count: 2,
          marks: 5,
          attempt: null,
          difficulty: 'mixed' as Difficulty,
          qtype: 'any' as const,
          bloom: [],
        },
      ];
    });
  };

  const handleSave = () => {
    setLocalError('');
    if (!sections || sections.length === 0) {
      setLocalError('Add at least one section.');
      return;
    }
    if (totalQ > 30) {
      setLocalError(`Total questions ${totalQ} exceeds the cap of 30.`);
      return;
    }
    if (totalQ < 1) {
      setLocalError('Blueprint needs at least 1 question.');
      return;
    }
    onSaveSections(duration, sections);
  };

  const presetId = view?.preset ?? '';
  const source = view?.source ?? 'generic';

  if (!subjectId) return null;

  return (
    <div className="border border-primary/20 bg-surface-container-low p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-widest text-primary">
            Exam blueprint
          </p>
          <p className="text-xs text-on-surface/60 mt-1">
            Sections, marks and duration the generated test follows.
          </p>
        </div>
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-primary/10 text-primary shrink-0">
          {source === 'subject' ? 'custom' : presetId || 'generic'}
        </span>
      </div>

      {loading && !view ? <Skeleton className="h-24" /> : null}

      {/* Preset picker */}
      {presets.length > 0 && (
        <div className="space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
            Start from a preset
          </span>
          <div className="grid grid-cols-1 gap-2">
            {presets.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => onSavePreset(p.id)}
                disabled={saving}
                className={cn(
                  'text-left border px-3 py-2 transition-colors disabled:opacity-50',
                  source !== 'subject' && presetId === p.id
                    ? 'border-primary bg-primary/5'
                    : 'border-outline-variant/30 hover:border-primary/40'
                )}
              >
                <span className="text-xs font-bold text-on-surface block">{p.label}</span>
                <span className="text-[11px] text-on-surface/50 block">{p.description}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Section editors */}
      {sections && sections.length > 0 ? (
        <div className="space-y-3">
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
            Sections
          </span>
          {sections.map((s, i) => (
            <BlueprintSectionEditor
              key={i}
              index={i}
              section={s}
              canRemove={sections.length > 1}
              onChange={(next) => updateSection(i, next)}
              onRemove={() => removeSection(i)}
            />
          ))}
          {sections.length < MAX_SECTIONS && (
            <button
              type="button"
              onClick={addSection}
              className="w-full border border-dashed border-outline-variant/40 text-on-surface/50 hover:border-primary/50 hover:text-primary py-2 text-[10px] font-bold uppercase tracking-widest transition-colors"
            >
              + Add section
            </button>
          )}
        </div>
      ) : (
        !loading && (
          <p className="text-xs text-on-surface/50">No sections loaded for this subject yet.</p>
        )
      )}

      {/* Duration */}
      <label className="flex items-center justify-between gap-3">
        <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/50">
          Duration (minutes)
        </span>
        <input
          type="number"
          min={1}
          max={600}
          value={duration}
          onChange={(e) => setDuration(Number(e.target.value))}
          className="w-24 bg-surface border border-outline-variant/30 focus:border-primary focus:ring-0 px-3 py-1.5 text-sm text-on-surface"
        />
      </label>

      {/* Totals */}
      <div className="flex items-center justify-between text-xs text-on-surface/60 border-t border-outline-variant/20 pt-3">
        <span>
          <strong className="text-on-surface">{totalQ}</strong> questions ·{' '}
          <strong className="text-on-surface">{totalM}</strong> marks
        </span>
        <span>
          <strong className="text-on-surface">{duration}</strong> min
        </span>
      </div>

      {(localError || error) && (
        <div className="px-3 py-2 text-xs border-l-2 border-error bg-error/5 text-error">
          {localError || error}
        </div>
      )}

      <button
        type="button"
        onClick={handleSave}
        disabled={saving || !sections}
        className="w-full border border-primary text-primary py-2.5 text-[10px] font-bold uppercase tracking-widest hover:bg-primary/10 transition-colors disabled:opacity-40"
      >
        {saving ? 'Saving…' : 'Save blueprint'}
      </button>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function DesktopMockTests() {
  const router = useRouter();
  const { subjects, isLoading: subjectsLoading } = useSubjects();
  const { tests, isLoading: testsLoading, generate } = useMockTests();

  // Form state
  const [subjectId, setSubjectId] = useState<string | ''>('');
  const [numQuestions, setNumQuestions] = useState(10);
  const [difficulty, setDifficulty] = useState<Difficulty>('mixed');
  const [source, setSource] = useState<TestSource>('predictions');
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState('');

  // Blueprint drawer state (Phase 1.6)
  const [useBlueprint, setUseBlueprint] = useState(true);
  const [presets, setPresets] = useState<BlueprintPreset[]>([]);
  const [bpView, setBpView] = useState<BlueprintView | null>(null);
  const [bpLoading, setBpLoading] = useState(false);
  const [bpSaving, setBpSaving] = useState(false);
  const [bpError, setBpError] = useState('');

  // Load preset list once.
  useEffect(() => {
    let dead = false;
    mockTestsService
      .getBlueprintPresets()
      .then((p) => {
        if (!dead) setPresets(p ?? []);
      })
      .catch(() => {
        // presets are optional; the drawer can still edit the resolved blueprint
      });
    return () => {
      dead = true;
    };
  }, []);

  // Load the subject's resolved blueprint whenever the subject changes.
  useEffect(() => {
    if (!subjectId) {
      setBpView(null);
      return;
    }
    let dead = false;
    setBpLoading(true);
    setBpError('');
    mockTestsService
      .getSubjectBlueprint(subjectId)
      .then((v) => {
        if (!dead) setBpView(v);
      })
      .catch((e: unknown) => {
        if (!dead) setBpError(e instanceof Error ? e.message : 'Failed to load blueprint.');
      })
      .finally(() => {
        if (!dead) setBpLoading(false);
      });
    return () => {
      dead = true;
    };
  }, [subjectId]);

  if (!API_URL) {
    return (
      <DesktopLayout>
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
          <h2 className="text-2xl font-bold text-on-surface mb-2">Configuration Error</h2>
          <p className="text-on-surface/60">
            <code className="bg-surface-container px-1 rounded">NEXT_PUBLIC_API_URL</code> is not
            set. Add it to your <code>.env.local</code> file and restart the dev server.
          </p>
        </div>
      </DesktopLayout>
    );
  }

  const handleGenerate = async () => {
    if (!subjectId) return;
    setGenerating(true);
    setGenerateError('');
    try {
      const payload: MockTestCreate = {
        subject_id: subjectId,
        num_questions: numQuestions,
        difficulty,
        source,
        useBlueprint,
      };
      const test = await generate(payload);
      if (!test.test_id || test.test_id === 'none') {
        setGenerateError(
          test.message || test.error || 'No questions available for this subject yet.'
        );
        return;
      }
      router.push(`/desktop/mock-tests/${test.test_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setGenerateError(msg);
    } finally {
      setGenerating(false);
    }
  };

  // ── Blueprint persistence ────────────────────────────────────────────────

  const handleSavePreset = async (presetId: string) => {
    if (!subjectId) return;
    setBpSaving(true);
    setBpError('');
    try {
      const view = await mockTestsService.putSubjectBlueprint(subjectId, { preset: presetId });
      setBpView(view);
    } catch (err: unknown) {
      setBpError(err instanceof Error ? err.message : 'Failed to apply preset.');
    } finally {
      setBpSaving(false);
    }
  };

  const handleSaveSections = async (
    duration: number,
    sections: BlueprintSectionSpec[]
  ) => {
    if (!subjectId) return;
    setBpSaving(true);
    setBpError('');
    try {
      const view = await mockTestsService.putSubjectBlueprint(subjectId, {
        duration_minutes: duration,
        sections,
      });
      setBpView(view);
    } catch (err: unknown) {
      setBpError(err instanceof Error ? err.message : 'Failed to save blueprint.');
    } finally {
      setBpSaving(false);
    }
  };

  const isInsufficientData =
    generateError.toLowerCase().includes('insufficient_data') ||
    generateError.toLowerCase().includes('no questions') ||
    generateError.toLowerCase().includes('not enough');

  return (
    <>
      <Head>
        <title>Mock Tests | PrepIQ</title>
        <meta name="description" content="Generate and take AI-powered mock tests" />
      </Head>
      <DesktopLayout>
        {/* Header */}
        <div className="mb-8 md:mb-12">
          <span className="text-xs font-bold tracking-[0.2em] uppercase text-primary mb-3 block">
            Assessment Engine
          </span>
          <h1 className="text-4xl md:text-6xl font-serif italic leading-none mb-4">Mock Tests</h1>
          <p className="text-on-surface/60 font-light max-w-xl">
            Generate personalised mock tests from your predictions or full question pool, then
            review your results inline.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* ── LEFT: Generate panel ── */}
          <section>
            <h2 className="text-xs font-bold uppercase tracking-widest text-primary mb-6 pb-3 border-b border-outline-variant/20">
              Generate New Test
            </h2>

            <div className="space-y-6">
              {/* Subject */}
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="mt-subject"
                  className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60"
                >
                  Subject
                </label>
                {subjectsLoading ? (
                  <Skeleton className="h-12" />
                ) : (
                  <div className="relative">
                    <select
                      id="mt-subject"
                      className="w-full bg-surface-container-low border-b-2 border-primary/20 focus:border-primary appearance-none py-3 px-4 text-on-surface text-sm font-medium focus:ring-0 cursor-pointer"
                      value={subjectId}
                      onChange={(e) => setSubjectId(e.target.value)}
                    >
                      <option value="">Select a subject…</option>
                      {subjects.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-primary">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <polyline points="6 9 12 15 18 9" />
                      </svg>
                    </span>
                  </div>
                )}
              </div>

              {/* Generation mode */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60">
                  Generation
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setUseBlueprint(true)}
                    className={cn(
                      'flex-1 py-2 text-xs font-bold uppercase tracking-wider border transition-colors',
                      useBlueprint
                        ? 'bg-primary text-on-primary border-primary'
                        : 'border-outline-variant/30 text-on-surface/60 hover:border-primary/40'
                    )}
                  >
                    Exam blueprint
                  </button>
                  <button
                    type="button"
                    onClick={() => setUseBlueprint(false)}
                    className={cn(
                      'flex-1 py-2 text-xs font-bold uppercase tracking-wider border transition-colors',
                      !useBlueprint
                        ? 'bg-primary text-on-primary border-primary'
                        : 'border-outline-variant/30 text-on-surface/60 hover:border-primary/40'
                    )}
                  >
                    Quick pick
                  </button>
                </div>
              </div>

              {!useBlueprint && (
                <>
              {/* Number of questions */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="mt-questions"
                    className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60"
                  >
                    Number of Questions
                  </label>
                  <span className="text-sm font-bold text-primary">{numQuestions}</span>
                </div>
                <input
                  id="mt-questions"
                  type="range"
                  min={5}
                  max={30}
                  step={5}
                  value={numQuestions}
                  onChange={(e) => setNumQuestions(Number(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-[10px] text-on-surface/40 font-bold">
                  <span>5</span>
                  <span>10</span>
                  <span>15</span>
                  <span>20</span>
                  <span>25</span>
                  <span>30</span>
                </div>
              </div>

              {/* Difficulty */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60">
                  Difficulty
                </span>
                <div className="grid grid-cols-4 gap-2">
                  {(['easy', 'medium', 'hard', 'mixed'] as Difficulty[]).map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setDifficulty(d)}
                      className={cn(
                        'py-2 text-xs font-bold uppercase tracking-wider border transition-colors',
                        difficulty === d
                          ? 'bg-primary text-on-primary border-primary'
                          : 'border-outline-variant/30 text-on-surface/60 hover:border-primary/40'
                      )}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              {/* Source toggle */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface/60">
                  Question Source
                </span>
                <div className="flex gap-2">
                  {(
                    [
              { value: 'predictions' as TestSource, label: 'From Predictions' },
              { value: 'all_questions' as TestSource, label: 'All Questions' },
                    ] as const
                  ).map(({ value, label }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setSource(value)}
                      className={cn(
                        'flex-1 py-2 text-xs font-bold uppercase tracking-wider border transition-colors',
                        source === value
                          ? 'bg-primary text-on-primary border-primary'
                          : 'border-outline-variant/30 text-on-surface/60 hover:border-primary/40'
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

                </>
              )}

              {/* Blueprint drawer (exam-blueprint mode) */}
              {useBlueprint && subjectId && (
                <BlueprintDrawer
                  subjectId={subjectId}
                  presets={presets}
                  view={bpView}
                  loading={bpLoading}
                  saving={bpSaving}
                  error={bpError}
                  onSavePreset={handleSavePreset}
                  onSaveSections={handleSaveSections}
                />
              )}

              {/* Insufficient data notice */}
              {isInsufficientData && (
                <div className="flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-300 text-amber-800 text-sm">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="shrink-0 mt-0.5"
                  >
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <p>
                    No questions available yet for this subject. Upload past papers first.
                  </p>
                </div>
              )}

              {/* Generic error */}
              {generateError && !isInsufficientData && (
                <div className="px-4 py-3 text-sm border-l-2 border-error bg-error/5 text-error">
                  {generateError}
                </div>
              )}

              {/* Generate button */}
              <button
                onClick={handleGenerate}
                disabled={!subjectId || generating}
                className="w-full bg-primary text-on-primary py-4 text-xs font-bold uppercase tracking-widest hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {generating ? (
                  <>
                    <svg
                      className="animate-spin"
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                    Generating…
                  </>
                ) : (
                  <>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                    </svg>
                    Generate Test
                  </>
                )}
              </button>
            </div>
          </section>

          {/* ── RIGHT: Test History ── */}
          <section>
            <h2 className="text-xs font-bold uppercase tracking-widest text-primary mb-6 pb-3 border-b border-outline-variant/20">
              Test History
            </h2>

            {testsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : tests.length === 0 ? (
              <div className="text-center py-16 text-on-surface/40">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="40"
                  height="40"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="mx-auto mb-3 text-on-surface/20"
                >
                  <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
                  <rect x="9" y="3" width="6" height="4" rx="1" />
                  <line x1="9" y1="12" x2="15" y2="12" />
                  <line x1="9" y1="16" x2="13" y2="16" />
                </svg>
                <p className="text-sm">No tests yet. Generate one to get started.</p>
              </div>
            ) : (
              <div className="divide-y divide-outline-variant/20 border-y border-outline-variant/20">
                {[...tests]
                  .sort(
                    (a, b) =>
                      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                  )
                  .map((test) => (
                    <button
                      key={test.test_id}
                      onClick={() =>
                        router.push(`/desktop/mock-tests/${test.test_id}`)
                      }
                      className="w-full text-left px-4 py-4 hover:bg-surface-container-low transition-colors flex items-center gap-4"
                    >
                      {/* Date */}
                      <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface/40 w-20 shrink-0">
                        {formatDate(test.created_at)}
                      </span>

                      {/* Subject + questions */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-on-surface truncate">
                          {test.subject_name || `Subject #${test.subject_id}`}
                        </p>
                        <p className="text-xs text-on-surface/50">
                          {test.total_questions} question
                          {test.total_questions !== 1 ? 's' : ''}
                        </p>
                      </div>

                      {/* Status + score */}
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        <StatusBadge status={test.status} />
                        {test.status === 'completed' && test.score_percentage != null && (
                          <span
                            className={cn(
                              'text-xs font-bold',
                              test.score_percentage >= 70
                                ? 'text-green-700'
                                : test.score_percentage >= 40
                                ? 'text-amber-600'
                                : 'text-red-600'
                            )}
                          >
                            {Math.round(test.score_percentage)}%
                          </span>
                        )}
                      </div>

                      {/* Chevron */}
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="text-on-surface/30 shrink-0"
                      >
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </button>
                  ))}
              </div>
            )}
          </section>
        </div>
      </DesktopLayout>
    </>
  );
}
