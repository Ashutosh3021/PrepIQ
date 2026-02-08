from fastapi.testclient import TestClient
from main import app
import json

# Create test client
client = TestClient(app)

def test_dashboard_endpoint():
    """Test the dashboard stats endpoint to identify the exact issue"""
    print("Testing dashboard stats endpoint...")
    
    # First, let's try to get a valid token by simulating a login
    # Since we don't have actual credentials, let's test with a mock approach
    
    try:
        # Test the endpoint without authentication first to see the error
        response = client.get("/api/dashboard/stats")
        print(f"Response without auth: {response.status_code}")
        if response.status_code == 403:
            print("✓ Authentication required (expected)")
        else:
            print(f"? Unexpected status: {response.status_code}")
            
        # Test with a mock authorization header
        response = client.get("/api/dashboard/stats", headers={"Authorization": "Bearer fake-token"})
        print(f"Response with fake token: {response.status_code}")
        if response.status_code == 500:
            print("✓ Got 500 error (expected with fake token)")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print("Could not parse error response")
        else:
            print(f"? Unexpected status with fake token: {response.status_code}")
            
    except Exception as e:
        print(f"Error during testing: {e}")

def test_database_connection():
    """Test database connection and queries directly"""
    print("\nTesting database connection...")
    
    try:
        from app.database import get_db
        from app import models
        from sqlalchemy import text
        
        # Test database connection
        db = next(get_db())
        print("✓ Database connection successful")
        
        # Test basic query
        result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"✓ Users count: {result}")
        
        # Test subjects query
        result = db.execute(text("SELECT COUNT(*) FROM subjects")).scalar()
        print(f"✓ Subjects count: {result}")
        
        # Test predictions query
        result = db.execute(text("SELECT COUNT(*) FROM predictions")).scalar()
        print(f"✓ Predictions count: {result}")
        
        db.close()
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")

if __name__ == "__main__":
    print("Debugging dashboard 500 errors...")
    print("=" * 50)
    
    test_database_connection()
    test_dashboard_endpoint()
    
    print("\n" + "=" * 50)
    print("Debugging complete")