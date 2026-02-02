import os
from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

def add_missing_columns():
    """Add missing columns to the users table"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Add language column if it doesn't exist
            connection.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
            """))
            
            # Commit the transaction
            connection.commit()
            
            print("Added missing 'language' column to users table")
            
            # Verify the column was added
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'language'
            """))
            
            columns = [row.column_name for row in result]
            if 'language' in columns:
                print("✅ Successfully added 'language' column")
            else:
                print("❌ Failed to add 'language' column")
                
    except Exception as e:
        print(f"Error adding missing columns: {e}")
        # Rollback in case of error
        try:
            connection.rollback()
        except:
            pass

if __name__ == "__main__":
    add_missing_columns()