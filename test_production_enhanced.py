#!/usr/bin/env python3
"""
Production Test for Enhanced Job Scraper
Tests the live production API to ensure 100-500+ jobs per search
"""

import requests
import json
import time
from datetime import datetime

def test_production_agent_creation():
    """Test the production API with enhanced job scraper"""
    
    base_url = "https://coogi-backend.onrender.com"
    
    # Test cases for production
    test_cases = [
        {
            "query": "software engineer",
            "company_size": "medium",
            "target_type": "hiring_manager",
            "location": "San Francisco",
            "expected_min_jobs": 100
        },
        {
            "query": "nurse",
            "company_size": "all",
            "target_type": "hiring_manager", 
            "location": "California",
            "expected_min_jobs": 100
        }
    ]
    
    print("🚀 Testing Production Enhanced Job Scraper")
    print("🎯 Goal: Verify 100-500+ jobs per agent creation")
    print(f"🌐 API Base URL: {base_url}")
    print("="*80)
    
    # Check health first
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Backend health check: PASSED")
        else:
            print(f"❌ Backend health check: FAILED ({health_response.status_code})")
            return
    except Exception as e:
        print(f"❌ Backend health check: FAILED ({e})")
        return
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 TEST CASE {i}: {test_case['query']} in {test_case['location']}")
        print(f"🎯 Expected: {test_case['expected_min_jobs']}+ jobs")
        
        try:
            # Create progressive agent
            create_payload = {
                "query": test_case["query"],
                "company_size": test_case["company_size"],
                "target_type": test_case["target_type"],
                "location": test_case["location"]
            }
            
            print("⏳ Creating agent...")
            start_time = time.time()
            
            create_response = requests.post(
                f"{base_url}/progressive-agents/create",
                json=create_payload,
                timeout=180  # 3 minutes for job scraping
            )
            
            if create_response.status_code != 200:
                print(f"❌ Agent creation failed: {create_response.status_code}")
                print(f"   Response: {create_response.text}")
                continue
            
            agent_data = create_response.json()
            agent_id = agent_data.get("agent_id")
            
            if not agent_id:
                print("❌ No agent ID returned")
                continue
            
            print(f"✅ Agent created with ID: {agent_id}")
            
            # Wait a moment for initial processing
            time.sleep(5)
            
            # Check agent status and results
            print("📊 Checking results...")
            status_response = requests.get(f"{base_url}/progressive-agents/{agent_id}/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                # Extract job counts
                linkedin_jobs = len(status_data.get("staged_results", {}).get("linkedin_jobs", []))
                other_jobs = len(status_data.get("staged_results", {}).get("other_jobs", []))
                total_jobs = linkedin_jobs + other_jobs
                
                duration = time.time() - start_time
                
                result = {
                    "test_case": test_case,
                    "agent_id": agent_id,
                    "linkedin_jobs": linkedin_jobs,
                    "other_jobs": other_jobs,
                    "total_jobs": total_jobs,
                    "target_met": total_jobs >= test_case["expected_min_jobs"],
                    "duration_seconds": round(duration, 1),
                    "success_rate": (total_jobs / test_case["expected_min_jobs"]) * 100
                }
                
                results.append(result)
                
                print(f"📈 RESULTS:")
                print(f"   LinkedIn Jobs: {linkedin_jobs}")
                print(f"   Other Jobs: {other_jobs}")
                print(f"   Total Jobs: {total_jobs}")
                print(f"   Target Met: {'YES' if result['target_met'] else 'NO'} ({result['success_rate']:.1f}%)")
                print(f"   Duration: {duration:.1f} seconds")
                
            else:
                print(f"❌ Failed to get agent status: {status_response.status_code}")
                
        except Exception as e:
            print(f"❌ Test case {i} failed: {e}")
    
    # Overall summary
    print("\n" + "="*80)
    print("📊 PRODUCTION TEST SUMMARY")
    print("="*80)
    
    if results:
        successful_tests = sum(1 for r in results if r["target_met"])
        total_jobs = sum(r["total_jobs"] for r in results)
        avg_jobs = total_jobs / len(results) if results else 0
        
        print(f"✅ SUCCESSFUL TESTS: {successful_tests} / {len(results)}")
        print(f"📈 TOTAL JOBS FOUND: {total_jobs}")
        print(f"📊 AVERAGE JOBS PER TEST: {avg_jobs:.1f}")
        
        if successful_tests >= len(results) * 0.8:  # 80% success rate
            print(f"\n🎉 SUCCESS: Enhanced job scraper is working in production!")
        else:
            print(f"\n⚠️  NEEDS ATTENTION: Only {successful_tests}/{len(results)} tests passed")
    
    # Save results
    with open("production_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: production_test_results.json")

if __name__ == "__main__":
    test_production_agent_creation()
