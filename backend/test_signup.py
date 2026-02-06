import requests
import json
from datetime import datetime

# Test the signup endpoint
url = "http://127.0.0.1:8001/auth/signup"
headers = {"Content-Type": "application/json"}

# Test data with a new email
data = {
    "email": "prepiqtestuser123456789@gmail.com",
    "password": "password123",
    "full_name": "Test User",
    "college_name": "Test College",
    "program": "BTech",
    "year_of_study": 2
}

try:
    print("Testing SIGNUP...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Signup Status Code: {response.status_code}")
    print(f"Signup Response: {response.text}")
    
    # If signup succeeds, test login
    if response.status_code == 200:
        print("\nTesting LOGIN...")
        login_url = "http://127.0.0.1:8001/auth/login"
        login_data = {
            "email": data["email"],
            "password": data["password"]
        }
        
        login_response = requests.post(login_url, headers=headers, json=login_data)
        print(f"Login Status Code: {login_response.status_code}")
        print(f"Login Response: {login_response.text}")
    
except Exception as e:
    print(f"Error: {e}")