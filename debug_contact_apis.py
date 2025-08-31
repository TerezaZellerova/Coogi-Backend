#!/usr/bin/env python3
"""
Debug Contact APIs - Test all contact enrichment APIs individually
"""
import os
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContactAPIDebugger:
    def __init__(self):
        self.hunter_api_key = os.getenv("HUNTER_API_KEY", "")
        self.clearout_api_key = os.getenv("CLEAROUT_API_KEY", "")
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
        
    async def test_hunter_api(self, domain: str) -> Dict[str, Any]:
        """Test Hunter.io API directly"""
        if not self.hunter_api_key:
            return {"error": "No Hunter API key"}
        
        url = "https://api.hunter.io/v2/domain-search"
        params = {
            "domain": domain,
            "api_key": self.hunter_api_key,
            "limit": 10
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "domain": domain,
                            "emails_found": len(data.get("data", {}).get("emails", [])),
                            "status": response.status,
                            "data": data.get("data", {})
                        }
                    else:
                        text = await response.text()
                        return {
                            "error": f"Hunter API error: {response.status}",
                            "response": text
                        }
        except Exception as e:
            return {"error": f"Hunter API exception: {e}"}
    
    async def test_clearout_api(self, email: str) -> Dict[str, Any]:
        """Test Clearout API directly"""
        if not self.clearout_api_key:
            return {"error": "No Clearout API key"}
        
        url = "https://api.clearout.io/v2/email_verify/instant"
        headers = {
            "Authorization": f"Bearer:{self.clearout_api_key}",
            "Content-Type": "application/json"
        }
        data = {"email": email}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "email": email,
                            "status": response.status,
                            "data": result
                        }
                    else:
                        text = await response.text()
                        return {
                            "error": f"Clearout API error: {response.status}",
                            "response": text
                        }
        except Exception as e:
            return {"error": f"Clearout API exception: {e}"}
    
    async def test_rapidapi_contact_search(self, company: str) -> Dict[str, Any]:
        """Test RapidAPI contact search"""
        if not self.rapidapi_key:
            return {"error": "No RapidAPI key"}
        
        # Try the Apollo.io API via RapidAPI
        url = "https://apollo-io.p.rapidapi.com/people/search"
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "apollo-io.p.rapidapi.com",
            "Content-Type": "application/json"
        }
        data = {
            "organization_names": [company],
            "page": 1,
            "per_page": 10
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "company": company,
                            "status": response.status,
                            "contacts_found": len(result.get("people", [])),
                            "data": result
                        }
                    else:
                        text = await response.text()
                        return {
                            "error": f"RapidAPI Apollo error: {response.status}",
                            "response": text
                        }
        except Exception as e:
            return {"error": f"RapidAPI Apollo exception: {e}"}

async def main():
    debugger = ContactAPIDebugger()
    
    # Test companies
    test_companies = ["google.com", "microsoft.com", "apple.com"]
    test_emails = ["test@google.com", "example@microsoft.com"]
    
    print("=== API Keys Status ===")
    print(f"Hunter API Key: {'✅ SET' if debugger.hunter_api_key else '❌ NOT SET'}")
    print(f"Clearout API Key: {'✅ SET' if debugger.clearout_api_key else '❌ NOT SET'}")
    print(f"RapidAPI Key: {'✅ SET' if debugger.rapidapi_key else '❌ NOT SET'}")
    print()
    
    print("=== Testing Hunter.io API ===")
    for domain in test_companies:
        print(f"\nTesting Hunter.io for {domain}:")
        result = await debugger.test_hunter_api(domain)
        if "success" in result:
            print(f"✅ Success: Found {result['emails_found']} emails")
            if result['emails_found'] > 0:
                emails = result['data'].get('emails', [])[:3]  # Show first 3
                for email in emails:
                    print(f"   - {email.get('value', 'N/A')} ({email.get('first_name', 'N/A')} {email.get('last_name', 'N/A')})")
        else:
            print(f"❌ Error: {result['error']}")
    
    print("\n=== Testing Clearout API ===")
    for email in test_emails:
        print(f"\nTesting Clearout for {email}:")
        result = await debugger.test_clearout_api(email)
        if "success" in result:
            print(f"✅ Success: {result['data']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    print("\n=== Testing RapidAPI Contact Search ===")
    for company in ["Google", "Microsoft", "Apple"]:
        print(f"\nTesting RapidAPI for {company}:")
        result = await debugger.test_rapidapi_contact_search(company)
        if "success" in result:
            print(f"✅ Success: Found {result['contacts_found']} contacts")
            if result['contacts_found'] > 0:
                contacts = result['data'].get('people', [])[:3]  # Show first 3
                for contact in contacts:
                    print(f"   - {contact.get('name', 'N/A')} ({contact.get('email', 'N/A')})")
        else:
            print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
