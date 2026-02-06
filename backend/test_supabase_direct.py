import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection and user creation"""
    print("=== Supabase Connection Test ===")
    
    # Use the credentials from your .env file
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase environment variables not set properly")
        print(f"URL: {SUPABASE_URL}")
        print(f"Key length: {len(SUPABASE_SERVICE_KEY) if SUPABASE_SERVICE_KEY else 'NOT FOUND'}")
        return False
    
    print(f"Using URL: {SUPABASE_URL}")
    
    try:
        print("Creating Supabase client...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client created successfully")
        
        # Test admin access
        print("Testing admin access...")
        try:
            response = supabase.auth.admin.list_users()
            # For Supabase v2, the response format is different
            if hasattr(response, 'data') and 'users' in response.data:
                users_data = response.data['users']
            else:
                users_data = []
            print(f"✅ Admin access working - {len(users_data)} existing users found")
            
            # Show existing users
            if users_data:
                print("Existing users:")
                for user in users_data[:3]:  # Show first 3 users
                    email = user.email if hasattr(user, 'email') else getattr(user, 'email', 'N/A')
                    created = user.created_at if hasattr(user, 'created_at') else getattr(user, 'created_at', 'N/A')
                    confirmed = "✅" if (hasattr(user, 'email_confirmed_at') and user.email_confirmed_at) else "❌"
                    print(f"  {email} - {created} - Confirmed: {confirmed}")
        except Exception as e:
            print(f"⚠️  Admin access test failed: {e}")
            print("Continuing with user creation test...")
            users_data = []
        
        # Test creating a user with a unique email
        import random
        import string
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        test_email = f"debug-test-{random_suffix}@example.com"
        test_password = "DebugTest123"
        
        print(f"\nTesting user creation with email: {test_email}")
        
        # Create test user directly
        print("Creating test user...")
        try:
            result = supabase.auth.admin.create_user({
                "email": test_email,
                "password": test_password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": "Debug Test User",
                    "test": True
                }
            })
            
            # Handle the response format
            user_id = None
            if hasattr(result, 'data') and 'user' in result.data:
                user = result.data['user']
                user_id = user.id if hasattr(user, 'id') else getattr(user, 'id', None)
            elif hasattr(result, 'user'):
                user = result.user
                user_id = user.id if hasattr(user, 'id') else getattr(user, 'id', None)
            
            if user_id:
                print(f"✅ Test user created successfully: {user_id}")
            else:
                print("❌ Failed to create test user - no user ID returned")
                print(f"Response type: {type(result)}")
                print(f"Response attributes: {dir(result) if hasattr(result, '__dict__') else 'No __dict__'}")
                return False
        except Exception as e:
            print(f"❌ Failed to create test user: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Verify user exists by trying to sign in
        print("Verifying user can sign in...")
        try:
            sign_in_result = supabase.auth.sign_in_with_password({
                "email": test_email,
                "password": test_password
            })
            
            user_verified = False
            if hasattr(sign_in_result, 'data') and 'user' in sign_in_result.data:
                user_verified = True
            elif hasattr(sign_in_result, 'user'):
                user_verified = True
            
            if user_verified:
                print("✅ User can sign in successfully")
            else:
                print("❌ User sign in failed")
                return False
        except Exception as e:
            print(f"❌ User verification failed: {e}")
            return False
        
        # Clean up
        print("Cleaning up test user...")
        try:
            if user_id:
                supabase.auth.admin.delete_user(user_id)
                print("✅ Test user cleaned up")
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False

def test_local_database():
    """Check local database users"""
    print("\n=== Local Database Check ===")
    
    try:
        import sqlite3
        db_path = "./prepiq_local.db"
        
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("❌ 'users' table not found")
            conn.close()
            return False
            
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM users;")
        count = cursor.fetchone()[0]
        print(f"✅ Found {count} users in local database")
        
        # Show recent users
        cursor.execute("SELECT id, email, full_name, created_at FROM users ORDER BY created_at DESC LIMIT 5;")
        users = cursor.fetchall()
        
        if users:
            print("Recent users:")
            for user in users:
                print(f"  {user[1]} ({user[2]}) - {user[3]}")
        else:
            print("No users found in local database")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Local database check failed: {e}")
        return False

if __name__ == "__main__":
    print("PrepIQ Supabase Authentication Diagnostic")
    print("=" * 50)
    
    # Test local database first
    local_ok = test_local_database()
    
    # Test Supabase connection
    supabase_ok = test_supabase_connection()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"  Local database: {'✅ OK' if local_ok else '❌ FAILED'}")
    print(f"  Supabase connection: {'✅ OK' if supabase_ok else '❌ FAILED'}")
    
    if local_ok and not supabase_ok:
        print("\n🔍 DIAGNOSIS: Users are being created locally but not syncing to Supabase")
        print("   This confirms the hybrid approach issue described in the debug guide.")
    elif not local_ok and not supabase_ok:
        print("\n🚨 CRITICAL: Both local database and Supabase are failing")
    elif local_ok and supabase_ok:
        print("\n✅ Both systems are working - the issue might be in the sync logic")