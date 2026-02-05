# PrepIQ - Corrected Startup Guide

## Default Ports
According to documentation, the applications should run on these default ports:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000

## Starting the Applications

### Method 1: Using the Combined Startup Script (Recommended)
```bash
# From the project root directory
python start_all.py
```

This will start both backend and frontend on their correct default ports.

### Method 2: Starting Services Individually

#### Backend
```bash
cd backend
python start_server.py
# OR
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run dev:default
# OR
npx next dev -p 3000
```

## Environment Configuration

### Backend (.env)
The backend will use port 8000 by default. You can override this with:
```env
PORT=8000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Port Already in Use
If the default ports are occupied:
1. Check what's using the ports:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :3000
   ```

2. Stop the conflicting processes or use different ports by setting the PORT environment variable.

### Connection Issues
Ensure both services are running and the frontend can reach the backend:
- Backend health check: http://localhost:8000/health
- Frontend: http://localhost:3000