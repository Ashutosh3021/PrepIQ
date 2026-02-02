import os
from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

def add_all_missing_columns():
    """Add all missing columns that our application model expects to the users table"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Add missing columns that our application model expects
            # These are the columns defined in our User model in models.py
            
            # Add language column if it doesn't exist
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
            """))
            
            # Add college_name column if it doesn't exist
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS college_name VARCHAR(255);
            """))
            
            # Add program column if it doesn't exist
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS program VARCHAR(100);
            """))
            
            # Add year_of_study column if it doesn't exist
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS year_of_study INTEGER;
            """))
            
            # Add exam_date column if it doesn't exist
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS exam_date TIMESTAMP WITH TIME ZONE;
            """))
            
            # Add email_verified column if it doesn't exist
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
            """))
            
            # Add deleted_at column if it doesn't exist
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
            """))
            
            # Commit the transaction
            connection.commit()
            
            print("Added all missing columns to users table")
            
            # Verify the columns were added
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name IN ('language', 'college_name', 'program', 'year_of_study', 'exam_date', 'email_verified', 'deleted_at')
            """))
            
            columns = [row.column_name for row in result]
            expected_columns = ['language', 'college_name', 'program', 'year_of_study', 'exam_date', 'email_verified', 'deleted_at']
            
            print("Verification results:")
            for col in expected_columns:
                if col in columns:
                    print(f"✅ '{col}' column exists/added")
                else:
                    print(f"❌ '{col}' column missing")
                    
            print(f"\nTotal expected columns: {len(expected_columns)}")
            print(f"Columns found: {len([col for col in expected_columns if col in columns])}")
                
    except Exception as e:
        print(f"Error adding missing columns: {e}")
        # Rollback in case of error
        try:
            connection.rollback()
        except:
            pass

if __name__ == "__main__":
    add_all_missing_columns()