import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, subjects, papers, predictions, chat, tests, analysis, plans, dashboard

app = FastAPI(title="PrepIQ Backend API", version="1.0.0")

# Get allowed origins from environment variable, default to localhost for development
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002").split(",")

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
app.include_router(dashboard.router)

@app.get("/")
async def root():
    return {"message": "Welcome to PrepIQ Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}