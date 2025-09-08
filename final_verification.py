#!/usr/bin/env python3
"""Final verification test - check API and run one location."""

from utils.apollo_manager import ApolloManager

def final_verification():
    """Final test to verify everything is working correctly."""
    
    print("🔧 Final Apollo Integration Verification")
    print("=" * 50)
    
    apollo = ApolloManager()
    
    # Test API connectivity
    print("1. Testing API connectivity...")
    api_test = apollo.test_api_connection()
    print(f"   API Status: {api_test.get('status')}")
    print(f"   API Key Valid: {api_test.get('api_key_valid')}")
    
    if not api_test.get('api_key_valid'):
        print("❌ API key invalid, stopping test")
        return
    
    # Test one location with minimal requirements
    print("\n2. Testing Sebastian, FL with minimal requirements...")
    result = apollo.search_candidates(
        job_title="veterinarian",
        location="Sebastian, FL",
        limit=3,
        require_email=False,  # Don't require email to see raw results
        require_phone=False,
        unlock_emails=False,  # Don't unlock to see original data
    )
    
    print(f"   Success: {result.get('success')}")
    print(f"   Found: {result.get('total_found')} candidates")
    
    candidates = result.get('candidates', [])
    for i, candidate in enumerate(candidates, 1):
        print(f"\n   Candidate {i}:")
        print(f"     Name: {candidate.get('name')}")
        print(f"     Title: {candidate.get('title')}")
        print(f"     Company: {candidate.get('company')}")
        print(f"     Raw emails: {candidate.get('emails')}")
        print(f"     Raw phones: {candidate.get('phones')}")
    
    # Test with unlock enabled for just 1 candidate
    if candidates:
        print(f"\n3. Testing email unlock for first candidate...")
        test_candidate = candidates[0].copy()
        unlock_result = apollo.unlock_person_email(test_candidate)
        print(f"   Unlock success: {unlock_result.get('success')}")
        if unlock_result.get('success'):
            print(f"   Unlocked email: {unlock_result.get('email')}")
        else:
            print(f"   Unlock error: {unlock_result.get('error')}")
    
    print(f"\n✅ Verification complete!")
    
    return result

if __name__ == "__main__":
    final_verification()
