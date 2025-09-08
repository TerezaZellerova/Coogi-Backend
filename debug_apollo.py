#!/usr/bin/env python3
"""
Debug Apollo.io search to understand why we're getting 0 results
"""

from utils.apollo_manager import ApolloManager
import json

def debug_apollo_search():
    apollo = ApolloManager()
    
    print("🔍 Debugging Apollo.io Search")
    print("=" * 50)
    
    # Test 1: Very basic search
    print("\n1. Testing basic search (any professional in Miami)")
    result1 = apollo.search_candidates(
        job_title="Manager",
        location="Miami, FL", 
        limit=5,
        require_email=False,
        require_phone=False,
        reveal_emails=True,
        reveal_phones=True,
        hunter_verify=False
    )
    
    print(f"Basic search success: {result1.get('success')}")
    print(f"Basic search candidates: {len(result1.get('candidates', []))}")
    
    if result1.get('candidates'):
        sample = result1['candidates'][0]
        print(f"Sample candidate: {sample.get('name')} | {sample.get('title')} | {sample.get('emails')} | {sample.get('phones')}")
    
    # Test 2: Veterinarian search in Miami (bigger city)
    print("\n2. Testing veterinarian search in Miami, FL")
    result2 = apollo.search_candidates(
        job_title="Veterinarian",
        location="Miami, FL",
        limit=5,
        require_email=False,
        require_phone=False,
        reveal_emails=True,
        reveal_phones=True,
        hunter_verify=False
    )
    
    print(f"Vet search success: {result2.get('success')}")
    print(f"Vet search candidates: {len(result2.get('candidates', []))}")
    
    if result2.get('candidates'):
        sample = result2['candidates'][0]
        print(f"Sample vet: {sample.get('name')} | {sample.get('title')} | {sample.get('emails')} | {sample.get('phones')}")
    
    # Test 3: Check for errors
    if not result2.get('success'):
        print(f"Error details: {result2}")
    
    # Test 4: Try the original small cities
    print("\n3. Testing Sebastian, FL specifically")
    result3 = apollo.search_candidates(
        job_title="Veterinarian",
        location="Sebastian, FL",
        limit=5,
        require_email=False,
        require_phone=False,
        reveal_emails=True,
        reveal_phones=True,
        hunter_verify=False
    )
    
    print(f"Sebastian search success: {result3.get('success')}")
    print(f"Sebastian search candidates: {len(result3.get('candidates', []))}")
    
    if not result3.get('success'):
        print(f"Sebastian error: {result3}")

if __name__ == "__main__":
    debug_apollo_search()
