"""
PrepIQ Database Configuration
PostgreSQL with Supabase configuration
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration - PostgreSQL only (via Supabase)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Please set it to your Supabase PostgreSQL connection string."
    )

# Create engine with connection pooling optimized for Supabase
# Use connection pool pre-ping to handle stale connections
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections after 5 minutes
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30 second query timeout
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Get database session with proper error handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    from .models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    from .models import Base as ModelsBase
    ModelsBase.metadata.drop_all(bind=engine)
    print("⚠️  Database tables dropped")
