"""
PrepIQ Backend - Production Ready FastAPI Application
Optimized for Render free tier deployment
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Load environment variables BEFORE any other imports
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded environment from {env_path}")
else:
    # Try .env.production as fallback
    env_prod_path = backend_path / '.env.production'
    if env_prod_path.exists():
        load_dotenv(dotenv_path=env_prod_path, override=True)
        print(f"✅ Loaded environment from {env_prod_path}")
    else:
        print("⚠️  No .env file found. Using system environment variables.")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# ENVIRONMENT VALIDATION
# ============================================
def validate_environment():
    """Validate that all required environment variables are set.
    
    Raises:
        SystemExit: If any required variable is missing
    """
    required_vars = {
        'DATABASE_URL': 'Supabase PostgreSQL connection pooler URL',
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_SERVICE_KEY': 'Supabase service role key',
        'JWT_SECRET': 'JWT secret key (generate with: openssl rand -base64 32)',
        'ALLOWED_ORIGINS': 'Comma-separated list of allowed CORS origins',
        'GEMINI_API_KEY': 'Google Gemini API key',
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")
    
    if missing_vars:
        logger.error("❌ Missing required environment variables:")
        for var in missing_vars:
            logger.error(var)
        logger.error("\n📝 Please set these variables in your .env.production file")
        logger.error("   or configure them in your deployment platform dashboard.")
        sys.exit(1)
    
    logger.info("✅ All required environment variables are set")

# Run validation on startup
validate_environment()

# Now import application modules (after validation)
from app.core.config import settings
from app.database import engine
from sqlalchemy import text

# ============================================
# LIFESPAN MANAGEMENT
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("🚀 Starting PrepIQ Backend Application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    # Verify database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise RuntimeError("Cannot start without database connection")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down PrepIQ Backend Application")

# ============================================
# APPLICATION FACTORY
# ============================================
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="PrepIQ API",
        description="AI-Powered Exam Preparation Platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )
    
    # ============================================
    # CORS CONFIGURATION
    # ============================================
    # Get allowed origins from environment variable
    allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]
    
    # Check if we're in development mode
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    if is_development:
        # In development, allow all origins for easier testing
        logger.info("🔓 Development mode: Allowing all CORS origins")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            max_age=600,
        )
    else:
        # In production, use strict origins
        if not allowed_origins:
            logger.warning("⚠️  No CORS origins configured! Using safe defaults.")
            allowed_origins = ["https://prepiq.vercel.app"]
        
        logger.info(f"🔒 CORS configured for origins: {allowed_origins}")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            max_age=600,
        )
    
    # ============================================
    # SECURITY MIDDLEWARE
    # ============================================
    # Trust only known hosts in production
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.onrender.com", "*.vercel.app", "localhost"]
        )
    
    # ============================================
    # EXCEPTION HANDLERS
    # ============================================
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # ============================================
    # HEALTH CHECK ENDPOINT
    # ============================================
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for Render and monitoring."""
        try:
            # Check database connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return {
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "environment": settings.ENVIRONMENT,
                "database": "connected"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database": "disconnected",
                    "error": str(e)
                }
            )
    
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to PrepIQ API",
            "version": "1.0.0",
            "docs": "/docs" if settings.DEBUG else None,
            "health": "/health"
        }
    
    # ============================================
    # INCLUDE ROUTERS
    # ============================================
    from app.routers import auth, subjects, papers, predictions, chat, tests, analysis, plans, dashboard, questions, wizard, upload
    
    app.include_router(auth.router, tags=["Authentication"])
    app.include_router(subjects.router, tags=["Subjects"])
    app.include_router(papers.router, tags=["Papers"])
    app.include_router(predictions.router, tags=["Predictions"])
    app.include_router(chat.router, tags=["Chat"])
    app.include_router(tests.router, tags=["Tests"])
    app.include_router(analysis.router, tags=["Analysis"])
    app.include_router(plans.router, tags=["Study Plans"])
    app.include_router(dashboard.router, tags=["Dashboard"])
    app.include_router(questions.router, tags=["Questions"])
    app.include_router(wizard.router, tags=["Wizard"])
    app.include_router(upload.router, tags=["Upload"])
    
    return app

# Create application instance
app = create_app()

# ============================================
# MAIN ENTRY POINT (for local development)
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info(f"📚 API Documentation: http://{host}:{port}/docs")
    logger.info(f"💓 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
        workers=1  # Use 1 worker for Render free tier
    )
