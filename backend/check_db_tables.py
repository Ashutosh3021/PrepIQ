from app.database import engine
from sqlalchemy import text

def check_database_tables():
    """Check if database tables exist and are accessible"""
    try:
        with engine.connect() as conn:
            # Get all tables
            result = conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
            tables = [row[0] for row in result]
            print(f"Database tables: {tables}")
            
            # Check if users table exists
            if 'users' in tables:
                user_count = conn.execute(text('SELECT COUNT(*) FROM users')).scalar()
                print(f"Users table has {user_count} records")
            else:
                print("Users table not found!")
                
            # Check if subjects table exists
            if 'subjects' in tables:
                subject_count = conn.execute(text('SELECT COUNT(*) FROM subjects')).scalar()
                print(f"Subjects table has {subject_count} records")
            else:
                print("Subjects table not found!")
                
            # Check if predictions table exists
            if 'predictions' in tables:
                prediction_count = conn.execute(text('SELECT COUNT(*) FROM predictions')).scalar()
                print(f"Predictions table has {prediction_count} records")
            else:
                print("Predictions table not found!")
                
        return True
    except Exception as e:
        print(f"Error checking database tables: {e}")
        return False

if __name__ == "__main__":
    print("Checking database tables...")
    check_database_tables()