#!/usr/bin/env python3
"""
Test LadybugDB chat endpoint functionality separately
"""

import asyncio
import sys
import os
import requests
import json

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

async def test_chat_endpoint():
    """Test LadybugDB chat endpoint directly"""
    
    print("Testing LadybugDB chat endpoint...")
    
    try:
        # Test basic health check first
        health_response = requests.get("http://localhost:8000/healthcheck", timeout=10)
        print(f"✅ Health check: {health_response.status_code}")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health status: {health_data.get('status', 'unknown')}")
        
        # Test chat endpoint with a simple prompt
        chat_payload = {
            "model": "huihui_ai/qwen3.5-abliterated:9b",
            "messages": [
                {
                    "role": "user", 
                    "content": "Hello, this is a test message. What is 2+2?"
                }
            ],
            "stream": False
        }
        
        print("🔄 Testing chat endpoint...")
        chat_response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json=chat_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"✅ Chat response status: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            print(f"✅ Chat response: {json.dumps(chat_data, indent=2)}")
            return True
        else:
            print(f"❌ Chat failed: {chat_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chat_endpoint())
    if success:
        print("\n🎉 Chat endpoint test completed successfully!")
    else:
        print("\n❌ Chat endpoint test failed!")
