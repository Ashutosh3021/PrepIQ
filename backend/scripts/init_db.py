#!/usr/bin/env python3
"""
PrepIQ Database Initialization Script

This script initializes the database schema on a fresh Supabase PostgreSQL instance.
It creates all tables, indexes, and sets up Row Level Security (RLS) policies.

Usage:
    python scripts/init_db.py
    
Environment Variables Required:
    - DATABASE_URL: Supabase PostgreSQL connection string
    - SUPABASE_URL: Supabase project URL
    - SUPABASE_SERVICE_KEY: Supabase service role key
"""

import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Verify all required environment variables are set"""
    required_vars = [
        'DATABASE_URL',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file")
        sys.exit(1)
    
    print("✅ All required environment variables are set")

def test_connection():
    """Test database connection"""
    try:
        from app.database import engine
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Database connection successful")
            print(f"   PostgreSQL version: {version}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_tables():
    """Create all database tables"""
    try:
        from app.database import engine
        from app.models import Base
        
        print("\n📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def verify_tables():
    """Verify all expected tables were created"""
    try:
        from app.database import engine
        
        expected_tables = [
            'users',
            'subjects',
            'question_papers',
            'questions',
            'predictions',
            'chat_history',
            'mock_tests',
            'study_plans'
        ]
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            existing_tables = {row[0] for row in result}
        
        print("\n📋 Verifying tables:")
        all_found = True
        for table in expected_tables:
            if table in existing_tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} - NOT FOUND")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Failed to verify tables: {e}")
        return False

def print_rls_instructions():
    """Print instructions for setting up RLS policies"""
    print("\n" + "="*60)
    print("ROW LEVEL SECURITY (RLS) SETUP INSTRUCTIONS")
    print("="*60)
    print("""
You MUST manually configure RLS policies in the Supabase dashboard:

1. Enable RLS on all tables:
   Go to: Database → Tables → [table_name] → Policies
   Enable RLS for each table

2. Create RLS policies for each table:

   **users table:**
   - Policy: "Users can view own profile"
     Operation: SELECT
     Expression: auth.uid() = id
   
   - Policy: "Users can update own profile"
     Operation: UPDATE
     Expression: auth.uid() = id

   **subjects table:**
   - Policy: "Users can view own subjects"
     Operation: ALL
     Expression: auth.uid() = user_id

   **question_papers, questions, predictions, chat_history, 
   mock_tests, study_plans tables:**
   - Policy: "Users can access own data"
     Operation: ALL
     Expression: auth.uid() IN (
       SELECT user_id FROM subjects WHERE id = subject_id
     )
     
     OR for tables with direct user_id:
     Expression: auth.uid() = user_id

3. Create indexes for performance:
   The following indexes are automatically created by SQLAlchemy:
   - idx_users_email
   - idx_subjects_user_id
   - idx_question_papers_subject_id
   - idx_questions_paper_id
   - idx_predictions_user_id
   - idx_chat_history_user_id
   - idx_mock_tests_user_id
   - idx_study_plans_user_id

For more details, see: RLS_POLICIES.md
""")

def print_next_steps():
    """Print next steps after initialization"""
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("""
1. ✅ Database schema created
2. 📝 Set up RLS policies (see instructions above)
3. 🔑 Configure Supabase Auth providers
4. 🚀 Start the backend server:
   cd backend && python -m app.main
5. 🧪 Run tests to verify everything works

For troubleshooting, check:
- Database connection: Verify DATABASE_URL is correct
- Supabase connection: Verify SUPABASE_URL and SUPABASE_SERVICE_KEY
- Logs: Check app.log for detailed error messages
""")

def main():
    """Main initialization function"""
    print("="*60)
    print("PREPIQ DATABASE INITIALIZATION")
    print("="*60)
    
    # Check environment
    print("\n🔍 Checking environment variables...")
    check_environment()
    
    # Test connection
    print("\n🔌 Testing database connection...")
    if not test_connection():
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        sys.exit(1)
    
    # Verify tables
    if not verify_tables():
        print("\n⚠️  Some tables were not created. Check the error messages above.")
        sys.exit(1)
    
    # Print RLS instructions
    print_rls_instructions()
    
    # Print next steps
    print_next_steps()
    
    print("\n✅ Database initialization complete!")
    print("="*60)

if __name__ == "__main__":
    main()
