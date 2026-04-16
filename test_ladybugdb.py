#!/usr/bin/env python3
"""
Test script for LadybugDB setup
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/healthcheck")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_messages():
    """Test messages endpoint (ingestion)"""
    try:
        # Sample data to ingest
        test_data = {
            "messages": [
                {"role": "user", "content": "John works at Google as a software engineer"},
                {"role": "assistant", "content": "I understand that John is employed at Google in a software engineering role."}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/messages",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Messages test: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Messages test failed: {e}")
        return False

def test_search():
    """Test search endpoint (retrieval)"""
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json={"query": "What does John do?"},
            headers={"Content-Type": "application/json"}
        )
        print(f"Search test: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Search test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing LadybugDB Setup")
    print("=" * 50)
    
    # Wait a moment for service to be fully ready
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health),
        ("Messages (Ingest)", test_messages),
        ("Search (Retrieve)", test_search),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
