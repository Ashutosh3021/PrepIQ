import requests
import json

# Test the backend endpoints
base_url = "http://localhost:8000"

# Test the wizard status endpoint (this should work without auth for testing)
print("Testing /wizard/status endpoint...")
try:
    response = requests.get(f"{base_url}/wizard/status")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 403:
        print("Success! Endpoint requires authentication (expected behavior)")
        print(f"Response: {response.text}")
    elif response.status_code == 200:
        data = response.json()
        print("Success! Response data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Exception occurred: {e}")

print("\n" + "="*50 + "\n")

# Test the analysis data endpoint
print("Testing /analysis/data endpoint...")
try:
    response = requests.get(f"{base_url}/analysis/data")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 403:
        print("Success! Endpoint requires authentication (expected behavior)")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception occurred: {e}")

print("\n" + "="*50 + "\n")

# Test the important questions endpoint
print("Testing /questions/important endpoint...")
try:
    response = requests.get(f"{base_url}/questions/important")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 403:
        print("Success! Endpoint requires authentication (expected behavior)")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception occurred: {e}")