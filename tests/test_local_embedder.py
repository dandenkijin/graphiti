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

def cleanup_model(model_name):
    """Unload model to prevent CPU spinning"""
    try:
        # Use correct Ollama endpoint for model management
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={
            "model": model_name,
            "prompt": "",
            "keep_alive": "0s"
        })
        print(f"Model cleanup status: {response.status_code}")
    except Exception as e:
        print(f"Model cleanup failed: {e}")

def test_local_embedder():
    """Test if local embedder (Ollama) is working"""
    embedding_model = os.getenv('EMBEDDING_MODEL_NAME', 'qwen3-embedding:0.6b')
    
    try:
        # Test Ollama health endpoint
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        print(f"Ollama service test: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return False
        
        models = response.json()
        available_models = [model['name'] for model in models.get('models', [])]
        print(f"Available models: {available_models}")
        
        # Check if embedding model is available
        embedding_available = any(embedding_model in model for model in available_models)
        if not embedding_available:
            print(f"Embedding model '{embedding_model}' not found in available models")
            return False
        
        print(f"Testing embedding with model: {embedding_model}")
        
        # Make actual embedding request
        embed_response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": embedding_model,
                "prompt": "This is a test sentence for embedding."
            },
            timeout=30
        )
        
        print(f"Embedding request status: {embed_response.status_code}")
        if embed_response.status_code == 200:
            embedding_data = embed_response.json()
            embedding = embedding_data.get('embedding', [])
            if embedding:
                print(f"Embedding successful - dimension: {len(embedding)}")
                print(f"Sample embedding values: {embedding[:5]}...")
                return True
            else:
                print("Embedding response missing embedding data")
                return False
        else:
            print(f"Embedding request failed: {embed_response.text}")
            return False
            
    except Exception as e:
        print(f"Embedder test failed: {e}")
        return False
    finally:
        # Always cleanup the model to prevent CPU spinning
        print("Cleaning up embedding model...")
        cleanup_model(embedding_model)

def check_env_vars():
    """Check what environment variables are being used"""
    print("Environment Variables:")
    print(f"  OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'not set')}")
    print(f"  MODEL_NAME: {os.getenv('MODEL_NAME', 'not set')}")
    print(f"  EMBEDDING_MODEL_NAME: {os.getenv('EMBEDDING_MODEL_NAME', 'not set')}")
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
