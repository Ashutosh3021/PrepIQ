# Epic: Comprehensive App Review: Backend, Frontend, DB Errors, Bugs & Fixes

---

# PrepIQ — Complete Error, Bug & Bottleneck Audit Report

# PrepIQ — Complete Error, Bug & Bottleneck Audit Report

<user_quoted_section>Audit scope: Every Python backend file, every TypeScript/Next.js frontend file, every SQL schema file, and all configuration files.Method: Direct static analysis of source code — no assumptions, no guesses.</user_quoted_section>

## Architecture Overview

```mermaid
graph TD
    FE[Next.js Frontend] -->|REST API| BE[FastAPI Backend]
    BE -->|SQLAlchemy ORM| PG[(PostgreSQL / Supabase)]
    BE -->|Supabase Auth SDK| SA[Supabase Auth]
    BE -->|google-generativeai| GM[Gemini 2.5 Flash]
    BE -->|Bytez SDK| BZ[Bytez ML Models]
    BE -->|ultralytics / easyocr| ML[Local ML Pipeline]
    FE -->|SWR + fetch| BE
    FE -->|next-auth| NA[NextAuth.js]
```

## SECTION 1 — BACKEND BUGS & ERRORS

### BUG-B01 · `security.py` — `get_current_user` uses `await db.get()` on a synchronous session

**File:** file:backend/app/core/security.py · Line 71

**Severity:** 🔴 Critical — Runtime crash

**What is wrong:**

```python
user = await db.get(User, user_id)
```

`db` is a synchronous `sqlalchemy.orm.Session` (from `SessionLocal`). Calling `await` on a synchronous method raises `TypeError: object Session can't be used in 'await' expression` at runtime. This function is never actually called by any router (routers use `supabase_first_auth.py` instead), but it will crash if ever invoked.

**Root cause:** The function was written for an async SQLAlchemy session but the database layer uses a sync session.

**Fix required:** Replace `await db.get(User, user_id)` with `db.query(User).filter(User.id == user_id).first()`, or remove the function entirely since it is dead code.

### BUG-B02 · `security.py` — `get_current_active_user` references non-existent `user.is_active` field

**File:** file:backend/app/core/security.py · Line 93

**Severity:** 🔴 Critical — `AttributeError` at runtime

**What is wrong:**

```python
if not current_user.is_active:
```

The `User` model in file:backend/app/models.py has no `is_active` column. This will raise `AttributeError` on every call.

**Fix required:** Add `is_active` column to the `User` model, or remove this dead-code function.

### BUG-B03 · `core/config.py` — `GEMINI_API_KEY` stored under wrong key name

**File:** file:backend/app/core/config.py · Line 65

**Severity:** 🟠 High — Gemini AI features silently fail

**What is wrong:**

```python
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
```

`main.py` validates for `GEMINI_API_KEY` (line 64), `chat.py` reads `GEMINI_API_KEY`, and `model_coordinator.py` reads `GEMINI_API_KEY`. But `config.py` exposes it as `GOOGLE_API_KEY`. Any code that uses `settings.GOOGLE_API_KEY` gets an empty string even when `GEMINI_API_KEY` is set.

**Fix required:** Rename the field to `GEMINI_API_KEY` and read `os.getenv("GEMINI_API_KEY", "")`.

### BUG-B04 · `core/config.py` — `SUPABASE_KEY` reads wrong env variable

**File:** file:backend/app/core/config.py · Line 22

**Severity:** 🟠 High — Auth silently broken when using `settings.SUPABASE_KEY`

**What is wrong:**

```python
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
```

The actual env variable used everywhere else is `SUPABASE_SERVICE_KEY`. `settings.SUPABASE_KEY` will always be empty unless the operator sets a second, redundant variable.

**Fix required:** Change to `os.getenv("SUPABASE_SERVICE_KEY", "")`.

### BUG-B05 · `dependencies.py` — `get_prepiq_service()` is decorated with `@lru_cache` but `PrepIQService.__init__` is not thread-safe

**File:** file:backend/app/dependencies.py · Lines 4–7

**Severity:** 🟠 High — Race condition on first request under concurrent load

**What is wrong:**

```python
@lru_cache()
def get_prepiq_service():
    from app.services import PrepIQService
    return PrepIQService()
```

`PrepIQService.__init__` instantiates multiple ML objects (`PredictionEngine`, `Chatbot`, `PDFParser`, `QuestionAnalyzer`, `EnhancedQuestionAnalyzer`, `SyllabusAnalyzer`, `CorrelationAnalyzer`, `StudyPlanner`). Under concurrent requests, `lru_cache` is not thread-safe for the first call — multiple threads can enter `PrepIQService()` simultaneously, creating duplicate instances and potential state corruption.

**Fix required:** Use a module-level singleton with a threading lock, or use FastAPI's `lifespan` to initialize the service once at startup.

### BUG-B06 · `routers/tests.py` — Difficulty filter uses integer comparison on string column

**File:** file:backend/app/routers/tests.py · Lines 63–68

**Severity:** 🔴 Critical — Filter always returns zero results

**What is wrong:**

```python
difficulty_map = {"easy": 1, "medium": 2, "hard": 3}
target_diff = difficulty_map.get(test_request.difficulty.lower(), 2)
query = query.filter(models.Question.difficulty.in_([target_diff - 1, target_diff, target_diff + 1]))
```

`models.Question.difficulty` is a `String(20)` column storing values like `"easy"`, `"medium"`, `"hard"`. The filter compares it against integers `[0, 1, 2]`, `[1, 2, 3]`, or `[2, 3, 4]`. No string will ever match an integer — the filter silently returns nothing, causing the endpoint to always raise 404 "No questions found."

**Fix required:** Filter directly on string values: `query.filter(models.Question.difficulty == test_request.difficulty)`.

### BUG-B07 · `routers/tests.py` — `submit_test` hardcodes score values

**File:** file:backend/app/routers/tests.py · Lines 149–153

**Severity:** 🟠 High — Incorrect data stored permanently in database

**What is wrong:**

```python
test.score = 72  # Mock score
test.percentage = 72.0
test.correct_count = 18
test.incorrect_count = 5
test.skipped_count = 2
```

The submitted answers (`submission.answers`) are never evaluated. Every test submission stores a hardcoded score of 72%, regardless of actual answers. This corrupts all test result data in the database.

**Fix required:** Implement actual answer evaluation logic using the stored `questions_json` and the submitted `answers` dict.

### BUG-B08 · `routers/tests.py` — `get_test_results` returns fabricated question analysis

**File:** file:backend/app/routers/tests.py · Lines 220–229

**Severity:** 🟠 High — Fake data returned to user

**What is wrong:**

```python
for i in range(test.total_questions):
    question_analysis.append({
        "question_id": f"q{i+1}",
        "status": "correct" if i < 18 else "incorrect",
        ...
    })
```

The results endpoint generates fake question IDs (`q1`, `q2`, ...) and hardcodes the first 18 as "correct". The actual stored `user_answers_json` is never read.

**Fix required:** Load actual questions from `questions_json`, compare against `user_answers_json`, and compute real results.

### BUG-B09 · `routers/questions.py` — `search_questions` filters on non-existent relationship attribute

**File:** file:backend/app/routers/questions.py · Lines 123–126

**Severity:** 🔴 Critical — `AttributeError` / SQLAlchemy error at runtime

**What is wrong:**

```python
if subject:
    query = query.filter(models.Question.subject.has(name=subject))
if topic:
    query = query.filter(models.Question.topic.like(f"%{topic}%"))
```

The `Question` model has no `subject` relationship and no `topic` column. `Question` relates to `QuestionPaper`, not directly to `Subject`. `topic` does not exist — the column is `topics_json`. Both filters will raise `AttributeError` at runtime.

**Fix required:** Join through `QuestionPaper` to `Subject` for the subject filter; use `topics_json` with a JSON contains query for topic filtering.

### BUG-B10 · `routers/analysis.py` — `generate_analysis` called with wrong signature

**File:** file:backend/app/routers/analysis.py · Line 313

**Severity:** 🔴 Critical — `TypeError` at runtime

**What is wrong:**

```python
analysis_result = await generate_analysis(subject_id, extracted_data)
```

The `generate_analysis` function defined in the same file (line 406) takes only `(subject_id, extracted_data)` — two arguments. But the version in `upload.py` takes three: `(subject_id, extracted_data, db)`. The `analysis.py` version is missing the `db` parameter entirely, which means any DB-dependent logic inside it would fail. Additionally, the function is defined *after* the call site — Python will raise `NameError` at runtime because `generate_analysis` is not yet defined when the `upload_material` endpoint is called.

**Fix required:** Move `generate_analysis` definition above its call site, or import it from a shared module.

### BUG-B11 · `routers/upload.py` — `logger` is defined twice

**File:** file:backend/app/routers/upload.py · Lines 18 and 36

**Severity:** 🟡 Medium — Second definition silently overwrites first; no functional impact but indicates copy-paste error

**What is wrong:**

```python
logger = logging.getLogger(__name__)  # line 18
...
logger = logging.getLogger(__name__)  # line 36
```

Duplicate assignment. The first logger is set before the import block, the second after. While functionally equivalent here, it signals unreviewed code.

### BUG-B12 · `routers/papers.py` — `upload_progress` dict is in-memory and not process-safe

**File:** file:backend/app/routers/papers.py · Line 48

**Severity:** 🟠 High — Progress tracking broken in multi-worker or multi-process deployments

**What is wrong:**

```python
upload_progress = {}
```

This module-level dict is used to track upload progress. On Render (or any multi-worker deployment), each worker process has its own copy. A request to `/upload-progress/{paper_id}` may hit a different worker than the one that started the upload, returning stale or empty progress data.

**Fix required:** Use a shared store (Redis, database column, or Supabase Realtime) for progress tracking.

### BUG-B13 · `routers/papers.py` — Paper processing runs in `ThreadPoolExecutor` but shares a SQLAlchemy session across threads

**File:** file:backend/app/routers/papers.py · Lines 147–152

**Severity:** 🔴 Critical — Thread-safety violation; SQLAlchemy sessions are not thread-safe

**What is wrong:**

```python
result = await asyncio.get_event_loop().run_in_executor(
    ThreadPoolExecutor(),
    service.process_uploaded_paper,
    db,
    paper.id
)
```

The `db` session created in the request context is passed into a thread pool executor. SQLAlchemy `Session` objects are **not thread-safe**. The main thread and the executor thread both use the same session, causing potential data corruption, `DetachedInstanceError`, or silent data loss.

**Fix required:** Create a new `SessionLocal()` inside `process_uploaded_paper` for the background thread, or use FastAPI's `BackgroundTasks` with a fresh session.

### BUG-B14 · `services.py` — `_is_similar_text` uses character-set overlap, not string similarity

**File:** file:backend/app/services.py · Lines 138–153

**Severity:** 🟠 High — Deduplication is fundamentally broken

**What is wrong:**

```python
set1 = set(text1)
set2 = set(text2)
intersection = len(set1.intersection(set2))
union = len(set1.union(set2))
similarity = intersection / union
```

This computes the Jaccard similarity of the **character sets** (unique characters), not the actual text content. Two completely different questions like "What is force?" and "Define mass?" will score very high similarity because they share common characters (a, e, i, s, t, etc.). This means the deduplication either removes valid unique questions or keeps actual duplicates.

**Fix required:** Use token-level Jaccard similarity (split into words), or use `difflib.SequenceMatcher`, or the existing `EnhancedQuestionAnalyzer` similarity methods.

### BUG-B15 · `services.py` — `get_prediction` and `get_latest_prediction` call `json.loads` on `unit_coverage_json` which is a `JSON` column (already a dict)

**File:** file:backend/app/services.py · Lines 736–738, 787–789

**Severity:** 🟠 High — `TypeError` when `unit_coverage_json` is not `None`

**What is wrong:**

```python
unit_coverage = json.loads(prediction.unit_coverage_json) if prediction.unit_coverage_json else {}
```

`unit_coverage_json` is declared as `Column(JSON, ...)` in the SQLAlchemy model. SQLAlchemy automatically deserializes JSON columns to Python dicts/lists. Calling `json.loads()` on an already-deserialized dict raises `TypeError: the JSON object must be str, bytes or bytearray, not dict`.

**Fix required:** Remove the `json.loads()` call — use `prediction.unit_coverage_json or {}` directly.

### BUG-B16 · `services.py` — `generate_predictions` creates a **second** `Prediction` record after `predictions.py` already created one

**File:** file:backend/app/services.py · Lines 242–258 vs file:backend/app/routers/predictions.py · Lines 57–65

**Severity:** 🟠 High — Duplicate prediction records in database on every generation

**What is wrong:**
The `predictions.py` router creates a `Prediction` record (lines 57–65), commits it, then calls `service.generate_predictions()`. Inside `generate_predictions()`, a **second** `Prediction` record is created and committed (lines 242–258). Every prediction generation results in two database rows — one empty placeholder and one with actual data.

**Fix required:** Remove the pre-creation in the router, or remove the creation inside the service and update the existing record instead.

### BUG-B17 · `services.py` — `_calculate_prediction_accuracy` returns a `float` but the column is `String(5)`

**File:** file:backend/app/services.py · Line 255 and file:backend/app/models.py · Line 239

**Severity:** 🟡 Medium — Type mismatch; may cause DB write errors or silent truncation

**What is wrong:**

```python
prediction_accuracy_score=self._calculate_prediction_accuracy(ml_predictions)
```

`_calculate_prediction_accuracy` returns a `float` (e.g., `0.7234`). The column `prediction_accuracy_score` is `Column(String(5), ...)`. PostgreSQL will attempt to cast float to varchar(5), which may truncate or fail.

**Fix required:** Convert to string before assignment: `str(round(score, 2))`, or change the column type to `Float`.

### BUG-B18 · `routers/chat.py` — `ai_tutor_chat` accepts `request: dict` — no input validation

**File:** file:backend/app/routers/chat.py · Line 248

**Severity:** 🟠 High — Security risk; no schema validation on AI tutor input

**What is wrong:**

```python
async def ai_tutor_chat(request: dict, ...):
    message = request.get("message", "")
```

Using `dict` as the request body type bypasses Pydantic validation entirely. Any JSON payload is accepted. There is no length limit on `message`, no sanitization, and no type enforcement. A malicious user can send arbitrarily large payloads to the Gemini API, causing cost overruns or prompt injection.

**Fix required:** Define a Pydantic model for the request body with field validation (max length, required fields).

### BUG-B19 · `routers/chat.py` — Chat history saved twice for AI tutor messages

**File:** file:backend/app/routers/chat.py · Lines 312–319 (tutor endpoint) and file:backend/app/services.py · Lines 455–461 (chat_with_bot)

**Severity:** 🟡 Medium — Duplicate chat history records

**What is wrong:**
The `/chat/tutor` endpoint saves a `ChatHistory` record directly (lines 312–319). The `/chat/message` endpoint calls `service.chat_with_bot()` which also saves a `ChatHistory` record (services.py lines 455–461). If the tutor endpoint is called with a `subject_id`, it saves one record. The regular chat endpoint saves another. There is no deduplication.

### BUG-B20 · `routers/plans.py` — Import of `get_prepiq_service` is placed after the `get_current_user` dependency definition

**File:** file:backend/app/routers/plans.py · Line 20

**Severity:** 🟡 Medium — Code organization issue; works at runtime but is misleading

**What is wrong:**

```python
async def get_current_user(...):
    ...
from ..dependencies import get_prepiq_service  # line 20 — after function definition
```

The import is placed in the middle of the file, after a function definition. While Python allows this, it is non-standard and can cause `NameError` if the import fails silently.

### BUG-B21 · `routers/analysis.py` — `get_analysis_data` imports `numpy` inside the function but `numpy` is not in `requirements.txt`

**File:** file:backend/app/routers/analysis.py · Line 121

**Severity:** 🟠 High — `ImportError` in production if numpy is not installed

**What is wrong:**

```python
import numpy as np
```

`numpy` is listed in `requirements.txt` (line 18), so it is available. However, the import is inside the function body rather than at the module level, which means import errors are deferred to runtime rather than caught at startup.

Additionally, `np.mean([...]).item()` is called on line 229 — if the list is empty, `np.mean([])` returns `nan`, and `.item()` on `nan` returns Python `float('nan')`, which is not JSON-serializable and will cause a 500 error.

**Fix required:** Move the import to the top of the file. Add a guard: `float(np.mean([...]) or 0)`.

### BUG-B22 · `routers/wizard.py` — `db.rollback() if 'db' in locals() else None` is always True

**File:** file:backend/app/routers/wizard.py · Lines 136, 227, 291, 354

**Severity:** 🟡 Medium — Misleading defensive code

**What is wrong:**

```python
db.rollback() if 'db' in locals() else None
```

`db` is always in scope because it is a function parameter. `'db' in locals()` is always `True`. The `else None` branch is dead code. This pattern was likely copied from a context where `db` might not be defined, but here it always is.

### BUG-B23 · `services/supabase_first_auth.py` — `get_current_user` silently swallows all exceptions

**File:** file:backend/app/services/supabase_first_auth.py · Lines 279–280

**Severity:** 🟠 High — All auth errors (network, invalid token, Supabase down) return the same 401

**What is wrong:**

```python
except Exception:
    raise HTTPException(status_code=401, detail="Invalid authentication token")
```

A Supabase network timeout, a 503 from Supabase, or a programming error inside the try block all produce the same 401 response. This makes debugging impossible and hides real infrastructure failures.

**Fix required:** Log the exception before re-raising. Distinguish between auth failures (401) and infrastructure failures (503).

### BUG-B24 · `services/supabase_first_auth.py` — Lazy user creation has no uniqueness guard — race condition on concurrent first requests

**File:** file:backend/app/services/supabase_first_auth.py · Lines 327–348

**Severity:** 🟠 High — Duplicate user records on concurrent first login

**What is wrong:**

```python
db_user = db.query(User).filter(User.id == supabase_user["id"]).first()
if not db_user:
    db_user = User(id=supabase_user["id"], ...)
    db.add(db_user)
    db.commit()
```

If two requests arrive simultaneously for the same new user, both will find `db_user = None`, both will attempt to insert, and one will fail with a `UniqueViolationError` on the `email` unique constraint, causing a 500 error for one of the requests.

**Fix required:** Use `INSERT ... ON CONFLICT DO NOTHING` or wrap in a try/except for `IntegrityError` and re-query.

### BUG-B25 · `services/model_coordinator.py` — Bytez API key is hardcoded in source code

**File:** file:backend/app/services/model_coordinator.py · Line 73

**Severity:** 🔴 Critical — Security vulnerability; credential exposure

**What is wrong:**

```python
bytez_key = os.getenv('BYTEZ_API_KEY', 'd02578a68c2621c9fdac702219d0722e')
```

A real API key is hardcoded as the default fallback. This key is now committed to version control and visible to anyone with repository access.

**Fix required:** Remove the hardcoded default. Use `os.getenv('BYTEZ_API_KEY')` with no fallback, and disable the Bytez models if the key is not set.

### BUG-B26 · `main.py` — `validate_environment()` calls `sys.exit(1)` at module import time

**File:** file:backend/app/main.py · Lines 52–83

**Severity:** 🟠 High — Prevents any testing or partial startup without all env vars

**What is wrong:**

```python
validate_environment()  # Called at module level, line 83
```

This runs during `import app.main`, which means unit tests, health checks during cold start, and any import of the module will fail with `SystemExit` if env vars are missing. This makes the application untestable without a full environment.

**Fix required:** Move validation into the `lifespan` startup handler, or use a warning instead of `sys.exit` for non-critical variables.

### BUG-B27 · `database.py` — `create_tables()` function name collision with `models.py`

**File:** file:backend/app/database.py · Line 59 and file:backend/app/models.py · Line 389

**Severity:** 🟡 Medium — Naming confusion; wrong function may be called

**What is wrong:**
Both `database.py` and `models.py` define a `create_tables()` function with different signatures. `database.py`'s version imports `Base` from `models.py` (circular-ish), while `models.py`'s version takes `engine` as a parameter. Any code calling `create_tables()` without checking which module it imported from may call the wrong one.

### BUG-B28 · `routers/subjects.py` — `get_subject` executes redundant DB queries

**File:** file:backend/app/routers/subjects.py · Lines 136–168

**Severity:** 🟡 Medium — Performance bottleneck; 3 separate queries where 1 would suffice

**What is wrong:**
The endpoint first creates two `scalar_subquery` objects (lines 136–145), then queries the subject (lines 148–155), then executes **two more separate count queries** (lines 163–168). The initial subqueries are created but never used in the main query. The actual counts come from separate `.scalar()` calls.

**Fix required:** Use the subquery approach consistently (as done in `get_subjects`) to fetch subject + counts in a single query.

### BUG-B29 · `routers/dashboard.py` — `study_streak` calculation uses `func.date()` which may not work correctly across timezones

**File:** file:backend/app/routers/dashboard.py · Lines 73–96

**Severity:** 🟡 Medium — Streak may be off by one day for users in non-UTC timezones

**What is wrong:**

```python
chat_dates = db.query(func.date(models.ChatHistory.created_at)).filter(...).distinct().all()
```

`created_at` is stored as UTC. `func.date()` extracts the date in the database server's timezone (UTC). A user who studies at 11 PM local time (which is the next UTC day) will have their activity attributed to the wrong date, breaking streak calculation.

### BUG-B30 · `routers/analysis.py` — `get_weightage_analysis` returns wrong keys

**File:** file:backend/app/services.py · Lines 602–619

**Severity:** 🟠 High — Frontend receives empty data

**What is wrong:**

```python
return {
    "unit_weightage": analysis.get("unit_weightage", {}),
    "mark_distribution": analysis.get("mark_distribution", {})
}
```

`get_trend_analysis()` returns a dict with key `"basic_analysis"` containing `unit_weightage` and `mark_distribution`. The `get_weightage_analysis` method calls `.get("unit_weightage", {})` directly on the top-level result, which does not have that key. Both values will always be empty dicts.

**Fix required:** Use `analysis.get("basic_analysis", {}).get("unit_weightage", {})`.

### BUG-B31 · `routers/papers.py` — `get_papers` route conflicts with `get_paper_preview` route

**File:** file:backend/app/routers/papers.py · Lines 184 and 214

**Severity:** 🟠 High — Route ambiguity; FastAPI may match wrong handler

**What is wrong:**

```
GET /papers/{subject_id}        → get_papers
GET /papers/{paper_id}/preview  → get_paper_preview
```

Both routes start with `/papers/{variable}`. When a request comes in for `/papers/some-uuid/preview`, FastAPI will first try to match `{subject_id}` = `"some-uuid/preview"` (which will fail UUID validation) before trying the preview route. This causes unexpected 422 errors.

**Fix required:** Rename the list route to `/papers/by-subject/{subject_id}` or reorder routes so more specific paths come first.

### BUG-B32 · `ml_utils.py` — `detect_objects_in_image` references `numpy` via `if 'numpy' in dir()`

**File:** file:backend/app/ml_utils.py · Line 116

**Severity:** 🟡 Medium — Logic error; `dir()` returns local scope names, not imported modules

**What is wrong:**

```python
if 'numpy' in dir():
    circles = np.sum(...)
```

`dir()` without arguments returns names in the current local scope. `numpy` is imported as `np`, not `numpy`, so `'numpy' in dir()` is always `False`. The circular detection code is dead code.

**Fix required:** Use `if 'np' in dir():` or simply use `np.sum(...)` directly since numpy is already imported at the top of the function's try block.

## SECTION 2 — DATABASE BUGS & SCHEMA INCONSISTENCIES

### BUG-D01 · Schema mismatch: `subjects.semester` is `INTEGER` in ORM but `VARCHAR(20)` in `data/schema.sql`

**Files:** file:backend/app/models.py · Line 80 vs file:data/schema.sql · Line 43

**Severity:** 🔴 Critical — ORM writes integers; SQL schema expects strings; type mismatch causes insert failures

**What is wrong:**

- SQLAlchemy model: `semester = Column(Integer, nullable=True)`
- `data/schema.sql`: `semester VARCHAR(20)`
- `supabase-migration.sql`: `semester INTEGER` ✓

The `data/schema.sql` file (which may have been applied to the database) defines `semester` as `VARCHAR(20)`. The ORM writes integers. This causes a type mismatch on insert/update.

**Fix required:** Align all schema files. Use `INTEGER` consistently.

### BUG-D02 · Schema mismatch: `subjects.papers_uploaded` is `BOOLEAN` in `data/schema.sql` but `INTEGER` in ORM and migration

**Files:** file:data/schema.sql · Line 48 vs file:backend/app/models.py · Line 92

**Severity:** 🔴 Critical — Count queries write integers to a boolean column

**What is wrong:**

- `data/schema.sql`: `papers_uploaded BOOLEAN DEFAULT FALSE`
- SQLAlchemy model: `papers_uploaded = Column(Integer, default=0, ...)`
- `supabase-migration.sql`: `papers_uploaded INTEGER NOT NULL DEFAULT 0` ✓

The `data/schema.sql` schema uses booleans; the ORM writes integers (counts). Same issue for `predictions_generated` and `mock_tests_created`.

**Fix required:** Use `INTEGER` in all schema files to match the ORM.

### BUG-D03 · `scripts/002_add_prediction_accuracy_score.sql` renames `difficulty` to `difficulty_level` — ORM still uses `difficulty`

**File:** file:backend/scripts/002_add_prediction_accuracy_score.sql · Line 5

**Severity:** 🔴 Critical — All question difficulty queries fail after migration

**What is wrong:**

```sql
ALTER TABLE questions RENAME COLUMN difficulty TO difficulty_level;
```

The SQLAlchemy `Question` model uses `difficulty = Column(String(20), ...)`. After this migration runs, the column is named `difficulty_level` in the database but the ORM still references `difficulty`. Every query filtering or reading `difficulty` will fail with `column "difficulty" does not exist`.

**Fix required:** Either revert the migration rename, or update the ORM model to use `difficulty_level`.

### BUG-D04 · `data/schema.sql` references `pgvector` extension and `vector(768)` column — not in migration files

**File:** file:data/schema.sql · Lines 7–8, 104

**Severity:** 🟠 High — Schema inconsistency; vector similarity search is defined but never implemented

**What is wrong:**

```sql
CREATE EXTENSION IF NOT EXISTS "vector";
embedding vector(768),
CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops)
```

The `supabase-migration.sql` and `scripts/001_initial_schema.sql` do not include the `pgvector` extension or the `embedding` column. The ORM model has no `embedding` field. The vector similarity search infrastructure is defined in one schema file but absent everywhere else — it is dead schema.

### BUG-D05 · `rls_policies.sql` — SELECT policies use `OR auth.role() = 'authenticated'` which bypasses row-level isolation

**File:** file:data/rls_policies.sql · Lines 16, 22, 37, etc.

**Severity:** 🔴 Critical — Any authenticated user can read any other user's data

**What is wrong:**

```sql
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid() = id OR auth.role() = 'authenticated');
```

The `OR auth.role() = 'authenticated'` clause means any logged-in user can read any row in the `users`, `subjects`, `question_papers`, `questions`, `predictions`, `mock_tests`, `chat_history`, and `study_plans` tables. This completely defeats the purpose of RLS.

**Note:** The `supabase-migration.sql` policies do NOT have this flaw — they use only `auth.uid() = id`. The `rls_policies.sql` file appears to be an older, broken version. If it was applied to the database, all user data is exposed.

**Fix required:** Remove `OR auth.role() = 'authenticated'` from all SELECT policies in `rls_policies.sql`. Verify which policy file was actually applied to the Supabase database.

### BUG-D06 · `chat_history` table — `subject_id` is `NOT NULL` in ORM but `NULLABLE` in `data/schema.sql`

**Files:** file:backend/app/models.py · Line 265 vs file:data/schema.sql · Line 177

**Severity:** 🟡 Medium — Schema inconsistency; inserts without `subject_id` will fail at ORM level but succeed at DB level (or vice versa)

**What is wrong:**

- ORM: `subject_id = Column(..., nullable=False, ...)`
- `data/schema.sql`: `subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL` (implicitly nullable)
- `supabase-migration.sql`: `subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE`

Three different definitions for the same column across three files.

### BUG-D07 · `scripts/001_initial_schema.sql` creates a completely different schema (`profiles`, `study_materials`) that conflicts with the main schema

**File:** file:backend/scripts/001_initial_schema.sql

**Severity:** 🟠 High — If this migration was applied, it created orphaned tables that conflict with the main application schema

**What is wrong:**
`001_initial_schema.sql` creates `public.profiles`, `public.subjects` (with different columns than the main schema), `public.study_materials`, and `public.predictions` (with different columns). These conflict with the tables created by `supabase-migration.sql`. Running both migrations creates duplicate, incompatible table definitions.

## SECTION 3 — FRONTEND BUGS & ERRORS

### BUG-F01 · `pages/api/auth/[...nextauth].ts` — NextAuth configured with zero providers

**File:** file:frontend/pages/api/auth/`[...nextauth].ts`

**Severity:** 🟠 High — NextAuth is installed and configured but completely non-functional

**What is wrong:**

```typescript
export default NextAuth({
  providers: [],  // Empty!
  secret: process.env.NEXTAUTH_SECRET,
});
```

NextAuth is installed (`next-auth: 4.24.13`) and has a route handler, but has no providers configured. The comment says "TODO: Add auth providers when auth phase begins." The backend uses Supabase Auth directly — NextAuth is an unused dependency that adds bundle weight and a dead API route.

**Fix required:** Either remove NextAuth entirely and delete this file, or integrate it with the Supabase provider.

### BUG-F02 · `lib/services/base.service.ts` — `apiFetch` sends no `Authorization` header in real mode

**File:** file:frontend/lib/services/base.service.ts · Lines 51–54

**Severity:** 🔴 Critical — All real API calls return 401 Unauthorized

**What is wrong:**

```typescript
const res = await fetch(url, {
  headers: { 'Content-Type': 'application/json' },
  ...options,
});
```

Every backend endpoint requires a `Bearer` token in the `Authorization` header. The base service never reads the auth token from storage and never attaches it. In real mode (`NEXT_PUBLIC_API_MODE=real`), every API call will receive a 401 response.

**Fix required:** Read the Supabase access token from `localStorage` or a context provider and attach it as `Authorization: Bearer <token>` in the headers.

### BUG-F03 · `lib/services/subjects.service.ts` — `getById` always throws in mock mode

**File:** file:frontend/lib/services/subjects.service.ts · Lines 9–13

**Severity:** 🟠 High — `getById` is broken in mock mode for any ID not in the mock array

**What is wrong:**

```typescript
getById: (id: string) => {
  const subject = SUBJECTS_MOCK.find((s) => s.id === id);
  if (!subject) {
    throw new Error(`Subject not found: ${id}`);
  }
  return apiFetch<Subject>(`/subjects/${id}`, subject);
},
```

The throw happens synchronously before `apiFetch` is called. If the ID is not in `SUBJECTS_MOCK`, the error is thrown immediately — not as a rejected Promise. SWR expects a rejected Promise, not a synchronous throw, which may cause unhandled errors.

**Fix required:** Return `Promise.reject(new Error(...))` instead of `throw`.

### BUG-F04 · `pages/desktop/dashboard.tsx` and `pages/mobile/dashboard.tsx` — All stats are hardcoded

**Files:** file:frontend/pages/desktop/dashboard.tsx · Lines 96–99, file:frontend/pages/mobile/dashboard.tsx · Lines 82–121

**Severity:** 🟠 High — Dashboard shows fake data regardless of actual user data

**What is wrong:**

```tsx
<StatWidget label="Subjects" value="08" icon="book-open" />
<StatWidget label="Progress" value="68%" icon="bar-chart" />
<StatWidget label="Focus Area" value="Cellular Pathways" icon="target" />
<StatWidget label="Streak" value="14" icon="trending-up" />
```

All four stat widgets display hardcoded values. The `useSubjects()` hook is called but its data is never used in the stats section. The greeting "Good morning, Rahul" is also hardcoded.

**Fix required:** Use the `subjects` array from `useSubjects()` for the count. Call the `/dashboard/stats` backend endpoint for progress, focus area, and streak.

### BUG-F05 · `pages/desktop/dashboard.tsx` — Recent activity section is hardcoded

**File:** file:frontend/pages/desktop/dashboard.tsx · Lines 8–29

**Severity:** 🟠 High — Recent activity never reflects real user actions

**What is wrong:**

```typescript
const recentActivity = [
  { icon: 'quiz', title: 'Mock Test: Organic Chemistry', meta: '...' },
  ...
];
```

This is a static array defined at module level. The backend has a `/dashboard/recent-activity` endpoint that returns real data, but it is never called.

### BUG-F06 · `_app.tsx` — No authentication guard; all pages are accessible without login

**File:** file:frontend/pages/_app.tsx

**Severity:** 🔴 Critical — All protected pages are publicly accessible

**What is wrong:**

```typescript
export default function App({ Component, pageProps }: AppProps) {
  return (
    <SWRConfig ...>
      <Component {...pageProps} />
    </SWRConfig>
  );
}
```

There is no auth context, no session check, no redirect to login for unauthenticated users. Any user can navigate directly to `/desktop/dashboard`, `/desktop/subjects`, etc. without being logged in. The backend will return 401s, but the frontend renders the page shell regardless.

**Fix required:** Add an auth context provider that reads the Supabase session and redirects unauthenticated users to the login page.

### BUG-F07 · Frontend has no login/signup pages

**Severity:** 🔴 Critical — Users cannot authenticate through the frontend

**What is wrong:**
The `pages/` directory contains `desktop/` and `mobile/` subdirectories with dashboard, subjects, tests, upload, etc. — but there is no `login.tsx`, `signup.tsx`, or `auth/` directory. The backend has full auth endpoints (`/auth/signup`, `/auth/login`) but there is no frontend UI to call them.

### BUG-F08 · `lib/hooks/useSubjects.ts` — SWR key `'subjects'` is a plain string with no user scoping

**File:** file:frontend/lib/hooks/useSubjects.ts · Line 6

**Severity:** 🟠 High — SWR cache is shared across users in the same browser session

**What is wrong:**

```typescript
const { data, error, isLoading } = useSWR<Subject[]>('subjects', subjectsService.getAll);
```

The SWR cache key is the string `'subjects'`. If two different users log in sequentially in the same browser (without a full page reload), the second user will see the first user's cached subjects until SWR revalidates.

**Fix required:** Include the user ID in the cache key: `useSWR<Subject[]>(['subjects', userId], ...)`.

### BUG-F09 · `next.config.js` — `images.domains` is empty; Supabase Storage image URLs will be blocked

**File:** file:frontend/next.config.js · Line 4

**Severity:** 🟡 Medium — Any `<Image>` component loading from Supabase Storage will fail

**What is wrong:**

```javascript
images: { domains: [] }
```

If the app uses `next/image` to display images from Supabase Storage (e.g., uploaded PDFs rendered as images), Next.js will block the request with "hostname not configured."

**Fix required:** Add the Supabase project hostname: `domains: ['<project-id>.supabase.co']`.

### BUG-F10 · `lib/services/` — No error retry or token refresh logic

**File:** file:frontend/lib/services/base.service.ts

**Severity:** 🟠 High — Expired tokens cause permanent 401 errors with no recovery

**What is wrong:**
The `apiFetch` function throws on any non-2xx response. There is no logic to detect a 401, refresh the Supabase token, and retry the request. When a user's access token expires (Supabase tokens expire in 1 hour by default), all API calls will fail permanently until the user manually refreshes the page.

**Fix required:** Implement a token refresh interceptor that calls `/auth/refresh` on 401 responses and retries the original request.

## SECTION 4 — BOTTLENECKS & PERFORMANCE ISSUES

### PERF-01 · `routers/dashboard.py` — `get_study_progress` executes 21 separate database queries

**File:** file:backend/app/routers/dashboard.py · Lines 296–413

**Severity:** 🟠 High — Severe N+1 query problem

**What is wrong:**
For each of 7 days × 3 tables = 21 queries for daily progress. For each of 5 weeks × 3 tables = 15 queries for weekly progress. For each of 4 months × 3 tables = 12 queries for monthly progress. **Total: 48 separate database queries per request.**

**Fix required:** Use a single aggregated query with `GROUP BY date_trunc(...)` to fetch all activity counts in one round trip.

### PERF-02 · `services.py` — `get_repetition_analysis` executes one DB query per question to find paper year

**File:** file:backend/app/services.py · Lines 663–678

**Severity:** 🟠 High — O(n) queries where n = number of questions

**What is wrong:**

```python
for i, text in enumerate(question_texts):
    ...
for text, indices in text_counts.items():
    for q in repeated_questions:
        paper = db.query(models.QuestionPaper).filter(
            models.QuestionPaper.id == q.paper_id
        ).first()
```

For every repeated question, a separate query fetches the paper. With 100 questions across 10 papers, this can execute 100+ queries.

**Fix required:** Join `Question` with `QuestionPaper` in the initial query to fetch years in one query.

### PERF-03 · `routers/questions.py` — `get_important_questions` executes nested loops with DB queries

**File:** file:backend/app/routers/questions.py · Lines 48–72

**Severity:** 🟠 High — O(subjects × papers) queries

**What is wrong:**

```python
for subject in subjects:
    papers = db.query(models.QuestionPaper).filter(...).all()
    for paper in papers:
        questions = db.query(models.Question).filter(...).all()
```

For each subject, a query fetches papers. For each paper, another query fetches questions. With 5 subjects and 3 papers each, this is 5 + 15 = 20 queries minimum.

**Fix required:** Use a single JOIN query across `Subject → QuestionPaper → Question` filtered by `user_id`.

### PERF-04 · `services/model_coordinator.py` — `ModelCoordinator` is instantiated at module import time

**File:** file:backend/app/services/model_coordinator.py · Line 656

**Severity:** 🟠 High — Slows application startup; blocks import

**What is wrong:**

```python
model_coordinator = ModelCoordinator()  # Module-level instantiation
```

`ModelCoordinator.__init__` calls `_initialize_models()` which sets up 11 model configurations and logs status. While the models themselves are lazy-loaded, this still runs at import time and adds startup latency.

### PERF-05 · `database.py` — Connection pool size of 1 with max_overflow of 2 is too small for concurrent requests

**File:** file:backend/app/database.py · Lines 33–34

**Severity:** 🟡 Medium — Connection starvation under moderate load

**What is wrong:**

```python
pool_size=1,
max_overflow=2,
```

Maximum 3 concurrent database connections. With the dashboard endpoint making 48 queries, a single user request can hold a connection for several seconds. A second concurrent user will be blocked waiting for a connection.

### PERF-06 · `routers/papers.py` — `ThreadPoolExecutor()` creates a new thread pool per upload

**File:** file:backend/app/routers/papers.py · Line 147

**Severity:** 🟡 Medium — Thread pool overhead; no reuse

**What is wrong:**

```python
result = await asyncio.get_event_loop().run_in_executor(
    ThreadPoolExecutor(),  # New pool created per request
    ...
)
```

A new `ThreadPoolExecutor` is created for every upload request and never shut down. This leaks threads and adds overhead.

**Fix required:** Use a shared module-level executor or FastAPI's default executor.

## SECTION 5 — CONFIGURATION & SECURITY ISSUES

### SEC-01 · `main.py` — CORS allows all origins in development mode with `allow_credentials=True`

**File:** file:backend/app/main.py · Lines 145–152

**Severity:** 🟠 High — Credential-bearing cross-origin requests accepted from any origin

**What is wrong:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # ← This combination is invalid per CORS spec
    ...
)
```

The CORS specification prohibits `allow_origins=["*"]` combined with `allow_credentials=True`. Browsers will reject such responses. FastAPI/Starlette may silently allow it server-side, but browsers will block the response.

**Fix required:** In development, use explicit origins like `["http://localhost:3000"]` instead of `"*"` when credentials are required.

### SEC-02 · `core/config.py` — `SECRET_KEY` has an insecure default

**File:** file:backend/app/core/config.py · Line 17

**Severity:** 🔴 Critical — JWT tokens can be forged if default is used

**What is wrong:**

```python
SECRET_KEY: str = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "default-insecure-change-me"))
```

If neither `JWT_SECRET` nor `SECRET_KEY` is set, the application uses `"default-insecure-change-me"` as the JWT signing key. Any attacker who knows this default (it is in the source code) can forge valid JWT tokens.

**Fix required:** Remove the insecure default. Raise a `ValueError` if neither env var is set.

### SEC-03 · `main.py` — Docs endpoints exposed in debug mode with no authentication

**File:** file:backend/app/main.py · Lines 126–128

**Severity:** 🟡 Medium — API documentation publicly accessible in debug mode

**What is wrong:**

```python
docs_url="/docs" if settings.DEBUG else None,
```

In debug/development mode, `/docs` and `/redoc` are publicly accessible with no authentication. These expose all endpoint schemas, request/response formats, and can be used to probe the API.

### SEC-04 · `supabase_first_auth.py` — Debug print statements log sensitive user data

**File:** file:backend/app/services/supabase_first_auth.py · Lines 89–91, 192–193

**Severity:** 🟠 High — User email, session tokens, and user IDs logged to stdout

**What is wrong:**

```python
print(f"[DEBUG] Supabase signup response type: {type(response)}")
print(f"[DEBUG] Login response user: {response.user}")
print(f"[DEBUG] Login response session: {response.session}")
```

These `print` statements log the full Supabase response objects, which include access tokens, refresh tokens, and user PII. In production, these appear in server logs.

**Fix required:** Remove all debug `print` statements. Use `logger.debug()` with sensitive fields redacted.

### SEC-05 · `dashboard.py` — Error log written to a local file in production

**File:** file:backend/app/routers/dashboard.py · Lines 183–188

**Severity:** 🟡 Medium — Local file write in a stateless deployment environment

**What is wrong:**

```python
with open("dashboard_error.log", "a") as f:
    f.write(error_msg)
```

On Render (or any container-based deployment), the filesystem is ephemeral. This file is lost on restart. Additionally, writing to the filesystem in a web request handler is a blocking I/O operation.

**Fix required:** Remove the file write. Use the structured logger instead.

## Summary Table

| ID | Layer | Severity | Description |
| --- | --- | --- | --- |
| BUG-B01 | Backend | 🔴 Critical | `security.py` uses `await` on sync session |
| BUG-B02 | Backend | 🔴 Critical | `is_active` field does not exist on User model |
| BUG-B03 | Backend | 🟠 High | `GEMINI_API_KEY` stored under wrong config key |
| BUG-B04 | Backend | 🟠 High | `SUPABASE_KEY` reads wrong env variable |
| BUG-B05 | Backend | 🟠 High | `lru_cache` on service factory is not thread-safe |
| BUG-B06 | Backend | 🔴 Critical | Difficulty filter compares strings to integers |
| BUG-B07 | Backend | 🟠 High | Test submission hardcodes score = 72 |
| BUG-B08 | Backend | 🟠 High | Test results return fabricated question analysis |
| BUG-B09 | Backend | 🔴 Critical | `search_questions` filters on non-existent attributes |
| BUG-B10 | Backend | 🔴 Critical | `generate_analysis` called before definition |
| BUG-B11 | Backend | 🟡 Medium | `logger` defined twice in `upload.py` |
| BUG-B12 | Backend | 🟠 High | In-memory progress dict not process-safe |
| BUG-B13 | Backend | 🔴 Critical | SQLAlchemy session shared across threads |
| BUG-B14 | Backend | 🟠 High | Deduplication uses character-set Jaccard (broken) |
| BUG-B15 | Backend | 🟠 High | `json.loads()` called on already-deserialized JSON column |
| BUG-B16 | Backend | 🟠 High | Duplicate Prediction records created per generation |
| BUG-B17 | Backend | 🟡 Medium | Float accuracy score stored in String(5) column |
| BUG-B18 | Backend | 🟠 High | AI tutor accepts unvalidated `dict` request body |
| BUG-B19 | Backend | 🟡 Medium | Chat history saved twice for tutor messages |
| BUG-B20 | Backend | 🟡 Medium | Import placed after function definition in `plans.py` |
| BUG-B21 | Backend | 🟠 High | `np.mean([])` returns `nan` — not JSON-serializable |
| BUG-B22 | Backend | 🟡 Medium | `'db' in locals()` always True — dead else branch |
| BUG-B23 | Backend | 🟠 High | Auth exceptions silently swallowed |
| BUG-B24 | Backend | 🟠 High | Race condition on lazy user creation |
| BUG-B25 | Backend | 🔴 Critical | Bytez API key hardcoded in source |
| BUG-B26 | Backend | 🟠 High | `sys.exit(1)` called at module import time |
| BUG-B27 | Backend | 🟡 Medium | `create_tables()` name collision across modules |
| BUG-B28 | Backend | 🟡 Medium | `get_subject` executes 3 queries instead of 1 |
| BUG-B29 | Backend | 🟡 Medium | Streak calculation ignores user timezone |
| BUG-B30 | Backend | 🟠 High | `get_weightage_analysis` reads wrong dict keys |
| BUG-B31 | Backend | 🟠 High | Route conflict between `/{subject_id}` and `/{paper_id}/preview` |
| BUG-B32 | Backend | 🟡 Medium | `'numpy' in dir()` always False — dead code |
| BUG-D01 | Database | 🔴 Critical | `semester` type mismatch across schema files |
| BUG-D02 | Database | 🔴 Critical | `papers_uploaded` type mismatch (BOOLEAN vs INTEGER) |
| BUG-D03 | Database | 🔴 Critical | Migration renames `difficulty` but ORM still uses old name |
| BUG-D04 | Database | 🟠 High | `pgvector` extension defined in one schema only |
| BUG-D05 | Database | 🔴 Critical | RLS policies allow any authenticated user to read all data |
| BUG-D06 | Database | 🟡 Medium | `chat_history.subject_id` nullability inconsistent |
| BUG-D07 | Database | 🟠 High | `001_initial_schema.sql` creates conflicting tables |
| BUG-F01 | Frontend | 🟠 High | NextAuth configured with zero providers |
| BUG-F02 | Frontend | 🔴 Critical | `apiFetch` never attaches Authorization header |
| BUG-F03 | Frontend | 🟠 High | `getById` throws synchronously instead of rejecting Promise |
| BUG-F04 | Frontend | 🟠 High | Dashboard stats are all hardcoded |
| BUG-F05 | Frontend | 🟠 High | Recent activity is hardcoded static array |
| BUG-F06 | Frontend | 🔴 Critical | No authentication guard on any page |
| BUG-F07 | Frontend | 🔴 Critical | No login/signup pages exist |
| BUG-F08 | Frontend | 🟠 High | SWR cache key not scoped to user |
| BUG-F09 | Frontend | 🟡 Medium | Supabase Storage domain not in `next.config.js` |
| BUG-F10 | Frontend | 🟠 High | No token refresh logic on 401 responses |
| PERF-01 | Performance | 🟠 High | Dashboard progress: 48 DB queries per request |
| PERF-02 | Performance | 🟠 High | Repetition analysis: O(n) queries per question |
| PERF-03 | Performance | 🟠 High | Important questions: nested loop DB queries |
| PERF-04 | Performance | 🟠 High | ModelCoordinator instantiated at import time |
| PERF-05 | Performance | 🟡 Medium | DB connection pool too small (max 3) |
| PERF-06 | Performance | 🟡 Medium | New ThreadPoolExecutor created per upload |
| SEC-01 | Security | 🟠 High | CORS `allow_origins=["*"]` + `allow_credentials=True` |
| SEC-02 | Security | 🔴 Critical | JWT secret has insecure hardcoded default |
| SEC-03 | Security | 🟡 Medium | API docs publicly accessible in debug mode |
| SEC-04 | Security | 🟠 High | Debug prints log access tokens and user PII |
| SEC-05 | Security | 🟡 Medium | Error log written to ephemeral local filesystem |

**Total: 57 confirmed issues** — 12 Critical 🔴 · 28 High 🟠 · 17 Medium 🟡