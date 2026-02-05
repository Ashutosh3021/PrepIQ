#!/usr/bin/env python3
"""
Quick startup script for testing the enhanced PrepIQ backend
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def setup_environment():
    """Setup basic environment variables for testing."""
    env_vars = {
        'DEBUG': 'True',
        'ENVIRONMENT': 'development',
        'SECRET_KEY': 'test-secret-key-for-development-only',
        'DATABASE_URL': 'sqlite:///./test.db',
        'SUPABASE_URL': '',
        'SUPABASE_KEY': '',
        'GOOGLE_API_KEY': '',
        'LOG_LEVEL': 'INFO'
    }
    
    for key, value in env_vars.items():
        if not os.getenv(key):
            os.environ[key] = value

def download_nltk_data():
    """Download required NLTK data."""
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        print("✓ NLTK data downloaded successfully")
    except Exception as e:
        print(f"⚠ Warning: Failed to download NLTK data: {e}")

def test_ml_models():
    """Test basic ML model functionality."""
    try:
        print("Testing ML models...")
        
        # Test Progress Forecaster
        from app.ml.engines.progress_forecaster import SimpleProgressRegressor
        model = SimpleProgressRegressor()
        print("✓ Progress Forecaster loaded")
        
        # Test Topic Recommender
        from app.ml.engines.topic_recommender import TopicRecommender
        recommender = TopicRecommender()
        print("✓ Topic Recommender loaded")
        
        # Test Focus Area Identifier
        from app.ml.engines.focus_area_identifier import FocusAreaIdentifier
        identifier = FocusAreaIdentifier()
        print("✓ Focus Area Identifier loaded")
        
        # Test Question Analyzer
        from app.ml.engines.question_importance import LightweightQuestionAnalyzer
        analyzer = LightweightQuestionAnalyzer()
        print("✓ Question Analyzer loaded")
        
        print("✓ All ML models loaded successfully")
        return True
        
    except Exception as e:
        print(f"✗ ML model test failed: {e}")
        return False

def test_core_components():
    """Test core application components."""
    try:
        print("Testing core components...")
        
        # Test configuration
        from app.core.config import settings
        print(f"✓ Configuration loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
        
        # Test logging
        from app.core.logging import get_logger
        logger = get_logger("test")
        logger.info("Logging system working")
        print("✓ Logging system working")
        
        # Test database models
        from app.models.enhanced_models import User, Subject, Topic
        print("✓ Database models loaded")
        
        return True
        
    except Exception as e:
        print(f"✗ Core component test failed: {e}")
        return False

def main():
    """Main startup function."""
    print("=" * 50)
    print("PrepIQ Enhanced Backend - Quick Test")
    print("=" * 50)
    
    # Setup environment
    print("Setting up environment...")
    setup_environment()
    print("✓ Environment configured")
    
    # Download NLTK data
    download_nltk_data()
    
    # Test components
    core_success = test_core_components()
    ml_success = test_ml_models()
    
    print("\n" + "=" * 50)
    if core_success and ml_success:
        print("🎉 All tests passed! Backend is ready.")
        print("\nTo start the server:")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("\nAPI Documentation will be available at:")
        print("  http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        if not core_success:
            print("  Core components failed to load")
        if not ml_success:
            print("  ML models failed to load")
    print("=" * 50)

if __name__ == "__main__":
    main()