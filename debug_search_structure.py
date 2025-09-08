#!/usr/bin/env python3
"""Debug the search result structure."""

import os
from utils.apollo_manager import ApolloManager

def debug_search():
    """Debug what the search method actually returns."""
    
    print("🔍 Debugging search result structure")
    print("=" * 50)
    
    apollo = ApolloManager()
    
    # Test one location
    location = "Sebastian, FL"
    print(f"Testing location: {location}")
    
    result = apollo.search_dvm_in_locations([location])
    
    print(f"Result type: {type(result)}")
    print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    
    if isinstance(result, dict):
        for key, value in result.items():
            print(f"  {key}: {type(value)} - {len(value) if hasattr(value, '__len__') else value}")
            if key == 'candidates' and isinstance(value, list) and value:
                print(f"    First candidate keys: {value[0].keys() if value else 'None'}")
    
    return result

if __name__ == "__main__":
    debug_search()
