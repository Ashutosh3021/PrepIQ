"""
PrepIQ Backend - Production Ready FastAPI Application
Phase 2: Pyronites auth/data + local file storage
"""
import os
import sys
import asyncio

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from datetime import datetime
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv

env_path = backend_path / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"[OK] Loaded environment from {env_path}")
else:
    env_prod_path = backend_path / ".env.production"
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_missing_environment_vars():
    required_vars = {
        "PYRONITES_URL": "Pyronites project URL",
        "PYRONITES_KEY": "Pyronites API key",
        "JWT_SECRET": "JWT secret key (openssl rand -base64 32)",
        "ALLOWED_ORIGINS": "Comma-separated list of allowed CORS origins",
    }
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  - {var}: {description}")
    return missing


from app.core.config import settings

import sys as _sys
import os as _os

_project_root = str(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
if _project_root not in _sys.path:
    _sys.path.insert(0, _project_root)

try:
    from trigger import start_keep_alive_thread, stop_keep_alive_thread

    _KEEP_ALIVE_AVAILABLE = True
except ImportError:
    _KEEP_ALIVE_AVAILABLE = False
    logger.warning("[keep-alive] trigger.py not found — keep-alive disabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PrepIQ Backend Application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    missing_vars = get_missing_environment_vars()
    if missing_vars:
        if settings.ENVIRONMENT == "production":
            logger.error("[FATAL] Missing required environment variables in production:")
            for var in missing_vars:
                logger.error(var)
            raise RuntimeError(
                "Cannot start in production with missing environment variables."
            )
        else:
            logger.warning("[WARN] Missing environment variables:")
            for var in missing_vars:
                logger.warning(var)

    for key in ("PYRONITES_URL", "PYRONITES_KEY", "GEMINI_API_KEY", "LLM_DEFAULT_API_KEY"):
        if not os.getenv(key):
            logger.warning("[WARN] %s not set — some features may be unavailable", key)

    _insecure_default = "default-insecure-change-me"
    if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == _insecure_default:
        raise RuntimeError("Cannot start in production with the default insecure SECRET_KEY.")

    try:
        from app.core.local_storage import _upload_root

        root = _upload_root()
        logger.info("[OK] Upload root ready: %s", root)
    except Exception as e:
        logger.warning("[WARN] Upload root init: %s", e)

    try:
        from app.core.pyronites_client import pyronites_configured, get_pyronites_client

        if pyronites_configured():
            get_pyronites_client()
            logger.info("[OK] Pyronites client constructed")
        else:
            logger.warning("[WARN] Pyronites not configured")
    except Exception as e:
        logger.warning("[WARN] Pyronites client init failed: %s", e)

    _keep_alive_thread = None
    if settings.ENVIRONMENT == "production" and _KEEP_ALIVE_AVAILABLE:
        _keep_alive_endpoint = os.getenv(
            "HEALTH_ENDPOINT",
            "https://prepiq-narg.onrender.com/health",
        )
        _keep_alive_thread = start_keep_alive_thread(url=_keep_alive_endpoint, logger=logger)
        logger.info("[keep-alive] Pinging %s every 14 min", _keep_alive_endpoint)

    # Exam context cache job (NEET/JEE) — monthly refresh via daemon thread
    # Same pattern as keep-alive; not request-triggered. See exam_context_job.py.
    _exam_context_thread = None
    try:
        from app.services.exam_context_job import (
            start_exam_context_thread,
            stop_exam_context_thread,
        )

        _exam_context_thread = start_exam_context_thread(logger_=logger)
        logger.info(
            "[exam-context] background thread started "
            "(monthly refresh; EXAM_CONTEXT_REFRESH_DAYS / EXAM_CONTEXT_CHECK_HOURS)"
        )
    except Exception as e:
        logger.warning("[exam-context] failed to start background thread: %s", e)

    yield

    if _keep_alive_thread is not None:
        stop_keep_alive_thread()
    if _exam_context_thread is not None:
        try:
            stop_exam_context_thread()
        except Exception:
            pass
    logger.info("[INFO] Shutting down PrepIQ Backend Application")


def create_app() -> FastAPI:
    app = FastAPI(
        title="PrepIQ API",
        description="AI-Powered Exam Preparation Platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        redirect_slashes=False,
    )

    allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
    allowed_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"

    if is_development:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            max_age=600,
        )
    else:
        # Always permit the known PrepIQ frontend deployments. The deployed
        # ALLOWED_ORIGINS may be empty or configured for a different domain,
        # which caused the browser to be blocked by CORS even when the request
        # succeeded server-side (e.g. from https://prep-iq-three.vercel.app).
        _known_frontends = [
            "https://prep-iq-three.vercel.app",
            "https://prepiq.vercel.app",
        ]
        frontend_url = (os.getenv("FRONTEND_URL") or "").strip()
        if frontend_url:
            _known_frontends.append(frontend_url)
        for origin in _known_frontends:
            if origin and origin not in allowed_origins:
                allowed_origins.append(origin)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
            max_age=600,
        )

    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.onrender.com", "*.vercel.app", "localhost"],
        )

    @app.exception_handler(ConnectionResetError)
    async def connection_reset_handler(request: Request, exc: ConnectionResetError):
        return JSONResponse(status_code=499, content={"detail": "Connection reset by client"})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "service": "prepiq-backend"}

    @app.get("/health/full", tags=["Health"])
    async def health_check_full():
        from app.core.pyronites_client import pyronites_configured

        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "pyronites_configured": pyronites_configured(),
            "upload_root": settings.UPLOAD_ROOT,
        }

    @app.get("/health/auth", tags=["Health"])
    async def auth_health_check():
        from app.core.pyronites_client import pyronites_configured, get_pyronites_client

        if not pyronites_configured():
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "error",
                    "auth_service": "unconfigured",
                    "message": "PYRONITES_URL or PYRONITES_KEY is not set",
                },
            )
        try:
            get_pyronites_client()
            return {
                "status": "ok",
                "auth_service": "pyronites",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail={"status": "error", "auth_service": "unreachable", "message": str(e)},
            )

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "Welcome to PrepIQ API",
            "version": "1.0.0",
            "docs": "/docs" if settings.DEBUG else None,
            "health": "/health",
        }

    from app.routers import (
        auth,
        subjects,
        papers,
        predictions,
        chat,
        tests,
        analysis,
        plans,
        dashboard,
        questions,
        wizard,
        upload,
    )

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


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=settings.DEBUG, workers=1)
