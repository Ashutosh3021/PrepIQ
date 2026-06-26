# PrepIQ Deployment Guide

## Architecture

| Service | Platform | Free Tier Limits |
|---------|----------|-----------------|
| Backend (FastAPI) | Render Web Service | 512MB RAM, spins down after 15 min inactivity |
| Database (PostgreSQL) | Render Postgres OR Supabase | 1GB (Render) / 500MB (Supabase) |
| Frontend (Next.js) | Vercel | 100GB bandwidth / month |
| Auth | Supabase | 50,000 MAU |

## Pre-Deployment Checklist

- [ ] Supabase project created, all migrations in `scripts/` run in order
- [ ] Google OAuth and GitHub OAuth configured in Supabase Auth dashboard
- [ ] Gemini API key obtained from Google AI Studio
- [ ] Bytez API key obtained (optional — fallback to ML-only if absent)
- [ ] Vercel project created and linked to repo
- [ ] Render account created

---

## Step-by-Step: Backend on Render

### 1. Connect GitHub repo to Render

Go to [render.com](https://render.com) → **New +** → **Web Service** → **Connect a repository**.
Authorise Render to access your GitHub account and select the PrepIQ repo.

### 2. Create Web Service — settings

| Field | Value |
|-------|-------|
| **Name** | `prepiq-backend` |
| **Runtime** | Python 3 |
| **Root Directory** | _(leave blank — render.yaml is at repo root)_ |
| **Build Command** | `pip install -r backend/requirements.txt` |
| **Start Command** | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| **Instance Type** | Free |
| **Health Check Path** | `/health` |

> Render will auto-detect `render.yaml` if it is at the repo root; the settings above are already encoded there.

### 3. Set environment variables

In the Render dashboard → your service → **Environment**, add each variable:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (Supabase pooler URL or Render Postgres internal URL) |
| `SUPABASE_URL` | Your Supabase project URL, e.g. `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (Settings → API → `service_role`) |
| `GEMINI_API_KEY` | Google Gemini API key from [Google AI Studio](https://aistudio.google.com/) |
| `JWT_SECRET` | Random 32-byte base64 string: `openssl rand -base64 32` |
| `BYTEZ_API_KEY` | Bytez API key (optional — predictions fall back to Gemini-only if absent) |
| `ALLOWED_ORIGINS` | Comma-separated list, e.g. `https://prepiq.vercel.app,https://your-domain.com` |
| `ENVIRONMENT` | `production` (already set in render.yaml) |
| `PYTHONUNBUFFERED` | `1` (already set in render.yaml) |

### 4. Deploy and verify /health

Click **Manual Deploy** → **Deploy latest commit**.  
Watch the build log — a successful deploy ends with:

```
INFO:     Application startup complete.
```

Once deployed, confirm the health endpoint responds:

```
curl https://your-prepiq-backend.onrender.com/health
# Expected: {"status":"ok","service":"prepiq-backend"}
```

### 5. Note the backend URL

Copy the URL shown at the top of the Render service page, e.g.:

```
https://prepiq-backend.onrender.com
```

You will need this for the frontend environment variable `NEXT_PUBLIC_API_URL`.

---

## Step-by-Step: Frontend on Vercel

### 1. Import repo in Vercel

Go to [vercel.com](https://vercel.com) → **Add New** → **Project** → import the PrepIQ repository.

### 2. Set root directory

In the project configuration screen, set **Root Directory** to `frontend/`.

### 3. Set environment variables

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-prepiq-backend.onrender.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/public key (Settings → API → `anon public`) |

### 4. Deploy

Click **Deploy**.  Vercel builds and deploys the Next.js app automatically.  
Subsequent pushes to `main` trigger a new deployment.

---

## Step-by-Step: Database Migrations

All migrations live in `scripts/` and must be run in numerical order using the **Supabase SQL Editor** (Dashboard → SQL Editor → New query).

| Order | File | Notes |
|-------|------|-------|
| 1 | `scripts/001_*.sql` | Base schema — users, subjects, papers |
| 2 | `scripts/002_*.sql` | Questions and question papers |
| 3 | `scripts/003_*.sql` | Predictions and ML results |
| 4 | `scripts/004_*.sql` | Mock tests and study plans |
| 5 | `scripts/005_*.sql` | Dashboard and analysis tables |
| 6 | `scripts/006_*.sql` | Renames `difficulty_level` → `difficulty` on the questions table |

> **Important:** Script 006 renames the `difficulty_level` column to `difficulty`. Run it only once. If you re-run it on a database where the rename already happened, it will error — that is safe to ignore.

Run each script individually, in order, and confirm "Success" before proceeding to the next.

---

## Cold Start Behaviour

Render's free tier spins down a web service after **15 minutes of inactivity**.  
The first request after a spin-down triggers a cold start, which takes approximately **30 seconds** while the Python process boots and imports load.

**What this means for users:** The first page load after inactivity will be slow. Subsequent requests are fast.

**Frontend handling:** The frontend already shows a loading state for all API calls. No additional change is required — the long first-request delay is expected behaviour, not a bug.

If you need to reduce cold-start impact, consider pinging `/health` from an external uptime monitor (e.g. UptimeRobot free tier) every 10–14 minutes. Note that Render's Terms of Service prohibit automated pinging *solely* to circumvent the spin-down; use genuine uptime monitoring with alerting.

---

## RAM Budget (512MB)

| Component | Estimated RAM |
|-----------|--------------|
| FastAPI base + uvicorn | ~80MB |
| LightweightQuestionAnalyzer (production mode) | ~120MB |
| Gemini API client | ~20MB |
| EasyOCR (lazy, loaded only during PDF parse) | ~150MB peak |
| Headroom | ~140MB |
| **Total peak** | **~370MB — within 512MB limit** |

> The `USE_LIGHTWEIGHT_MODELS` flag is automatically `True` when `ENVIRONMENT=production`, which selects the sklearn-based `QuestionAnalyzer` over the full `EnhancedQuestionAnalyzer` (which loads sentence-transformers + BERTopic and can consume 300–400MB on its own).
>
> EasyOCR is lazy-loaded inside `process_image_pipeline()` and only consumes RAM when a PDF with image-only pages is uploaded.  For text-based PDFs, it is never loaded.

---

## Troubleshooting

**Deploy fails: `ModuleNotFoundError: No module named 'X'`**  
The package `X` is missing from `backend/requirements.txt`. Add it with a pinned version and redeploy.

**Service crashes on start: `RuntimeError: Cannot start in production with missing environment variables`**  
One or more required env vars (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`, `JWT_SECRET`, `ALLOWED_ORIGINS`) are not set in the Render dashboard. Go to Environment → add the missing variable → Manual Deploy.

**Predictions return empty / `{"predictions": []}`**  
The Gemini API key is invalid, has expired, or the project has exceeded its free quota. Verify the key in Google AI Studio and check quota usage. The backend will log `"Gemini API connection failed"` on startup if the key is wrong.

**PDF upload completes but no questions are extracted**  
EasyOCR's first load takes 15–20 seconds while it downloads model weights. The upload request may time out on the first attempt. Retry the upload once — subsequent attempts will be fast because the weights are cached in the container's memory for the lifetime of the process.

**Service OOM-killed (exit code 137) / out of memory**  
The full CUDA `torch` package is installed instead of the CPU-only variant. On Render free tier, CUDA torch adds ~700MB just for the library, instantly exceeding the 512MB limit. Confirm that `requirements.txt` contains `torch==2.2.2+cpu` (with `+cpu` suffix) and that no other package is pulling in full torch as a dependency. Redeploy after fixing.

**`/health` returns 503 (database disconnected)**  
The lightweight `/health` endpoint never hits the DB and should always return 200. If you are hitting `/health/full`, the `DATABASE_URL` is likely wrong or the Supabase connection pooler is at capacity. Check the Supabase dashboard → Database → Connection Pooling.

---

## Keeping the Free Tier Alive

- **Render Postgres expires in 90 days.** Before the expiry date, export your data (`pg_dump`) and migrate to Supabase's hosted PostgreSQL (free tier, no expiry on the managed plan) or upgrade your Render database to a paid tier.
- **Monitor usage:** Render dashboard → your service → **Metrics** shows CPU, RAM, and request counts. If RAM consistently approaches 512MB, consider disabling `sentence-transformers` in `requirements.txt` (it is only used by `EnhancedQuestionAnalyzer`, which is already bypassed in production via `USE_LIGHTWEIGHT_MODELS=True`).
- **Instance hours:** Render's free tier provides 750 instance hours/month across all services. With one backend service this equates to roughly the full month, but spin-down helps stretch the budget. If you add a second web service (e.g. a separate worker), hours are shared — monitor via Dashboard → Settings → Usage.
- **If instance hours run low:** Pause any non-essential Render services (e.g. background workers, staging environments) from the dashboard to stop consuming hours until the monthly counter resets.
