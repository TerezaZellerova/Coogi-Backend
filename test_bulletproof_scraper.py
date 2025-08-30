#!/usr/bin/env python3
"""
Test the bulletproof job scraper to debug LinkedIn job fetching
"""
import asyncio
import json
import logging
import os
from dotenv import load_dotenv
from utils.bulletproof_job_scraper import BulletproofJobScraper

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bulletproof_scraper():
    """Test bulletproof job scraper with hiring manager query"""
    scraper = BulletproofJobScraper()
    
    print("🔍 Testing bulletproof job scraper...")
    print("=" * 50)
    
    # Test with a simple hiring manager query
    query = "hiring manager"
    company_size = "medium"
    location = "United States"
    
    print(f"Query: {query}")
    print(f"Company Size: {company_size}")
    print(f"Location: {location}")
    print()
    
    try:
        jobs = await scraper.search_jobs_bulletproof(
            query=query,
            hours_old=48,  # Increase hours for better results
            company_size=company_size,
            location=location,
            max_results=20
        )
        
        print(f"📊 Total jobs found: {len(jobs)}")
        print()
        
        # Group by site
        by_site = {}
        for job in jobs:
            site = job.get("site", "Unknown")
            if site not in by_site:
                by_site[site] = []
            by_site[site].append(job)
        
        print("📈 Jobs by site:")
        for site, site_jobs in by_site.items():
            print(f"  {site}: {len(site_jobs)} jobs")
        print()
        
        # Show sample jobs from each site
        for site, site_jobs in by_site.items():
            print(f"🔍 Sample {site} jobs:")
            for i, job in enumerate(site_jobs[:3]):  # Show first 3
                print(f"  {i+1}. {job.get('title', 'No title')} at {job.get('company', 'No company')}")
                print(f"     Location: {job.get('location', 'No location')}")
                print(f"     Posted: {job.get('posted_date', 'No date')}")
                print(f"     URL: {job.get('url', 'No URL')[:80]}...")
                print()
        
        # Save detailed results for inspection
        with open("/Users/waqaskhan/Documents/Coogi New Project/coogi-backend/test_scraper_results.json", "w") as f:
            json.dump(jobs, f, indent=2, default=str)
        
        print("💾 Detailed results saved to test_scraper_results.json")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bulletproof_scraper())
