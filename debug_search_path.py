#!/usr/bin/env python3
"""
Debug the exact search path used by DVM search
"""

import asyncio
import logging
from utils.apollo_manager import ApolloManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def debug_search_path():
    """Debug each step of the DVM search path"""
    
    print("🔍 DEBUGGING DVM SEARCH PATH")
    
    apollo = ApolloManager()
    
    print("\n1. Testing paged_city_search directly...")
    candidates = apollo.paged_city_search(
        job_title="Veterinarian",
        location="New York, NY",
        per_city_limit=5,
        require_email=False,  # Start without email requirement
        use_vet_industry_tags=True
    )
    
    print(f"Paged search found: {len(candidates)} candidates")
    
    if candidates:
        print("✅ Found candidates via paged search!")
        for i, candidate in enumerate(candidates[:2]):
            print(f"  {i+1}. {candidate.get('name')} - {candidate.get('title')}")
    else:
        print("❌ No candidates from paged search")
    
    print("\n2. Testing with email requirement...")
    candidates_with_email = apollo.paged_city_search(
        job_title="Veterinarian",
        location="New York, NY",
        per_city_limit=5,
        require_email=True,
        use_vet_industry_tags=True
    )
    
    print(f"With email requirement: {len(candidates_with_email)} candidates")
    
    if candidates_with_email:
        print("✅ Found candidates with emails!")
        for i, candidate in enumerate(candidates_with_email[:2]):
            emails = candidate.get('emails', [])
            print(f"  {i+1}. {candidate.get('name')} - Emails: {emails}")
    else:
        print("❌ No candidates when requiring emails")
    
    return candidates, candidates_with_email

if __name__ == "__main__":
    candidates, candidates_with_email = asyncio.run(debug_search_path())
    
    print(f"\n🏁 DEBUG RESULTS:")
    print(f"Without email req: {len(candidates)} candidates")
    print(f"With email req: {len(candidates_with_email)} candidates")
    
    if len(candidates) > 0 and len(candidates_with_email) == 0:
        print("💡 INSIGHT: Candidates exist but email filtering is too strict")
    elif len(candidates) == 0:
        print("💡 INSIGHT: No candidates found at all - check search parameters")
