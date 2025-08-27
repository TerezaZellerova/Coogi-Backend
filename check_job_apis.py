#!/usr/bin/env python3
"""
Check for alternative job search APIs that might be available
"""
import os
import requests
import json

def check_alternative_job_apis():
    """Check alternative job search APIs"""
    api_key = os.getenv("NEXT_PUBLIC_RAPIDAPI_KEY")
    
    if not api_key:
        print("❌ No RapidAPI key found")
        return
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # Test alternative job search APIs
    job_apis = [
        {
            "name": "Jobs API",
            "host": "jobs-api14.p.rapidapi.com",
            "endpoint": "/list",
            "test_params": {"query": "software engineer", "location": "United States"}
        },
        {
            "name": "JobSearch API",
            "host": "jobsearch4.p.rapidapi.com", 
            "endpoint": "/api/v2/search",
            "test_params": {"query": "software engineer", "location": "new york"}
        },
        {
            "name": "Indeed Jobs API",
            "host": "indeed12.p.rapidapi.com",
            "endpoint": "/jobs/search",
            "test_params": {"query": "software engineer", "location": "new york"}
        },
        {
            "name": "JSearch API",
            "host": "jsearch.p.rapidapi.com",
            "endpoint": "/search",
            "test_params": {"query": "software engineer in New York", "page": "1", "num_pages": "1"}
        },
        {
            "name": "Job Board API",
            "host": "job-board-api.p.rapidapi.com",
            "endpoint": "/search",
            "test_params": {"query": "software engineer", "location": "new york"}
        }
    ]
    
    available_apis = []
    
    for api in job_apis:
        print(f"\n🧪 Testing {api['name']}...")
        
        url = f"https://{api['host']}{api['endpoint']}"
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": api['host']
        }
        
        try:
            response = requests.get(url, headers=headers, params=api['test_params'], timeout=15)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ {api['name']} is available!")
                available_apis.append(api)
                
                # Try to parse response to see structure
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"   📊 Response keys: {list(data.keys())}")
                        # Look for common job data patterns
                        if 'data' in data and isinstance(data['data'], list):
                            print(f"   📈 Found {len(data['data'])} jobs in 'data' field")
                            if data['data']:
                                job = data['data'][0]
                                print(f"   📋 Sample job keys: {list(job.keys()) if isinstance(job, dict) else 'Not a dict'}")
                        elif 'jobs' in data and isinstance(data['jobs'], list):
                            print(f"   📈 Found {len(data['jobs'])} jobs in 'jobs' field")
                        elif isinstance(data, list):
                            print(f"   📈 Found {len(data)} jobs (root array)")
                    elif isinstance(data, list):
                        print(f"   📈 Found {len(data)} jobs")
                        if data:
                            job = data[0]
                            print(f"   📋 Sample job keys: {list(job.keys()) if isinstance(job, dict) else 'Not a dict'}")
                except Exception as e:
                    print(f"   📊 Could not parse JSON: {e}")
                    print(f"   📊 Raw response: {response.text[:200]}...")
                    
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
    print(f"   Available Job APIs: {len(available_apis)}")
    if available_apis:
        print("   Working APIs:")
        for api in available_apis:
            print(f"   - {api['name']} ({api['host']})")
        
        # Recommend the best one for integration
        if available_apis:
            recommended = available_apis[0]  # Take the first working one
            print(f"\n🎯 Recommended for integration: {recommended['name']}")
            print(f"   Host: {recommended['host']}")
            print(f"   Endpoint: {recommended['endpoint']}")
    else:
        print("   ❌ No Job APIs are currently accessible")
        print("   🔧 Options:")
        print("   1. Subscribe to a job search API on RapidAPI")
        print("   2. Use free APIs like GitHub Jobs, RemoteOK, etc.")
        print("   3. Improve demo data to be more realistic")

if __name__ == "__main__":
    check_alternative_job_apis()
