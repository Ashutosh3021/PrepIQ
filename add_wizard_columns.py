import sqlite3
import os

def add_wizard_columns():
    """Add wizard-related columns to the users table"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'backend', 'prepiq_local.db')
    
    # SQL to add new columns
    alter_sql = """
    ALTER TABLE users 
    ADD COLUMN wizard_completed BOOLEAN DEFAULT FALSE;
    
    ALTER TABLE users 
    ADD COLUMN exam_name TEXT;
    
    ALTER TABLE users 
    ADD COLUMN days_until_exam INTEGER;
    
    ALTER TABLE users 
    ADD COLUMN focus_subjects TEXT;
    
    ALTER TABLE users 
    ADD COLUMN study_hours_per_day INTEGER;
    
    ALTER TABLE users 
    ADD COLUMN target_score INTEGER;
    
    ALTER TABLE users 
    ADD COLUMN preparation_level TEXT;
    """
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_columns = ['wizard_completed', 'exam_name', 'days_until_exam', 'focus_subjects', 
                      'study_hours_per_day', 'target_score', 'preparation_level']
        
        columns_to_add = [col for col in new_columns if col not in columns]
        
        if columns_to_add:
            print(f"Adding columns: {', '.join(columns_to_add)}")
            
            # Add each column individually to avoid SQLite limitations
            for column in columns_to_add:
                if column == 'wizard_completed':
                    cursor.execute("ALTER TABLE users ADD COLUMN wizard_completed BOOLEAN DEFAULT FALSE")
                elif column == 'exam_name':
                    cursor.execute("ALTER TABLE users ADD COLUMN exam_name TEXT")
                elif column == 'days_until_exam':
                    cursor.execute("ALTER TABLE users ADD COLUMN days_until_exam INTEGER")
                elif column == 'focus_subjects':
                    cursor.execute("ALTER TABLE users ADD COLUMN focus_subjects TEXT")
                elif column == 'study_hours_per_day':
                    cursor.execute("ALTER TABLE users ADD COLUMN study_hours_per_day INTEGER")
                elif column == 'target_score':
                    cursor.execute("ALTER TABLE users ADD COLUMN target_score INTEGER")
                elif column == 'preparation_level':
                    cursor.execute("ALTER TABLE users ADD COLUMN preparation_level TEXT")
            
            conn.commit()
            print("Successfully added wizard columns to users table")
        else:
            print("All wizard columns already exist")
            
    except Exception as e:
        print(f"Error adding columns: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_wizard_columns()