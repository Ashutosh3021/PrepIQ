#!/usr/bin/env python3
"""
Simple test script for PrepIQ backend components
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_basic_imports():
    """Test basic imports without heavy dependencies."""
    try:
        print("Testing basic imports...")
        
        # Test core components
        from app.core.config import settings
        print(f"✓ Configuration: {settings.APP_NAME}")
        
        from app.core.logging import get_logger
        logger = get_logger("test")
        logger.info("Logging works")
        print("✓ Logging system")
        
        # Test basic models
        from app.models.enhanced_models import User, Subject
        print("✓ Database models")
        
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_simple_ml():
    """Test simplified ML components."""
    try:
        print("Testing simplified ML components...")
        
        # Test basic ML structure (without heavy dependencies)
        from app.ml.core.base_model import BaseModel
        print("✓ Base ML model class")
        
        # Test simple progress forecaster
        from app.ml.engines.progress_forecaster import SimpleProgressRegressor
        model = SimpleProgressRegressor()
        print("✓ Simple progress regressor")
        
        return True
    except Exception as e:
        print(f"✗ Simple ML test failed: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 50)
    print("PrepIQ Backend - Basic Component Test")
    print("=" * 50)
    
    # Set minimal environment
    os.environ['DEBUG'] = 'True'
    os.environ['SECRET_KEY'] = 'test-key'
    os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
    
    # Run tests
    basic_success = test_basic_imports()
    ml_success = test_simple_ml()
    
    print("\n" + "=" * 50)
    if basic_success and ml_success:
        print("🎉 Basic tests passed!")
        print("\nNext steps:")
        print("1. Install full requirements: pip install -r requirements-full.txt")
        print("2. Run complete test: python quick_start.py")
        print("3. Start server: uvicorn main:app --reload")
    else:
        print("❌ Some tests failed")
        if not basic_success:
            print("  Basic imports failed")
        if not ml_success:
            print("  ML components failed")
    print("=" * 50)

if __name__ == "__main__":
    main()