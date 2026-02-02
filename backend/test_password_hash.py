import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.auth_service import AuthService

def test_password_hashing():
    """Test that password hashing and verification works properly"""
    
    # Test password hashing
    password = "testpassword123"
    hashed = AuthService.hash_password(password)
    print(f"Original password: {password}")
    print(f"Hashed password: {hashed}")
    
    # Test password verification (should work)
    is_valid = AuthService.verify_password(password, hashed)
    print(f"Password verification result: {is_valid}")
    
    # Test with wrong password (should fail)
    is_invalid = AuthService.verify_password("wrongpassword", hashed)
    print(f"Wrong password verification result: {is_invalid}")
    
    # Test error handling with invalid hash format
    try:
        result = AuthService.verify_password("test", "invalid_hash_format")
        print(f"Invalid hash verification result: {result}")
    except Exception as e:
        print(f"Error with invalid hash: {e}")
    
    print("✅ Password hashing and verification tests completed successfully")

if __name__ == "__main__":
    test_password_hashing()