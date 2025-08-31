#!/usr/bin/env python3
"""
Test the LinkedIn job categorization fix
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bulletproof_job_scraper import BulletproofJobScraper

load_dotenv()

async def test_linkedin_categorization():
    """Test if LinkedIn jobs are now properly categorized"""
    print("🧪 Testing LinkedIn job categorization fix...")
    
    # Initialize scraper
    scraper = BulletproofJobScraper()
    
    # Get jobs
    jobs = await scraper.search_jobs_bulletproof(
        query="software engineer",
        hours_old=24,
        company_size="all",
        location="United States",
        max_results=20
    )
    
    print(f"📊 Total jobs found: {len(jobs)}")
    
    # Categorize jobs
    linkedin_jobs = []
    other_jobs = []
    
    for job in jobs:
        job_url = job.get("url", "").lower()
        job_site = job.get("site", "").lower()
        
        # Same logic as in progressive_agents.py
        if (job_site == "linkedin" or 
            (job_site == "jsearch" and "linkedin.com" in job_url)):
            linkedin_jobs.append(job)
        else:
            other_jobs.append(job)
    
    print(f"🔗 LinkedIn jobs: {len(linkedin_jobs)}")
    print(f"📋 Other jobs: {len(other_jobs)}")
    
    # Show sample LinkedIn jobs
    if linkedin_jobs:
        print(f"\n✅ LinkedIn jobs found! Sample:")
        for i, job in enumerate(linkedin_jobs[:3]):
            print(f"  {i+1}. {job.get('title')} at {job.get('company')}")
            print(f"     Site: {job.get('site')} | URL: {job.get('url')[:60]}...")
    else:
        print("\n❌ No LinkedIn jobs found")
        
    # Show job site breakdown
    site_counts = {}
    for job in jobs:
        site = job.get("site", "unknown")
        site_counts[site] = site_counts.get(site, 0) + 1
        
    print(f"\n📈 Job site breakdown:")
    for site, count in site_counts.items():
        print(f"  {site}: {count} jobs")

if __name__ == "__main__":
    asyncio.run(test_linkedin_categorization())
