#!/usr/bin/env python3
"""
Test free job APIs that don't require RapidAPI
"""
import requests
import json

def test_free_job_apis():
    """Test free job search APIs"""
    
    free_apis = [
        {
            "name": "Adzuna API",
            "url": "https://api.adzuna.com/v1/api/jobs/us/search/1",
            "params": {"what": "software engineer", "content-type": "application/json"},
            "note": "Requires free API key from adzuna.com"
        },
        {
            "name": "The Muse API", 
            "url": "https://www.themuse.com/api/public/jobs",
            "params": {"category": "Software%20Engineer", "page": "0"},
            "note": "Free, no API key required"
        },
        {
            "name": "GitHub Jobs API",
            "url": "https://jobs.github.com/positions.json",
            "params": {"description": "software engineer", "location": "new york"},
            "note": "Free, but deprecated (stopped working in 2021)"
        },
        {
            "name": "RemoteOK API",
            "url": "https://remoteok.io/api",
            "params": {},
            "note": "Free remote jobs API"
        }
    ]
    
    working_apis = []
    
    for api in free_apis:
        print(f"\n🧪 Testing {api['name']}...")
        print(f"   Note: {api['note']}")
        
        try:
            response = requests.get(api['url'], params=api['params'], timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   ✅ Found {len(data)} jobs!")
                        working_apis.append(api)
                        
                        # Show sample job structure
                        job = data[0]
                        if isinstance(job, dict):
                            print(f"   📋 Sample job keys: {list(job.keys())}")
                    elif isinstance(data, dict) and 'results' in data:
                        jobs = data['results']
                        print(f"   ✅ Found {len(jobs)} jobs in results!")
                        working_apis.append(api)
                    else:
                        print(f"   📊 Response structure: {type(data)}")
                        if isinstance(data, dict):
                            print(f"   📊 Response keys: {list(data.keys())}")
                except Exception as e:
                    print(f"   ❌ JSON parse error: {e}")
                    print(f"   📊 Raw response: {response.text[:200]}...")
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   📊 Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Request error: {e}")
    
    print(f"\n📋 Summary:")
    print(f"   Working free APIs: {len(working_apis)}")
    if working_apis:
        print("   Available options:")
        for api in working_apis:
            print(f"   - {api['name']}")
    
    return working_apis

if __name__ == "__main__":
    test_free_job_apis()
