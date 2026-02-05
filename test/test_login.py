import requests
import json

# Test the login endpoint
BASE_URL = "http://localhost:8000"

def test_login():
    """Test the login endpoint to ensure it's working"""
    try:
        # Try to login with a test user (this will fail with wrong credentials, but shouldn't crash)
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json={"email": "test@example.com", "password": "test123"},
                               headers={"Content-Type": "application/json"})
        print(f"Login endpoint response: {response.status_code}")
        if response.status_code == 401:  # Expected for wrong credentials
            print("✓ Login endpoint is working correctly (returning 401 for invalid credentials)")
        elif response.status_code == 200:
            print("Login successful")
        else:
            print(f"Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"✗ Login endpoint error: {e}")

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health endpoint response: {response.status_code}")
        if response.status_code == 200:
            print("✓ Health endpoint is working correctly")
        else:
            print(f"✗ Health endpoint unexpected response: {response.status_code}")
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")

if __name__ == "__main__":
    print("Testing backend endpoints after database fix...")
    test_health()
    test_login()