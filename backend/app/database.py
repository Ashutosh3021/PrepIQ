"""
PrepIQ Database Configuration
PostgreSQL with Supabase configuration
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# BUG-M09: removed redundant load_dotenv() — main.py already loads .env before
# any module is imported. Having a second load_dotenv() here can silently
# override values that main.py set with override=True.

# ---------------------------------------------------------------------------
# Lazy engine initialisation
# The DATABASE_URL check and engine creation are deferred to first use so that
# importing this module (e.g. during tests or when the .env file is absent)
# does NOT crash the process at import time.
# ---------------------------------------------------------------------------

_engine = None
_SessionLocal = None

Base = declarative_base()


def _get_database_url() -> str:
    """Return the (sanitised) DATABASE_URL or raise at call-time."""
    url = os.getenv("DATABASE_URL")
    if url and "pgbouncer" in url:
        url = url.split("?")[0]
        logger.info("[OK] Removed pgbouncer option from DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Please set it to your Supabase PostgreSQL connection string."
        )
    return url


def _init_engine():
    """Initialise the SQLAlchemy engine and session factory on first use."""
    global _engine, _SessionLocal
    if _engine is None:
        db_url = _get_database_url()
        _engine = create_engine(
            db_url,
            pool_size=1,
            max_overflow=2,
            pool_pre_ping=True,
            pool_recycle=300,  # Recycle connections after 5 minutes
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000"  # 30 second query timeout
            }
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


class _LazyEngine:
    """Proxy that initialises the real engine on first attribute access.

    This keeps the module-level ``engine`` name available for code that does
    ``from app.database import engine`` without triggering the DB connection
    check at import time.
    """

    def __getattr__(self, name):
        _init_engine()
        return getattr(_engine, name)

    def connect(self, *args, **kwargs):
        _init_engine()
        return _engine.connect(*args, **kwargs)

    def dispose(self, *args, **kwargs):
        _init_engine()
        return _engine.dispose(*args, **kwargs)


# Public names — backward-compatible with existing ``from app.database import engine``
engine = _LazyEngine()


def SessionLocal():
    """Return a new SQLAlchemy session (lazy, initialises engine on first call)."""
    _init_engine()
    return _SessionLocal()


def get_db():
    """Get database session with proper error handling"""
    _init_engine()
    db = _SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_new_db_session():
    """Create a new database session for background processing (e.g., ThreadPoolExecutor)"""
    _init_engine()
    return _SessionLocal()


def create_tables():
    """Create all database tables"""
    _init_engine()
    from .models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=_engine)
    print("✅ Database tables created successfully")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    _init_engine()
    from .models import Base as ModelsBase
    ModelsBase.metadata.drop_all(bind=_engine)
    print("⚠️  Database tables dropped")
