# PrepIQ - Complete Setup & Deployment Guide

## 📋 Overview

This guide provides **complete step-by-step instructions** for:
1. Setting up the project locally for development
2. Deploying to production using free tiers

### SQL Files Analysis

The project has **3 main SQL files**:

1. **`data/schema.sql`** ✅ **RECOMMENDED** - Complete schema with 8 tables
   - Users, Subjects, Question Papers, Questions, Predictions, Mock Tests, Chat History, Study Plans
   - All indexes and triggers included
   - Uses vector extension for ML embeddings

2. **`data/rls_policies.sql`** ✅ **RECOMMENDED** - Complete RLS policies
   - Security policies for all tables
   - User isolation enforced

3. **`backend/scripts/001_initial_schema.sql`** ⚠️ **LEGACY** - Simplified schema
   - Only 4 tables (profiles, subjects, study_materials, predictions)
   - Missing many features
   - **Don't use for new deployments**

4. **`supabase-migration.sql`** (created) - Combined schema + RLS
   - Merges schema.sql + rls_policies.sql
   - Ready for production

**Recommendation**: Use `data/schema.sql` + `data/rls_policies.sql` separately, or use the combined `supabase-migration.sql`.

---

## 🚀 PART 1: LOCAL DEVELOPMENT SETUP

### Prerequisites

**Required Software:**
- Git
- Node.js 18+ 
- Python 3.11+
- PostgreSQL 14+ (or use Supabase locally)
- VS Code (recommended)

**Required Accounts:**
- GitHub
- Supabase (free tier)
- Google AI Studio (for Gemini API)

---

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/prepiq.git
cd prepiq

# Verify structure
ls -la
# Should see: backend/, frontend/, data/, README.md, etc.
```

---

### Step 2: Set Up Supabase (Database)

#### Option A: Use Supabase Cloud (Recommended for beginners)

1. **Create Supabase Account**
   ```bash
   # Go to https://supabase.com
   # Sign up with GitHub
   ```

2. **Create New Project**
   - Click "New Project"
   - Name: `prepiq-local` (or any name)
   - Database Password: Generate strong password (save it!)
   - Region: Choose closest to you
   - Wait 2-3 minutes for creation

3. **Get Connection Details**
   - Go to Project Settings → Database
   - Copy "Connection String" (port 5432 for direct, 6543 for pooler)
   - Save for later

4. **Run Database Schema**
   - Go to SQL Editor in Supabase Dashboard
   - Click "New Query"
   - Open `data/schema.sql` from your local project
   - Copy entire contents and paste into SQL Editor
   - Click "Run"
   - Should see: "Success. No rows returned"

5. **Run RLS Policies**
   - Create another "New Query"
   - Open `data/rls_policies.sql`
   - Copy entire contents and paste
   - Click "Run"
   - Should see: "Success. No rows returned"

6. **Verify Setup**
   - Go to Database → Tables
   - Should see 8 tables: users, subjects, question_papers, questions, predictions, mock_tests, chat_history, study_plans
   - Click on each table → Policies
   - Should see RLS policies enabled

#### Option B: Use Local PostgreSQL (Advanced)

```bash
# Install PostgreSQL (Mac)
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb prepiq_local

# Run schema
psql -d prepiq_local -f data/schema.sql
psql -d prepiq_local -f data/rls_policies.sql
```

---

### Step 3: Set Up Backend (FastAPI)

#### 3.1 Create Python Virtual Environment

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Verify activation
which python
# Should show: .../backend/venv/bin/python
```

#### 3.2 Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# This installs:
# - FastAPI, Uvicorn
# - SQLAlchemy, psycopg2-binary
# - Supabase client
# - PyPDF2, PyMuPDF
# - scikit-learn, numpy, pandas
# - And more...
```

#### 3.3 Create Environment File

```bash
# Copy example file
cp .env.production.example .env

# Edit .env file
nano .env  # or use VS Code: code .env
```

**Fill in these required values:**

```env
# Database (use Supabase connection pooler URL)
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[PROJECT_ID].supabase.co:6543/postgres?pgbouncer=true

# Supabase
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_SERVICE_KEY=eyJ...  # Service role key (from Supabase dashboard)

# Security (generate a secure key)
JWT_SECRET=your-generated-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS (for local development)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# AI (get from Google AI Studio)
GEMINI_API_KEY=AIza...

# App Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

**How to get each value:**

1. **DATABASE_URL**: 
   - Supabase Dashboard → Settings → Database
   - Copy "Connection Pooling" URL
   - Replace `[YOUR-PASSWORD]` with your actual password

2. **SUPABASE_URL**:
   - Supabase Dashboard → Settings → API
   - Copy "Project URL"

3. **SUPABASE_SERVICE_KEY**:
   - Supabase Dashboard → Settings → API
   - Copy "service_role secret"
   - ⚠️ Keep this secret! Never commit to git!

4. **JWT_SECRET**:
   ```bash
   # Generate secure key
   openssl rand -base64 32
   # Copy the output
   ```

5. **GEMINI_API_KEY**:
   - Go to https://makersuite.google.com/app/apikey
   - Create new API key
   - Copy the key

#### 3.4 Test Backend Startup

```bash
# Make sure you're in backend directory and venv is activated
pwd  # Should show: .../prepiq/backend
which python  # Should show venv path

# Start the backend
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
🚀 Starting PrepIQ Backend Application
Environment: development
Debug Mode: True
✅ Database connection verified
✅ All required environment variables are set
🌐 Starting server on 0.0.0.0:8000
📚 API Documentation: http://0.0.0.0:8000/docs
💓 Health Check: http://0.0.0.0:8000/health
```

#### 3.5 Test Backend Health

```bash
# In another terminal window
curl http://localhost:8000/health

# Expected response:
{
  "status": "ok",
  "timestamp": "2026-01-06T...",
  "version": "1.0.0",
  "environment": "development",
  "database": "connected"
}
```

**Troubleshooting:**
- If "Database connection failed": Check DATABASE_URL format
- If "Missing environment variables": Check .env file exists and all vars are set
- If port 8000 in use: Change port: `--port 8001`

---

### Step 4: Set Up Frontend (Next.js)

#### 4.1 Install Node Dependencies

```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install

# This will take 2-5 minutes
# Creates node_modules/ directory
```

#### 4.2 Create Environment File

```bash
# Copy example file
cp .env.production.example .env.local

# Edit .env.local
nano .env.local  # or code .env.local
```

**Fill in these values:**

```env
# Backend API URL (your local backend)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase (public values only)
NEXT_PUBLIC_SUPABASE_URL=https://[PROJECT_ID].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...  # Anon/public key

# App Info
NEXT_PUBLIC_APP_NAME=PrepIQ
NEXT_PUBLIC_APP_DESCRIPTION=AI-Powered Exam Preparation
```

**How to get values:**

1. **NEXT_PUBLIC_API_URL**: 
   - Use `http://localhost:8000` (backend URL)

2. **NEXT_PUBLIC_SUPABASE_URL**:
   - Same as backend (Project URL from Supabase)

3. **NEXT_PUBLIC_SUPABASE_ANON_KEY**:
   - Supabase Dashboard → Settings → API
   - Copy "anon public" key (NOT the service role key)
   - This key is safe to expose in frontend

#### 4.3 Test Frontend Build

```bash
# Test production build locally
npm run build

# Should complete without errors
# Creates .next/ directory
```

**Troubleshooting build errors:**
- TypeScript errors: Fix or set `ignoreBuildErrors: true` in next.config.js (temporary)
- Missing dependencies: Run `npm install` again

#### 4.4 Start Frontend Development Server

```bash
# Start development server
npm run dev

# Or specify port
npm run dev -- --port 3000
```

**Expected Output:**
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

#### 4.5 Verify Frontend

1. **Open browser**: http://localhost:3000
2. **Check for errors**:
   - Open browser console (F12)
   - Should see no red errors
3. **Test API connection**:
   - Try to register/login
   - Check Network tab for API calls
   - Should see requests to localhost:8000

---

### Step 5: Test Complete Flow Locally

#### 5.1 Test User Registration

1. Open http://localhost:3000/signup
2. Fill in registration form:
   - Email: test@example.com
   - Password: TestPassword123!
   - Full Name: Test User
   - College: Test College
   - Program: BTech
   - Year: 2
3. Submit form
4. Check Supabase Dashboard → Authentication → Users
   - Should see new user

#### 5.2 Test Login

1. Go to http://localhost:3000/login
2. Enter credentials
3. Should redirect to dashboard

#### 5.3 Test Subject Creation

1. Click "Add Subject"
2. Fill subject details:
   - Name: Linear Algebra
   - Code: MA101
   - Semester: 2
3. Save
4. Should appear in subjects list

#### 5.4 Test PDF Upload

1. Go to Upload page
2. Select small PDF file (< 5MB)
3. Upload
4. Should process and extract questions

**Troubleshooting:**
- Upload fails: Check backend logs for errors
- CORS error: Verify ALLOWED_ORIGINS includes http://localhost:3000
- Database error: Check RLS policies are applied

---

## 🚀 PART 2: PRODUCTION DEPLOYMENT

### Architecture

```
User → Vercel (Frontend) → Render (Backend) → Supabase (Database)
         Free Tier          Free Tier           Free Tier
```

---

### Step 1: Prepare for Production

#### 1.1 Update Environment Files

**Backend `.env.production`:**
```bash
cd backend
cp .env.production.example .env.production

# Edit with production values
nano .env.production
```

Key differences from local:
- `ENVIRONMENT=production`
- `DEBUG=false`
- `ALLOWED_ORIGINS=https://your-app.vercel.app` (will update after Vercel deploy)
- Same database and API keys

**Frontend `.env.production`:**
```bash
cd frontend
cp .env.production.example .env.production

# Edit
nano .env.production
```

Key values:
- `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com` (will update after Render deploy)

#### 1.2 Verify Build Works Locally

```bash
# Test backend production startup
cd backend
python -m app.main
# Should start without errors
# Press Ctrl+C to stop

# Test frontend build
cd frontend
npm run build
# Should complete successfully
```

#### 1.3 Commit All Changes

```bash
# From project root
cd ..

# Check git status
git status

# Add all changes
git add .

# Commit
git commit -m "Production ready: environment files and configurations"

# Push to GitHub
git push origin main
```

---

### Step 2: Deploy Backend to Render

#### 2.1 Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Complete onboarding

#### 2.2 Create New Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select the `prepiq` repo
4. Click "Connect"

#### 2.3 Configure Service

**Basic Settings:**
- **Name**: `prepiq-backend` (or your choice)
- **Environment**: Python 3
- **Region**: Oregon (or closest to you)
- **Branch**: main

**Build Command:**
```bash
cd backend && pip install -r requirements.txt
```

**Start Command:**
```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

**Plan**: Free

#### 2.4 Add Environment Variables

Click "Advanced" → Add the following:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Supabase connection pooler URL |
| `SUPABASE_URL` | https://[PROJECT].supabase.co |
| `SUPABASE_SERVICE_KEY` | Your service_role key |
| `JWT_SECRET` | Generated secret (openssl rand -base64 32) |
| `JWT_ALGORITHM` | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 |
| `ALLOWED_ORIGINS` | Temporary: `https://prepiq.vercel.app` |
| `GEMINI_API_KEY` | Your Google AI key |
| `ENVIRONMENT` | production |
| `DEBUG` | false |
| `LOG_LEVEL` | INFO |
| `PYTHON_VERSION` | 3.11.0 |

**⚠️ Important:**
- Use the **Connection Pooler** URL (port 6543)
- Format: `postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:6543/postgres?pgbouncer=true`
- For `ALLOWED_ORIGINS`, use your expected Vercel URL or update after Vercel deploy

#### 2.5 Deploy

1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Check logs for "✅ Database connection verified"
4. Note the URL: `https://prepiq-backend.onrender.com`

#### 2.6 Test Backend

```bash
# Test health endpoint
curl https://prepiq-backend.onrender.com/health

# Expected:
{
  "status": "ok",
  "timestamp": "...",
  "database": "connected"
}
```

---

### Step 3: Deploy Frontend to Vercel

#### 3.1 Create Vercel Account

1. Go to https://vercel.com
2. Sign up with GitHub
3. Complete onboarding

#### 3.2 Import Project

1. Click "Add New..." → "Project"
2. Import from GitHub
3. Select `prepiq` repository
4. Click "Import"

#### 3.3 Configure Project

**Framework Preset**: Next.js

**Root Directory**: `frontend` ⚠️ **IMPORTANT!**

**Build Command**: (leave default)
```
next build
```

**Output Directory**: (leave default)
```
.next
```

#### 3.4 Add Environment Variables

Click "Environment Variables" and add:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://prepiq-backend.onrender.com` (your Render URL) |
| `NEXT_PUBLIC_SUPABASE_URL` | https://[PROJECT].supabase.co |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your anon/public key |
| `NEXT_PUBLIC_APP_NAME` | PrepIQ |
| `NEXT_PUBLIC_APP_DESCRIPTION` | AI-Powered Exam Preparation |

#### 3.5 Deploy

1. Click "Deploy"
2. Wait for build (3-5 minutes)
3. Note the URL: `https://prepiq-xyz.vercel.app`

#### 3.6 Update Backend CORS

1. Go back to Render Dashboard
2. Select your backend service
3. Go to "Environment" tab
4. Update `ALLOWED_ORIGINS`:
   ```
   https://prepiq-xyz.vercel.app
   ```
5. Save changes (auto-redeploys)

---

### Step 4: Post-Deployment Verification

#### 4.1 Test Complete Flow

1. **Visit Frontend**: https://prepiq-xyz.vercel.app
2. **Register New User**:
   - Fill signup form
   - Check Supabase Dashboard → Users (should appear)
3. **Login**: Should work and redirect to dashboard
4. **Create Subject**: Should save to database
5. **Upload PDF**: Test with small file
6. **Generate Prediction**: Test AI features

#### 4.2 Check Browser Console

- Open DevTools (F12)
- Check Console tab
- Should have NO red errors
- Check Network tab
- API calls should show 200 status

#### 4.3 Monitor Logs

**Render Logs:**
- Dashboard → Your Service → Logs
- Check for errors

**Vercel Logs:**
- Dashboard → Your Project → View Logs
- Check for build errors

**Supabase Logs:**
- Dashboard → Logs (if available on free tier)

---

### Step 5: Keep Render Awake (Free Tier)

Render free tier spins down after 15 minutes of inactivity.

#### 5.1 Set Up UptimeRobot

1. Go to https://uptimerobot.com
2. Create free account
3. Click "Add New Monitor"
4. Configure:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: PrepIQ Backend
   - **URL**: `https://prepiq-backend.onrender.com/health`
   - **Monitoring Interval**: 10 minutes (free tier max)
5. Click "Create Monitor"

This pings your backend every 10 minutes, keeping it awake!

---

## 🔧 TROUBLESHOOTING

### Backend Issues

#### "Database connection failed"
- Check DATABASE_URL format
- Use port 6543 (connection pooler), not 5432
- Verify password is URL-encoded if contains special chars
- Check Supabase project is active

#### "Missing environment variables"
- Check .env file exists
- Verify all required vars are set
- No quotes around values in production

#### "CORS error"
- Verify ALLOWED_ORIGINS includes frontend URL
- No trailing slashes
- Format: `https://app.vercel.app,https://www.domain.com`

### Frontend Issues

#### "Build failed"
- Check for TypeScript errors
- Run `npm run build` locally first
- Check Vercel build logs

#### "API calls failing"
- Check browser console for CORS errors
- Verify NEXT_PUBLIC_API_URL is correct
- Check backend is running (Render dashboard)

#### "Cannot connect to backend"
- Verify Render service is "Live"
- Check UptimeRobot is pinging it
- Test health endpoint directly

### Database Issues

#### "RLS policy violation"
- Check RLS policies are applied
- Verify auth.uid() is being set correctly
- Check service_role vs anon key usage

#### "Table does not exist"
- Run schema.sql in Supabase SQL Editor
- Check migration completed successfully
- Verify connected to correct database

---

## 📊 MONITORING & MAINTENANCE

### Free Tier Limits

**Render:**
- 750 hours/month (always free with UptimeRobot)
- 512 MB RAM
- 1 worker
- Sleeps after 15 min (use UptimeRobot)

**Vercel:**
- 100 GB bandwidth/month
- 6,000 build minutes/month
- Unlimited deployments

**Supabase:**
- 500 MB database
- 1 GB file storage
- 2 GB bandwidth/month
- 50,000 monthly active users

### Weekly Checks

```bash
# Check Render status
open https://dashboard.render.com

# Check Vercel analytics
open https://vercel.com/dashboard

# Check Supabase usage
open https://app.supabase.com/project/_/settings/usage
```

### Monthly Maintenance

1. Review error logs
2. Check resource usage
3. Update dependencies:
   ```bash
   # Backend
   cd backend
   pip list --outdated
   pip install -U package_name
   
   # Frontend
   cd frontend
   npm outdated
   npm update
   ```
4. Backup database (Supabase dashboard)

---

## 🎉 SUCCESS!

You now have:
- ✅ Local development environment working
- ✅ Production deployment on free tiers
- ✅ Database with proper security (RLS)
- ✅ Backend API with health checks
- ✅ Frontend with security headers
- ✅ Monitoring with UptimeRobot

**Your PrepIQ app is live and ready to use!**

---

## 📞 SUPPORT

**Documentation:**
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs
- Supabase: https://supabase.com/docs
- FastAPI: https://fastapi.tiangolo.com
- Next.js: https://nextjs.org/docs

**Community:**
- Render Discord: https://discord.gg/render
- Vercel Discord: https://vercel.com/discord
- Supabase Discord: https://discord.supabase.com

---

*Last Updated: January 2026*
