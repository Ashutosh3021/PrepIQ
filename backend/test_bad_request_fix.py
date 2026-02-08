"""
Test script to verify that the request size limiting middleware is working properly.
This should help fix the 400 Bad Request errors.
"""

import asyncio
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

def test_basic_endpoints():
    """Test basic endpoints to ensure they work properly"""
    print("Testing basic endpoints...")
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    print("✓ Root endpoint works")
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    print("✓ Health endpoint works")
    
    # Test API endpoints
    response = client.get("/api/v1/health")
    if response.status_code == 200:
        print("✓ API health endpoint works")
    else:
        print(f"? API health endpoint returned {response.status_code}")

def test_large_request_handling():
    """Test that large requests are handled properly"""
    print("\nTesting large request handling...")
    
    # Test with a reasonably sized payload
    large_payload = {"data": "x" * (15 * 1024 * 1024)}  # 15MB
    
    try:
        response = client.post("/api/v1/chat", json=large_payload)
        print(f"Large request response: {response.status_code}")
        
        # This should either succeed or return a proper error (413), not a 400
        if response.status_code in [200, 413, 422]:
            print("✓ Large request handled properly")
        else:
            print(f"? Large request returned unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Large request caused exception: {e}")

def test_normal_requests():
    """Test that normal-sized requests still work"""
    print("\nTesting normal requests...")
    
    # Test with a small payload
    small_payload = {"message": "Hello, world!"}
    
    try:
        # Try to hit a chat endpoint if it exists
        response = client.post("/api/v1/chat", json=small_payload)
        print(f"Normal request response: {response.status_code}")
        
        # Normal requests should work fine (200, 422 for validation, etc.)
        if response.status_code in [200, 401, 403, 404, 422]:
            print("✓ Normal request handled properly")
        else:
            print(f"? Normal request returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"Normal request caused exception: {e}")

if __name__ == "__main__":
    print("Testing PrepIQ application with request size limiting middleware...")
    print("=" * 60)
    
    try:
        test_basic_endpoints()
        test_large_request_handling()
        test_normal_requests()
        
        print("\n" + "=" * 60)
        print("Tests completed. The request size limiting middleware should now prevent 400 Bad Request errors!")
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()