# Fix Phase D — Cleanup + verification

## Done
- `dashboard.py` → Pyronites repos
- `wizard.py` → Pyronites users/subjects
- `questions.py` → Pyronites
- `analysis.py` / `plans.py` → **503** with clear message (deferred)
- `FINAL_VERIFICATION.md` checklist

## Intentionally not fully migrated
- `chat.py` — complex history + ORM; tutor still uses LLM provider
- `services.py` — large legacy module; not on critical path for predictions/tests/papers
- Heavy ML packages optional

## Residual risk
Calling `/chat/*` subject-bound routes may still require `DATABASE_URL` until chat is rewritten.
