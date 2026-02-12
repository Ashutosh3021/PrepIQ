# PrepIQ — Production Deployment Guide

Complete deployment guide for deploying PrepIQ to production using free tiers.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Vercel Free Tier)                                    │
│  • Next.js 14 + TypeScript                                      │
│  • Auto-deploy from GitHub                                      │
│  • Global CDN                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  URL: https://your-app.vercel.app                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │ API Calls
                      │ NEXT_PUBLIC_API_URL
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND (Render Free Tier)                                     │
│  • FastAPI + Python                                             │
│  • Auto-deploy from GitHub                                      │
│  • Health checks enabled                                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  URL: https://your-api.onrender.com                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Database Connection
                      │ SQLAlchemy + Connection Pooler
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  DATABASE (Supabase Free Tier)                                  │
│  • PostgreSQL 14                                                │
│  • Row Level Security (RLS)                                     │
│  • Built-in Auth                                                │
│  • Connection Pooler (PgBouncer)                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Host: [project].supabase.co:6543 (pooler)                      │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

### Required Accounts (All Free)
1. **GitHub** - Repository hosting
2. **Vercel** - Frontend deployment (vercel.com)
3. **Render** - Backend deployment (render.com)
4. **Supabase** - Database and auth (supabase.com)
5. **Google AI Studio** - Gemini API key (makersuite.google.com)

### Required Tools
- Git
- Node.js 18+ (for local testing)
- Python 3.11+ (for local testing)
- PostgreSQL client (optional, for database debugging)

---

## Step 1: Supabase Setup (Database & Auth)

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Fill in:
   - **Name:** prepiq-prod
   - **Database Password:** Generate a strong password (save this!)
   - **Region:** Choose closest to your users (e.g., US East)
4. Wait for project creation (~2 minutes)

### 1.2 Get Connection Strings

1. Go to **Project Settings** → **Database**
2. Copy the **Connection Pooling** URL:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:6543/postgres?pgbouncer=true
   ```
3. Save this for later - it's your `DATABASE_URL`

### 1.3 Get API Keys

1. Go to **Project Settings** → **API**
2. Copy:
   - **Project URL** (for `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL`)
   - **anon public** key (for `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
   - **service_role secret** key (for `SUPABASE_SERVICE_KEY`)

### 1.4 Run Database Migration

1. Go to **SQL Editor** in Supabase Dashboard
2. Click "New Query"
3. Copy and paste the entire contents of `supabase-migration.sql`
4. Click "Run"
5. You should see: `✅ PrepIQ database schema created successfully!`

### 1.5 Configure Auth Providers

1. Go to **Authentication** → **Providers**
2. Enable **Email** provider
3. Configure settings:
   - Confirm email: Enabled (recommended for production)
   - Secure email change: Enabled
   - Double confirm email changes: Enabled
4. (Optional) Enable Google OAuth:
   - Create credentials at [Google Cloud Console](https://console.cloud.google.com)
   - Add Client ID and Secret to Supabase
   - Add authorized redirect URL: `https://[project].supabase.co/auth/v1/callback`

### 1.6 Configure RLS Policies (Already Done!)

✅ The migration script already created all RLS policies. Verify by going to:
- **Database** → **Tables** → Each table → **Policies**

You should see policies like:
- "Users can view own profile"
- "Users can manage own subjects"
- etc.

---

## Step 2: Deploy Backend to Render

### 2.1 Prepare Your Repository

Ensure your repo has:
```
/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── ...
├── Procfile (in root)
├── render.yaml (in root)
└── ...
```

### 2.2 Create Render Account

1. Go to [render.com](https://render.com) and sign up
2. Connect your GitHub account
3. Click "New Web Service"

### 2.3 Configure Backend Service

1. **Connect Repository**
   - Select your GitHub repo
   - Branch: `main` (or your default)

2. **Configure Service**
   - **Name:** prepiq-backend
   - **Environment:** Python 3
   - **Region:** Oregon (or closest to your users)
   - **Branch:** main
   - **Root Directory:** (leave blank for root)
   - **Build Command:** 
     ```bash
     cd backend && pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
     ```

3. **Select Plan:** Free

### 2.4 Set Environment Variables

In Render dashboard, go to **Environment** and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | `postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:6543/postgres?pgbouncer=true` | Supabase connection pooler |
| `SUPABASE_URL` | `https://[PROJECT].supabase.co` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | `eyJ...` | Service role key (secret!) |
| `JWT_SECRET` | Generate with `openssl rand -base64 32` | JWT signing key |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expiration (24h) |
| `ALLOWED_ORIGINS` | `https://prepiq.vercel.app` | Your frontend URL(s) |
| `GEMINI_API_KEY` | `AIza...` | Google Gemini API key |
| `ENVIRONMENT` | `production` | Environment name |
| `DEBUG` | `false` | Debug mode off |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_FILE_SIZE` | `10485760` | 10MB upload limit |
| `PYTHON_VERSION` | `3.11.0` | Python version |

### 2.5 Configure Health Check

Render will automatically use the `/health` endpoint. Verify it's working:
1. After deployment, visit: `https://your-backend.onrender.com/health`
2. Should return:
   ```json
   {
     "status": "ok",
     "timestamp": "2026-01-06T...",
     "version": "1.0.0",
     "database": "connected"
   }
   ```

### 2.6 Test Backend Deployment

```bash
# Test health endpoint
curl https://your-backend.onrender.com/health

# Test API docs (if DEBUG=true)
curl https://your-backend.onrender.com/docs

# Test auth endpoint (should require auth)
curl https://your-backend.onrender.com/auth/profile
# Expected: 401 Unauthorized
```

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Account

1. Go to [vercel.com](https://vercel.com) and sign up
2. Connect your GitHub account

### 3.2 Import Project

1. Click "Add New Project"
2. Import from GitHub
3. Select your repository

### 3.3 Configure Build Settings

**Framework Preset:** Next.js

**Root Directory:** `frontend` (important!)

**Build Command:** (default should work)
```bash
next build
```

**Output Directory:** (default should work)
```
.next
```

### 3.4 Set Environment Variables

Go to **Settings** → **Environment Variables** and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com` | Your Render backend URL |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://[PROJECT].supabase.co` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | Supabase anon key |
| `NEXT_PUBLIC_APP_NAME` | `PrepIQ` | App name |
| `NEXT_PUBLIC_APP_DESCRIPTION` | `AI-Powered Exam Preparation` | App description |

### 3.5 Deploy

1. Click "Deploy"
2. Wait for build (~2-3 minutes)
3. Vercel will provide a URL like `https://prepiq-xyz.vercel.app`

### 3.6 Update CORS in Backend

Go back to Render dashboard and update `ALLOWED_ORIGINS`:
```
https://prepiq-xyz.vercel.app
```

If you have a custom domain:
```
https://prepiq-xyz.vercel.app,https://www.yourdomain.com
```

---

## Step 4: Post-Deployment Verification

### 4.1 Backend Health Check

```bash
# Test all endpoints
curl https://your-backend.onrender.com/health

# Test CORS (should succeed)
curl -H "Origin: https://your-frontend.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://your-backend.onrender.com/auth/login
```

### 4.2 Frontend Verification

1. Visit your Vercel URL
2. Verify page loads without errors
3. Check browser console for errors
4. Test signup flow
5. Test login flow
6. Test creating a subject
7. Test uploading a paper (small PDF < 5MB)

### 4.3 End-to-End Test

```bash
# Test full flow
curl -X POST https://your-backend.onrender.com/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User",
    "college_name": "Test College",
    "program": "BTech",
    "year_of_study": 2
  }'
```

### 4.4 Security Headers Verification

```bash
# Check security headers
curl -I https://your-frontend.vercel.app

# Should see:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=...
```

---

## Step 5: Keeping It Free

### Render Free Tier Limits

| Limit | Value | Strategy |
|-------|-------|----------|
| **Sleep** | After 15 min idle | Use UptimeRobot to ping every 10 min |
| **Bandwidth** | 100GB/month | Monitor in Render dashboard |
| **Build** | 500 minutes/month | Optimize builds, cache dependencies |
| **Disk** | 1GB | Clean up old uploads |

**Keep Render Awake:**
1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-backend.onrender.com/health`
   - Interval: 10 minutes
3. This keeps your backend warm (costs: $0)

### Supabase Free Tier Limits

| Limit | Value | Strategy |
|-------|-------|----------|
| **Database** | 500MB | Archive old predictions, clean up uploads |
| **Storage** | 1GB | Delete old PDFs, use compression |
| **Bandwidth** | 2GB/month | Monitor usage |
| **Auth** | 50,000 MAU | Should be plenty |
| **API** | 100k requests/day | Monitor if high traffic |

**Monitor Usage:**
- Supabase Dashboard → Usage → Check daily

### Vercel Free Tier Limits

| Limit | Value | Strategy |
|-------|-------|----------|
| **Bandwidth** | 100GB/month | Use image optimization |
| **Build** | 6,000 minutes/month | Optimize builds |
| **Functions** | 125k requests/day | API routes count |
| **Storage** | 1GB | Keep dependencies minimal |

**Optimize:**
- Use Next.js Image component (but we disabled for static export)
- Minimize bundle size
- Use `next/dynamic` for heavy components

### Free Monitoring Stack

| Service | Use | Cost |
|---------|-----|------|
| **UptimeRobot** | Keep Render awake + uptime monitoring | Free |
| **Sentry** | Error tracking (10k events/month) | Free |
| **Google Analytics** | User analytics | Free |
| **Vercel Analytics** | Web vitals (included) | Free |

---

## Environment Variables Reference

### Backend (Render)

| Variable | Service | Required | Example |
|----------|---------|----------|---------|
| `DATABASE_URL` | Supabase | ✅ | `postgresql://postgres:pass@db...supabase.co:6543/postgres?pgbouncer=true` |
| `SUPABASE_URL` | Supabase | ✅ | `https://abc123.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase | ✅ | `eyJhbGciOiJIUzI1NiIs...` |
| `JWT_SECRET` | App | ✅ | Generate with `openssl rand -base64 32` |
| `JWT_ALGORITHM` | App | ✅ | `HS256` |
| `ALLOWED_ORIGINS` | App | ✅ | `https://prepiq.vercel.app` |
| `GEMINI_API_KEY` | Google | ✅ | `AIzaSyDUo2sn081eoEO4w1TORwsbBdM8l592KhY` |
| `ENVIRONMENT` | App | ❌ | `production` |
| `DEBUG` | App | ❌ | `false` |
| `LOG_LEVEL` | App | ❌ | `INFO` |
| `MAX_FILE_SIZE` | App | ❌ | `10485760` |
| `PORT` | Render | Auto | `10000` |

### Frontend (Vercel)

| Variable | Service | Required | Example |
|----------|---------|----------|---------|
| `NEXT_PUBLIC_API_URL` | Render | ✅ | `https://prepiq-api.onrender.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase | ✅ | `https://abc123.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase | ✅ | `eyJhbGciOiJIUzI1NiIs...` |
| `NEXT_PUBLIC_APP_NAME` | App | ❌ | `PrepIQ` |
| `NEXT_PUBLIC_APP_DESCRIPTION` | App | ❌ | `AI-Powered Exam Preparation` |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | App | ❌ | `false` |

---

## Common Issues & Fixes

### Issue 1: "CORS Error" in Browser

**Symptom:** Frontend can't connect to backend

**Fix:**
1. Check `ALLOWED_ORIGINS` in Render includes your Vercel URL
2. Format: comma-separated, no spaces
3. Example: `https://prepiq.vercel.app,https://www.prepiq.com`
4. Restart Render service after updating

### Issue 2: "Database Connection Failed"

**Symptom:** Backend health check fails

**Fix:**
1. Verify `DATABASE_URL` uses port **6543** (connection pooler)
2. Check password is URL-encoded (special characters)
3. Verify Supabase project is active (not paused)
4. Test locally with same connection string

### Issue 3: "File Upload Fails"

**Symptom:** PDF uploads don't work

**Fix:**
1. Check `MAX_FILE_SIZE` (10MB = 10485760 bytes)
2. Verify file is actually PDF (not just .pdf extension)
3. Check Render disk is not full (1GB limit)
4. Review upload logs in Render dashboard

### Issue 4: "Auth Not Working"

**Symptom:** Can't login/signup

**Fix:**
1. Verify `SUPABASE_SERVICE_KEY` is correct (not anon key)
2. Check `JWT_SECRET` is set and consistent
3. Verify Supabase Auth is enabled (Email provider)
4. Check RLS policies are applied correctly

### Issue 5: "Render Sleeps Too Fast"

**Symptom:** First request is slow (cold start)

**Fix:**
1. Set up UptimeRobot pinger (see Step 5)
2. Ping interval: 10 minutes
3. URL: `https://your-backend.onrender.com/health`

### Issue 6: "Build Fails on Vercel"

**Symptom:** Deployment fails during build

**Fix:**
1. Check `Root Directory` is set to `frontend`
2. Verify `package.json` exists in frontend folder
3. Check build logs for TypeScript errors
4. Try building locally first: `cd frontend && npm run build`

---

## Custom Domain Setup (Optional)

### Vercel Custom Domain

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain
3. Follow DNS configuration instructions
4. Update `ALLOWED_ORIGINS` in Render

### Render Custom Domain

1. Go to Render Dashboard → Your Service → Settings → Custom Domains
2. Add your domain
3. Follow DNS configuration
4. Update `NEXT_PUBLIC_API_URL` in Vercel

---

## Monitoring & Logs

### View Logs

**Render:**
- Dashboard → Your Service → Logs
- Shows stdout/stderr in real-time
- Searchable history

**Vercel:**
- Dashboard → Your Project → Logs
- Function logs for API routes
- Build logs

**Supabase:**
- Dashboard → Logs (requires paid tier for history)
- Real-time logs available

### Health Monitoring

**Check backend health:**
```bash
watch -n 60 curl -s https://your-backend.onrender.com/health
```

**Monitor uptime:**
- UptimeRobot dashboard
- Render status page

---

## Updating Production

### Backend Updates

1. Push code to GitHub
2. Render auto-deploys (if auto-deploy enabled)
3. Or manually deploy from Render dashboard
4. Monitor logs for errors

### Frontend Updates

1. Push code to GitHub
2. Vercel auto-deploys
3. Preview deployment available for PRs
4. Production deployment on merge to main

### Database Migrations

**For schema changes:**
1. Test migration locally first
2. Backup database (Supabase dashboard)
3. Run migration in Supabase SQL Editor
4. Verify application still works
5. Monitor for errors

---

## Backup & Recovery

### Database Backup

**Supabase:**
1. Dashboard → Database → Backups
2. Download SQL dump
3. Or use Supabase CLI for automated backups

**Automated Backup Script:**
```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Backup
supabase db dump -f backup.sql
```

### Recovery

1. Create new Supabase project
2. Run `supabase-migration.sql`
3. Restore data from backup
4. Update all connection strings
5. Redeploy backend
6. Test everything

---

## Launch Checklist

### Pre-Launch

- [ ] All environment variables set in production
- [ ] Database migration executed successfully
- [ ] RLS policies verified in Supabase
- [ ] Backend deployed and health check passing
- [ ] Frontend deployed and loading without errors
- [ ] CORS configured correctly
- [ ] File upload size limits set appropriately
- [ ] Security headers verified
- [ ] No console errors in production build

### Launch Day

- [ ] Test user registration flow
- [ ] Test login flow
- [ ] Test subject creation
- [ ] Test PDF upload (small file first)
- [ ] Test prediction generation
- [ ] Test chat functionality
- [ ] Verify mobile responsiveness
- [ ] Check all security headers
- [ ] Monitor error logs

### Post-Launch

- [ ] Set up UptimeRobot pinger (keep Render awake)
- [ ] Configure Sentry for error tracking
- [ ] Add Google Analytics
- [ ] Create monitoring dashboard
- [ ] Document any issues
- [ ] Schedule weekly log reviews
- [ ] Set up alerts for high error rates

---

## Support & Resources

### Documentation
- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Next.js Docs](https://nextjs.org/docs)

### Community
- [Render Community](https://community.render.com)
- [Vercel Discord](https://vercel.com/discord)
- [Supabase Discord](https://discord.supabase.com)

### Emergency Contacts
- Render Status: [status.render.com](https://status.render.com)
- Vercel Status: [vercel-status.com](https://www.vercel-status.com)
- Supabase Status: [status.supabase.com](https://status.supabase.com)

---

## Conclusion

You now have a fully production-ready PrepIQ deployment using free tiers!

**Estimated Monthly Cost:** $0

**What You're Getting:**
- ✅ Global CDN via Vercel
- ✅ Auto-scaling backend via Render
- ✅ Production PostgreSQL via Supabase
- ✅ Built-in authentication
- ✅ Row-level security
- ✅ Automatic deployments
- ✅ Free SSL certificates
- ✅ DDoS protection

**Remember:**
- Monitor your usage to stay within free tier limits
- Set up UptimeRobot to keep Render awake
- Keep secrets in environment variables only
- Test thoroughly before major updates
- Back up your database regularly

🎉 **Happy Deploying!**
