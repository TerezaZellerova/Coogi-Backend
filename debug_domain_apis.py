#!/usr/bin/env python3
"""
Debug script to test domain extraction and API responses
"""
import asyncio
import logging
import os
import httpx
from utils.bulletproof_contact_finder import BulletproofContactFinder

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_domain_extraction_and_apis():
    """Test domain extraction and actual API responses"""
    
    contact_finder = BulletproofContactFinder()
    
    test_companies = [
        "Google",
        "Microsoft", 
        "Northwestern Medicine",
        "Wolters Kluwer"
    ]
    
    print("🔍 Testing Domain Extraction & API Responses")
    print("=" * 60)
    
    for company in test_companies:
        print(f"\n🏢 Company: {company}")
        print("-" * 40)
        
        # Test domain extraction
        domain = contact_finder._extract_domain(company)
        print(f"📧 Extracted domain: {domain}")
        
        # Test Hunter.io API directly
        if contact_finder.hunter_api_key:
            print("🔍 Testing Hunter.io API...")
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    params = {
                        "domain": domain,
                        "api_key": contact_finder.hunter_api_key,
                        "limit": 5,
                        "offset": 0
                    }
                    
                    response = await client.get(
                        "https://api.hunter.io/v2/domain-search", 
                        params=params
                    )
                    
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   Response keys: {list(data.keys())}")
                        if 'data' in data:
                            emails = data['data'].get('emails', [])
                            print(f"   Found {len(emails)} emails")
                            if emails:
                                print(f"   First email: {emails[0]}")
                        else:
                            print(f"   Full response: {data}")
                    else:
                        print(f"   Error response: {response.text}")
                        
            except Exception as e:
                print(f"   Error: {e}")
        
        # Test if RapidAPI key works
        if contact_finder.rapidapi_key:
            print("🔍 Testing RapidAPI AnyMailFinder...")
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    headers = {
                        "X-RapidAPI-Key": contact_finder.rapidapi_key,
                        "X-RapidAPI-Host": "anymail-finder.p.rapidapi.com"
                    }
                    
                    params = {"domain": domain}
                    
                    response = await client.get(
                        "https://anymail-finder.p.rapidapi.com/domain",
                        headers=headers,
                        params=params
                    )
                    
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   Response: {data}")
                    else:
                        print(f"   Error: {response.text}")
                        
            except Exception as e:
                print(f"   Error: {e}")
        
        print()
        await asyncio.sleep(2)  # Rate limiting
    
    print("=" * 60)
    print("🎯 Domain & API Test Complete")

if __name__ == "__main__":
    asyncio.run(test_domain_extraction_and_apis())
