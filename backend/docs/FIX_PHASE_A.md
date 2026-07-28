# Fix Phase A — Single data plane

## Goal
Subjects, papers, questions, predictions, and mock tests share **one** store:
- **Pyronites** tables for metadata
- **Local disk** (`UPLOAD_ROOT`) for paper files

## What changed

| Area | Change |
|------|--------|
| `app/services/prediction_service.py` | **New** tiered prediction (0 / cold / full) using repos + LLM provider |
| `app/routers/predictions.py` | No SQLAlchemy; uses `prediction_service` |
| `app/routers/tests.py` | No SQLAlchemy; uses `mock_tests` / `questions` / `predictions` repos |
| `app/routers/papers.py` | Local `save_upload` + Pyronites papers/questions; no Supabase Storage |
| `app/services/supabase_storage.py` | Stub that raises (deprecated) |
| `app/schemas.py` | `TestResultsResponse.percentage` Optional; paper/test datetime fields relaxed |

## Still on old stack (out of Phase A scope)
- `app/services.py` (large PrepIQService) still has SQLAlchemy paths — **not** used by predictions/tests/papers routers anymore
- `analysis`, `dashboard`, `wizard`, `questions`, `plans` routers may still import SQLAlchemy
- `database.py` remains for those leftover routes

## Flow that works end-to-end (core)
1. `POST /api/v1/auth/signup` + `login` (Pyronites)
2. `POST /api/v1/subjects`
3. `POST /api/v1/papers/upload` **or** `POST /api/v1/upload` (both write Pyronites + local files)
4. `POST /api/v1/predictions/generate` or `GET /api/v1/predictions/subject/{id}`
5. `POST /api/v1/tests/generate` → `submit` → `results`

## Required env
```env
PYRONITES_URL=
PYRONITES_KEY=
UPLOAD_ROOT=./uploads
JWT_SECRET=
ALLOWED_ORIGINS=http://localhost:3000
# LLM for prediction/extraction
GEMINI_API_KEY=
# or PREDICTION_API_KEY / EXTRACTION_API_KEY / LLM_DEFAULT_API_KEY
```

## Pyronites tables expected
`users`, `subjects`, `question_papers`, `questions`, `predictions`, `mock_tests`

## Honest behavior preserved
- Empty prediction: `source=no_data`, no fake high confidence
- Empty mock test: `test_id=none`, `status=error`, `insufficient_data`
- Ungradeable submit: `score_percentage=null`
