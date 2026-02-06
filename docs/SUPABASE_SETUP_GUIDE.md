# PrepIQ Supabase Setup Guide

## 🚀 Switching to Supabase-First Authentication

### Step 1: Create New Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign in or create account
3. Click "New Project"
4. Fill in:
   - **Project name:** PrepIQ
   - **Database password:** (create strong password)
   - **Region:** (closest to your users)
5. Click "Create Project" (wait 2-3 minutes)

### Step 2: Get Your Credentials

In your new Supabase project dashboard:

1. Go to **Project Settings** → **API**
2. Copy these values:
   - **Project URL** (starts with `https://`)
   - **Service Role Key** (long secret key)
   - **Anonymous Key** (another long key)

### Step 3: Update Environment Files

**Backend (.env):**
```bash
# Replace with your NEW Supabase credentials
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Keep these for local tokens (optional)
JWT_SECRET=your-jwt-secret-here
DATABASE_URL=sqlite:///./prepiq_local.db
```

**Frontend (.env.local):**
```bash
# Replace with your NEW Supabase credentials
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Keep this
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 4: Test the Connection

```bash
# Test backend connection
cd backend
python test_supabase_direct.py

# Should show: ✅ Supabase client created successfully
# Should show: ✅ Admin access working
```

### Step 5: Start Your Application

```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend (in new terminal)
cd frontend
npm run dev
```

### Step 6: Test Signup/Login

1. Go to `http://localhost:3000/signup`
2. Create a new account
3. Check Supabase dashboard:
   - Go to **Authentication** → **Users**
   - You should see your new user!

### 🎯 What's Different Now

**Before (Hybrid):**
- Users created in local database
- Attempted sync to Supabase (failed)
- Local SQLite as primary storage

**After (Supabase-First):**
- Users created directly in Supabase
- Supabase as single source of truth
- Local database only for non-auth data
- Real-time user management in dashboard

### 📋 Verification Checklist

- [ ] New Supabase project created
- [ ] Environment variables updated
- [ ] `test_supabase_direct.py` passes
- [ ] Backend starts without errors
- [ ] Signup creates user in Supabase dashboard
- [ ] Login works with Supabase tokens
- [ ] User profile data accessible

### 🆘 Troubleshooting

**If signup fails:**
1. Check Supabase credentials in .env files
2. Run `python test_supabase_direct.py` to verify connection
3. Check backend console for error messages

**If users don't appear in dashboard:**
1. Refresh the Supabase Authentication → Users page
2. Check "Show unconfirmed users" toggle
3. Verify your service key has admin permissions

**If login fails:**
1. Ensure user was created successfully
2. Check that email confirmation is disabled in Supabase settings
3. Verify password meets requirements (6+ characters)

### 🎉 Success!

Once everything works, you'll have:
- ✅ Users stored in Supabase
- ✅ Real-time dashboard monitoring
- ✅ Professional authentication system
- ✅ Scalable cloud infrastructure
- ✅ No more local database sync issues

Let me know when you've created your new Supabase project and updated the credentials - I'll help you test it!