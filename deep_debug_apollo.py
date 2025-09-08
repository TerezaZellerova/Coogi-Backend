#!/usr/bin/env python3
"""
Deep debug Apollo.io API response to see raw data
"""

from utils.apollo_manager import ApolloManager
import json

def deep_debug_apollo():
    apollo = ApolloManager()
    
    print("🔍 Deep Debugging Apollo.io API Response")
    print("=" * 60)
    
    # Test with direct API call to see raw response
    payload = {
        "page": 1,
        "per_page": 2,
        "person_titles": ["Veterinarian"],
        "person_locations": ["Miami, FL"],
        "reveal_work_emails": True,
        "reveal_personal_emails": True,
        "reveal_phone": True
    }
    
    print(f"1. Testing direct API call with payload:")
    print(json.dumps(payload, indent=2))
    
    # Make the raw request
    raw_result = apollo._request("POST", "/mixed_people/search", json=payload)
    
    print(f"\n2. Raw API Response:")
    print(f"Keys in response: {list(raw_result.keys())}")
    
    if "people" in raw_result:
        people = raw_result["people"]
        print(f"Number of people found: {len(people)}")
        
        if people:
            person = people[0]
            print(f"\n3. First person raw data:")
            print(f"Name: {person.get('name')}")
            print(f"Title: {person.get('title')}")
            print(f"Email (direct): {person.get('email')}")
            print(f"Emails array: {person.get('emails')}")
            print(f"Phone numbers: {person.get('phone_numbers')}")
            print(f"Email status: {person.get('email_status')}")
            print(f"Phone status: {person.get('phone_status')}")
            
            print(f"\n4. All person keys:")
            for key in sorted(person.keys()):
                value = person[key]
                if isinstance(value, (str, int, float, bool)):
                    print(f"  {key}: {value}")
                elif isinstance(value, list):
                    print(f"  {key}: [list with {len(value)} items]")
                elif isinstance(value, dict):
                    print(f"  {key}: [dict with keys: {list(value.keys())}]")
                else:
                    print(f"  {key}: {type(value)}")
    
    print(f"\n5. Full raw response structure:")
    print(json.dumps(raw_result, indent=2, default=str)[:2000] + "..." if len(str(raw_result)) > 2000 else json.dumps(raw_result, indent=2, default=str))

if __name__ == "__main__":
    deep_debug_apollo()
