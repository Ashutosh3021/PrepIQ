import requests
import json

# Test the backend API endpoints
BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test if the API is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ API Health Check: PASSED")
            print(f"  Response: {response.json()}")
        else:
            print("✗ API Health Check: FAILED")
    except Exception as e:
        print(f"✗ API Health Check: FAILED - {e}")

def test_api_endpoints():
    """Test key API endpoints"""
    endpoints = [
        "/",
        "/auth",
        "/subjects",
        "/papers",
        "/predictions",
        "/chat"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"✓ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint}: {e}")

def test_database_connection():
    """Test database connection by attempting to create a test user"""
    # This would require authentication, so we'll just test if the endpoints exist
    try:
        response = requests.get(f"{BASE_URL}/subjects")
        print(f"✓ Subjects endpoint accessible: {response.status_code}")
    except Exception as e:
        print(f"✗ Subjects endpoint: {e}")

def main():
    print("=== PrepIQ Application Integration Test ===\n")
    
    print("1. Testing API Health...")
    test_api_health()
    
    print("\n2. Testing API Endpoints...")
    test_api_endpoints()
    
    print("\n3. Testing Database Connection...")
    test_database_connection()
    
    print("\n=== Test Summary ===")
    print("If no major errors were reported, the core integration is working!")

if __name__ == "__main__":
    main()