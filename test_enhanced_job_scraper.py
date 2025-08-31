#!/usr/bin/env python3
"""
Test Enhanced Bulletproof Job Scraper
Tests the aggressive search strategies to ensure 100-500+ jobs per search
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bulletproof_job_scraper import bulletproof_job_scraper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_job_search():
    """Test the enhanced job search with different queries and filters"""
    
    test_cases = [
        {
            "query": "software engineer",
            "company_size": "medium", 
            "location": "San Francisco",
            "target_jobs": 200
        },
        {
            "query": "product manager",
            "company_size": "all",
            "location": "New York",
            "target_jobs": 300
        },
        {
            "query": "data analyst",
            "company_size": "small",
            "location": "United States", 
            "target_jobs": 150
        },
        {
            "query": "marketing manager",
            "company_size": "medium",
            "location": "Los Angeles",
            "target_jobs": 250
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"🧪 TEST CASE {i}: {test_case['query']} | {test_case['company_size']} | {test_case['location']}")
        print(f"🎯 TARGET: {test_case['target_jobs']} jobs")
        print(f"{'='*80}")
        
        try:
            start_time = datetime.now()
            
            jobs = await bulletproof_job_scraper.search_jobs_bulletproof(
                query=test_case["query"],
                company_size=test_case["company_size"],
                location=test_case["location"],
                max_results=test_case["target_jobs"]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze results
            job_sites = {}
            linkedin_jobs = 0
            demo_jobs = 0
            recent_jobs = 0
            
            for job in jobs:
                site = job.get("site", "Unknown")
                job_sites[site] = job_sites.get(site, 0) + 1
                
                if "linkedin" in site.lower():
                    linkedin_jobs += 1
                    
                if job.get("is_demo", False):
                    demo_jobs += 1
                    
                posted_date = job.get("posted_date", "").lower()
                if any(term in posted_date for term in ["today", "1 day", "2 days", "3 days"]):
                    recent_jobs += 1
            
            result = {
                "test_case": test_case,
                "jobs_found": len(jobs),
                "target_met": len(jobs) >= test_case["target_jobs"] * 0.8,  # 80% threshold
                "duration_seconds": duration,
                "job_sites": job_sites,
                "linkedin_jobs": linkedin_jobs,
                "demo_jobs": demo_jobs,
                "recent_jobs": recent_jobs,
                "success_rate": (len(jobs) / test_case["target_jobs"]) * 100
            }
            
            results.append(result)
            
            # Print detailed results
            print(f"✅ JOBS FOUND: {len(jobs)} / {test_case['target_jobs']} ({result['success_rate']:.1f}%)")
            print(f"⏱️  DURATION: {duration:.1f} seconds")
            print(f"🌐 JOB SITES: {job_sites}")
            print(f"🔗 LINKEDIN JOBS: {linkedin_jobs}")
            print(f"📅 RECENT JOBS: {recent_jobs}")
            print(f"🎭 DEMO JOBS: {demo_jobs}")
            print(f"✅ TARGET MET: {'YES' if result['target_met'] else 'NO'}")
            
            # Show sample jobs
            print(f"\n📋 SAMPLE JOBS:")
            for j, job in enumerate(jobs[:5], 1):
                print(f"  {j}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')} ({job.get('site', 'N/A')})")
            
        except Exception as e:
            logger.error(f"❌ Test case {i} failed: {e}")
            result = {
                "test_case": test_case,
                "jobs_found": 0,
                "target_met": False,
                "error": str(e)
            }
            results.append(result)
    
    # Overall summary
    print(f"\n{'='*80}")
    print(f"📊 OVERALL TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get("target_met", False))
    total_jobs = sum(r.get("jobs_found", 0) for r in results)
    
    print(f"✅ SUCCESSFUL TESTS: {successful_tests} / {total_tests}")
    print(f"📈 TOTAL JOBS FOUND: {total_jobs}")
    print(f"📊 AVERAGE JOBS PER TEST: {total_jobs / total_tests:.1f}")
    
    # Save detailed results
    with open("enhanced_job_scraper_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: enhanced_job_scraper_test_results.json")
    
    return results

if __name__ == "__main__":
    print("🚀 Testing Enhanced Bulletproof Job Scraper")
    print("🎯 Goal: Reliably find 100-500+ jobs per search")
    
    try:
        results = asyncio.run(test_enhanced_job_search())
        
        # Quick success check
        successful = sum(1 for r in results if r.get("target_met", False))
        if successful >= len(results) * 0.75:  # 75% success rate
            print(f"\n🎉 SUCCESS: Enhanced job scraper is working! ({successful}/{len(results)} tests passed)")
        else:
            print(f"\n⚠️  NEEDS IMPROVEMENT: Only {successful}/{len(results)} tests passed")
            
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        sys.exit(1)
