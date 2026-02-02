import requests

def test_signup_cors():
    """Test CORS headers on the signup endpoint"""
    url = "http://localhost:8000/auth/signup"
    
    # Send a preflight request (OPTIONS)
    headers = {
        "Origin": "http://localhost:3001",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    try:
        response = requests.options(url, headers=headers)
        print(f"OPTIONS response status for signup: {response.status_code}")
        
        # Check if CORS headers are present
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("Signup CORS Headers:")
        for header, value in cors_headers.items():
            print(f"  {header}: {value}")
            
        if cors_headers['Access-Control-Allow-Origin']:
            if 'http://localhost:3001' in cors_headers['Access-Control-Allow-Origin'] or '*' in cors_headers['Access-Control-Allow-Origin']:
                print("✅ CORS is properly configured for signup endpoint")
            else:
                print("❌ CORS header doesn't include http://localhost:3001")
        else:
            print("❌ No Access-Control-Allow-Origin header found")
            
    except Exception as e:
        print(f"Error testing signup CORS: {e}")

if __name__ == "__main__":
    test_signup_cors()