"""
Minimal PrepIQ Backend for testing auth endpoints
This version excludes ML components that require PyTorch
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = FastAPI(title="PrepIQ Backend API", version="1.0.0")
    
    # Get allowed origins from environment variable
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002").split(",")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include auth router (this should work without ML dependencies)
    try:
        from app.routers import auth
        app.include_router(auth.router)
        logger.info("✅ Auth router included successfully")
    except Exception as e:
        logger.error(f"❌ Failed to include auth router: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    # Basic health check
    @app.get("/")
    async def root():
        return {"message": "Welcome to PrepIQ Backend API"}
        
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}
        
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)