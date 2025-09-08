#!/usr/bin/env python3
"""
Test search_candidates directly vs paged_city_search to find the difference
"""

import asyncio
import logging
from utils.apollo_manager import ApolloManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def compare_searches():
    """Compare direct search_candidates vs paged_city_search"""
    
    print("🔍 COMPARING SEARCH METHODS")
    
    apollo = ApolloManager()
    
    print("\n1. Testing search_candidates directly...")
    direct_result = apollo.search_candidates(
        job_title="Veterinarian",
        location="New York, NY",
        limit=5,
        require_email=False,
        unlock_emails=False
    )
    
    print(f"Direct search: success={direct_result.get('success')}, candidates={len(direct_result.get('candidates', []))}")
    
    if direct_result.get('candidates'):
        for i, candidate in enumerate(direct_result.get('candidates', [])[:2]):
            print(f"  {i+1}. {candidate.get('name')} - {candidate.get('title')}")
    
    print("\n2. Testing paged_city_search...")
    paged_candidates = apollo.paged_city_search(
        job_title="Veterinarian",
        location="New York, NY",
        per_city_limit=5,
        require_email=False,
        use_vet_industry_tags=False  # Try without vet tags first
    )
    
    print(f"Paged search: {len(paged_candidates)} candidates")
    
    if paged_candidates:
        for i, candidate in enumerate(paged_candidates[:2]):
            print(f"  {i+1}. {candidate.get('name')} - {candidate.get('title')}")
    
    print("\n3. Testing paged_city_search with vet tags...")
    paged_vet_candidates = apollo.paged_city_search(
        job_title="Veterinarian",
        location="New York, NY",
        per_city_limit=5,
        require_email=False,
        use_vet_industry_tags=True  # With vet tags
    )
    
    print(f"Paged search with vet tags: {len(paged_vet_candidates)} candidates")
    
    return direct_result, paged_candidates, paged_vet_candidates

if __name__ == "__main__":
    direct, paged, paged_vet = asyncio.run(compare_searches())
    
    print(f"\n🏁 COMPARISON RESULTS:")
    print(f"Direct search_candidates: {len(direct.get('candidates', []))} candidates")
    print(f"Paged search (no vet tags): {len(paged)} candidates")
    print(f"Paged search (with vet tags): {len(paged_vet)} candidates")
    
    if len(direct.get('candidates', [])) > 0 and len(paged) == 0:
        print("💡 INSIGHT: Issue is in paged_city_search implementation")
