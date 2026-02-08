"""ML Configuration for PrepIQ backend."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class MLSettings(BaseSettings):
    """ML-specific configuration settings."""
    
    # Model paths
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "models/ml_models")
    ML_DATA_PATH: str = os.getenv("ML_DATA_PATH", "data/ml_data")
    ML_TRAINING_DATA_PATH: str = os.getenv("ML_TRAINING_DATA_PATH", "data/ml_training")
    
    # Training configuration
    ML_TRAINING_EPOCHS: int = int(os.getenv("ML_TRAINING_EPOCHS", "100"))
    ML_BATCH_SIZE: int = int(os.getenv("ML_BATCH_SIZE", "32"))
    ML_LEARNING_RATE: float = float(os.getenv("ML_LEARNING_RATE", "0.001"))
    
    # Model evaluation
    ML_MIN_ACCURACY_THRESHOLD: float = float(os.getenv("ML_MIN_ACCURACY_THRESHOLD", "0.8"))
    ML_CROSS_VALIDATION_FOLDS: int = int(os.getenv("ML_CROSS_VALIDATION_FOLDS", "5"))
    
    # Feature engineering
    ML_MAX_FEATURES: int = int(os.getenv("ML_MAX_FEATURES", "1000"))
    ML_NGRAM_RANGE: tuple = tuple(map(int, os.getenv("ML_NGRAM_RANGE", "1,2").split(",")))
    
    # Cache settings
    ML_CACHE_TTL: int = int(os.getenv("ML_CACHE_TTL", "3600"))  # 1 hour
    ML_ENABLE_CACHE: bool = os.getenv("ML_ENABLE_CACHE", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = MLSettings()