#!/usr/bin/env python3
"""
Debug script to test contact enrichment for specific companies
"""
import asyncio
import logging
import os
from utils.bulletproof_contact_finder import BulletproofContactFinder

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_contact_enrichment():
    """Test contact enrichment for real companies"""
    
    # Test companies from the actual job results
    test_companies = [
        "Northwestern Medicine",
        "Wolters Kluwer", 
        "Evolent",
        "Google",
        "Microsoft"
    ]
    
    contact_finder = BulletproofContactFinder()
    
    print("🔍 Testing Contact Enrichment APIs")
    print("=" * 50)
    
    for company in test_companies:
        print(f"\n🏢 Testing: {company}")
        print("-" * 30)
        
        try:
            contacts = await contact_finder._find_company_contacts(
                company=company,
                target_roles=["recruiter", "hr manager", "talent acquisition"],
                max_contacts=3
            )
            
            print(f"✅ Found {len(contacts)} contacts for {company}")
            
            for i, contact in enumerate(contacts[:2], 1):
                print(f"   {i}. {contact.get('name', 'N/A')} - {contact.get('email', 'N/A')}")
                print(f"      Role: {contact.get('position', 'N/A')}")
                print(f"      Source: {contact.get('source', 'N/A')}")
        
        except Exception as e:
            print(f"❌ Error for {company}: {e}")
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    print("\n" + "=" * 50)
    print("🎯 Contact Enrichment Test Complete")

if __name__ == "__main__":
    asyncio.run(test_contact_enrichment())
