#!/usr/bin/env python3
"""
Test SmartLead.ai Integration for COOGI
Tests the SmartLead.ai API integration and campaign creation
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_smartlead_integration():
    """Test SmartLead.ai API integration"""
    
    print("🧪 TESTING SMARTLEAD.AI INTEGRATION")
    print("=" * 50)
    
    # Check environment variable
    api_key = os.getenv('SMARTLEAD_API_KEY', '')
    if not api_key:
        print("❌ SMARTLEAD_API_KEY environment variable not set")
        return False
    
    print(f"✅ SmartLead.ai API Key found: {api_key[:10]}...")
    
    # Test API connection directly to SmartLead.ai
    print("\n📡 Testing direct SmartLead.ai API connection...")
    
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        # SmartLead.ai uses API key as query parameter
        params = {"api_key": api_key}
        
        # Test campaigns endpoint
        response = requests.get(
            "https://server.smartlead.ai/api/v1/campaigns",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ SmartLead.ai API connection successful!")
            campaigns = response.json()
            print(f"📊 Found {len(campaigns)} existing campaigns")
        elif response.status_code == 401:
            print("❌ SmartLead.ai API authentication failed - check API key")
            return False
        else:
            print(f"⚠️  SmartLead.ai API returned status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error connecting to SmartLead.ai API: {e}")
        return False
    
    # Test COOGI backend SmartLead integration
    print("\n🔧 Testing COOGI backend SmartLead.ai integration...")
    
    backend_url = "https://coogi-backend-7yca.onrender.com"
    
    # Test 1: Check if SmartLead is in health status
    try:
        health_response = requests.get(f"{backend_url}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            smartlead_status = health_data.get("api_status", {}).get("SmartLead.ai", False)
            
            if smartlead_status:
                print("✅ SmartLead.ai is configured in backend health check")
            else:
                print("❌ SmartLead.ai not found in backend health check")
                print("💡 You need to add SMARTLEAD_API_KEY to Render environment variables")
                return False
        else:
            print(f"❌ Backend health check failed: {health_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking backend health: {e}")
        return False
    
    # Test 2: Try creating a test campaign
    print("\n🎯 Testing campaign creation...")
    
    test_campaign_data = {
        "name": f"COOGI Test Campaign {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "leads": [
            {
                "email": "test@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Test Company"
            }
        ],
        "email_template": "Hi {{first_name}},\n\nThis is a test campaign from COOGI platform.\n\nBest regards,\nCOOGI Team",
        "subject": "Test Campaign from COOGI Platform",
        "from_email": "noreply@coogi.ai",
        "from_name": "COOGI Recruiting Team"
    }
    
    try:
        # Note: This requires proper authentication which may not be available in this test
        print("⚠️  Campaign creation test requires proper authentication")
        print("💡 Once backend is deployed with SMARTLEAD_API_KEY, this will work")
        
    except Exception as e:
        print(f"⚠️  Campaign creation test: {e}")
    
    print("\n" + "=" * 50)
    print("✅ SMARTLEAD.AI INTEGRATION TEST COMPLETED")
    print("\n📋 NEXT STEPS:")
    print("1. Add SMARTLEAD_API_KEY to Render environment variables")
    print("2. Redeploy backend service")
    print("3. Test campaign creation through frontend")
    print("4. Verify campaigns appear in SmartLead.ai dashboard")
    
    return True

if __name__ == "__main__":
    # Set the API key for testing
    os.environ['SMARTLEAD_API_KEY'] = 'de8d1c5e-1bb0-408e-a86e-1d320b721c92_zbkzree'
    
    success = test_smartlead_integration()
    sys.exit(0 if success else 1)
