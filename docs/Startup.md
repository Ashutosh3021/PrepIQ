# PrepIQ Application Startup Guide

This guide provides comprehensive instructions for setting up and running the PrepIQ AI-powered study assistant application. Follow these steps to get the application up and running on your local machine.

## Prerequisites

Before starting the setup, ensure you have the following software installed on your system:

### System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Git**: For version control (download from [git-scm.com](https://git-scm.com/))

### Software Requirements
- **Python 3.10+**: Required for the backend (download from [python.org](https://www.python.org/downloads/))
- **Node.js 18+**: Required for the frontend (download from [nodejs.org](https://nodejs.org/))
- **PostgreSQL**: Database server (download from [postgresql.org](https://www.postgresql.org/download/))
- **pnpm**: Package manager for the frontend (install via `npm install -g pnpm`)

## Getting Started

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone <repository-url>
cd PrepIQ
```

### 2. Set Up Backend

#### Navigate to Backend Directory
```bash
cd backend
```

#### Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Set Up Environment Variables
Create a `.env` file in the backend directory based on the example:

```bash
cp .env.example .env
```

Edit the `.env` file and update the following values:
- `DATABASE_URL`: Your PostgreSQL connection string (e.g., `postgresql://username:password@localhost:5432/prepiq_db`)
- `GEMINI_API_KEY`: Your Google Gemini API key
- `JWT_SECRET`: A strong secret key for JWT tokens (change in production)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key

### 3. Set Up Frontend

#### Navigate to Frontend Directory
```bash
cd ../frontend
```

#### Install Dependencies
```bash
pnpm install
# Or if you prefer npm:
npm install
```

#### Set Up Environment Variables
Create a `.env.local` file in the frontend directory:

```bash
cp .env.example .env.local
```

Edit the `.env.local` file and update the following values:
- `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `NEXT_PUBLIC_API_URL`: The URL of your backend server (typically `http://localhost:8000`)

## Database Setup

### 1. Start PostgreSQL Server
Make sure your PostgreSQL server is running on your system.

### 2. Create Database
Create a new database for the application:
```sql
CREATE DATABASE prepiq_db;
```

### 3. Initialize Database Schema
Run the initial schema script to set up the database tables:
```bash
cd backend/scripts
python init_db.py
```

## Running the Application

### 1. Start the Backend Server

From the backend directory, run:
```bash
python start_server.py
```

Or alternatively, you can use uvicorn directly:
```bash
uvicorn app.main:app --reload
```

The backend server will start on `http://localhost:8000`.

### 2. Start the Frontend Server

Open a new terminal, navigate to the frontend directory, and run:
```bash
cd frontend
pnpm run dev
```

Or with npm:
```bash
npm run dev
```

The frontend server will start on `http://localhost:5173`.

## Accessing the Application

Once both servers are running:
- Frontend: Open your browser and navigate to `http://localhost:5173`
- Backend API: Available at `http://localhost:8000`
- Backend Health Check: `http://localhost:8000/health`

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - If port 8000 (backend) or 5173 (frontend) is already in use, you'll see an error.
   - Change the port in your environment variables or terminate the conflicting process.

2. **Database Connection Issues**
   - Ensure PostgreSQL is running
   - Verify your `DATABASE_URL` in the `.env` file is correct
   - Check that the database exists and has the right permissions

3. **API Key Issues**
   - Make sure you have a valid Google Gemini API key
   - Ensure the API key is properly set in your environment variables

4. **Dependency Installation Issues**
   - If you encounter issues with installing Python dependencies, try updating pip:
     ```bash
     pip install --upgrade pip
     ```
   - For frontend dependencies, try clearing the cache:
     ```bash
     pnpm store prune
     ```

### Environment Configuration

The application expects the following environment variables:

**Backend (.env):**
- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `JWT_SECRET`: Secret key for JWT tokens
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key

**Frontend (.env.local):**
- `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase anonymous key
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Development Commands

### Backend Commands
- Start development server: `python start_server.py`
- Run tests: `pytest`
- Run with uvicorn: `uvicorn app.main:app --reload`

### Frontend Commands
- Start development server: `pnpm run dev`
- Build for production: `pnpm run build`
- Start production server: `pnpm run start`
- Run linter: `pnpm run lint`

## API Endpoints

The backend provides the following main endpoints:
- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /subjects/` - Get all subjects
- `GET /papers/` - Get exam papers
- `POST /predictions/` - Get predictions
- `POST /chat/` - Chat with AI assistant
- `GET /tests/` - Get tests
- `POST /analysis/` - Analyze documents
- `GET /plans/` - Get study plans

## Stopping the Application

To stop either server, press `Ctrl+C` in the terminal where it's running.

## Next Steps

After successfully starting the application:
1. Create an account or log in to access the dashboard
2. Upload study materials in PDF format
3. Use the AI features for predictions and study planning
4. Try the chatbot for study assistance