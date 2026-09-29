# PrepIQ v1 Implementation Plan — Phase 0 (Foundation) + Phase 1 (Test-Maker)

Status: **APPROVED** (architecture + phase sequence green-lit by academic/psychology expert review)
Companion docs: `comparision.md` (Astra AI competitive analysis), `chunk-plan.md` (past fix plan).

---

## Part A — Architecture Summary (locked decisions)

### Expert decisions (locked)

| # | Decision |
|---|---|
| D1 | Exam-day scoring = **family-key deterministic join**, LLM only for ~10–15% unmatched leftovers (batch, cached) |
| D2 | **Phase 1 = expert-seeded priors + isolated user data**; cross-user numeric pooling only Phase 2, opt-in |
| D3 | S/T/C (solvability/transfer/study-cost) = **LLM-estimated once per question family, cached**; adjusted later by user error logs |
| D4 | **Strict metric wall**: `Self-Verified` (metacognitive, drives learning guide) vs `Exam-Validated` (drives prediction accuracy). Tests never touch `prediction_accuracy_score` |
| D5 | v1 branches: **CSE + Electrical (university), NEET-UG (government)** |
| D6 | **Depth first** (accuracy proof + learning science + branch-faithful blueprints), breadth later |
| D7 | Free LLM tiers → every LLM path cache-first with deterministic fallback |

### The foundation: Question Families
A **question family** = the generative template behind question variants (e.g., "LRU cache hit/miss trace", "KVL loop derivation"). All engines key off it:

- exam-day prediction scoring (family-key join, D1)
- rubric/distractor reuse (one LLM call per family)
- S/T/C caching (Expected-Score priority = P×M×S×T/C)
- mastery tracking (family mastery levels 0–4)
- flashcards (post-v1)

Ingestion: PDF → OCR (`papers.py`) → unit tagging (`unit_tagging.py`) → **family assignment (new)**: seed-template match → content-hash match → LLM assign-or-create (cached forever). Runs in a background job.

### Free-tier LLM budget
- `llm_cache` table: `capability + prompt_hash → response` — zero repeat spend.
- Capability buckets via `llm_provider.py` env prefixes (`prediction_*`, `family_*`, `rubric_*`, `match_*`).
- Deterministic fallbacks stay: university stats-fallback, gov signal tiers, keyword rubric checks.
- Job queue (`jobs` table + daemon worker, pattern from `exam_context_job.py`).
- 500MB Render compliance: no on-disk models, no vector DB, PDFs deleted after successful OCR (keep `raw_text`).

### Engine 1 — Prediction (Phase 2, architecture approved)
- University: LLM ranks **families** by HM / recurrence / cyclical gap / prerequisite centrity / Bloom verb; Expected-Score priority → **tiers A ≥70% Must Master / B 40–69% Must Know / C <40% Strategic Coverage**; UI frames as "Expected ROI on study time" (no deterministic claims).
- NEET: keep causal features + `exam_context_cache`; add expert NTA/NCERT prior blend (posterior ∝ P(uploaded|topic) × P_prior) for cold start.
- Exam-day loop: `subjects.exam_date` banner → upload actual paper → family assignment → deterministic join → **Marks-Weighted Recall** + **Brier** stored in new `exam_outcomes` table → copied to `prediction_accuracy_score`; `novel_families` feed per-user stats (no cross-tenant pooling).

### Engine 2 — Test-Maker (Phase 1, this plan)
- Blueprint presets: `btech_default` (Sec A 10×2=20 short mandatory; Sec B 5×10 internal choice "attempt 3 of 5" = 50), `neet` (180 MCQ/720, +4/−1), `jee_main` (90/300), `generic_70_30` (70% core syllabus / 30% uniform; cognitive mix 20% recall / 50% application / 30% problem-solving). User-editable per subject.
- Blueprint-constrained sampler replaces `random.sample`: section filters (type/marks/topic/difficulty) → cognitive mix via `bloom_level` → choice groups → dedupe by family. Default source = full family bank (wall-off: tests train transfer, prediction evaluation stays pred-snapshot vs actual paper).
- Gradeability: family-level rubric + distractor generation (one cached LLM call per question): MCQ → correct + 3 misconception distractors; descriptive → model answer + rubric bullets + keyword anchors.
- **Hybrid grading (zero LLM cost at submit)**: MCQ exact-match auto; descriptive = deterministic keyword-coverage provisional score, then student **self-verify** (marks rubric bullets + error class: Knowledge/Retrieval/Conceptual/Execution) → final score labeled `Self-Verified`. Never influences prediction accuracy (D4).

### Engine 3 — Learning Guide (Phase 3, architecture approved)
- Revive `plans.py` (currently 503 stubs; schemas + frontend exist): expert allocations — >30d: 35 learning / 30 problem / 25 retrieval / 10 past-paper; final 7d: 15 triage / 35 high-yield retrieval / 30 targeted practice / 20 timed sims; T-48 protocol.
- Implementation intentions (if-then cues), 1 buffer day/week, non-punitive re-plan (never stack hours).
- `revision_queue`: D1→D3→D7→D21 spaced retests; `family_mastery` levels 0–4; Minimum Viable Topic survival cards; no streak penalties.

### Sequencing (validated by expert)
Test-Maker (1) before Learning Guide (3): practice testing is the feedback loop that feeds error logs. Prediction (2) before Guide (3): planner allocates by Expected-Score priority.

---

## Part B — Phase 0: Foundation (file-level)

### Key technical facts
1. `migration.py` only creates missing tables — never ALTERs columns. But pyronites SDK has `client.sql(query)` (`pyronites/client.py:41`, transport rewrites `/sql/execute`) and `table.schema()` returns column list → **probe-first column migration**, join-table fallback.
2. Upload pipeline (`papers.py:58-177`): save → `PDFParser.parse_questions_from_text` (extracts `marks` regex — 0=unknown, `question_type`, `difficulty`, `unit`) → `questions_repo.create_many` → `tag_after_upload` (gov-only hook — family hook mirrors it) → files on Render disk via `local_storage.py` (500MB risk).
3. Bank questions have **no `options` field** — MCQ options/rubrics need new home (`question_rubrics` table).

### Step 0.1 — Column-migration probe (decides schema approach)
Script against live PyroCore: `table("questions").schema()` → `ALTER TABLE questions ADD COLUMN family_id TEXT` → re-probe → same for:
- `subjects.blueprint_json JSON`
- `mock_tests.grading_mode TEXT`
- `mock_tests.self_grade_json JSON`

If SQL writable → columns. If read-only → fallback join tables: `question_family_map(question_id, family_id)` + `subject_blueprints(subject_id, config_json)` (only repo layer differs).

### Step 0.2 — Schema: `backend/app/core/migration.py`
New `_TABLES` entries:
- `question_families` (pk id): `id, scope TEXT` (`seed|user`), `user_id TEXT NULL, subject_id TEXT NULL, branch TEXT, canonical_text TEXT, normalized_hash TEXT, topic TEXT, bloom_level TEXT, command_verb TEXT, marks_typical INTEGER, difficulty TEXT, solvability REAL, transfer REAL, study_cost REAL, stc_cached_at TEXT, seed_source TEXT, created_at TEXT`
- `llm_cache` (pk id): `id, capability TEXT, prompt_hash TEXT, response_json JSON, created_at TEXT`
- `jobs` (pk id): `id, kind TEXT, payload_json JSON, status TEXT` (`queued|running|done|failed`), `attempts INTEGER, last_error TEXT, created_at, updated_at`
- `question_rubrics` (pk id): `id, question_id TEXT, family_id TEXT, mode TEXT` (`mcq|descriptive`), `model_answer TEXT, rubric_json JSON, keywords_json JSON, options_json JSON, needs_review BOOLEAN, generated_at, created_at`

New `_COLUMNS` spec + `_ensure_columns()` inside `run_startup_migration()`: probe `table.schema()`, `ALTER` missing via `client.sql`, verify, **fail-hard with dashboard hint** (mirrors existing philosophy).

### Step 0.3 — LLM cache layer
- `backend/app/repositories/llm_cache.py`: `get(capability, prompt_hash)`, `put(...)`.
- `backend/app/services/llm_cache.py`: `cached_json(capability, namespace, prompt, fn)` — every Phase 0/1 LLM call goes through it.

### Step 0.4 — Family assignment
- `backend/app/services/family_assignment.py`: normalize → `normalized_hash` exact lookup → seed-template match → LLM assign-or-create (capability `family`, via cache) → write `questions.family_id`.
- `backend/app/repositories/question_families.py`: CRUD + `list_for_branch`.
- `backend/app/data/seed_question_families.json`: CSE starter set (LLM-drafted, expert reviews later — non-blocking).

### Step 0.5 — Job queue
- `backend/app/services/job_queue.py`: `enqueue(kind, payload)` + daemon worker (pattern from `exam_context_job.py`), handlers: `family_assign`, `rubric_backfill` (Phase 1), later `exam_score`.
- `backend/app/main.py` lifespan: start/stop worker.

### Step 0.6 — Storage budget
- `papers.py` after `processing_status="completed"`: `delete_upload(rel_path)` only if `raw_text` ≥ 200 chars (mangled-OCR caveat: keep file + flag otherwise).
- Nightly prune job: files of papers completed > 7 days.

### Step 0.7 — Wire ingestion
- `papers.py:144` after `tag_after_upload`: `job_queue.enqueue("family_assign", {paper_id})`.

---

## Part C — Phase 1: Test-Maker (file-level)

### Step 1.1 — Blueprints
- `backend/app/blueprints.py`: presets + validators; `resolve(subject)` = subject override → track preset → generic.
- `subjects.py`: `PUT/GET /subjects/{id}/blueprint`.

### Step 1.2 — Test generator
- `backend/app/services/test_generator.py` (extracted from `tests.py:96-202`): blueprint-constrained sampler; unknown-marks questions stamped with section-default marks (never mutate bank); choice groups as `{"group","attempt","of"}` in `questions_json`; dedupe by family; default source = full bank; `test_id:"none"` contract preserved with section-specific message.

### Step 1.3 — Rubric backfill job
- Job handler `rubric_backfill`: MCQ → `{options[4], correct_index, distractor_rationale[3]}` (misapplied formula / sign flip / misconception); descriptive → `{model_answer, rubric_bullets, keyword_anchors}`; via `llm_cache` (capability `rubric`, keyed by normalized text — one call ever per question); `needs_review=true` for Phase 4 audit.
- Enqueued after upload + lazy at `generate` (sync batch ≤5, else async).
- `backend/app/repositories/question_rubrics.py`.

### Step 1.4 — Hybrid grading
- `tests.py` submit rework: MCQ exact-match auto; descriptive provisional keyword-coverage, `pending_self_grade` when answered; response += `grading_mode`, `pending_self_grade`.
- New `GET /tests/{id}/review` (completed): model answers + rubrics.
- New `POST /tests/{id}/self-grade`: `{items:[{question_id, points_hit, error_class}]}` → final percentage; write `mock_tests.grading_mode='self_verified'` + `self_grade_json`; weak/strong topics recomputed; enqueue `revision_seed` stub (Phase 3).

### Step 1.5 — Schemas (`backend/app/schemas.py`)
- `MockTestRequest` += `use_blueprint: bool = True`, `blueprint: Optional[Dict]`.
- New: `BlueprintConfig`, `SelfGradeRequest`/`SelfGradeItem`, `TestReviewResponse`, `BlueprintPreset`.
- `TestSubmissionResponse` += `grading_mode`, `pending_self_grade`. Null percentages stay honest until self-grade.

### Step 1.6 — Frontend
- `pages/desktop/mock-tests.tsx`: blueprint drawer (preset picker, editable sections, cognitive mix).
- `pages/desktop/mock-tests/[testId].tsx`: submit → results with self-verify prompt.
- `pages/desktop/test-results.tsx`: **null-percentage crash fix (line 88 `.toFixed`)** → "Awaiting self-check"; self-verify UI (rubric checkboxes + error-class selector → POST self-grade → score + "Self-Verified" badge); dual-metric labels; growth-mindset microcopy.
- `lib/services/mock-tests.service.ts`: `getReview`, `selfGrade`, `getBlueprintPresets`, `putSubjectBlueprint`.
- Mobile mirrors if present.

---

## Part D — Verification

### Phase 0
- pytest: hash-reuse family assign without LLM; `llm_cache` hit/miss; migration `_ensure_columns` idempotent (mocked client); job enqueue/worker round-trip.
- Live probe script: columns exist; upload → family_id populated; PDF deleted after OCR; jobs `queued→done`.
- `npm run check` (no frontend changes).

### Phase 1
- pytest: blueprint sampler (counts/marks/choice/dedupe/unknown-marks fallback); hybrid grading math (auto/provisional/finalization); review auth/ownership; presets validation; rubric idempotency (second run = 0 LLM calls).
- Live e2e: upload → jobs done → rubrics exist → generate w/ blueprint → submit → review → self-grade → percentage non-null + `grading_mode=self_verified` → analysis no-crash.
- `npm run check` + `pytest tests -q` + existing `verify_e2e.py` (22 checks stay green — contracts preserved).

## Part E — Risks

| Risk | Mitigation |
|---|---|
| PyroCore SQL read-only → no ALTERs | Probe is Step 0.1; join-table fallback pre-designed |
| Key lacks SQL scope on Render | Fail-hard + dashboard SQL-console hint (existing migration pattern) |
| Expert seeds not delivered | LLM-drafted CSE seed set ships; expert swaps JSON later (content, not code) |
| Free LLM limits during backfill | Queue throttles; `llm_cache` = one-time; keyword fallback if LLM down |
| `verify_e2e.py` contract drift | Additive response fields only |

## Part F — Execution order
`0.1 probe → 0.2 schema → 0.3 cache → 0.4 families → 0.5 jobs → 0.6/0.7 papers → [Phase 0 verify] → 1.1 blueprints → 1.2 generator → 1.3 rubrics → 1.4 grading → 1.5 schemas → 1.6 frontend → [Phase 1 verify]`

Then: Phase 2 (prediction + exam-day loop), Phase 3 (learning guide + ROADMAP.md), Phase 4 (polish + expert audit views).
