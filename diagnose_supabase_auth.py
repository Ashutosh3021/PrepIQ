"""
Diagnostic script to identify why users aren't being created in Supabase
"""
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('frontend/.env.local')  # Load frontend environment variables

def test_supabase_config():
    """Test Supabase configuration and connectivity"""
    print("=== SUPABASE CONFIGURATION TEST ===")
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    next_public_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    next_public_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_SERVICE_KEY: {supabase_service_key[:10]}..." if supabase_service_key else "NOT SET")
    print(f"NEXT_PUBLIC_SUPABASE_URL: {next_public_url}")
    print(f"NEXT_PUBLIC_SUPABASE_ANON_KEY: {next_public_key[:10]}..." if next_public_key else "NOT SET")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase configuration in backend")
        return False
    
    if not next_public_url or not next_public_key:
        print("❌ Missing Supabase configuration in frontend")
        return False
    
    # Test connection with service key
    try:
        supabase: Client = create_client(supabase_url, supabase_service_key)
        print("✅ Supabase service client initialized successfully")
        
        # Test admin access
        try:
            users = supabase.auth.admin.list_users()
            print(f"✅ Admin access working - Found {len(users.data or [])} users")
            return True
        except Exception as e:
            print(f"❌ Admin access failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Supabase client initialization failed: {e}")
        return False

def test_direct_user_creation():
    """Test creating a user directly with Supabase service key"""
    print("\n=== DIRECT USER CREATION TEST ===")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Cannot test - missing configuration")
        return False
    
    supabase: Client = create_client(supabase_url, supabase_service_key)
    
    # Test user data
    test_email = "test-user-diagnostic@prepiq.com"
    test_password = "TestPassword123!"
    
    print(f"Creating test user: {test_email}")
    
    try:
        # Try to create user with service key (admin method)
        response = supabase.auth.admin.create_user({
            "email": test_email,
            "password": test_password,
            "email_confirm": True,  # Skip email confirmation
            "user_metadata": {
                "full_name": "Test User",
                "test": True
            }
        })
        
        print("✅ User created successfully with service key")
        print(f"User ID: {response.data['user']['id']}")
        print(f"Email: {response.data['user']['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create user with service key: {e}")
        
        # Try alternative approach - direct signup with client
        try:
            print("Trying client signup approach...")
            client_supabase = create_client(supabase_url, supabase_service_key)
            signup_response = client_supabase.auth.sign_up({
                "email": test_email,
                "password": test_password,
                "options": {
                    "data": {
                        "full_name": "Test User",
                        "test": True
                    }
                }
            })
            
            print("✅ User created successfully with signup method")
            print(f"User ID: {signup_response.data['user']['id']}")
            print(f"Email: {signup_response.data['user']['email']}")
            return True
            
        except Exception as e2:
            print(f"❌ Failed with signup method too: {e2}")
            return False

def check_email_confirmation_settings():
    """Check if email confirmation is enabled (which might prevent user visibility)"""
    print("\n=== EMAIL CONFIRMATION CHECK ===")
    
    # This would require checking Supabase dashboard settings
    # For now, we'll suggest manual verification
    print("Please check your Supabase dashboard:")
    print("1. Go to: Authentication → Providers → Email")
    print("2. Check if 'Confirm Email' is enabled")
    print("3. If enabled, users won't appear until they confirm their email")
    print("4. Consider disabling email confirmation for testing")

def check_triggers_and_policies():
    """Check for triggers that might be failing"""
    print("\n=== DATABASE TRIGGERS CHECK ===")
    
    print("Check if there are any triggers on auth.users table:")
    print("1. In Supabase dashboard: Database → Triggers")
    print("2. Look for any triggers on auth.users")
    print("3. Disable any problematic triggers for testing")
    
    print("\nCheck RLS policies:")
    print("1. In Supabase dashboard: Database → Tables → auth.users")
    print("2. Check if there are RLS policies that might block reads")

def suggested_fixes():
    """Provide step-by-step fixes"""
    print("\n=== SUGGESTED FIXES ===")
    
    fixes = [
        "1. **Add detailed error logging** in backend supabase_auth.py:",
        "   - Log the full exception details, not just a generic message",
        "   - Don't silently continue on Supabase failure",
        "",
        "2. **Fix the signup method** in backend/services/supabase_auth.py:",
        "   - Use admin.create_user() instead of sign_up() with service key",
        "   - Handle email confirmation properly",
        "",
        "3. **Update backend supabase client usage**:",
        "   - Use create_client() for admin operations, not the client auth methods",
        "",
        "4. **Disable email confirmation** in Supabase dashboard temporarily",
        "",
        "5. **Check and disable failing triggers** on auth.users table",
        "",
        "6. **Add proper error handling** to show users when Supabase operations fail"
    ]
    
    for fix in fixes:
        print(fix)

if __name__ == "__main__":
    print("PrepIQ Supabase Authentication Diagnostic Tool")
    print("=" * 50)
    
    # Run all tests
    config_ok = test_supabase_config()
    if config_ok:
        creation_ok = test_direct_user_creation()
        if not creation_ok:
            print("\n🔍 Since user creation failed, here's the detailed analysis:")
            print("The issue is likely in your backend signup logic in services/supabase_auth.py")
            print("The current implementation tries to use sign_up() with service key, which doesn't work")
    
    check_email_confirmation_settings()
    check_triggers_and_policies()
    suggested_fixes()
    
    print("\n" + "=" * 50)
    print("Diagnostic complete. Please implement the suggested fixes above.")