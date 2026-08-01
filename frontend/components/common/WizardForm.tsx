/**
 * WizardForm — 3-step onboarding wizard.
 *
 *   Step 1 → POST /wizard/step1
 *     { exam_type, exam_name, days_until_exam, university_name? }
 *   Step 2 → POST /wizard/step2  { focus_subjects, study_hours_per_day }
 *   Step 3 → POST /wizard/step3  { target_score, preparation_level }
 *   Final  → POST /wizard/complete { wizard_completed: true }
 */
import { useState } from 'react';
import { useRouter } from 'next/router';
import { apiFetch } from '@/lib/services/base.service';
import { getDashboardPath } from '@/lib/utils/device';

interface Step1Data {
  exam_type: 'government' | 'university' | '';
  exam_name: string;
  university_name: string;
  days_until_exam: number | '';
}

interface Step2Data {
  focus_subjects: string[];
  study_hours_per_day: number | '';
}

interface Step3Data {
  target_score: number | '';
  preparation_level: string;
}

const PREP_LEVELS = ['beginner', 'intermediate', 'advanced'] as const;
const HOURS_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8] as const;
const GOVT_EXAMS = ['NEET', 'JEE'] as const;

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-b py-5" style={{ borderColor: 'var(--color-outline-variant)' }}>
      <label
        className="block text-xs font-bold uppercase tracking-[0.15em] mb-3"
        style={{ color: 'var(--color-primary)' }}
      >
        {label}
      </label>
      {children}
    </div>
  );
}

function Chip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="px-4 py-2 text-xs font-bold uppercase tracking-wider transition-colors duration-150"
      style={{
        backgroundColor: active ? 'var(--color-primary)' : 'var(--color-surface-container)',
        color: active ? 'var(--color-on-primary)' : 'var(--color-on-surface)',
        opacity: active ? 1 : 0.65,
      }}
    >
      {label}
    </button>
  );
}

function NextButton({
  onClick,
  loading,
  disabled,
  label = 'Continue',
}: {
  onClick: () => void;
  loading: boolean;
  disabled: boolean;
  label?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className="flex items-center gap-3 px-10 py-4 text-sm font-bold uppercase tracking-[0.2em] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed group"
      style={{ backgroundColor: 'var(--color-primary)', color: 'var(--color-on-primary)' }}
    >
      {loading ? (
        <>
          <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
          Saving…
        </>
      ) : (
        <>
          {label}
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="group-hover:translate-x-1 transition-transform duration-150">
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </>
      )}
    </button>
  );
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-2 px-6 py-4 text-sm font-bold uppercase tracking-[0.2em] transition-colors duration-150"
      style={{
        backgroundColor: 'var(--color-surface-container)',
        color: 'var(--color-on-surface)',
        opacity: 0.7,
      }}
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="19" y1="12" x2="5" y2="12" />
        <polyline points="12 19 5 12 12 5" />
      </svg>
      Back
    </button>
  );
}

export default function WizardForm() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [step1, setStep1] = useState<Step1Data>({
    exam_type: '',
    exam_name: '',
    university_name: '',
    days_until_exam: '',
  });

  const [step2, setStep2] = useState<Step2Data>({ focus_subjects: [], study_hours_per_day: '' });
  const [subjectInput, setSubjectInput] = useState('');
  const [step3, setStep3] = useState<Step3Data>({ target_score: '', preparation_level: '' });

  const addSubject = () => {
    const trimmed = subjectInput.trim();
    if (trimmed && !step2.focus_subjects.includes(trimmed) && step2.focus_subjects.length < 10) {
      setStep2((p) => ({ ...p, focus_subjects: [...p.focus_subjects, trimmed] }));
    }
    setSubjectInput('');
  };

  const removeSubject = (s: string) =>
    setStep2((p) => ({ ...p, focus_subjects: p.focus_subjects.filter((x) => x !== s) }));

  const step1Valid =
    !!step1.exam_type &&
    !!step1.exam_name.trim() &&
    !!step1.days_until_exam &&
    (step1.exam_type === 'university' || GOVT_EXAMS.includes(step1.exam_name as (typeof GOVT_EXAMS)[number]));

  const submitStep = async (stepNum: number) => {
    setLoading(true);
    setError('');
    try {
      if (stepNum === 1) {
        if (!step1.exam_type) {
          setError('Select government or university track.');
          return;
        }
        if (!step1.exam_name.trim()) {
          setError('Exam name is required.');
          return;
        }
        if (step1.exam_type === 'government' && !GOVT_EXAMS.includes(step1.exam_name as (typeof GOVT_EXAMS)[number])) {
          setError('Government track currently supports NEET or JEE only.');
          return;
        }
        if (!step1.days_until_exam || step1.days_until_exam < 1 || step1.days_until_exam > 365) {
          setError('Days until exam must be between 1 and 365.');
          return;
        }
        await apiFetch('/wizard/step1', {}, {
          method: 'POST',
          body: JSON.stringify({
            exam_type: step1.exam_type,
            exam_name: step1.exam_name.trim(),
            days_until_exam: Number(step1.days_until_exam),
            university_name:
              step1.exam_type === 'university' ? step1.university_name.trim() || null : null,
          }),
        });
        setStep(2);
      } else if (stepNum === 2) {
        if (step2.focus_subjects.length === 0) {
          setError('Add at least one subject.');
          return;
        }
        if (!step2.study_hours_per_day || step2.study_hours_per_day < 1) {
          setError('Select how many hours per day you can study.');
          return;
        }
        await apiFetch('/wizard/step2', {}, {
          method: 'POST',
          body: JSON.stringify({
            focus_subjects: step2.focus_subjects,
            study_hours_per_day: Number(step2.study_hours_per_day),
          }),
        });
        setStep(3);
      } else {
        if (!step3.target_score || Number(step3.target_score) < 1 || Number(step3.target_score) > 100) {
          setError('Target score must be between 1 and 100.');
          return;
        }
        if (!step3.preparation_level) {
          setError('Select your preparation level.');
          return;
        }
        await apiFetch('/wizard/step3', {}, {
          method: 'POST',
          body: JSON.stringify({
            target_score: Number(step3.target_score),
            preparation_level: step3.preparation_level,
          }),
        });
        await apiFetch('/wizard/complete', {}, {
          method: 'POST',
          body: JSON.stringify({ wizard_completed: true }),
        });
        router.replace(getDashboardPath());
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: 'var(--color-background)', color: 'var(--color-on-surface)' }}
    >
      <header
        className="flex items-center justify-between px-6 sm:px-12 py-6 border-b"
        style={{ borderColor: 'var(--color-outline-variant)' }}
      >
        <span className="text-xs font-bold uppercase tracking-[0.25em]" style={{ color: 'var(--color-primary)' }}>
          PrepIQ
        </span>
        <div className="flex items-center gap-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="flex items-center gap-3">
              <div
                className="flex items-center justify-center w-7 h-7 text-xs font-bold transition-colors duration-200"
                style={{
                  backgroundColor: step >= n ? 'var(--color-primary)' : 'var(--color-surface-container)',
                  color: step >= n ? 'var(--color-on-primary)' : 'var(--color-on-surface)',
                  opacity: step >= n ? 1 : 0.4,
                }}
              >
                {n}
              </div>
              {n < 3 && (
                <div
                  className="w-8 h-px"
                  style={{
                    backgroundColor: step > n ? 'var(--color-primary)' : 'var(--color-outline-variant)',
                    opacity: step > n ? 1 : 0.4,
                  }}
                />
              )}
            </div>
          ))}
        </div>
      </header>

      <main className="flex-1 flex items-start justify-center px-6 sm:px-12 py-16">
        <div className="w-full max-w-lg">
          {error && (
            <div
              className="mb-8 px-4 py-3 text-sm font-medium border-l-2"
              style={{
                backgroundColor: 'var(--color-error-container)',
                borderColor: 'var(--color-error)',
                color: 'var(--color-on-error-container)',
              }}
            >
              {error}
            </div>
          )}

          {step === 1 && (
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] mb-3" style={{ color: 'var(--color-primary)' }}>
                Step 1 of 3
              </p>
              <h1
                className="text-4xl sm:text-5xl mb-12"
                style={{
                  fontFamily: 'var(--font-family-serif)',
                  fontStyle: 'italic',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.15,
                }}
              >
                What are you preparing for?
              </h1>

              <div className="border-t" style={{ borderColor: 'var(--color-outline-variant)' }}>
                <FieldRow label="Track">
                  <div className="flex flex-wrap gap-2 pt-1">
                    <Chip
                      label="Government (NEET / JEE)"
                      active={step1.exam_type === 'government'}
                      onClick={() =>
                        setStep1({
                          ...step1,
                          exam_type: 'government',
                          exam_name: '',
                          university_name: '',
                        })
                      }
                    />
                    <Chip
                      label="University"
                      active={step1.exam_type === 'university'}
                      onClick={() =>
                        setStep1({
                          ...step1,
                          exam_type: 'university',
                          exam_name: '',
                        })
                      }
                    />
                  </div>
                </FieldRow>

                {step1.exam_type === 'government' && (
                  <FieldRow label="Exam">
                    <div className="flex flex-wrap gap-2 pt-1">
                      {GOVT_EXAMS.map((ex) => (
                        <Chip
                          key={ex}
                          label={ex}
                          active={step1.exam_name === ex}
                          onClick={() => setStep1({ ...step1, exam_name: ex })}
                        />
                      ))}
                    </div>
                    <p className="text-xs opacity-40 mt-2">v1 supports NEET and JEE only.</p>
                  </FieldRow>
                )}

                {step1.exam_type === 'university' && (
                  <>
                    <FieldRow label="University Name">
                      <input
                        type="text"
                        value={step1.university_name}
                        onChange={(e) => setStep1({ ...step1, university_name: e.target.value })}
                        placeholder="e.g. VTU, Anna University"
                        className="w-full bg-transparent outline-none text-base font-medium placeholder:font-normal placeholder:opacity-40"
                        style={{ color: 'var(--color-on-surface)' }}
                      />
                    </FieldRow>
                    <FieldRow label="Exam Name">
                      <input
                        type="text"
                        value={step1.exam_name}
                        onChange={(e) => setStep1({ ...step1, exam_name: e.target.value })}
                        placeholder="e.g. Final Semester Exam, GATE 2026"
                        className="w-full bg-transparent outline-none text-base font-medium placeholder:font-normal placeholder:opacity-40"
                        style={{ color: 'var(--color-on-surface)' }}
                      />
                    </FieldRow>
                  </>
                )}

                <FieldRow label="Days Until Exam">
                  <input
                    type="number"
                    min={1}
                    max={365}
                    value={step1.days_until_exam}
                    onChange={(e) =>
                      setStep1({
                        ...step1,
                        days_until_exam: e.target.value === '' ? '' : Number(e.target.value),
                      })
                    }
                    placeholder="e.g. 60"
                    className="w-full bg-transparent outline-none text-base font-medium placeholder:font-normal placeholder:opacity-40"
                    style={{ color: 'var(--color-on-surface)' }}
                  />
                  <p className="text-xs opacity-40 mt-1">Between 1 and 365 days</p>
                </FieldRow>
              </div>

              <div className="mt-10">
                <NextButton onClick={() => submitStep(1)} loading={loading} disabled={!step1Valid} />
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] mb-3" style={{ color: 'var(--color-primary)' }}>
                Step 2 of 3
              </p>
              <h1
                className="text-4xl sm:text-5xl mb-12"
                style={{
                  fontFamily: 'var(--font-family-serif)',
                  fontStyle: 'italic',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.15,
                }}
              >
                What are you studying?
              </h1>

              <div className="border-t" style={{ borderColor: 'var(--color-outline-variant)' }}>
                <FieldRow label={`Focus Subjects (${step2.focus_subjects.length}/10)`}>
                  <div className="flex gap-2 items-center">
                    <input
                      type="text"
                      value={subjectInput}
                      onChange={(e) => setSubjectInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSubject())}
                      placeholder="Type a subject and press Enter"
                      className="flex-1 bg-transparent outline-none text-base font-medium placeholder:font-normal placeholder:opacity-40"
                      style={{ color: 'var(--color-on-surface)' }}
                    />
                    <button
                      type="button"
                      onClick={addSubject}
                      disabled={!subjectInput.trim() || step2.focus_subjects.length >= 10}
                      className="text-xs font-bold uppercase tracking-wider px-3 py-1.5 transition-colors disabled:opacity-40"
                      style={{
                        backgroundColor: 'var(--color-surface-container)',
                        color: 'var(--color-primary)',
                      }}
                    >
                      Add
                    </button>
                  </div>
                  {step2.focus_subjects.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {step2.focus_subjects.map((s) => (
                        <span
                          key={s}
                          className="flex items-center gap-2 px-3 py-1 text-xs font-bold uppercase tracking-wider"
                          style={{
                            backgroundColor: 'var(--color-primary)',
                            color: 'var(--color-on-primary)',
                          }}
                        >
                          {s}
                          <button type="button" onClick={() => removeSubject(s)} className="opacity-70 hover:opacity-100 leading-none">
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </FieldRow>

                <FieldRow label="Study Hours Per Day">
                  <div className="flex flex-wrap gap-2 pt-1">
                    {HOURS_OPTIONS.map((h) => (
                      <Chip
                        key={h}
                        label={`${h}h`}
                        active={step2.study_hours_per_day === h}
                        onClick={() => setStep2({ ...step2, study_hours_per_day: h })}
                      />
                    ))}
                  </div>
                </FieldRow>
              </div>

              <div className="mt-10 flex items-center gap-4">
                <BackButton onClick={() => setStep(1)} />
                <NextButton
                  onClick={() => submitStep(2)}
                  loading={loading}
                  disabled={step2.focus_subjects.length === 0 || !step2.study_hours_per_day}
                />
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] mb-3" style={{ color: 'var(--color-primary)' }}>
                Step 3 of 3
              </p>
              <h1
                className="text-4xl sm:text-5xl mb-12"
                style={{
                  fontFamily: 'var(--font-family-serif)',
                  fontStyle: 'italic',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.15,
                }}
              >
                Set your target and level.
              </h1>

              <div className="border-t" style={{ borderColor: 'var(--color-outline-variant)' }}>
                <FieldRow label="Target Score (%)">
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={step3.target_score}
                    onChange={(e) =>
                      setStep3({
                        ...step3,
                        target_score: e.target.value === '' ? '' : Number(e.target.value),
                      })
                    }
                    placeholder="e.g. 80"
                    className="w-full bg-transparent outline-none text-base font-medium placeholder:font-normal placeholder:opacity-40"
                    style={{ color: 'var(--color-on-surface)' }}
                  />
                  <p className="text-xs opacity-40 mt-1">Between 1 and 100</p>
                </FieldRow>

                <FieldRow label="Preparation Level">
                  <div className="flex flex-wrap gap-2 pt-1">
                    {PREP_LEVELS.map((level) => (
                      <Chip
                        key={level}
                        label={level.charAt(0).toUpperCase() + level.slice(1)}
                        active={step3.preparation_level === level}
                        onClick={() => setStep3({ ...step3, preparation_level: level })}
                      />
                    ))}
                  </div>
                </FieldRow>
              </div>

              <div className="mt-10 flex items-center gap-4">
                <BackButton onClick={() => setStep(2)} />
                <NextButton
                  label="Finish Setup"
                  onClick={() => submitStep(3)}
                  loading={loading}
                  disabled={!step3.target_score || !step3.preparation_level}
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
