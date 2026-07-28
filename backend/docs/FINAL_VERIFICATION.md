# PrepIQ backend — final verification (Fix Phases A–D)

## Core path (must work with Pyronites only — no DATABASE_URL)

1. `POST /api/v1/auth/signup` — strong password + valid email  
2. `POST /api/v1/auth/login` — receive `access_token`  
3. `Authorization: Bearer <token>` on all protected routes  
4. `POST /api/v1/subjects`  
5. `POST /api/v1/papers/upload` (multipart) **or** `POST /api/v1/upload`  
6. `GET /api/v1/predictions/subject/{id}` — tier 0 empty OK  
7. After papers extracted: predictions non-empty or stats fallback  
8. `POST /api/v1/tests/generate` — empty → `test_id=none`  
9. With questions: generate → submit → results (`percentage` null if no answers)  
10. `GET /api/v1/dashboard/stats`  
11. `GET /api/v1/wizard/status`  

## Env
```env
PYRONITES_URL=
PYRONITES_KEY=
JWT_SECRET=
ALLOWED_ORIGINS=http://localhost:3000
UPLOAD_ROOT=./uploads
GEMINI_API_KEY=   # or PREDICTION_API_KEY
```

## Tables
See `PYRONITES_SCHEMA.md`.

## Status by router

| Router | Data plane |
|--------|------------|
| auth | Pyronites |
| subjects | Pyronites |
| papers | Local disk + Pyronites |
| upload | Local disk + Pyronites |
| predictions | Pyronites + LLM provider |
| tests | Pyronites |
| dashboard | Pyronites |
| wizard | Pyronites |
| questions | Pyronites |
| analysis | **503 deferred** |
| plans | **503 deferred** |
| chat | Still may touch SQLAlchemy for history/subjects — tutor LLM works if key set; full chat history needs later rewrite |

## Known limitations
- Frontend still may use old OAuth/Supabase client  
- Chat history / tutor subject lookup may fail without Postgres  
- Analysis + study plans intentionally offline  
- `app/services.py` legacy ORM code remains but core routers do not use it  
- Scoring needs `correct_answer` on questions (extraction often leaves it null)  

## Smoke
```bash
cd backend && python scripts/smoke_phase_b.py
```
