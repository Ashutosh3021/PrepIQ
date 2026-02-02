import requests
import json

def test_all_endpoints():
    """Test all critical endpoints"""
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health endpoint is working")
        else:
            print(f"❌ Health endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test CORS preflight for auth endpoints
    print("\nTesting CORS for login endpoint...")
    try:
        response = requests.options(
            f"{base_url}/auth/login",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        print(f"Login CORS preflight: {response.status_code}")
        origin_header = response.headers.get('Access-Control-Allow-Origin')
        if origin_header and 'localhost:3001' in origin_header:
            print("✅ Login CORS is properly configured")
        else:
            print(f"❌ Login CORS issue: {origin_header}")
    except Exception as e:
        print(f"❌ Login CORS error: {e}")
    
    print("\nTesting CORS for signup endpoint...")
    try:
        response = requests.options(
            f"{base_url}/auth/signup",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        print(f"Signup CORS preflight: {response.status_code}")
        origin_header = response.headers.get('Access-Control-Allow-Origin')
        if origin_header and 'localhost:3001' in origin_header:
            print("✅ Signup CORS is properly configured")
        else:
            print(f"❌ Signup CORS issue: {origin_header}")
    except Exception as e:
        print(f"❌ Signup CORS error: {e}")
    
    # Test login with invalid credentials (should return 401, not 500)
    print("\nTesting login endpoint...")
    try:
        response = requests.post(
            f"{base_url}/auth/login",
            headers={"Content-Type": "application/json"},
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        print(f"Login endpoint: {response.status_code}")
        if response.status_code == 401:
            print("✅ Login endpoint is working correctly (returning 401 for invalid credentials)")
        else:
            print(f"❌ Login endpoint unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Login endpoint error: {e}")
    
    # Test signup with sample data
    print("\nTesting signup endpoint...")
    import uuid
    test_email = f"test_{uuid.uuid4()}@example.com"
    try:
        response = requests.post(
            f"{base_url}/auth/signup",
            headers={"Content-Type": "application/json"},
            json={
                "email": test_email,
                "password": "testpassword123",
                "full_name": "Test User",
                "college_name": "Test College",
                "program": "Computer Science",
                "year_of_study": 2
            }
        )
        print(f"Signup endpoint: {response.status_code}")
        if response.status_code in [200, 400]:  # 200 for success, 400 for validation errors
            print("✅ Signup endpoint is accessible")
        else:
            print(f"❌ Signup endpoint unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Signup endpoint error: {e}")

if __name__ == "__main__":
    test_all_endpoints()