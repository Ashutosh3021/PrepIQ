"""
Enhanced PrepIQ Backend with ML Integration
Production-ready web application with machine learning capabilities
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import prep_iq_exception_handler, validation_exception_handler
from app.ml.training.model_trainer import ModelTrainer

# Set up logging
logger = setup_logging()

# Initialize ML components
model_trainer = ModelTrainer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI application."""
    # Startup
    logger.info("Starting PrepIQ Backend Application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    # Load training history
    try:
        model_trainer.load_training_history()
        logger.info("Training history loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load training history: {str(e)}")
    
    # Log important configurations
    logger.info(f"API Version: {settings.API_V1_STR}")
    logger.info(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PrepIQ Backend Application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]  # Configure properly for production
    )
    
    # Add exception handlers
    app.add_exception_handler(Exception, prep_iq_exception_handler)
    app.add_exception_handler(422, validation_exception_handler)
    
    # Include routers (to be implemented)
    # app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": "2026-01-06T00:00:00Z"
        }
    
    # ML Model Status endpoint
    @app.get("/ml/status")
    async def ml_status():
        """Get status of all ML models."""
        try:
            report = model_trainer.get_model_performance_report()
            return {
                "status": "success",
                "models": report.get("models_by_type", {}),
                "total_models": report.get("total_models_trained", 0),
                "timestamp": "2026-01-06T00:00:00Z"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get ML status: {str(e)}")
    
    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    logger.info("Starting PrepIQ Backend Server")
    logger.info(f"Listening on port {settings.PORT if hasattr(settings, 'PORT') else 8000}")
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.DEBUG else 4
    )