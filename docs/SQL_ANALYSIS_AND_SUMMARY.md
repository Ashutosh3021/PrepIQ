# PrepIQ - SQL Files Analysis & Summary

## 📊 SQL Files Overview

### File Locations

```
prepiq/
├── data/
│   ├── schema.sql          ✅ Recommended (Complete - 8 tables)
│   └── rls_policies.sql    ✅ Recommended (Security policies)
├── backend/scripts/
│   ├── 001_initial_schema.sql      ⚠️ Legacy (4 tables only)
│   ├── 002_add_prediction_accuracy_score.sql  (Migration)
│   └── 003_add_language_column.sql            (Migration)
└── supabase-migration.sql   (Combined schema + RLS)
```

---

## ✅ Recommended SQL Files

### 1. `data/schema.sql` - COMPLETE SCHEMA ⭐

**Contains:**
- **8 Tables** with proper relationships
- **25+ Indexes** for performance
- **Auto-update triggers** for timestamps
- **Vector extension** for ML embeddings
- **Proper data types** (UUID, JSONB, TIMESTAMP)

**Tables:**
1. `users` - User profiles and auth data
2. `subjects` - Courses/subjects
3. `question_papers` - PDF uploads
4. `questions` - Extracted questions
5. `predictions` - AI predictions
6. `mock_tests` - Practice tests
7. `chat_history` - AI chat logs
8. `study_plans` - Study schedules

**Status:** ✅ CORRECT - Use this for production

---

### 2. `data/rls_policies.sql` - SECURITY POLICIES ⭐

**Contains:**
- **RLS enabled** on all tables
- **30+ Policies** for data protection
- **User isolation** enforced
- **CRUD permissions** per user

**Security Features:**
- Users can only see their own data
- Automatic user_id injection
- Auth role checks
- Subquery-based access control

**Status:** ✅ CORRECT - Use this for production

---

## ⚠️ Legacy SQL Files

### 3. `backend/scripts/001_initial_schema.sql` - SIMPLIFIED

**Contains:**
- **4 Tables only** (profiles, subjects, study_materials, predictions)
- **Missing**: question_papers, questions, mock_tests, chat_history, study_plans
- **Different structure** than current app

**Status:** ⚠️ OUTDATED - Don't use for new deployments

---

## 🎯 Which SQL Files to Use?

### For Local Development:
```sql
-- Option A: Run separately (recommended)
1. Run data/schema.sql
2. Run data/rls_policies.sql

-- Option B: Use combined file
Run supabase-migration.sql
```

### For Production:
```sql
-- Always use the complete schema
Run data/schema.sql
Run data/rls_policies.sql
```

---

## 📋 Complete Setup Checklist

### Phase 1: Prerequisites (5 minutes)
- [ ] Git installed
- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] GitHub account created
- [ ] Supabase account created
- [ ] Google AI Studio account created

### Phase 2: Local Development Setup (30 minutes)

#### Step 1: Clone Repository (2 min)
```bash
git clone https://github.com/yourusername/prepiq.git
cd prepiq
```

#### Step 2: Database Setup (10 min)
1. Go to https://supabase.com
2. Create new project
3. Save database password
4. Open SQL Editor
5. Copy `data/schema.sql` contents
6. Paste and run
7. Copy `data/rls_policies.sql` contents
8. Paste and run
9. Verify 8 tables created in Database → Tables

#### Step 3: Backend Setup (10 min)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.production.example .env
# Edit .env with your values
python -m app.main
```

**Test:**
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok", ...}
```

#### Step 4: Frontend Setup (8 min)
```bash
cd frontend
npm install
cp .env.production.example .env.local
# Edit .env.local with your values
npm run dev
```

**Test:**
- Open http://localhost:3000
- Should see login page
- No console errors

#### Step 5: Test Complete Flow (5 min)
- [ ] Register new user
- [ ] Login works
- [ ] Create subject
- [ ] Upload small PDF
- [ ] Generate prediction

### Phase 3: Production Deployment (45 minutes)

#### Step 1: Prepare Production (10 min)
- [ ] Update backend/.env.production
- [ ] Update frontend/.env.production
- [ ] Test builds locally
- [ ] Commit all changes
- [ ] Push to GitHub

#### Step 2: Deploy Backend to Render (15 min)
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Select your repo
5. Configure:
   - Name: `prepiq-backend`
   - Environment: Python 3
   - Build: `cd backend && pip install -r requirements.txt`
   - Start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
6. Add environment variables from .env.production
7. Click "Create Web Service"
8. Wait for deployment
9. Note the URL: `https://prepiq-backend.onrender.com`
10. Test: `curl https://your-url.onrender.com/health`

#### Step 3: Deploy Frontend to Vercel (15 min)
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "Add New..." → "Project"
4. Select your repo
5. Configure:
   - Framework: Next.js
   - Root Directory: `frontend` ⚠️ Important!
6. Add environment variables:
   - `NEXT_PUBLIC_API_URL`: Your Render URL
   - `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your anon key
7. Click "Deploy"
8. Wait for build
9. Note the URL: `https://prepiq-xyz.vercel.app`

#### Step 4: Update CORS (5 min)
1. Go to Render Dashboard
2. Select your backend service
3. Environment tab
4. Update `ALLOWED_ORIGINS` to your Vercel URL
5. Save (auto-redeploys)

### Phase 4: Post-Deployment (15 minutes)

#### Step 1: Verify Everything Works
- [ ] Visit Vercel URL
- [ ] Register new user
- [ ] Login works
- [ ] Create subject
- [ ] Upload PDF
- [ ] Generate prediction
- [ ] No console errors

#### Step 2: Set Up Monitoring
1. Go to https://uptimerobot.com
2. Create free account
3. Add new monitor:
   - Type: HTTP(s)
   - URL: `https://your-backend.onrender.com/health`
   - Interval: 10 minutes
4. Save

#### Step 3: Documentation
- [ ] Save all URLs:
  - Frontend: https://prepiq-xyz.vercel.app
  - Backend: https://prepiq-backend.onrender.com
  - Supabase: https://app.supabase.com/project/...
- [ ] Save all credentials in password manager
- [ ] Document any custom changes

---

## 🚨 Common Issues & Solutions

### Issue 1: "Database connection failed"
**Cause:** Wrong connection string format
**Solution:** Use port 6543 (connection pooler), not 5432
```
postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:6543/postgres?pgbouncer=true
```

### Issue 2: "CORS error"
**Cause:** Frontend URL not in ALLOWED_ORIGINS
**Solution:** Update Render environment variable
```
ALLOWED_ORIGINS=https://your-app.vercel.app
```

### Issue 3: "RLS policy violation"
**Cause:** RLS policies not applied
**Solution:** Run `data/rls_policies.sql` in Supabase SQL Editor

### Issue 4: "Build failed on Vercel"
**Cause:** Root directory not set correctly
**Solution:** Set Root Directory to `frontend` in Vercel settings

### Issue 5: "Render sleeps after 15 minutes"
**Cause:** Free tier limitation
**Solution:** Set up UptimeRobot to ping /health every 10 minutes

---

## 📚 Files Reference

### Documentation Created:
1. `COMPLETE_SETUP_GUIDE.md` - Full step-by-step guide
2. `deploy.md` - Deployment guide with architecture
3. `LAUNCH_CHECKLIST.md` - Production launch checklist
4. `DATABASE_AUDIT_REPORT.md` - Database audit
5. `CODE_AUDIT_REPORT.md` - Security audit

### Configuration Files:
1. `backend/.env.production.example` - Backend env template
2. `frontend/.env.production.example` - Frontend env template
3. `Procfile` - Render process definition
4. `render.yaml` - Render blueprint
5. `frontend/vercel.json` - Vercel configuration
6. `frontend/next.config.js` - Next.js with security headers

### SQL Files:
1. `data/schema.sql` - Complete database schema
2. `data/rls_policies.sql` - Security policies
3. `supabase-migration.sql` - Combined schema + RLS

---

## 🎯 Quick Start Commands

### Local Development:
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python -m app.main

# Terminal 2 - Frontend
cd frontend
npm run dev

# Open http://localhost:3000
```

### Production URLs:
```
Frontend: https://prepiq-xyz.vercel.app
Backend:  https://prepiq-backend.onrender.com
Health:   https://prepiq-backend.onrender.com/health
Database: https://app.supabase.com/project/...
```

---

## ✅ Verification Checklist

Before considering setup complete, verify:

### Local Development:
- [ ] Backend starts without errors
- [ ] Health endpoint returns OK
- [ ] Frontend loads without console errors
- [ ] Can register new user
- [ ] Can login
- [ ] Can create subject
- [ ] Can upload PDF
- [ ] Can generate prediction

### Production:
- [ ] Backend deployed and healthy
- [ ] Frontend deployed and accessible
- [ ] CORS working (no cross-origin errors)
- [ ] Database connected
- [ ] Can register new user in production
- [ ] All features working end-to-end
- [ ] UptimeRobot monitoring active
- [ ] No sensitive data in logs

---

## 🎉 You're Ready!

Follow the `COMPLETE_SETUP_GUIDE.md` for detailed instructions with all commands and explanations.

**Estimated Total Time:**
- Local Setup: 30 minutes
- Production Deployment: 45 minutes
- Testing & Verification: 15 minutes
- **Total: ~1.5 hours**

**Monthly Cost:** $0 (Free tiers only!)

Good luck with your PrepIQ deployment! 🚀
