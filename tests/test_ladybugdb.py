#!/usr/bin/env python3
"""
Test script for LadybugDB setup
"""

import requests
import json
import time
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

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint via container exec"""
    try:
        import subprocess
        result = subprocess.run(
            ["docker-compose", "-f", "docker/docker-compose.ladybugdb.yml", "exec", "ladybugdb-graphiti", "curl", "-s", "http://localhost:8000/healthcheck"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"Health check: PASS - {result.stdout.strip()}")
            return True
        else:
            print(f"Health check: FAIL - {result.stderr}")
            return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_openapi():
    """Test OpenAPI specification via container exec"""
    try:
        import subprocess
        result = subprocess.run(
            ["docker-compose", "-f", "docker/docker-compose.ladybugdb.yml", "exec", "ladybugdb-graphiti", "curl", "-s", "http://localhost:8000/openapi.json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"OpenAPI spec: PASS")
            return True
        else:
            print(f"OpenAPI test: FAIL - {result.stderr}")
            return False
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
    """Test search endpoint with local model via container exec"""
    try:
        import subprocess
        result = subprocess.run(
            ["docker-compose", "-f", "docker/docker-compose.ladybugdb.yml", "exec", "ladybugdb-graphiti", "curl", "-s", "-X", "POST", "-H", "Content-Type: application/json", "-d", '{"query": "What is LadybugDB?"}', "http://localhost:8000/search"],
            capture_output=True, text=True, timeout=10
        )
        print(f"Search test: {result.returncode}")
        if result.returncode == 0:
            print(f"Search request: PASS - {result.stdout.strip()}")
            return True
        else:
            print(f"Search test: FAIL - {result.stderr}")
            return False
    except Exception as e:
        print(f"Search test failed: {e}")
        return False

def test_messages():
    """Test messages endpoint for data ingestion via container exec"""
    try:
        import subprocess
        test_data = '{"group_id": "test-group-123", "messages": [{"role_type": "user", "role": "user", "content": "LadybugDB is a fork of Kuzu"}, {"role_type": "user", "role": "assistant", "content": "I understand that LadybugDB is a Graph database forked from Kuzu"}]}'
        result = subprocess.run(
            ["docker-compose", "-f", "docker/docker-compose.ladybugdb.yml", "exec", "ladybugdb-graphiti", "curl", "-s", "-X", "POST", "-H", "Content-Type: application/json", "-d", test_data, "http://localhost:8000/messages"],
            capture_output=True, text=True, timeout=10
        )
        print(f"Messages test: {result.returncode}")
        if result.returncode == 0:
            print(f"Messages ingestion: PASS - {result.stdout.strip()}")
            return True
        else:
            print(f"Messages test: FAIL - {result.stderr}")
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
