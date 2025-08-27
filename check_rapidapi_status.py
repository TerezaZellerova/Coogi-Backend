#!/usr/bin/env python3
"""
Check RapidAPI subscription status and available LinkedIn APIs
"""
import os
import requests
import json

def check_rapidapi_subscription():
    """Check current RapidAPI subscription status"""
    api_key = os.getenv("NEXT_PUBLIC_RAPIDAPI_KEY")
    
    if not api_key:
        print("❌ No RapidAPI key found")
        return
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # Test different LinkedIn APIs to see which ones are available
    linkedin_apis = [
        {
            "name": "LinkedIn Data API",
            "host": "linkedin-data-api.p.rapidapi.com",
            "endpoint": "/search-jobs",
            "test_params": {"keywords": "software engineer", "locationId": "United States"}
        },
        {
            "name": "LinkedIn Jobs API",
            "host": "linkedin-jobs-api.p.rapidapi.com", 
            "endpoint": "/jobs",
            "test_params": {"q": "software engineer", "location": "united-states"}
        },
        {
            "name": "LinkedIn API by Toolbench",
            "host": "linkedin-api8.p.rapidapi.com",
            "endpoint": "/search-jobs",
            "test_params": {"keywords": "software engineer"}
        },
        {
            "name": "Real Time LinkedIn Jobs API",
            "host": "real-time-linkedin-jobs-api.p.rapidapi.com",
            "endpoint": "/search-jobs",
            "test_params": {"query": "software engineer", "location": "United States"}
        }
    ]
    
    available_apis = []
    
    for api in linkedin_apis:
        print(f"\n🧪 Testing {api['name']}...")
        
        url = f"https://{api['host']}{api['endpoint']}"
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": api['host']
        }
        
        try:
            response = requests.get(url, headers=headers, params=api['test_params'], timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ {api['name']} is available!")
                available_apis.append(api)
                
                # Try to parse response to see structure
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"   📊 Response keys: {list(data.keys())}")
                        if 'data' in data and isinstance(data['data'], list):
                            print(f"   📈 Found {len(data['data'])} results")
                    elif isinstance(data, list):
                        print(f"   📈 Found {len(data)} results")
                except:
                    print("   📊 Response is not JSON")
                    
            elif response.status_code == 403:
                try:
                    error_data = response.json()
                    if "not subscribed" in error_data.get("message", "").lower():
                        print(f"   🚫 Not subscribed to {api['name']}")
                    else:
                        print(f"   🚫 Access denied: {error_data.get('message', 'Unknown error')}")
                except:
                    print(f"   🚫 Access denied (403)")
            elif response.status_code == 429:
                print(f"   ⏰ Rate limited")
            else:
                print(f"   ❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   ❌ Message: {error_data.get('message', 'Unknown error')}")
                except:
                    print(f"   ❌ Raw response: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📋 Summary:")
    print(f"   Available APIs: {len(available_apis)}")
    if available_apis:
        print("   Working APIs:")
        for api in available_apis:
            print(f"   - {api['name']} ({api['host']})")
    else:
        print("   ❌ No LinkedIn APIs are currently accessible")
        print("   🔧 Possible solutions:")
        print("   1. Subscribe to a LinkedIn API on RapidAPI")
        print("   2. Use a different job search API")
        print("   3. Continue with demo data for development")

if __name__ == "__main__":
    check_rapidapi_subscription()
