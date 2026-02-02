import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, subjects, papers, predictions, chat, tests, analysis, plans

app = FastAPI(title="PrepIQ Backend API", version="1.0.0")

# Get allowed origins from environment variable, default to localhost for development
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:3001").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(papers.router)
app.include_router(predictions.router)
app.include_router(chat.router)
app.include_router(tests.router)
app.include_router(analysis.router)
app.include_router(plans.router)

@app.get("/")
async def root():
    return {"message": "Welcome to PrepIQ Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}