I'll provide a step-by-step explanation for beginners on how to set up the .env files for the PrepIQ application.

## Understanding the .env Files in PrepIQ

### 1. Difference Between the Two .env Files

The PrepIQ application has two separate .env files because it's a full-stack application with distinct frontend and backend components:

- **Backend .env** (in `backend/.env`): Contains server-side configuration including database connections, JWT secrets, API keys, and Supabase credentials
- **Frontend environment**: Uses NEXT_PUBLIC_ prefixed variables that are accessible in the browser (these are typically configured in the frontend's .env.local or similar)

### 2. Environment Variables to Configure in Each File

**Backend .env file** (backend/.env):
- `DATABASE_URL` - PostgreSQL database connection string
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Your Supabase service role key
- `JWT_SECRET` - Secret key for JWT token generation
- `GEMINI_API_KEY` - Google Gemini API key for AI features
- `ALLOWED_ORIGINS` - List of allowed origins for CORS

### 3. How to Set Up Both Files with Required Values

**For the Backend (.env in backend folder):**

1. **DATABASE_URL**: 
   - Format: `postgresql://username:password@localhost:5432/prepiq_db`
   - Replace with your actual PostgreSQL credentials
   - If using a cloud database, use the full connection string

2. **SUPABASE_URL and SUPABASE_SERVICE_KEY**:
   - Go to your Supabase dashboard
   - SUPABASE_URL: Found in Project Settings > Configuration
   - SUPABASE_SERVICE_KEY: Found in Project Settings > API (the "Service role key")

3. **JWT_SECRET**:
   - Create a strong, random secret string
   - Example: `very_secure_jwt_secret_key_for_development_only`
   - Never use the default example value in production

4. **GEMINI_API_KEY**:
   - Get from Google AI Studio
   - Format: `your_gemini_api_key_here`

5. **ALLOWED_ORIGINS**:
   - List your frontend URLs separated by commas
   - Example: `http://localhost:3000,http://localhost:5173,https://yourdomain.com`

### 4. Steps to Rename .env.example to .env

**Backend setup:**
1. Navigate to the `backend` folder
2. Locate the `.env.example` file
3. Rename it to `.env`
4. Open the `.env` file in a text editor
5. Replace the placeholder values with your actual values

**Example commands:**
```bash
# In the backend directory
cp .env.example .env
# Then edit the .env file with your actual values
```

### 5. Common Mistakes to Avoid

1. **Using Default Values**: Never use default example values in production
2. **Exposing Secrets**: Never commit .env files to version control
3. **Incorrect Formatting**: Ensure no spaces around the `=` sign, and no quotes around values unless specifically needed
4. **Missing Variables**: Ensure all required variables are set before starting the application
5. **Wrong API Keys**: Double-check API keys are copied correctly without extra spaces
6. **Database Connection**: Ensure PostgreSQL is running and accessible before starting the backend

### 6. How the Application Uses These Variables

**Backend Variables:**
- `DATABASE_URL` is used by SQLAlchemy to connect to your PostgreSQL database
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are used for authentication and real-time features
- `JWT_SECRET` is used to sign and verify authentication tokens
- `GEMINI_API_KEY` is used for AI-powered question prediction features
- `ALLOWED_ORIGINS` configures CORS to allow frontend connections

**Frontend Variables:**
- The frontend uses `NEXT_PUBLIC_API_URL` to know where to send API requests
- Supabase client-side variables are used for authentication in the browser

**Important Notes for Beginners:**
- The backend .env file is for server-side secrets that should never be exposed to the browser
- Frontend environment variables need the `NEXT_PUBLIC_` prefix to be accessible in client-side code
- Always keep your .env files secure and never commit them to Git
- When deploying, ensure these environment variables are set in your hosting environment
- Test your setup by starting the backend server first, then the frontend to ensure they can communicate properly

The application is designed so that sensitive credentials like database passwords and API keys remain server-side, while the frontend only gets the information it needs to connect to the backend API.