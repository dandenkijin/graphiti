#!/usr/bin/env python3
"""
Test script to verify local embedder configuration
"""

import requests
import os
from pathlib import Path

# Load environment variables from .env file
def load_env():
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment variables at import
load_env()

OLLAMA_BASE_URL = "http://localhost:11434"

def test_local_embedder():
    """Test if local embedder (Ollama) is working"""
    try:
        # Test Ollama health endpoint
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        print(f"Ollama service test: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"Available models: {[model['name'] for model in models.get('models', [])]}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Ollama service test failed: {e}")
        return False

def check_env_vars():
    """Check what environment variables are being used"""
    print("Environment Variables:")
    print(f"  OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'not set')}")
    print(f"  MODEL_NAME: {os.getenv('MODEL_NAME', 'not set')}")
    print(f"  OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
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
