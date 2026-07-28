import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "PrepIQ Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PrepIQ API"
    SECRET_KEY: str = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "default-insecure-change-me"))
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/prepiq")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    # BUG-B04 FIX: Read SUPABASE_KEY from actual env var SUPABASE_SERVICE_KEY
    SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    JWT_ALGORITHM: str = "HS256"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://yourdomain.com"
    ]
    
    # ML settings
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "./ml_models")
    ML_TRAINING_DATA_PATH: str = os.getenv("ML_TRAINING_DATA_PATH", "./data")
    ML_MAX_TRAINING_TIME: int = 3600  # 1 hour in seconds
    
    # File upload settings
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    
    # Redis settings (for caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Email settings (if needed)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # ------------------------------------------------------------------
    # LLM / provider layer (Phase 1) — capability-scoped, env-driven
    # Resolution is implemented in app.core.llm_provider.resolve_llm_settings
    # ------------------------------------------------------------------
    # Shared defaults
    LLM_DEFAULT_PROVIDER: str = os.getenv("LLM_DEFAULT_PROVIDER", "gemini")
    LLM_DEFAULT_MODEL: str = os.getenv("LLM_DEFAULT_MODEL", "gemini-1.5-flash")
    LLM_DEFAULT_API_KEY: str = os.getenv("LLM_DEFAULT_API_KEY", "")
    LLM_DEFAULT_BASE_URL: str = os.getenv("LLM_DEFAULT_BASE_URL", "")

    # Prediction capability
    PREDICTION_PROVIDER: str = os.getenv("PREDICTION_PROVIDER", "")
    PREDICTION_MODEL: str = os.getenv("PREDICTION_MODEL", "")
    PREDICTION_API_KEY: str = os.getenv("PREDICTION_API_KEY", "")
    PREDICTION_BASE_URL: str = os.getenv("PREDICTION_BASE_URL", "")

    # Extraction capability (paper/text → questions)
    EXTRACTION_PROVIDER: str = os.getenv("EXTRACTION_PROVIDER", "")
    EXTRACTION_MODEL: str = os.getenv("EXTRACTION_MODEL", "")
    EXTRACTION_API_KEY: str = os.getenv("EXTRACTION_API_KEY", "")
    EXTRACTION_BASE_URL: str = os.getenv("EXTRACTION_BASE_URL", "")

    # Chat / tutor capability
    CHAT_PROVIDER: str = os.getenv("CHAT_PROVIDER", "")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "")
    CHAT_API_KEY: str = os.getenv("CHAT_API_KEY", "")
    CHAT_BASE_URL: str = os.getenv("CHAT_BASE_URL", "")

    # Legacy Google AI key (still accepted as fallback key by llm_provider)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"


settings = Settings()
