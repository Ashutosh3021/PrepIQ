import os
from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

def create_app_users_table():
    """Create a separate app_users table that links to auth.users"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Create app_users table with foreign key reference to auth.users
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS app_users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    auth_user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
                    full_name VARCHAR(255),
                    college_name VARCHAR(255),
                    program VARCHAR(100),
                    year_of_study INTEGER,
                    theme_preference VARCHAR(20) DEFAULT 'system',
                    language VARCHAR(10) DEFAULT 'en',
                    exam_date TIMESTAMP WITH TIME ZONE,
                    email_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    deleted_at TIMESTAMP WITH TIME ZONE
                );
            """))
            
            # Commit the transaction
            connection.commit()
            
            print("Created app_users table successfully")
            
            # Verify the table was created
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'app_users'
            """))
            
            tables = [row.table_name for row in result]
            if 'app_users' in tables:
                print("✅ Successfully created 'app_users' table")
            else:
                print("❌ Failed to create 'app_users' table")
                
    except Exception as e:
        print(f"Error creating app_users table: {e}")
        # Rollback in case of error
        try:
            connection.rollback()
        except:
            pass

if __name__ == "__main__":
    create_app_users_table()