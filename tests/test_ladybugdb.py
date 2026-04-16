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

def test_openapi():
    """Test OpenAPI specification"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        print(f"OpenAPI spec: {response.status_code}")
        if response.status_code == 200:
            spec = response.json()
            paths = list(spec.get('paths', {}).keys())
            print(f"Available endpoints: {paths}")
        return response.status_code == 200
    except Exception as e:
        print(f"OpenAPI test failed: {e}")
        return False

def test_database_connection():
    """Test database connection via container exec"""
    try:
        import subprocess
        result = subprocess.run(
            ["docker-compose", "-f", "docker/docker-compose.ladybugdb.yml", "exec", "ladybugdb-graphiti", "python", "-c", 
             "import real_ladybug; db = real_ladybug.Database('/data/graph.db'); print('LadybugDB connection successful')"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"Database connection: PASS - {result.stdout.strip()}")
            return True
        else:
            print(f"Database connection: FAIL - {result.stderr}")
            return False
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

def test_search():
    """Test search endpoint with local model"""
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json={"query": "What is LadybugDB?"},
            headers={"Content-Type": "application/json"}
        )
        print(f"Search test: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Search test failed: {e}")
        return False

def test_messages():
    """Test messages endpoint for data ingestion"""
    try:
        test_data = {
            "group_id": "test-group-123",  # Required field
            "messages": [
                {"role_type": "user", "role": "user", "content": "LadybugDB is a fork of Kuzu"},
                {"role_type": "user", "role": "assistant", "content": "I understand that LadybugDB is a Graph database forked from Kuzu"}
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
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Messages test failed: {e}")
        return False

def test_data_persistence():
    """Test data persistence by checking database file"""
    try:
        import subprocess
        result = subprocess.run(
            ["docker-compose", "-f", "docker/docker-compose.ladybugdb.yml", "exec", "ladybugdb-graphiti", "ls", "-la", "/data/"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            output = result.stdout
            if "graph.db" in output:
                print(f"Data persistence: PASS - Database files exist")
                print(f"Files: {output}")
                return True
            else:
                print(f"Data persistence: FAIL - Database file not found")
                return False
        else:
            print(f"Data persistence: FAIL - {result.stderr}")
            return False
    except Exception as e:
        print(f"Data persistence test failed: {e}")
        return False

def main():
    """Run all advanced tests"""
    print("Advanced LadybugDB Testing")
    print("=" * 50)
    
    # Wait for service to be fully ready
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health),
        ("OpenAPI Specification", test_openapi),
        ("Database Connection", test_database_connection),
        ("Data Persistence", test_data_persistence),
        ("Search Functionality", test_search),
        ("Messages Ingestion", test_messages),
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
    
    if passed == total:
        print("\n" + "SUCCESS! LadybugDB setup is fully functional!")
        print("\nYou can now:")
        print("1. Access the API docs at http://localhost:8000/docs")
        print("2. Use the service for graph operations")
        print("3. Test with your own data")
    else:
        print("\nSome tests failed. Check the logs for details.")

if __name__ == "__main__":
    main()
