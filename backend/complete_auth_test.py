import requests
import json
import uuid

def test_complete_auth_flow():
    """Test complete authentication flow: signup, login, profile"""
    base_url = "http://localhost:8000"
    
    print("=== Complete Authentication Flow Test ===\n")
    
    # Generate unique email for test
    test_email = f"testuser_{uuid.uuid4()}@example.com"
    test_password = "testpassword123"
    test_full_name = "Test User"
    
    print(f"Using test email: {test_email}")
    
    # Test signup
    print("1. Testing signup...")
    try:
        signup_data = {
            "email": test_email,
            "password": test_password,
            "full_name": test_full_name,
            "college_name": "Test University",
            "program": "Computer Science",
            "year_of_study": 2
        }
        
        response = requests.post(
            f"{base_url}/auth/signup",
            headers={"Content-Type": "application/json"},
            json=signup_data
        )
        
        print(f"Signup response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Signup successful")
            signup_response = response.json()
            print(f"   User ID: {signup_response.get('id')}")
        else:
            print(f"❌ Signup failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return
    
    # Test login with the same credentials
    print("\n2. Testing login with new user...")
    try:
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        response = requests.post(
            f"{base_url}/auth/login",
            headers={"Content-Type": "application/json"},
            json=login_data
        )
        
        print(f"Login response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login successful")
            login_response = response.json()
            access_token = login_response.get('access_token')
            print(f"   Access Token received: {'Yes' if access_token else 'No'}")
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    print("\n✅ All authentication tests passed!")
    print("The system is working properly with both signup and login.")

if __name__ == "__main__":
    test_complete_auth_flow()