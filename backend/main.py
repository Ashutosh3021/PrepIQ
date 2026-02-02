from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.main import app as api_app  # Import the main app from the app module
import os

# Check that required environment variables are set
if not os.getenv("JWT_SECRET"):
    raise ValueError("JWT_SECRET environment variable must be set")

# Create the main app instance and add CORS
app = FastAPI(title="PrepIQ API")

# Get allowed origins from environment, default to localhost for development
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount the API app
app.mount("/api", api_app)

@app.get("/")
async def root():
    return {"message": "PrepIQ API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
