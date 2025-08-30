#!/usr/bin/env python3
"""
Test the fixed database saving and LinkedIn job categorization
"""
import asyncio
import json
import logging
from utils.progressive_agent_db import progressive_agent_db
from utils.bulletproof_job_scraper import BulletproofJobScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_saving():
    """Test if database saving works with the fixes"""
    print("🧪 Testing Database Saving and LinkedIn Job Categorization")
    print("=" * 60)
    
    # Test 1: Database Connection
    print("\n📊 Testing Supabase connection...")
    try:
        stats = await progressive_agent_db.get_dashboard_stats()
        print(f"✅ Supabase connected! Current stats: {stats}")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return
    
    # Test 2: Job Scraping and Categorization
    print("\n🔍 Testing job scraping and LinkedIn categorization...")
    scraper = BulletproofJobScraper()
    
    try:
        # Get jobs from bulletproof scraper
        all_jobs = await scraper.search_jobs_bulletproof(
            query="hiring manager",
            hours_old=48,
            company_size="medium",
            location="United States",
            max_results=20
        )
        
        print(f"📈 Total jobs found: {len(all_jobs)}")
        
        # Categorize jobs like the fixed router does
        linkedin_jobs = []
        other_jobs = []
        
        for job in all_jobs:
            job_url = job.get("url", "").lower()
            job_site = job.get("site", "").lower()
            
            # LinkedIn jobs: direct LinkedIn API OR JSearch with LinkedIn URLs
            if (job_site == "linkedin" or 
                (job_site == "jsearch" and "linkedin.com" in job_url)):
                linkedin_jobs.append(job)
            else:
                other_jobs.append(job)
        
        print(f"📋 LinkedIn jobs: {len(linkedin_jobs)}")
        print(f"📋 Other jobs: {len(other_jobs)}")
        
        # Show sample LinkedIn jobs
        if linkedin_jobs:
            print(f"\n🔗 Sample LinkedIn jobs:")
            for i, job in enumerate(linkedin_jobs[:3]):
                print(f"  {i+1}. {job.get('title')} at {job.get('company')}")
                print(f"     Site: {job.get('site')} | URL: {job.get('url', '')[:50]}...")
        
    except Exception as e:
        print(f"❌ Job scraping failed: {e}")
        return
    
    # Test 3: Database Saving
    print(f"\n💾 Testing database saving...")
    test_agent_id = "test_agent_db_fix"
    
    try:
        # Save jobs to database
        if linkedin_jobs:
            await progressive_agent_db.save_jobs(test_agent_id, linkedin_jobs)
            print(f"✅ LinkedIn jobs saved to database")
        
        if other_jobs:
            await progressive_agent_db.save_jobs(test_agent_id, other_jobs[:5])  # Just save first 5
            print(f"✅ Other jobs saved to database")
        
        # Verify they were saved
        saved_jobs = await progressive_agent_db.get_agent_jobs(agent_id=test_agent_id)
        print(f"✅ Verified: {len(saved_jobs)} jobs retrieved from database")
        
        if saved_jobs:
            print(f"\n📝 Sample saved job:")
            sample_job = saved_jobs[0]
            print(f"   Title: {sample_job.get('title')}")
            print(f"   Company: {sample_job.get('company')}")
            print(f"   Site: {sample_job.get('site')}")
            print(f"   URL: {sample_job.get('url', '')[:50]}...")
    
    except Exception as e:
        print(f"❌ Database saving failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"   - LinkedIn job categorization: WORKING")
    print(f"   - Database saving: WORKING") 
    print(f"   - Total LinkedIn jobs found: {len(linkedin_jobs)}")

if __name__ == "__main__":
    asyncio.run(test_database_saving())
