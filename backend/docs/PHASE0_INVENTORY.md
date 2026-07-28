# Phase 0 Inventory & Target Contracts

**Scope:** `backend/` only (branch `main`).  
**Rule:** Inventory and contracts only — no code, config, or other doc changes in this phase.  
**Method:** File-backed from repository tree and source; where runtime behavior cannot be inferred from code, marked **UNKNOWN — needs runtime check**.

---

## 1. LLM / ML / “agent” call sites

### 1.1 External LLM / gateway call sites (grouped by capability)

#### Prediction

| File | Function/class | Capability | Hard-coded provider/model | Env vars used today | Always-on / lazy / optional | Notes |
|------|----------------|------------|---------------------------|---------------------|-----------------------------|-------|
| `backend/app/prediction_engine.py` | `PredictionEngine.__init__` | Configure Gemini | `gemini-1.5-flash` via `google.generativeai` | `GEMINI_API_KEY` | Lazy (init on service construct) | If key missing → `self.model = None` |
| `backend/app/prediction_engine.py` | `PredictionEngine._generate_gemini_response` | Prediction JSON generation | Hard-coded JSON schema + Gemini | `GEMINI_API_KEY` (via `self.model`) | On-demand | Retry via tenacity |
| `backend/app/prediction_engine.py` | `PredictionEngine.predict_exam_topics` | Prediction (primary path) | Tries external API first, then Gemini | `GEMINI_API_KEY`; external via `_get_external_api()` | On-demand | Imports **missing** `ml.external_api_wrapper` — falls through on import failure |
| `backend/app/prediction_engine.py` | `PredictionEngine.generate_personalized_revision_guide` | Revision guide | Gemini `generate_content` | `GEMINI_API_KEY` | On-demand | Hard-coded fallback JSON if parse fails |
| `backend/app/prediction_engine.py` | `PredictionEngine.generate_study_plan` | Study plan | Gemini (then **hard-coded mock** return) | `GEMINI_API_KEY` | On-demand | Return value is mock regardless of API success |
| `backend/app/services.py` | `PrepIQService._cold_start_prediction` | Cold-start prediction (1–2 papers) | Gemini `gemini-1.5-flash` (via engine model) | `GEMINI_API_KEY` | On-demand | If Gemini fails → 3 placeholder “upload more papers” items |
| `backend/app/services.py` | `PrepIQService.generate_predictions` | Orchestrates tiers 0 / 1–2 / ≥3 | Gemini + optional ML analyzers | `GEMINI_API_KEY` | On-demand | Tier 0 = no LLM call |

#### Extraction (paper → questions / concepts)

| File | Function/class | Capability | Hard-coded provider/model | Env vars used today | Always-on / lazy / optional | Notes |
|------|----------------|------------|---------------------------|---------------------|-----------------------------|-------|
| `backend/app/routers/upload.py` | `_extract_questions_with_gemini` (and related helpers) | Question extraction | Google Gemini (`gemini-1.5-flash` per prior inventory + `google.generativeai` import) | `GEMINI_API_KEY` | Optional | Code path: if no key → regex/parser via PDF parser; comments reference model coordinator (lazy) |
| `backend/app/services.py` | `PrepIQService.process_uploaded_paper` | Extract text + parse questions | Local `PDFParser` (no LLM in this path) | None for LLM | On-demand | Downloads from Supabase Storage then regex/parser |
| `backend/app/pdf_parser.py` | `PDFParser` | Text extract / question parse | Local (PyMuPDF / pypdf / etc.) | None | Instantiated in service | Primary non-LLM extraction |

#### Tutor / chat / agent

| File | Function/class | Capability | Hard-coded provider/model | Env vars used today | Always-on / lazy / optional | Notes |
|------|----------------|------------|---------------------------|---------------------|-----------------------------|-------|
| `backend/app/chatbot.py` | `Chatbot.__init__` / `get_response` | Tutor/chatbot | `gemini-1.5-flash` | `GEMINI_API_KEY` | Optional | Unavailable message if no key |
| `backend/app/chatbot.py` | `Chatbot.explain_concept` | Concept explanation | Gemini (then **mock structured return**) | `GEMINI_API_KEY` | Optional | Mock return body even when model exists |
| `backend/app/routers/chat.py` | Chat routes + summarizer helpers | Tutor / summarize | Gemini + Bytez (bart-large-cnn) | `GEMINI_API_KEY`, Bytez via external API | Optional | References `get_external_api()` / `bytez_sdk` |
| `backend/app/services.py` | `PrepIQService.chat_with_bot` | Tutor entry | Delegates to `Chatbot` | via chatbot | Optional | |

#### Bytez / external model gateway

| File | Function/class | Capability | Hard-coded provider/model | Env vars used today | Always-on / lazy / optional | Notes |
|------|----------------|------------|---------------------------|---------------------|-----------------------------|-------|
| `backend/app/prediction_engine.py` | `_get_external_api` | Gateway singleton | Import `ml.external_api_wrapper.get_external_api` | `BYTEZ_API_KEY` (expected by missing module) | Lazy | **File does not exist in repo** — import fails → `external_api = None` |
| `backend/app/routers/chat.py` | Summarizer path | Summarization via Bytez | `facebook/bart-large-cnn` (docstring) | Bytez SDK | Optional | Depends on missing wrapper |
| `backend/requirements.txt` | — | Dependency | `bytez` package listed | `BYTEZ_API_KEY` in `.env.example` | Optional | No in-tree implementation of wrapper |
| `backend/BYTEZ_SETUP.md` | Docs only | Setup notes | Documents multiple Bytez models | — | Docs | Marketing/docs noise vs actual code |

**Duplicate / dead paths (prediction):**
- Dual orchestration: `PrepIQService.generate_predictions` **and** `PredictionEngine.predict_exam_topics` both call Gemini / ML; engine also tries missing Bytez wrapper first.
- `EnhancedQuestionAnalyzer` imported in `services.py` and `prediction_engine.py` but **file `backend/app/ml_models/enhanced_question_analyzer.py` is absent** → always fails init → ML branch empty.
- `ConceptExplainer` imported from `ml_engines.concept_explainer` — **file absent**.
- `model_coordinator` referenced in `upload.py` comments — **no such file under `backend/app/services/`**.

### 1.2 Local ML (sklearn / transformers / LSTM-style / etc.)

| File | Function/class | Capability | Hard-coded provider/model | Env vars used today | Always-on / lazy / optional | Notes |
|------|----------------|------------|---------------------------|---------------------|-----------------------------|-------|
| `backend/app/ml_models/question_analyzer.py` | `QuestionAnalyzer` | Pattern / trend analysis | sklearn-style local | None | Lazy in service / engine | Present in tree |
| `backend/app/ml/syllabus_analyzer.py` | `SyllabusAnalyzer` | Curriculum alignment / similarity | `sentence-transformers` (lazy import) + sklearn | None | Lazy | `_lazy_import_sentence_transformers` |
| `backend/app/ml/correlation_analyzer.py` | `CorrelationAnalyzer` | Correlation / high-impact topics | Local analysis | None | Lazy | Used in prediction path |
| `backend/app/ml/engines/question_importance.py` | Question importance | Importance / similarity | transformers / sentence-transformers / TF-IDF fallback | None | Lazy | Heavy optional |
| `backend/app/ml/engines/progress_forecaster.py` | `ProgressForecaster` | Forecasting | LSTM / RandomForest (per code structure) | None | Module present | Not wired into core prediction/test routes from inventory of routers |
| `backend/app/ml/engines/topic_recommender.py` | `TopicRecommender` | Recommendation | sklearn TF-IDF/SVD/KNN | None | Module present | Core flow usage: **UNKNOWN — needs runtime check** |
| `backend/app/ml/engines/focus_area_identifier.py` | `FocusAreaIdentifier` | Classification | sklearn RF/SVC | None | Module present | Core flow usage: **UNKNOWN — needs runtime check** |
| `backend/app/ml_engines/study_planner.py` | `StudyPlanner` | Study plan optimization | Local + optional AI | None | Optional in service | Used by `generate_study_plan` |
| `backend/app/ml/training/*` | Training pipeline | Offline train | sklearn / torch stack | `ML_*` paths in config | Not on request path | |
| `backend/app/ml_utils.py` | Utilities | Helpers | — | — | — | |
| `backend/app/ml/core/base_model.py` | Base model abstractions | Framework | — | — | — | |

**YOLOv8 / EasyOCR / BERTopic:** referenced in `.env.example` (`ENABLE_HEAVY_ML`) and requirements comments as optional/lazy; **no concrete call sites found under current tree file list** for YOLO/EasyOCR/BERTopic imports in active routers. Treat as deferred / dead-on-default.

**Requirements pins of note:** `google-generativeai==0.8.3`, `bytez`, `sentence-transformers==3.0.1`, `scikit-learn`, `torch` (CPU), `supabase`, `PyMuPDF`, `pypdf`.

---

## 2. Supabase & data-layer touchpoints

| File | What it does | Tables or storage involved | Auth assumption |
|------|--------------|----------------------------|-----------------|
| `backend/app/core/config.py` | Reads `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (as `SUPABASE_KEY`), `GEMINI_API_KEY` | Config only | — |
| `backend/app/database.py` | Lazy SQLAlchemy engine/session from `DATABASE_URL` (strips pgbouncer query) | All app tables via SQLAlchemy | No auth; connection string must be Supabase Postgres (or compatible) |
| `backend/app/models.py` | ORM models | `users`, `subjects`, `question_papers`, `questions`, `predictions`, `chat_history`, `mock_tests`, `study_plans` | User has **no** `password_hash` — “Supabase manages authentication” |
| `backend/app/services/supabase_first_auth.py` | Signup, login, JWT verify, lazy local user row create | Supabase Auth + local `users` | Supabase JWT is source of truth; local DB synced on first authenticated request |
| `backend/app/routers/auth.py` | `/auth/signup`, `/login`, `/logout`, `/profile`, `/me`, `/verify-token`, `/refresh` | Supabase Auth + `users` | Bearer Supabase tokens |
| `backend/app/services/supabase_storage.py` | Upload/download/delete/list | Bucket **`question-papers`** | Service role key bypasses RLS |
| `backend/app/services.py` | `process_uploaded_paper` downloads via storage | `question_papers.s3_key` + storage | Service role |
| `backend/app/main.py` | Startup warnings for missing `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY` | — | — |
| `backend/scripts/init_db.py` | Schema init notes | Postgres | — |
| `backend/scripts/00x_*.sql` | Migrations | Columns on predictions/questions/etc. | — |
| `backend/.env.example` / `.env.production.example` | Env templates | DATABASE_URL (pooler), SUPABASE_*, BYTEZ_*, GEMINI_* | — |

**Auth assumption (today):** Email/password against Supabase Auth; JWT validated with service client `get_user`; optional comments about OAuth metadata year parsing — **no Google/GitHub OAuth implementation found under `backend/` code search** (only email/password signup/login).

### Logical tables/entities the app actually needs for core flows

| Entity | Role |
|--------|------|
| `users` | Account + wizard profile |
| `subjects` | Per-user subject scope |
| `question_papers` | Uploaded papers metadata + local/storage path + processing status |
| `questions` | Extracted items; optional `correct_answer` for grading |
| `predictions` | Stored prediction JSON + coverage metadata |
| `mock_tests` | Generated tests; `questions_json` embeds questions (no separate join table) |
| `chat_history` | Tutor history (defer heavy use) |
| `study_plans` | Plans (defer) |

---

## 3. Core feature reality check

### 3a. Prediction

**Entry points**
- Router: `backend/app/routers/predictions.py`
  - `GET /predictions/subject/{subject_id}` → `get_predictions_for_subject`
  - `POST /predictions/generate` → `generate_prediction`
  - `GET /predictions/{prediction_id}`, `GET /predictions/{subject_id}/latest`, `PUT /predictions/{prediction_id}`
- Service: `PrepIQService.generate_predictions` / `_cold_start_prediction` in `backend/app/services.py`
- Engine: `PredictionEngine.predict_exam_topics` in `backend/app/prediction_engine.py`

**Data required**
- `subject_id`, authenticated `user_id`
- Count of `question_papers` with `processing_status == "completed"`
- For ≥3 papers: joined `questions` rows (text, marks, unit, type, difficulty)
- Optional `subject.syllabus_json`

**Path by paper count (from `generate_predictions`)**

| Papers (completed) | Behavior |
|--------------------|----------|
| **0** | No Gemini call. Returns `id=None`, empty predictions, `fallback_used=True`, `fallback_reason="no_papers"`, instructional `message`, `source="no_data"`. Router POST maps to `prediction_id="none"`, `status="no_data"`. |
| **1–2** | `_cold_start_prediction`: Gemini prompt from subject name + syllabus snippet; tags `source="syllabus_fallback"`, `fallback_used=True`, warning *“Generated from subject knowledge, not your past papers”*. On Gemini failure: 3 low-confidence placeholder texts. Persists a `Prediction` row. |
| **≥3** | Load questions → try `EnhancedQuestionAnalyzer` (missing module → empty ML) → correlation/syllabus if available → `prediction_engine.predict_exam_topics` (Gemini + missing Bytez) → combine/rank top 10 → persist. `fallback_used` true if Gemini failed (`source` becomes `ml_fallback` or similar). |

**Real vs fallback vs placeholder**
- Tier 0 message: real structured empty response (good).
- Tier 1–2: LLM hallucination over subject name is explicit (warning field) — not paper-derived.
- Tier ≥3: Gemini is real when key works; ML path largely **broken** because `enhanced_question_analyzer` is missing; Bytez path **broken** (missing wrapper).
- `prediction_accuracy_score` is **estimated** from confidence/consistency, not post-exam truth.

**Response shape today (GET subject)**
- `schemas.SubjectPredictionResponse`: `id`, `subject_id`, `predictions[]` (`PredictedQuestionFull`: question_number, text, topic, unit, marks, probability, confidence_score, reasoning, source), `total_marks`, `coverage_percentage`, `unit_coverage`, `generated_at`, `fallback_used`, `fallback_reason`, `warning`, `message`, `source`.

### 3b. Mock test generate + submit

**Entry points**
- `backend/app/routers/tests.py`: `POST /tests/generate`, `POST /tests/{test_id}/submit`, list/get/results/progress
- Legacy/alternate: `PrepIQService.generate_mock_test` in `services.py` (simpler; router path is the live API)

**Where questions come from**
- `source == "predictions"`: latest `Prediction.predicted_questions_json`, weighted sample by `confidence_score`; deficit backfilled from `questions` for subject
- Else (`all_questions`): random sample from `questions` joined to papers for subject
- Empty pool → HTTP 200 with `status="error"`, `error="insufficient_data"`, empty questions (not a hard 4xx)

**Scoring when `correct_answer` missing**
- Submit grades only questions that have non-empty `correct_answer`
- If `gradeable == 0` → `score_percentage = None` (explicit; no fake %)
- Persists `score`, `percentage`, counts, weak/strong topics

**Response shapes**
- Generate: `MockTestResponse`-compatible (`test_id`, `subject_id`, `status`, totals, `time_limit_minutes`, `created_at`, `score_percentage`, `questions[]`)
- Submit: `test_id`, `score_percentage` (nullable), `total_questions`, `answers_graded`

**Note:** Questions live in `MockTest.questions_json` (no separate questions table for mocks).

### 3c. Upload / paper processing

**Upload routes**
- `backend/app/routers/upload.py` — primary upload/analyze flows (Gemini extract optional)
- `backend/app/routers/papers.py` — paper upload helpers

**How text/questions are extracted**
1. File stored to Supabase Storage; metadata row in `question_papers` (`s3_key`, `file_name`, …)
2. Processing: download bytes → temp file → `PDFParser.extract_text` / metadata / images
3. Questions: `parse_questions_from_text` (regex/heuristic) and/or Gemini extract helpers in upload router when key present
4. Dedup via Jaccard token similarity in `PrepIQService._remove_duplicate_questions`

**Where files are stored today**
- Supabase Storage bucket `question-papers` (`SupabaseStorageService`)
- DB: `file_path` (often public URL), `s3_key`, sizes, status

**What ends up in DB**
- `QuestionPaper` row (status pending → processing → completed/failed, `raw_text`, `metadata_json`)
- Child `Question` rows (text, number, marks, unit, type, difficulty; `correct_answer` often null unless extraction sets it)

---

## 4. Target contracts (source of truth for refactor — do not implement in Phase 0)

### 4.1 Provider config (env-driven)

```env
# Prediction
PREDICTION_PROVIDER=...
PREDICTION_MODEL=...
PREDICTION_API_KEY=...
PREDICTION_BASE_URL=   # optional

# Extraction (paper → questions)
EXTRACTION_PROVIDER=...
EXTRACTION_MODEL=...
EXTRACTION_API_KEY=...
EXTRACTION_BASE_URL=

# Tutor/chat deferred to later phases
# TUTOR_PROVIDER=...
# TUTOR_MODEL=...
# TUTOR_API_KEY=...
```

**State after Phase 1:** no hard-coded model names (`gemini-1.5-flash`, etc.) in application code; a single provider layer is the only place that talks to external LLMs. Local sklearn analyzers may remain behind the same capability interface or be feature-flagged.

### 4.2 Auth (confirmed product decision)

- Remove Google + GitHub OAuth completely (none implemented in backend routers today; ensure frontend/docs do not assume them).
- Email + password only via **Pyronites auth**.
- Email validation + strong password rules on signup.
- **Replace later:** `backend/app/services/supabase_first_auth.py`, `backend/app/routers/auth.py`, JWT verification paths that call Supabase `get_user` / `refresh_session`.

### 4.3 Storage (confirmed product decision)

- Pyronites has **no** storage basket.
- Paper files = **local filesystem only**; DB stores metadata + **local path**.
- **Replace later:** `backend/app/services/supabase_storage.py` and all `s3_key` / public URL assumptions in `process_uploaded_paper` and upload routers.

### 4.4 Database

- Target: Pyronites client (`PYRONITES_URL`, `PYRONITES_KEY`) as data + auth layer.
- Keep logical entities: `users`, `subjects`, `question_papers`, `questions`, `predictions`, `mock_tests` (plus optional `chat_history` / `study_plans` if product keeps them).
- Remove SQLAlchemy↔Supabase Postgres coupling and dual-write auth pattern in Phase 2.

### 4.5 Prediction API contract (stable response intent)

Client must always receive explicit fields for:

| Scenario | Required signals |
|----------|------------------|
| Empty / 0 papers | `predictions: []`, `fallback_used: true`, `source: "no_data"` (or equivalent), human `message`, no inflated confidence |
| Cold-start (insufficient papers) | `fallback_used: true`, `warning` stating non-paper basis, moderate/low confidence, `source` e.g. `syllabus_fallback` |
| Full prediction | `source` (`provider` / `ml` / hybrid), `fallback_used` boolean, per-item `confidence`, `reasoning` |
| Errors | Structured failure without fake high accuracy |

**Ban:** fabricating high accuracy / high confidence when data is missing.

### 4.6 Mock test API contract

- **Generate:** declare source (`predictions` vs question bank); empty bank → explicit insufficient payload (no silent fake questions preferred; today’s placeholder-only path in legacy service should die).
- **Submit:** `score_percentage` only when gradeable answers exist; otherwise explicit `null` — no fabricated percentages.

---

## 5. Recommended kill / keep / adapt

### Kill
- Dead imports / missing modules: `ml/external_api_wrapper.py` (referenced but absent), `ml_models/enhanced_question_analyzer.py` (absent), `ml_engines/concept_explainer.py` (absent), any `model_coordinator` stubs
- Bytez multi-agent noise: `BYTEZ_SETUP.md` operational dependency, unused Bytez paths until product reintroduces a provider
- Unused heavy engines not on prediction/test critical path: progress_forecaster, topic_recommender, focus_area_identifier (confirm with runtime then remove)
- OAuth provider assumptions in docs/comments if any remain outside backend
- Mock returns that ignore model output (`generate_study_plan` mock schedule; `explain_concept` mock body)

### Keep
- Thin shells: FastAPI router structure (`predictions`, `tests`, `upload`, `papers`, `auth`)
- `pdf_parser.py` local extraction
- Tiered prediction policy (0 / 1–2 / ≥3) as product behavior
- Explicit null score on mock submit when ungradeable
- SQLAlchemy models as schema reference until Pyronites cutover

### Adapt
- All Gemini/Bytez calls → env-driven **provider layer** (Phase 1 priority)
- Auth + DB sessions → Pyronites (Phase 2)
- Storage → local FS + path columns (Phase 2)
- Prediction engine / `PrepIQService.generate_predictions` → provider + honest contracts (Phase 3)
- Test generator sourcing + empty-bank behavior (Phase 4)

**Product priority order**
1. Provider layer  
2. DB + auth + local file storage cutover  
3. Prediction engine  
4. Test generator  
5. Verification  
*(Chat/tutor and heavy ML deferred.)*

---

## Phase 1 ready checklist

1. **Introduce provider abstraction** under `backend/app/` (e.g. `providers/`) reading `PREDICTION_*` / `EXTRACTION_*` env vars only — no hard-coded `gemini-1.5-flash` in call sites.
2. **Route prediction + extraction call sites** through that layer: `prediction_engine.py`, `services.py` (`_cold_start_prediction`, `generate_predictions`), `routers/upload.py` Gemini helpers.
3. **Remove or stub-guard missing imports** so startup cannot claim ML/Bytez success for absent modules (`external_api_wrapper`, `enhanced_question_analyzer`, `concept_explainer`).
4. **Preserve response contracts** for 0 / cold-start / full prediction (`fallback_used`, `source`, `message`, `warning`, confidence honesty).
5. **Do not yet** migrate auth, storage, or SQLAlchemy; leave Supabase paths intact until Phase 2.
6. **Smoke:** `scripts/smoke_test.py` paths for PredictionEngine without key still pass; document required env for Phase 1 CI.
7. **Kill list items** that block clarity (dead Bytez init on import paths) without expanding tutor/chat scope.

---

*End of Phase 0 inventory. Single deliverable: this file only.*
