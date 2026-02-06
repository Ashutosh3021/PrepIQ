"""
Migration script to move users from local database to new Supabase project
Use this after creating a new Supabase project and updating environment variables
"""

import os
import sqlite3
from supabase import create_client, Client
import sys

def migrate_users_to_supabase():
    """Migrate all users from local SQLite to Supabase"""
    
    # Get new Supabase credentials (should be updated in .env)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase credentials not found in environment variables")
        print("Please update your .env file with new Supabase project credentials")
        return False
    
    print(f"Using Supabase URL: {SUPABASE_URL}")
    
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client connected")
        
        # Test connection
        response = supabase.auth.admin.list_users()
        print(f"✅ Supabase admin access working - {len(response.data['users'])} existing users")
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False
    
    try:
        # Connect to local database
        conn = sqlite3.connect('./prepiq_local.db')
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("""
            SELECT id, email, password_hash, full_name, college_name, program, year_of_study, created_at 
            FROM users 
            ORDER BY created_at
        """)
        users = cursor.fetchall()
        
        print(f"Found {len(users)} users in local database")
        
        migrated_count = 0
        failed_count = 0
        
        for user in users:
            user_id, email, password_hash, full_name, college_name, program, year_of_study, created_at = user
            
            try:
                print(f"Migrating user: {email}")
                
                # Create user in Supabase
                # Note: We can't migrate password hashes directly, so we'll need to:
                # 1. Create user with temporary password
                # 2. Let them reset password, or
                # 3. Use a default password and notify users
                
                temp_password = f"TempPass123!"  # You should change this or implement proper password reset
                
                result = supabase.auth.admin.create_user({
                    "email": email,
                    "password": temp_password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": full_name or "",
                        "college_name": college_name or "",
                        "program": program or "",
                        "year_of_study": year_of_study or 1,
                        "migrated_from_local": True,
                        "migration_date": created_at
                    }
                })
                
                print(f"✅ Migrated: {email} -> {result.data['user']['id']}")
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Failed to migrate {email}: {e}")
                failed_count += 1
                continue
        
        conn.close()
        
        print(f"\n=== Migration Summary ===")
        print(f"Total users: {len(users)}")
        print(f"Successfully migrated: {migrated_count}")
        print(f"Failed: {failed_count}")
        
        if failed_count == 0:
            print("✅ All users migrated successfully!")
            return True
        else:
            print(f"⚠️  {failed_count} users failed to migrate")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify that users exist in new Supabase project"""
    try:
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        response = supabase.auth.admin.list_users()
        users = response.data['users']
        
        print(f"=== Supabase Users ({len(users)} total) ===")
        for user in users:
            metadata = user.get('user_metadata', {})
            migrated = metadata.get('migrated_from_local', False)
            print(f"  {user['email']} - {'[MIGRATED]' if migrated else '[NEW]'} - {user['created_at']}")
            
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("PrepIQ User Migration Tool")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        print("Verifying current Supabase users...")
        verify_migration()
    else:
        print("Migrating users from local database to Supabase...")
        success = migrate_users_to_supabase()
        
        if success:
            print("\nVerifying migration...")
            verify_migration()