"""
PrepIQ Backend - Production Ready FastAPI Application
Optimized for Render free tier deployment
"""
import os
import sys
import asyncio

# ── Windows: fix joblib/loky wmic CPU detection crash ────────────────────────
# Must be set BEFORE any sklearn/joblib import. joblib reads this env var to
# skip the wmic subprocess call that fails when wmic is unavailable.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

# Fix for Windows asyncio ProactorEventLoop connection reset errors
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
    print(f"[OK] Loaded environment from {env_path}")
else:
    # Try .env.production as fallback
    env_prod_path = backend_path / '.env.production'
    if env_prod_path.exists():
        load_dotenv(dotenv_path=env_prod_path, override=True)
        print(f"[OK] Loaded environment from {env_prod_path}")
    else:
        print("[WARN] No .env file found. Using system environment variables.")

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
        logger.error("[ERROR] Missing required environment variables:")
        for var in missing_vars:
            logger.error(var)
        logger.error("\n[INFO] Please set these variables in your .env.production file")
        logger.error("   or configure them in your deployment platform dashboard.")
        sys.exit(1)
    
    logger.info("[OK] All required environment variables are set")

# Run validation on startup (moved from module import time)
# Now called inside lifespan to avoid sys.exit during import
def get_missing_environment_vars():
    """Get list of missing required environment variables.
    
    Returns:
        list: List of missing variable descriptions
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
    
    return missing_vars

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
    logger.info("Starting PrepIQ Backend Application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    # Validate environment variables (non-blocking in dev, fatal in production)
    missing_vars = get_missing_environment_vars()
    if missing_vars:
        if settings.ENVIRONMENT == "production":
            # BUG-L01: hard-fail in production — never start with missing secrets
            logger.error("[FATAL] Missing required environment variables in production:")
            for var in missing_vars:
                logger.error(var)
            raise RuntimeError(
                "Cannot start in production with missing environment variables. "
                "Set all required vars in your deployment platform dashboard."
            )
        else:
            logger.warning("[WARN] Missing optional environment variables:")
            for var in missing_vars:
                logger.warning(var)
            logger.warning("[INFO] Application will run with limited functionality")

    # BUG-L01: also refuse to start in production with the default insecure key
    _insecure_default = "default-insecure-change-me"
    if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == _insecure_default:
        raise RuntimeError(
            "Cannot start in production with the default insecure SECRET_KEY. "
            "Set JWT_SECRET to a strong random value (openssl rand -base64 32)."
        )
    
    # Verify database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[OK] Database connection verified")
    except Exception as e:
        logger.error(f"[ERROR] Database connection failed: {e}")
        raise RuntimeError("Cannot start without database connection")

    # BUG-H10: pre-warm PrepIQService during startup so the first request
    # does not hang for 10-30 seconds while ML models load.
    try:
        from app.dependencies import get_prepiq_service
        get_prepiq_service()
        logger.info("[OK] PrepIQService initialized")
    except Exception as e:
        logger.warning(f"[WARN] PrepIQService pre-warm failed (non-fatal): {e}")
    
    yield
    
    # Shutdown
    logger.info("[INFO] Shutting down PrepIQ Backend Application")

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
        redirect_slashes=False,  # Disable trailing slash redirects to avoid 307
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
        logger.info("[DEV] Development mode: Allowing all CORS origins")
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
            logger.warning("[WARN] No CORS origins configured! Using safe defaults.")
            allowed_origins = ["https://prepiq.vercel.app"]
        
        logger.info(f"[SECURE] CORS configured for origins: {allowed_origins}")
        
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

    @app.exception_handler(ConnectionResetError)
    async def connection_reset_handler(request: Request, exc: ConnectionResetError):
        """Handle ConnectionResetError to prevent log spam on Windows."""
        logger.debug(f"Connection reset by client: {request.url}")
        return JSONResponse(
            status_code=499,  # Client Closed Request
            content={"detail": "Connection reset by client"}
        )

    # BUG-L06: HTTPException handler MUST be registered before the generic
    # Exception handler. FastAPI checks handlers in registration order;
    # since HTTPException is a subclass of Exception, the generic handler
    # would otherwise swallow all HTTP errors and return 500.
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with their correct status codes."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled non-HTTP exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
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

    @app.get("/health/auth", tags=["Health"])
    async def auth_health_check():
        """Check whether the Supabase auth service is reachable and configured."""
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "error",
                    "auth_service": "unconfigured",
                    "message": "SUPABASE_URL or SUPABASE_SERVICE_KEY is not set",
                }
            )

        try:
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            # Lightweight probe: list users with limit=1 (service-role only)
            client.auth.admin.list_users(page=1, per_page=1)
            return {
                "status": "ok",
                "auth_service": "reachable",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Auth health check failed: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "error",
                    "auth_service": "unreachable",
                    "message": str(e),
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
    
    app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Authentication"])
    app.include_router(subjects.router, prefix=settings.API_V1_STR, tags=["Subjects"])
    app.include_router(papers.router, prefix=settings.API_V1_STR, tags=["Papers"])
    app.include_router(predictions.router, prefix=settings.API_V1_STR, tags=["Predictions"])
    app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["Chat"])
    app.include_router(tests.router, prefix=settings.API_V1_STR, tags=["Tests"])
    app.include_router(analysis.router, prefix=settings.API_V1_STR, tags=["Analysis"])
    app.include_router(plans.router, prefix=settings.API_V1_STR, tags=["Study Plans"])
    app.include_router(dashboard.router, prefix=settings.API_V1_STR, tags=["Dashboard"])
    app.include_router(questions.router, prefix=settings.API_V1_STR, tags=["Questions"])
    app.include_router(wizard.router, prefix=settings.API_V1_STR, tags=["Wizard"])
    app.include_router(upload.router, prefix=settings.API_V1_STR, tags=["Upload"])
    
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
