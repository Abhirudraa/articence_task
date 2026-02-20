"""
Test script for the Universal Data Connector API.
Run this with: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_generate_api_key():
    """Test generating a new API key."""
    print("\n=== Testing Generate API Key ===")
    
    # This should be a POST request with the name in the request body
    response = requests.post(
        f"{BASE_URL}/auth/generate-key",
        params={"name": "Test Key"}  # Using params for query parameter
        # Or use json={"name": "Test Key"} if your endpoint expects JSON body
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data.get("api_key")
    else:
        print(f"Error: {response.text}")
        return None

def test_validate_api_key(api_key):
    """Test validating an API key."""
    print("\n=== Testing Validate API Key ===")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        f"{BASE_URL}/auth/validate",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_customers(api_key):
    """Test getting customers."""
    print("\n=== Testing Get Customers ===")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        f"{BASE_URL}/data/customers",
        headers=headers,
        params={"limit": 5}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")

def test_health_check():
    """Test health check endpoint (no auth required)."""
    print("\n=== Testing Health Check ===")
    
    response = requests.get(f"{BASE_URL}/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_cache_status(api_key):
    """Test cache status endpoint."""
    print("\n=== Testing Cache Status ===")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        f"{BASE_URL}/cache/status",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")

def test_rate_limit_status(api_key):
    """Test rate limit status endpoint."""
    print("\n=== Testing Rate Limit Status ===")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        f"{BASE_URL}/rate-limit/status",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Universal Data Connector API")
    print("=" * 50)
    
    # Test health check first (no auth needed)
    test_health_check()
    
    # Generate API key
    api_key = test_generate_api_key()
    
    if api_key:
        print(f"\n✅ Generated API Key: {api_key}")
        
        # Test with the new API key
        test_validate_api_key(api_key)
        test_get_customers(api_key)
        test_cache_status(api_key)
        test_rate_limit_status(api_key)
    else:
        print("\n❌ Failed to generate API key. Check if the endpoint exists.")
        print("If the endpoint is GET instead of POST, try:")
        print("  curl 'http://localhost:8000/api/auth/generate-key?name=Test'")