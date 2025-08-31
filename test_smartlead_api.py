#!/usr/bin/env python3
"""
Test SmartLead.ai API key format and connection
"""
import requests
import os

def test_smartlead_api():
    """Test SmartLead.ai API connectivity"""
    api_key = "de8d1c5e-1bb0-408e-a86e-1d320b721c92_zbkzree"
    base_url = "https://server.smartlead.ai/api/v1"
    
    print(f"🔑 Testing SmartLead.ai API key: {api_key[:20]}...")
    
    # Test 1: Bearer token in header
    print(f"\n🧪 Test 1: Bearer token in Authorization header")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        response = requests.get(f"{base_url}/account", headers=headers, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Success with Bearer token!")
            return True
        else:
            print(f"❌ Response: {response.text[:200]}")
    except Exception as e:
        print(f"🚨 Error: {e}")
    
    # Test 2: API key as query parameter
    print(f"\n🧪 Test 2: API key as query parameter")
    try:
        response = requests.get(f"{base_url}/account?api_key={api_key}", timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Success with query parameter!")
            return True
        else:
            print(f"❌ Response: {response.text[:200]}")
    except Exception as e:
        print(f"🚨 Error: {e}")
    
    # Test 3: Try the campaign endpoint instead
    print(f"\n🧪 Test 3: Testing campaigns endpoint with Bearer")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        response = requests.get(f"{base_url}/campaigns", headers=headers, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Success with campaigns endpoint!")
            return True
        else:
            print(f"❌ Response: {response.text[:200]}")
    except Exception as e:
        print(f"� Error: {e}")
    
    # Test 4: Check if the base URL is correct
    print(f"\n🧪 Test 4: Testing base URL connectivity")
    try:
        response = requests.get("https://server.smartlead.ai", timeout=10)
        print(f"📡 Server Response Status: {response.status_code}")
        print(f"📋 Server available: {response.status_code < 500}")
    except Exception as e:
        print(f"🚨 Server connection error: {e}")
    
    return False

if __name__ == "__main__":
    test_smartlead_api()
