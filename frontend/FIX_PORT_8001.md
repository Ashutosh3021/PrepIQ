# Fix: Frontend Connecting to Port 8001 Instead of 8000

## Quick Fix

Your frontend is trying to connect to port **8001**, but your backend runs on port **8000**. Here's how to fix it:

### Option 1: Run the Fix Script (Recommended)

```powershell
cd frontend
node fix-api-url.js
```

This script will automatically:
- Check your `.env.local` file
- Fix any port 8001 references to 8000
- Create `.env.local` if it doesn't exist

### Option 2: Manual Fix

1. **Create or edit `.env.local` in the `frontend` directory:**

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

2. **Make sure it says `8000`, NOT `8001`**

3. **Restart your Next.js dev server:**
   ```powershell
   # Stop the server (Ctrl+C)
   # Then restart:
   npm run dev
   # or
   pnpm dev
   ```

### Option 3: Delete and Recreate .env.local

If the above doesn't work:

1. **Delete `.env.local`** in the `frontend` directory
2. **Create a new `.env.local`** with:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. **Restart the dev server**

## Verify the Fix

1. **Check backend is running:**
   - Visit: http://localhost:8000/health
   - Should return: `{"status":"healthy"}`

2. **Check your `.env.local` file:**
   - Open `frontend/.env.local`
   - Verify it says: `NEXT_PUBLIC_API_URL=http://localhost:8000`

3. **Clear browser cache:**
   - Press `Ctrl+Shift+R` (hard refresh)
   - Or clear browser cache

4. **Try logging in again**

## Why This Happened

The frontend was configured to use port 8001, likely from:
- An old `.env.local` file
- A cached environment variable
- A previous configuration

## All Fixed Files

I've updated all frontend files to use port 8000 as the default fallback:
- ✅ `app/login/page.tsx`
- ✅ `app/signup/page.tsx`
- ✅ `app/protected/profile/page.tsx`
- ✅ `src/lib/api.ts`
- ✅ `src/components/user-nav.tsx`

Even if `.env.local` is missing or wrong, the frontend will now default to port 8000.

## Still Having Issues?

1. **Check browser console (F12)** for specific errors
2. **Check Network tab** to see what URL is being called
3. **Verify backend is running:**
   ```powershell
   python backend\start_server.py
   ```
4. **Try using `127.0.0.1` instead of `localhost`:**
   ```env
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
   ```
