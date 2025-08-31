#!/usr/bin/env python3
"""
Test and fix LinkedIn API issues
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_linkedin_apis():
    """Test different LinkedIn job APIs to find working ones"""
    
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    print(f"🔑 Using RapidAPI Key: {rapidapi_key[:10]}...")
    
    # Test current LinkedIn API
    print("\n🧪 Testing current LinkedIn Jobs API...")
    try:
        params = {
            "keywords": "software engineer",
            "locationId": "92000000",  # US
            "dateSincePosted": "past-24-hours",
            "sort": "recent"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://linkedin-jobs-search.p.rapidapi.com/jobs",
                headers={
                    "X-RapidAPI-Key": rapidapi_key,
                    "X-RapidAPI-Host": "linkedin-jobs-search.p.rapidapi.com"
                },
                params=params
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ LinkedIn API working! Found {len(data.get('data', []))} jobs")
            else:
                print(f"❌ LinkedIn API failed with {response.status_code}")
                
    except Exception as e:
        print(f"❌ LinkedIn API error: {e}")
    
    # Test alternative LinkedIn APIs
    print("\n🧪 Testing alternative LinkedIn APIs...")
    
    alternative_apis = [
        {
            "name": "LinkedIn Job Search API v2",
            "url": "https://linkedin-api8.p.rapidapi.com/search-jobs",
            "host": "linkedin-api8.p.rapidapi.com",
            "params": {
                "keywords": "software engineer",
                "location": "United States",
                "datePosted": "pastWeek"
            }
        },
        {
            "name": "Jobs Search API",
            "url": "https://jobs-search-api.p.rapidapi.com/jobs",
            "host": "jobs-search-api.p.rapidapi.com", 
            "params": {
                "query": "software engineer",
                "location": "United States",
                "site": "linkedin"
            }
        }
    ]
    
    for api in alternative_apis:
        try:
            print(f"\nTesting {api['name']}...")
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    api["url"],
                    headers={
                        "X-RapidAPI-Key": rapidapi_key,
                        "X-RapidAPI-Host": api["host"]
                    },
                    params=api["params"]
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {api['name']} working!")
                    print(f"Response sample: {str(data)[:200]}...")
                else:
                    print(f"❌ {api['name']} failed: {response.text[:100]}")
                    
        except Exception as e:
            print(f"❌ {api['name']} error: {e}")

async def test_jsearch_linkedin_jobs():
    """Test if JSearch returns jobs with LinkedIn URLs"""
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    
    print("\n🔍 Testing JSearch for LinkedIn jobs...")
    
    try:
        params = {
            "query": "software engineer",
            "page": "1",
            "num_pages": "1",
            "date_posted": "today",
            "employment_types": "FULLTIME",
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={
                    "X-RapidAPI-Key": rapidapi_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                },
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("data", [])
                print(f"✅ JSearch returned {len(jobs)} jobs")
                
                # Check for LinkedIn jobs
                linkedin_jobs = []
                for job in jobs:
                    job_url = job.get("job_apply_link", "").lower()
                    if "linkedin.com" in job_url:
                        linkedin_jobs.append(job)
                        
                print(f"🔗 Found {len(linkedin_jobs)} jobs with LinkedIn URLs!")
                
                if linkedin_jobs:
                    print("\nSample LinkedIn job from JSearch:")
                    job = linkedin_jobs[0]
                    print(f"Title: {job.get('job_title')}")
                    print(f"Company: {job.get('employer_name')}")
                    print(f"URL: {job.get('job_apply_link')}")
                    
                return linkedin_jobs
            else:
                print(f"❌ JSearch failed: {response.status_code}")
                return []
                
    except Exception as e:
        print(f"❌ JSearch error: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(test_linkedin_apis())
    asyncio.run(test_jsearch_linkedin_jobs())
