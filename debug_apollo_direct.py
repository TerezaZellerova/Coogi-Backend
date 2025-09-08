#!/usr/bin/env python3
"""
Debug Apollo.io API to understand why no candidates are returned
"""

import asyncio
import logging
from utils.apollo_manager import ApolloManager

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def debug_apollo_search():
    """Debug Apollo.io search to see what's happening"""
    
    print("🔍 DEBUGGING APOLLO.IO SEARCH")
    
    apollo = ApolloManager()
    
    # Test basic search first
    print("\n1. Testing basic DVM search in New York...")
    result = apollo.search_candidates(
        job_title="Veterinarian",
        location="New York, NY",
        limit=5,
        require_email=False,  # Don't require email for initial test
        unlock_emails=False   # Don't unlock for basic test
    )
    
    print(f"Basic search result: success={result.get('success')}, candidates={len(result.get('candidates', []))}")
    
    if result.get('candidates'):
        print("✅ Found candidates! Sample:")
        for i, candidate in enumerate(result.get('candidates', [])[:2]):
            print(f"  {i+1}. {candidate.get('name')} - {candidate.get('title')} at {candidate.get('company')}")
    else:
        print("❌ No candidates found")
        print(f"Error: {result.get('error')}")
    
    # Test with alternative terms
    print("\n2. Testing with alternative terms...")
    alt_terms = ["DVM", "Animal Doctor", "Veterinary"]
    
    for term in alt_terms:
        print(f"\nTesting '{term}'...")
        result = apollo.search_candidates(
            job_title=term,
            location="United States",
            limit=3,
            require_email=False,
            unlock_emails=False
        )
        print(f"  {term}: {len(result.get('candidates', []))} candidates")

if __name__ == "__main__":
    asyncio.run(debug_apollo_search())
