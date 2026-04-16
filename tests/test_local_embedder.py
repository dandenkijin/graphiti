#!/usr/bin/env python3
"""
Test script to verify local embedder configuration
"""

import requests
import os

BASE_URL = "http://localhost:8000"

def test_local_embedder():
    """Test if local embedder is working by checking configuration"""
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json={"query": "test local embedder"},
            headers={"Content-Type": "application/json"}
        )
        print(f"Local embedder test: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Local embedder test failed: {e}")
        return False

def check_env_vars():
    """Check what environment variables are being used"""
    print("Environment Variables:")
    print(f"  OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'not set')}")
    print(f"  MODEL_NAME: {os.getenv('MODEL_NAME', 'not set')}")
    print(f"  OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'not set')}")
    print("")

if __name__ == "__main__":
    print("Testing Local Embedder Configuration")
    print("=" * 50)
    
    check_env_vars()
    print()
    
    result = test_local_embedder()
    if result:
        print("\n✅ Local embedder test PASSED")
    else:
        print("\n❌ Local embedder test FAILED")
