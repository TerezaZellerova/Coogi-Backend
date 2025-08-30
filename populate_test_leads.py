#!/usr/bin/env python3
"""
Manual Lead Database Population Script
Populates the database with test data to verify the leads page is working
"""
import os
import sys
import asyncio
from datetime import datetime

# Add the parent directory to sys.path so we can import our modules
sys.path.append('/Users/waqaskhan/Documents/Coogi New Project/coogi-backend')

from utils.progressive_agent_db import progressive_agent_db

async def populate_test_data():
    """Populate database with test leads data"""
    
    print("🚀 Starting test data population...")
    
    # Test agent ID
    agent_id = "test_agent_demo_data"
    
    # Sample jobs data
    test_jobs = [
        {
            "id": "demo_job_1",
            "title": "Senior Software Engineer",
            "company": "TechCorp Inc",
            "location": "San Francisco, CA",
            "url": "https://example.com/job/1",
            "description": "We are looking for a senior software engineer...",
            "posted_date": "2025-08-30",
            "employment_type": "Full-time",
            "salary": "$120,000 - $180,000",
            "site": "LinkedIn",
            "is_remote": True,
            "skills": ["Python", "JavaScript", "AWS"],
            "is_demo": True,
            "scraped_at": datetime.now().isoformat()
        },
        {
            "id": "demo_job_2", 
            "title": "Marketing Manager",
            "company": "StartupXYZ",
            "location": "Remote",
            "url": "https://example.com/job/2",
            "description": "Join our growing marketing team...",
            "posted_date": "2025-08-29",
            "employment_type": "Full-time",
            "salary": "$80,000 - $120,000",
            "site": "Indeed",
            "is_remote": True,
            "skills": ["Marketing", "Analytics", "Content"],
            "is_demo": True,
            "scraped_at": datetime.now().isoformat()
        },
        {
            "id": "demo_job_3",
            "title": "Product Designer",
            "company": "Design Studio",
            "location": "New York, NY", 
            "url": "https://example.com/job/3",
            "description": "Creative product designer needed...",
            "posted_date": "2025-08-28",
            "employment_type": "Contract",
            "salary": "$90,000 - $130,000",
            "site": "Glassdoor",
            "is_remote": False,
            "skills": ["Figma", "UI/UX", "Prototyping"],
            "is_demo": True,
            "scraped_at": datetime.now().isoformat()
        }
    ]
    
    # Sample contacts data
    test_contacts = [
        {
            "id": "demo_contact_1",
            "name": "Sarah Johnson",
            "first_name": "Sarah",
            "last_name": "Johnson", 
            "email": "sarah.johnson@techcorp.com",
            "company": "TechCorp Inc",
            "role": "VP Engineering",
            "title": "VP Engineering",
            "linkedin_url": "https://linkedin.com/in/sarah-johnson",
            "phone": "+1-555-123-4567",
            "verified": True,
            "source": "Hunter.io",
            "confidence_score": 95
        },
        {
            "id": "demo_contact_2",
            "name": "Michael Chen",
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "mike.chen@startupxyz.com", 
            "company": "StartupXYZ",
            "role": "Head of Marketing",
            "title": "Head of Marketing",
            "linkedin_url": "https://linkedin.com/in/michael-chen",
            "verified": True,
            "source": "Clearout",
            "confidence_score": 88
        },
        {
            "id": "demo_contact_3",
            "name": "Emily Rodriguez",
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.r@designstudio.com",
            "company": "Design Studio", 
            "role": "Creative Director",
            "title": "Creative Director",
            "linkedin_url": "https://linkedin.com/in/emily-rodriguez",
            "verified": True,
            "source": "RapidAPI",
            "confidence_score": 92
        }
    ]
    
    try:
        # Save agent metadata
        await progressive_agent_db.save_agent_metadata(
            agent_id=agent_id,
            query="Demo test data",
            status="completed",
            total_jobs=len(test_jobs),
            total_contacts=len(test_contacts),
            total_campaigns=0
        )
        print(f"✅ Saved agent metadata for {agent_id}")
        
        # Save jobs
        await progressive_agent_db.save_jobs(agent_id, test_jobs)
        print(f"💼 Saved {len(test_jobs)} test jobs")
        
        # Save contacts  
        await progressive_agent_db.save_contacts(agent_id, test_contacts)
        print(f"👥 Saved {len(test_contacts)} test contacts")
        
        print("\n🎉 Test data population completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Agent ID: {agent_id}")
        print(f"   - Jobs: {len(test_jobs)}")
        print(f"   - Contacts: {len(test_contacts)}")
        print(f"   - Status: completed")
        
    except Exception as e:
        print(f"❌ Error populating test data: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(populate_test_data())
