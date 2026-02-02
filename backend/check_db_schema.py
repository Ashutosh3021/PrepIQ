import os
from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

def check_users_table_schema():
    """Check the schema of the users table"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Query to check columns in the users table
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))
            
            print("Columns in users table:")
            for row in result:
                print(f"  {row.column_name}: {row.data_type}")
                
            # Check specifically for language and theme_preference columns
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name IN ('language', 'theme_preference')
            """))
            
            found_columns = [row.column_name for row in result]
            print(f"\nFound language and theme_preference columns: {found_columns}")
            
            if 'language' not in found_columns:
                print("❌ Missing 'language' column")
            else:
                print("✅ 'language' column exists")
                
            if 'theme_preference' not in found_columns:
                print("❌ Missing 'theme_preference' column")
            else:
                print("✅ 'theme_preference' column exists")
                
    except Exception as e:
        print(f"Error checking database schema: {e}")

if __name__ == "__main__":
    check_users_table_schema()