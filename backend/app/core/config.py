import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "PrepIQ Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PrepIQ API"
    SECRET_KEY: str = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "default-insecure-change-me"))

    # Phase 2 — Pyronites (required for auth + data)
    PYRONITES_URL: str = os.getenv("PYRONITES_URL", "")
    PYRONITES_KEY: str = os.getenv("PYRONITES_KEY", "")

    # Local paper storage (no cloud storage basket)
    UPLOAD_ROOT: str = os.getenv("UPLOAD_ROOT", "./uploads")

    # Obsolete after Phase 2 (kept only so old .env files do not crash pydantic)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    JWT_ALGORITHM: str = "HS256"

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://yourdomain.com",
    ]

    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "./ml_models")
    ML_TRAINING_DATA_PATH: str = os.getenv("ML_TRAINING_DATA_PATH", "./data")
    ML_MAX_TRAINING_TIME: int = 3600

    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx", ".txt"]

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_CACHE_TTL: int = 3600

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")

    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # Phase 1 LLM
    LLM_DEFAULT_PROVIDER: str = os.getenv("LLM_DEFAULT_PROVIDER", "gemini")
    LLM_DEFAULT_MODEL: str = os.getenv("LLM_DEFAULT_MODEL", "gemini-1.5-flash")
    LLM_DEFAULT_API_KEY: str = os.getenv("LLM_DEFAULT_API_KEY", "")
    LLM_DEFAULT_BASE_URL: str = os.getenv("LLM_DEFAULT_BASE_URL", "")
    PREDICTION_PROVIDER: str = os.getenv("PREDICTION_PROVIDER", "")
    PREDICTION_MODEL: str = os.getenv("PREDICTION_MODEL", "")
    PREDICTION_API_KEY: str = os.getenv("PREDICTION_API_KEY", "")
    PREDICTION_BASE_URL: str = os.getenv("PREDICTION_BASE_URL", "")
    EXTRACTION_PROVIDER: str = os.getenv("EXTRACTION_PROVIDER", "")
    EXTRACTION_MODEL: str = os.getenv("EXTRACTION_MODEL", "")
    EXTRACTION_API_KEY: str = os.getenv("EXTRACTION_API_KEY", "")
    EXTRACTION_BASE_URL: str = os.getenv("EXTRACTION_BASE_URL", "")
    CHAT_PROVIDER: str = os.getenv("CHAT_PROVIDER", "")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "")
    CHAT_API_KEY: str = os.getenv("CHAT_API_KEY", "")
    CHAT_BASE_URL: str = os.getenv("CHAT_BASE_URL", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"


settings = Settings()
