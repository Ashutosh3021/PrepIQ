# PrepIQ — Startup & Feature Testing Guide

Everything you need to run the app locally and manually test every feature end-to-end.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [Database Setup (Supabase)](#3-database-setup-supabase)
4. [Run the Backend](#4-run-the-backend)
5. [Run the Frontend](#5-run-the-frontend)
6. [Feature Testing — Complete Walkthrough](#6-feature-testing)
   - [Auth — OAuth Sign-in](#61-auth--oauth-sign-in)
   - [Setup Wizard](#62-setup-wizard)
   - [Subjects](#63-subjects)
   - [Paper Upload & Processing](#64-paper-upload--processing)
   - [AI Predictions](#65-ai-predictions)
   - [Mock Tests](#66-mock-tests)
   - [AI Tutor / Chat](#67-ai-tutor--chat)
   - [Analysis Dashboard](#68-analysis-dashboard)
   - [Study Plans](#69-study-plans)
   - [Dashboard & Stats](#610-dashboard--stats)
   - [Profile Page](#611-profile-page)
7. [API Reference (curl cheatsheet)](#7-api-reference-curl-cheatsheet)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites

| Tool | Minimum version | Check |
|------|----------------|-------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | any | `git --version` |

External services required:

- **Supabase** — free tier works: https://supabase.com
  - You need a project with **Google** and/or **GitHub** OAuth providers enabled (see §3)
- **Google Gemini API** — free tier works: https://aistudio.google.com/app/apikey

> **Auth note:** PrepIQ uses OAuth-only authentication (Google + GitHub via Supabase).
> There is no email/password signup or login. `pages/login.tsx` and `pages/signup.tsx`
> have been deleted. The auth entry point is `/auth`.

---

## 2. Environment Setup

### Backend

```bash
# From the repo root
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in every value:

```dotenv
# Supabase → Project Settings → Database → Connection string (Transaction pooler)
DATABASE_URL=postgresql://postgres.YOURPROJECT:YOURPASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?pgbouncer=true

# Supabase → Project Settings → API
SUPABASE_URL=https://YOURPROJECT.supabase.co
SUPABASE_SERVICE_KEY=eyJ...   # service_role key — keep secret, never expose to browser
SUPABASE_ANON_KEY=eyJ...      # anon/public key

# Generate: openssl rand -base64 32
JWT_SECRET=your-32-char-minimum-secret

# Must include your frontend origin
ALLOWED_ORIGINS=http://localhost:3000

# Google AI Studio → Get API key
GEMINI_API_KEY=AIza...

# Optional
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Frontend

```bash
cp frontend/.env.example frontend/.env.local
```

Open `frontend/.env.local`:

```dotenv
# "real" hits the live backend; "mock" returns hardcoded data (no backend needed)
NEXT_PUBLIC_API_MODE=real
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Supabase — required for OAuth
# Supabase → Project Settings → API
NEXT_PUBLIC_SUPABASE_URL=https://YOURPROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...   # anon/public key
```

> Set `NEXT_PUBLIC_API_MODE=mock` to explore the UI without a running backend.
> OAuth sign-in still requires the Supabase vars even in mock mode.

---

## 3. Database Setup (Supabase)

### 3.1 Run the schema

Go to **Supabase Dashboard → SQL Editor → New query**.

**Step 1 — Create all tables, indexes, triggers, and the OAuth auto-create trigger:**

Paste the entire contents of `global.sql` (repo root) and click **Run**.

**Step 2 — Apply Row Level Security policies:**

Paste the entire contents of `rls.sql` (repo root) and click **Run**.

Both files are idempotent — safe to re-run without dropping data.

**Verify:**
```sql
-- All should return without error
SELECT wizard_completed, exam_name, focus_subjects FROM users LIMIT 1;
SELECT metadata_json FROM question_papers LIMIT 1;
SELECT text_length FROM questions LIMIT 1;
SELECT ml_analysis_json, prediction_accuracy_score FROM predictions LIMIT 1;
```

### 3.2 Enable OAuth providers

**Google:**
1. [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials → Create OAuth 2.0 Client ID
2. Application type: **Web application**
3. Authorised redirect URI: `https://YOURPROJECT.supabase.co/auth/v1/callback`
4. Copy the Client ID and Client Secret
5. Supabase Dashboard → Authentication → Providers → Google → paste both values → Save

**GitHub:**
1. GitHub → Settings → Developer Settings → OAuth Apps → New OAuth App
2. Homepage URL: `http://localhost:3000`
3. Callback URL: `https://YOURPROJECT.supabase.co/auth/v1/callback`
4. Copy the Client ID, generate a Client Secret
5. Supabase Dashboard → Authentication → Providers → GitHub → paste both values → Save

### 3.3 Create the Storage bucket

1. Supabase Dashboard → Storage → New bucket
2. Name: `question-papers`
3. Public: **yes** (so the frontend can display paper URLs)

---

## 4. Run the Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies (2-5 minutes first time — sentence-transformers is large)
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected startup output:**
```
[OK] Loaded environment from backend/.env
INFO  Starting PrepIQ Backend Application
INFO  Environment: development
INFO  [OK] Database connection verified
INFO  [OK] PrepIQService initialized
INFO  Uvicorn running on http://0.0.0.0:8000
```

**Verify it's running:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","database":"connected",...}
```

**Interactive API docs** (development mode only):
```
http://localhost:8000/docs
```

---

## 5. Run the Frontend

Open a **second terminal**:

```bash
cd frontend

npm install

npm run dev
```

**Expected output:**
```
▲ Next.js 15.x
- Local: http://localhost:3000
```

Open http://localhost:3000. The root page auto-redirects to `/desktop` or `/mobile` based on your user agent.

---

## 6. Feature Testing

Work through these in order — each section depends on the previous one.

---

### 6.1 Auth — OAuth Sign-in

**There is no email/password form.** Authentication is OAuth-only via Supabase.

**Via the UI:**

1. Go to http://localhost:3000/auth
2. Click **Continue with Google** or **Continue with GitHub**
3. Complete the OAuth consent screen in the popup
4. Supabase redirects to `/auth/callback`
5. The callback page exchanges the code for a session, then checks wizard status:
   - First-time user → redirected to `/wizard`
   - Returning user (wizard done) → redirected to `/desktop/dashboard`

**Verify sign-in worked:**
- Supabase Dashboard → Authentication → Users — your account should appear
- The `users` table in the database should have a new row (auto-created by the `handle_new_auth_user` trigger in `global.sql`)

**Getting a token for curl testing:**

Since there's no password login endpoint, get your token from the browser after signing in:

```javascript
// Open browser DevTools → Console on any page after signing in
const { data } = await window.__supabase?.auth.getSession()
  ?? { data: null };
// Or read from localStorage:
const session = JSON.parse(
  Object.entries(localStorage)
    .find(([k]) => k.includes('supabase') || k.includes('sb-'))?.[1] ?? '{}'
);
console.log(session.access_token);
```

Or use the Supabase JS SDK directly in the console:

```javascript
// In browser DevTools console (after signing in at /auth)
const { data: { session } } = await supabase.auth.getSession();
console.log(session.access_token);
```

Save the token:
```bash
TOKEN="eyJ..."   # paste your access_token here
```

Tokens expire after the configured `ACCESS_TOKEN_EXPIRE_MINUTES` (default 1440 = 24 hours). Supabase auto-refreshes them in the browser. For curl testing, re-copy the token from DevTools when it expires.

**Verify the token works:**
```bash
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
# Expected: your user object with id, email, wizard_completed, etc.
```

---

### 6.2 Setup Wizard

First-time users are redirected to `/wizard` automatically after OAuth sign-in.
The wizard collects onboarding data in 3 steps and calls the backend to save it.

**Via the UI:**

- **Step 1 — Institution**
  - College / University name (e.g. "Gita Autonomous College")
  - Program: select from B.Tech / B.Sc / BCA / M.Tech / MCA / Other
  - Year of Study: select 1st–4th Year

- **Step 2 — Semester & Subjects**
  - Semester: select Sem 1–8
  - Subjects: type a subject name and press Enter or click Add (e.g. "Linear Algebra", "Data Structures")
  - Add as many subjects as you're studying this semester

- **Step 3 — Goals**
  - Exam Date: pick from the date picker
  - Study Goal: select one (e.g. "Score distinction")
  - Preferred Study Style: select one (e.g. "Mixed (theory + practice)")

- Click **Finish Setup** — redirected to `/desktop/dashboard`

**Verify via API:**
```bash
curl -s http://localhost:8000/api/v1/wizard/status \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
# Expected: {"completed": true, "exam_name": "...", "focus_subjects": [...], ...}
```

**Re-run the wizard (for testing):**
```bash
# Reset wizard_completed to false in Supabase SQL Editor:
UPDATE users SET wizard_completed = FALSE WHERE id = 'your-user-id';
# Then reload /wizard in the browser
```

---

### 6.3 Subjects

**Create a subject via UI:**
- Go to `/desktop/subjects` → click **Add Subject**

**Create via API:**
```bash
curl -s -X POST http://localhost:8000/api/v1/subjects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Linear Algebra",
    "code": "MA201",
    "semester": 3,
    "academic_year": "2025-2026",
    "total_marks": 100,
    "exam_date": "2026-06-15"
  }' | python -m json.tool
```

Save the `id` from the response:
```bash
SUBJECT_ID="<id from response>"
```

**List subjects:**
```bash
curl -s http://localhost:8000/api/v1/subjects \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

### 6.4 Paper Upload & Processing

This is the core data-ingestion step. Everything else (predictions, tests, analysis) depends on having at least one processed paper.

**Via the UI:**
1. Go to `/desktop/upload`
2. Drag a PDF question paper onto the drop zone (or click to browse)
3. Select the subject from the dropdown (populated from your real subjects)
4. Click **Upload & Analyze**
5. Wait for the success message — it shows how many questions were extracted

**Via curl (multipart form):**
```bash
curl -s -X POST http://localhost:8000/api/v1/papers/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/paper.pdf" \
  -F "subject_id=$SUBJECT_ID" \
  -F "exam_year=2024" | python -m json.tool
```

**Expected response:**
```json
{
  "paper_id": "...",
  "status": "completed",
  "message": "Successfully processed 18 unique questions from 20 total",
  "questions_count": 18
}
```

**Check papers for a subject:**
```bash
curl -s "http://localhost:8000/api/v1/papers/by-subject/$SUBJECT_ID" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Preview extracted questions:**
```bash
PAPER_ID="<paper_id from upload response>"
curl -s "http://localhost:8000/api/v1/papers/$PAPER_ID/preview" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

> Upload at least **2–3 papers** for the same subject to get meaningful predictions.

---

### 6.5 AI Predictions

Requires at least one processed paper for the subject.

**Generate predictions:**
```bash
curl -s -X POST http://localhost:8000/api/v1/predictions/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"subject_id\": \"$SUBJECT_ID\", \"use_all_papers\": true}" \
  | python -m json.tool
```

Save the `prediction_id`:
```bash
PREDICTION_ID="<prediction_id from response>"
```

**Fetch the prediction:**
```bash
curl -s "http://localhost:8000/api/v1/predictions/$PREDICTION_ID" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Get latest prediction for a subject:**
```bash
curl -s "http://localhost:8000/api/v1/predictions/$SUBJECT_ID/latest" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**What to verify:**
- `predicted_questions` array is non-empty
- Each question has `text`, `marks`, `unit`, `probability`, `reasoning`
- `unit_coverage` shows which units are covered

---

### 6.6 Mock Tests

Requires processed papers for the subject.

**Generate a test:**
```bash
curl -s -X POST http://localhost:8000/api/v1/tests/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"subject_id\": \"$SUBJECT_ID\",
    \"num_questions\": 10,
    \"difficulty\": \"medium\",
    \"time_limit_minutes\": 30
  }" | python -m json.tool
```

Save the `test_id`:
```bash
TEST_ID="<test_id from response>"
```

**Submit answers** (use question IDs from the generate response):
```bash
curl -s -X POST "http://localhost:8000/api/v1/tests/$TEST_ID/submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"answers\": {\"<question_id_1>\": \"A\", \"<question_id_2>\": \"B\"},
    \"end_time\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }" | python -m json.tool
```

**Get results:**
```bash
curl -s "http://localhost:8000/api/v1/tests/$TEST_ID/results" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**What to verify:**
- `score`, `percentage`, `correct_count`, `incorrect_count`, `skipped_count` are all numbers
- `weak_topics` and `strong_topics` are populated
- `recommendations` array is non-empty

**List all your tests:**
```bash
curl -s "http://localhost:8000/api/v1/tests/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

### 6.7 AI Tutor / Chat

Requires `GEMINI_API_KEY` to be set. Without it the endpoint returns a graceful fallback message.

**Send a message via the subject-scoped chat:**
```bash
curl -s -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"subject_id\": \"$SUBJECT_ID\",
    \"message\": \"Explain eigenvalues in simple terms\"
  }" | python -m json.tool
```

**Use the standalone AI Tutor (Socratic mode):**
```bash
curl -s -X POST http://localhost:8000/api/v1/chat/tutor \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the difference between a matrix and a determinant?",
    "conversation_history": []
  }' | python -m json.tool
```

**Get chat history for a subject:**
```bash
curl -s "http://localhost:8000/api/v1/chat/history/$SUBJECT_ID" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Clear chat history:**
```bash
curl -s -X DELETE "http://localhost:8000/api/v1/chat/history/$SUBJECT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Via the UI:**
- Go to `/desktop/ai-tutor`
- Type a question and press Enter or click the send button
- The tutor responds with a diagnostic question first (Socratic style)

---

### 6.8 Analysis Dashboard

Requires at least one subject with processed papers.

**Get full analysis data (used by the Analysis page):**
```bash
curl -s http://localhost:8000/api/v1/analysis/data \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Frequency analysis for a subject:**
```bash
curl -s "http://localhost:8000/api/v1/analysis/$SUBJECT_ID/frequency" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Unit weightage:**
```bash
curl -s "http://localhost:8000/api/v1/analysis/$SUBJECT_ID/weightage" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Question repetition analysis:**
```bash
curl -s "http://localhost:8000/api/v1/analysis/$SUBJECT_ID/repetitions" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Trend analysis:**
```bash
curl -s "http://localhost:8000/api/v1/analysis/$SUBJECT_ID/trends" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Via the UI:**
- Go to `/desktop/analysis`
- The gauge shows overall proficiency derived from subject performance
- Bar chart shows per-subject performance
- Roadmap section shows high-priority topics from correlation analysis

---

### 6.9 Study Plans

Requires a subject with processed papers.

**Generate a study plan:**
```bash
curl -s -X POST http://localhost:8000/api/v1/plan/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"subject_id\": \"$SUBJECT_ID\",
    \"start_date\": \"$(date -u +%Y-%m-%d)\",
    \"exam_date\": \"2026-06-15\"
  }" | python -m json.tool
```

**Get your current plan:**
```bash
curl -s http://localhost:8000/api/v1/plan/me \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Update progress:**
```bash
PLAN_ID="<plan_id from generate response>"
curl -s -X PUT "http://localhost:8000/api/v1/plan/$PLAN_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days_completed": 5, "on_track": true}' | python -m json.tool
```

**What to verify:**
- `daily_schedule` array has one entry per day between start and exam date
- Each day has `topics`, `recommended_hours`, `priority_topics`
- After updating progress, `completion_percentage` is a float (e.g. `16.67`), not a string

---

### 6.10 Dashboard & Stats

**Get dashboard stats:**
```bash
curl -s http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Expected fields:**
```json
{
  "subjects_count": 2,
  "predictions_count": 1,
  "completion_percentage": 50,
  "focus_area": "Linear Algebra",
  "study_streak": 3,
  "days_to_exam": 43,
  "recent_activity": [...]
}
```

**Get recent activity:**
```bash
curl -s http://localhost:8000/api/v1/dashboard/recent-activity \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Get study progress (weekly/monthly charts):**
```bash
curl -s http://localhost:8000/api/v1/dashboard/progress \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Via the UI:**
- Go to `/desktop/dashboard`
- Stats row shows real counts from the API
- Recent Activity panel shows real events
- "Days to Exam" counter uses the wizard exam date

---

### 6.11 Profile Page

**Get your profile:**
```bash
curl -s http://localhost:8000/api/v1/auth/profile \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Verify `created_at` is your real account creation date** (not the current time).

**Get full user info (includes wizard data):**
```bash
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Via the UI:**
- Go to `/desktop/profile`
- Your real name comes from OAuth metadata (`user_metadata.full_name`)
- Email, college, program, year of study are shown
- Stats (subjects, progress %, predictions, streak) come from the dashboard API
- Recent activity section shows real events

---

## 7. API Reference (curl cheatsheet)

All endpoints are prefixed with `http://localhost:8000/api/v1`.
All protected endpoints require `-H "Authorization: Bearer $TOKEN"`.

> **Auth is OAuth-only.** There are no `/auth/signup` or `/auth/login` endpoints.
> Get your token from the browser after signing in at `/auth` (see §6.1).

| Feature | Method | Path |
|---------|--------|------|
| Get profile | GET | `/auth/profile` |
| Get full user | GET | `/auth/me` |
| Verify token | GET | `/auth/verify-token` |
| Refresh token | POST | `/auth/refresh` |
| Wizard status | GET | `/wizard/status` |
| Wizard step 1 | POST | `/wizard/step1` |
| Wizard step 2 | POST | `/wizard/step2` |
| Wizard step 3 | POST | `/wizard/step3` |
| Complete wizard | POST | `/wizard/complete` |
| List subjects | GET | `/subjects` |
| Create subject | POST | `/subjects` |
| Get subject | GET | `/subjects/{id}` |
| Update subject | PUT | `/subjects/{id}` |
| Delete subject | DELETE | `/subjects/{id}` |
| Upload paper | POST | `/papers/upload` |
| Papers by subject | GET | `/papers/by-subject/{subject_id}` |
| Paper preview | GET | `/papers/{paper_id}/preview` |
| Delete paper | DELETE | `/papers/{paper_id}` |
| Generate predictions | POST | `/predictions/generate` |
| Get prediction | GET | `/predictions/{id}` |
| Latest prediction | GET | `/predictions/{subject_id}/latest` |
| Generate test | POST | `/tests/generate` |
| Submit test | POST | `/tests/{id}/submit` |
| List tests | GET | `/tests/` |
| Test results | GET | `/tests/{id}/results` |
| Chat message | POST | `/chat/message` |
| AI Tutor | POST | `/chat/tutor` |
| Chat history | GET | `/chat/history/{subject_id}` |
| Clear history | DELETE | `/chat/history/{subject_id}` |
| Analysis data | GET | `/analysis/data` |
| Frequency | GET | `/analysis/{subject_id}/frequency` |
| Weightage | GET | `/analysis/{subject_id}/weightage` |
| Repetitions | GET | `/analysis/{subject_id}/repetitions` |
| Trends | GET | `/analysis/{subject_id}/trends` |
| Generate plan | POST | `/plan/generate` |
| Get my plan | GET | `/plan/me` |
| Update plan | PUT | `/plan/{plan_id}` |
| Dashboard stats | GET | `/dashboard/stats` |
| Recent activity | GET | `/dashboard/recent-activity` |
| Study progress | GET | `/dashboard/progress` |
| Important questions | GET | `/questions/important` |
| Search questions | GET | `/questions/search?subject=&topic=&difficulty=` |
| Health check | GET | `/health` (no auth needed) |

---

## 8. Troubleshooting

**Backend won't start — `DATABASE_URL` error**
```
ValueError: DATABASE_URL environment variable is required
```
→ Make sure `backend/.env` exists and `DATABASE_URL` is set. The app strips `?pgbouncer=true` automatically.

**Backend won't start — `RuntimeError` in production mode**
```
RuntimeError: Cannot start in production with missing environment variables
```
→ Either set all required env vars, or set `ENVIRONMENT=development` in your `.env`.

**OAuth button does nothing / redirects to a blank page**
→ Check that `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set in `frontend/.env.local`. Without them the Supabase client can't initiate the OAuth flow.

**OAuth redirect fails with "redirect_uri_mismatch"**
→ The redirect URI registered in Google Cloud Console or GitHub OAuth App must exactly match `https://YOURPROJECT.supabase.co/auth/v1/callback`. Check for trailing slashes or http vs https mismatches.

**After OAuth, stuck on `/auth/callback` spinner**
→ The callback page calls `supabase.auth.exchangeCodeForSession()`. If this fails, check the browser console for errors. Common cause: `NEXT_PUBLIC_SUPABASE_URL` or `NEXT_PUBLIC_SUPABASE_ANON_KEY` is wrong.

**After OAuth, redirected to `/wizard` every time even after completing it**
→ The wizard completion wasn't saved. Check `GET /api/v1/wizard/status` — if `completed` is `false`, the backend didn't receive the `POST /wizard/complete` call. Check the browser network tab for errors on the wizard's final step.

**User row not created in `users` table after OAuth sign-in**
→ The `handle_new_auth_user` trigger in `global.sql` wasn't applied. Re-run `global.sql` in the Supabase SQL Editor.

**401 on every API call**
→ Your token has expired. Re-copy it from the browser DevTools (see §6.1). Tokens last 24 hours by default.

**Paper upload returns 503**
```json
{"detail": "Supabase storage is not configured"}
```
→ `SUPABASE_URL` or `SUPABASE_SERVICE_KEY` is missing or wrong in `backend/.env`.

**Paper upload returns 404 "Subject not found"**
→ The `subject_id` you passed doesn't belong to the authenticated user. List your subjects first and use a real ID.

**Predictions return "No processed papers found"**
→ The paper upload either failed or is still processing. Check `GET /papers/by-subject/{id}` — the `processing_status` field must be `"completed"`.

**AI Tutor returns a fallback message instead of a real response**
→ `GEMINI_API_KEY` is missing or invalid. Check `backend/.env` and verify the key at https://aistudio.google.com.

**Frontend shows blank analysis page**
→ Make sure `NEXT_PUBLIC_API_MODE=real` in `frontend/.env.local`. In mock mode the analysis page returns empty data.

**`npm install` fails with ERESOLVE**
→ Delete `frontend/node_modules` and `frontend/package-lock.json`, then run `npm install` again. If it still fails, check that `package.json` has `"next": "15.3.2"` and `"eslint": "9.25.1"` — the old `^16.x` versions don't exist.

**CORS error in browser console**
```
Access-Control-Allow-Origin header missing
```
→ Add `http://localhost:3000` to `ALLOWED_ORIGINS` in `backend/.env` and restart the backend.

**ML models take 30+ seconds to load on first request**
→ Normal on first run — `sentence-transformers` downloads model weights (~400 MB). The backend pre-warms the service during startup so subsequent requests are fast.
