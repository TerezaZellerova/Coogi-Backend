#!/usr/bin/env python3
"""
Test script to verify LinkedIn API functionality
"""
import os
import requests

def test_linkedin_api():
    api_key = os.getenv("NEXT_PUBLIC_RAPIDAPI_KEY")
    
    print(f"🔑 API Key present: {bool(api_key)}")
    if api_key:
        print(f"🔑 API Key first 10 chars: {api_key[:10]}...")
    
    if not api_key:
        print("❌ No API key found!")
        return
    
    # Test API call
    url = "https://linkedin-data-api.p.rapidapi.com/search-jobs"
    
    querystring = {
        "keywords": "software engineer",
        "locationId": "United States",
        "dateSincePosted": "past-24-hours",
        "sort": "most-recent",
        "start": "0"
    }
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
    }
    
    print("📡 Making test API call...")
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if isinstance(data, dict) and 'data' in data:
                jobs = data.get('data', [])
                print(f"🎯 Found {len(jobs)} jobs")
                if jobs:
                    first_job = jobs[0]
                    print(f"📋 First job: {first_job.get('title', 'No title')} at {first_job.get('company', {}).get('name', 'No company')}")
        else:
            print(f"❌ API Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_linkedin_api()
