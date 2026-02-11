"""
Quick test script to verify backend connectivity
Run this to check if backend is working properly
"""
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test a specific endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"✅ {method} {endpoint} - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} - Connection refused. Is the backend running?")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing PrepIQ Backend Connectivity")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Test health endpoint
    print("1. Testing Health Endpoint...")
    if not test_endpoint("/health"):
        print("\n❌ Backend is not running or not accessible!")
        print("   Please start the backend first:")
        print("   cd backend && python start_server.py")
        sys.exit(1)
    
    print()
    
    # Test CORS preflight
    print("2. Testing CORS (OPTIONS request)...")
    try:
        response = requests.options(
            f"{BASE_URL}/auth/signup",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=5
        )
        print(f"✅ CORS Preflight - Status: {response.status_code}")
        print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
    except Exception as e:
        print(f"❌ CORS Preflight failed: {e}")
    
    print()
    
    # Test auth endpoints
    print("3. Testing Auth Endpoints...")
    
    # Test signup (will fail with validation error, but that's ok - means backend is responding)
    print("   Testing /auth/signup (expecting validation error)...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={},
            timeout=5
        )
        print(f"   Status: {response.status_code} (Expected: 422 for empty body)")
        if response.status_code == 422:
            print("   ✅ Backend is responding correctly!")
        elif response.status_code == 500:
            print(f"   ⚠️  Backend error: {response.text[:200]}")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
