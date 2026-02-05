"""
Simple PrepIQ Backend for testing
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.core.config import settings

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": "2026-01-06T00:00:00Z"
        }
    
    # Simple test endpoint
    @app.get("/")
    async def root():
        return {"message": "PrepIQ Backend is running!"}
    
    # Test endpoint
    @app.get("/test")
    async def test():
        return {"message": "Test endpoint working", "data": [1, 2, 3, 4, 5]}
    
    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    logger.info("Starting Simple PrepIQ Backend Server")
    logger.info(f"Listening on port 8000")
    
    # Run the application
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )