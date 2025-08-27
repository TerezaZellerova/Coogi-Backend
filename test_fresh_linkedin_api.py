#!/usr/bin/env python3
"""
Test the Fresh LinkedIn Scraper API that the user has access to
"""
import os
import requests
import json

def test_fresh_linkedin_api():
    """Test the Fresh LinkedIn Scraper API"""
    
    # Get API key
    api_key = os.getenv("NEXT_PUBLIC_RAPIDAPI_KEY")
    
    print(f"🔑 API Key present: {bool(api_key)}")
    if api_key:
        print(f"🔑 API Key first 10 chars: {api_key[:10]}...")
    
    if not api_key:
        print("❌ No API key found!")
        return
    
    # Test endpoint based on the screenshot - looks like it's for LinkedIn job search
    url = "https://fresh-linkedin-scraper-api.p.rapidapi.com/api/v1/job/search"
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "fresh-linkedin-scraper-api.p.rapidapi.com"
    }
    
    # Test with a simple job search - using correct parameter names
    params = {
        "keyword": "software engineer",
        "location": "New York",
        "limit": 10
    }
    
    print("📡 Making test API call to Fresh LinkedIn Scraper...")
    print(f"🎯 URL: {url}")
    print(f"📊 Params: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            print(f"📈 Response keys: {list(data.keys())}")
            
            # Check if we have jobs data
            if 'jobs' in data or 'data' in data:
                jobs = data.get('jobs', data.get('data', []))
                print(f"🎯 Found {len(jobs)} jobs")
                
                # Show sample job
                if jobs:
                    job = jobs[0]
                    print("📋 Sample job:")
                    print(f"  - Title: {job.get('title', 'N/A')}")
                    print(f"  - Company: {job.get('company', 'N/A')}")
                    print(f"  - Location: {job.get('location', 'N/A')}")
                    print(f"  - URL: {job.get('url', 'N/A')}")
            else:
                print("📋 Full response:")
                print(json.dumps(data, indent=2)[:500] + "...")
                
        else:
            print(f"❌ API Error: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text[:200]}...")

if __name__ == "__main__":
    test_fresh_linkedin_api()
