# Frontend Environment Setup

## Quick Fix for "Failed to fetch" Error

The "Failed to fetch" error occurs when the frontend cannot connect to the backend API. Follow these steps:

### 1. Create `.env.local` file

Create a file named `.env.local` in the `frontend` directory with the following content:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Verify Backend is Running

Make sure your backend server is running:

```powershell
# In the backend directory
python backend\start_server.py
```

You should see:
```
Starting PrepIQ Backend Server on http://0.0.0.0:8000
```

### 3. Restart Frontend Dev Server

After creating `.env.local`, restart your Next.js dev server:

```powershell
# Stop the current server (Ctrl+C)
# Then restart:
npm run dev
# or
pnpm dev
```

### 4. Verify Connection

Test the backend health endpoint:
- Open: http://localhost:8000/health
- Should return: `{"status":"healthy"}`

### 5. Check CORS Configuration

The backend should allow requests from:
- `http://localhost:3000` (Next.js default)
- `http://localhost:3001`
- `http://localhost:3002`

If your frontend runs on a different port, update `backend/app/main.py`:

```python
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002").split(",")
```

## Troubleshooting

### Error: "Failed to fetch"

**Possible causes:**
1. Backend server not running
2. Wrong API URL in `.env.local`
3. CORS not configured correctly
4. Port mismatch

**Solutions:**
1. Check backend is running: `http://localhost:8000/health`
2. Verify `.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Check browser console for specific error
4. Verify both frontend and backend are on allowed ports

### Error: "Network error"

**Solutions:**
1. Check firewall isn't blocking localhost connections
2. Try using `127.0.0.1` instead of `localhost`
3. Verify no other service is using port 8000

## Environment Variables Reference

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional (if using Supabase)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional (for AI features)
NEXT_PUBLIC_GEMINI_API_KEY=your_gemini_api_key
```

## Testing the Connection

After setup, test the login:
1. Go to http://localhost:3000/login
2. Enter credentials
3. Check browser console (F12) for any errors
4. Check Network tab to see if request reaches backend
