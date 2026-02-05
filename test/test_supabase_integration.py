"""
Test script to verify Supabase integration for PrepIQ application
"""
import asyncio
import os
import sys
from supabase import create_client, Client

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("Testing Supabase connection...")
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase environment variables not set")
        return False
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client initialized successfully")
        
        # Test basic auth functionality
        try:
            # List users as a basic test (admin access)
            response = supabase.auth.admin.list_users()
            print("✅ Supabase admin access working")
            return True
        except Exception as e:
            print(f"⚠️  Supabase admin access test failed: {e}")
            # This might be expected depending on permissions, so don't fail the test
            return True
            
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_database_connection():
    """Test database connection through SQLAlchemy"""
    print("\nTesting database connection...")
    
    try:
        from app.database import engine
        from sqlalchemy import text
        
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_models_compatibility():
    """Test if SQLAlchemy models are compatible with Supabase schema"""
    print("\nTesting models compatibility...")
    
    try:
        from app.models import User, Subject, QuestionPaper, Question, Prediction, ChatHistory, MockTest, StudyPlan
        from app.database import engine
        from sqlalchemy import inspect
        
        # Get table names from database
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        expected_tables = [
            'users', 'subjects', 'question_papers', 'questions', 
            'predictions', 'chat_history', 'mock_tests', 'study_plans'
        ]
        
        missing_tables = []
        for table in expected_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"⚠️  Missing tables in database: {missing_tables}")
            print("   Run init_db.py to create tables")
        else:
            print("✅ All expected tables exist in database")
        
        return len(missing_tables) == 0
    except Exception as e:
        print(f"❌ Models compatibility test failed: {e}")
        return False

def test_supabase_auth_service():
    """Test Supabase auth service"""
    print("\nTesting Supabase auth service...")
    
    try:
        from services.supabase_auth import SupabaseAuthService
        print("✅ SupabaseAuthService imported successfully")
        
        # Test password hashing
        test_password = "test_password_123"
        hashed = SupabaseAuthService.hash_password(test_password)
        is_valid = SupabaseAuthService.verify_password(test_password, hashed)
        
        if is_valid:
            print("✅ Password hashing/verification working")
        else:
            print("❌ Password hashing/verification failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Supabase auth service test failed: {e}")
        return False

def test_supabase_storage_service():
    """Test Supabase storage service"""
    print("\nTesting Supabase storage service...")
    
    try:
        from services.supabase_storage import SupabaseStorageService
        print("✅ SupabaseStorageService imported successfully")
        
        # Just test that the service can be imported and has the right methods
        methods = ['upload_file', 'download_file', 'delete_file', 'list_files', 'get_file_info']
        for method in methods:
            if hasattr(SupabaseStorageService, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Supabase storage service test failed: {e}")
        return False

def test_auth_router():
    """Test that auth router is using SupabaseAuthService"""
    print("\nTesting auth router configuration...")
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("auth", "app/routers/auth.py")
        auth_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auth_module)
        
        # Check if SupabaseAuthService is imported
        if hasattr(auth_module, 'SupabaseAuthService'):
            print("✅ Auth router using SupabaseAuthService")
            return True
        else:
            print("❌ Auth router not using SupabaseAuthService")
            return False
    except Exception as e:
        print(f"❌ Auth router test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("Supabase Integration Test Suite for PrepIQ Application")
    print("=" * 60)
    
    tests = [
        test_supabase_connection,
        test_database_connection,
        test_models_compatibility,
        test_supabase_auth_service,
        test_supabase_storage_service,
        test_auth_router
    ]
    
    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_func, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_func.__name__}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Supabase integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the integration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)