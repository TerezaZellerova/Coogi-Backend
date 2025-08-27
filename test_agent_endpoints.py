#!/usr/bin/env python3
"""
Test script to verify all AGENT management endpoints are working
"""

import requests
import json
from datetime import datetime

# Backend URL
BASE_URL = "http://localhost:8001"

def test_agent_endpoints():
    """Test all agent management endpoints"""
    print("🧪 Testing AGENT Management Endpoints")
    print("="*50)
    
    # Test 1: Get all agents
    print("\n1. Testing GET /api/agents")
    try:
        response = requests.get(f"{BASE_URL}/api/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ GET /api/agents - Status: {response.status_code}")
            print(f"   Found {len(agents)} agents")
        else:
            print(f"❌ GET /api/agents - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ GET /api/agents - Error: {e}")
    
    # Test 2: Get dashboard stats
    print("\n2. Testing GET /api/dashboard/stats")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ GET /api/dashboard/stats - Status: {response.status_code}")
            print(f"   Active agents: {stats.get('activeAgents', 0)}")
        else:
            print(f"❌ GET /api/dashboard/stats - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ GET /api/dashboard/stats - Error: {e}")
    
    # Test 3: Create a test agent using search-jobs-instant
    print("\n3. Testing POST /api/search-jobs-instant (Create Agent)")
    test_batch_id = None
    try:
        payload = {
            "query": "software engineer",
            "hours_old": 24,
            "custom_tags": "test-agent"
        }
        response = requests.post(f"{BASE_URL}/api/search-jobs-instant", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ POST /api/search-jobs-instant - Status: {response.status_code}")
            print(f"   Jobs found: {result.get('jobs_found', 0)}")
            # Get the batch_id from a test agent for subsequent tests
            test_batch_id = f"test_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            print(f"❌ POST /api/search-jobs-instant - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ POST /api/search-jobs-instant - Error: {e}")
    
    # Use a test batch ID for the remaining tests
    if not test_batch_id:
        test_batch_id = "test_batch_20250827_120000"
    
    # Test 4: Agent status endpoint
    print(f"\n4. Testing GET /api/status/{test_batch_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/status/{test_batch_id}")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ GET /api/status - Status: {response.status_code}")
            print(f"   Agent status: {status.get('status', 'unknown')}")
        else:
            print(f"❌ GET /api/status - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ GET /api/status - Error: {e}")
    
    # Test 5: Search status endpoint (alias)
    print(f"\n5. Testing GET /api/search-status/{test_batch_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/search-status/{test_batch_id}")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ GET /api/search-status - Status: {response.status_code}")
            print(f"   Agent status: {status.get('status', 'unknown')}")
            print(f"   Is cancelled: {status.get('is_cancelled', False)}")
        else:
            print(f"❌ GET /api/search-status - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ GET /api/search-status - Error: {e}")
    
    # Test 6: Agent logs endpoint
    print(f"\n6. Testing GET /api/logs/{test_batch_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/logs/{test_batch_id}")
        if response.status_code == 200:
            logs_data = response.json()
            logs = logs_data.get('logs', [])
            print(f"✅ GET /api/logs - Status: {response.status_code}")
            print(f"   Found {len(logs)} log entries")
        else:
            print(f"❌ GET /api/logs - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ GET /api/logs - Error: {e}")
    
    # Test 7: Pause agent endpoint
    print(f"\n7. Testing POST /api/pause-agent/{test_batch_id}")
    try:
        response = requests.post(f"{BASE_URL}/api/pause-agent/{test_batch_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ POST /api/pause-agent - Status: {response.status_code}")
            print(f"   Result: {result.get('message', 'No message')}")
        else:
            print(f"❌ POST /api/pause-agent - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ POST /api/pause-agent - Error: {e}")
    
    # Test 8: Resume agent endpoint
    print(f"\n8. Testing POST /api/resume-agent/{test_batch_id}")
    try:
        response = requests.post(f"{BASE_URL}/api/resume-agent/{test_batch_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ POST /api/resume-agent - Status: {response.status_code}")
            print(f"   Result: {result.get('message', 'No message')}")
        else:
            print(f"❌ POST /api/resume-agent - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ POST /api/resume-agent - Error: {e}")
    
    # Test 9: Cancel agent endpoint
    print(f"\n9. Testing POST /api/cancel-search/{test_batch_id}")
    try:
        response = requests.post(f"{BASE_URL}/api/cancel-search/{test_batch_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ POST /api/cancel-search - Status: {response.status_code}")
            print(f"   Result: {result.get('message', 'No message')}")
        else:
            print(f"❌ POST /api/cancel-search - Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ POST /api/cancel-search - Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting AGENT Management Endpoint Tests")
    print("Make sure the backend server is running on localhost:8001")
    print()
    
    test_agent_endpoints()
    
    print("\n" + "="*50)
    print("✅ Test completed! Check the results above.")
