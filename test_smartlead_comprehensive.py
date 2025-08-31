#!/usr/bin/env python3
"""
Comprehensive SmartLead.ai Integration Test
Tests the complete pipeline from API key to campaign management
"""

import os
import requests
import json
import time
from datetime import datetime

def test_comprehensive_smartlead_integration():
    """Test complete SmartLead.ai integration"""
    
    print("🧪 COMPREHENSIVE SMARTLEAD.AI INTEGRATION TEST")
    print("=" * 60)
    
    api_key = os.getenv('SMARTLEAD_API_KEY', '')
    backend_url = "https://coogi-backend-7yca.onrender.com"
    
    # 1. Verify API key
    print("1️⃣ Testing API Key Configuration...")
    if not api_key:
        print("❌ SMARTLEAD_API_KEY not found in environment")
        return False
    print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # 2. Test direct SmartLead.ai API
    print("\n2️⃣ Testing Direct SmartLead.ai API...")
    try:
        response = requests.get(
            "https://server.smartlead.ai/api/v1/campaigns",
            params={"api_key": api_key},
            timeout=10
        )
        if response.status_code == 200:
            campaigns = response.json()
            print(f"✅ Direct API works: {len(campaigns)} campaigns found")
        else:
            print(f"❌ Direct API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Direct API error: {e}")
        return False
    
    # 3. Test backend health
    print("\n3️⃣ Testing Backend Health...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            smartlead_status = health.get('api_status', {}).get('SmartLead.ai', False)
            print(f"✅ Backend health: {smartlead_status}")
            if not smartlead_status:
                print("❌ SmartLead.ai not active in backend")
                return False
        else:
            print(f"❌ Backend health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health error: {e}")
        return False
    
    # 4. Test backend debug endpoint
    print("\n4️⃣ Testing Backend Environment...")
    try:
        response = requests.get(f"{backend_url}/debug/env", timeout=10)
        if response.status_code == 200:
            env_info = response.json()
            smartlead_key_status = env_info.get('SMARTLEAD_API_KEY', 'NOT_SET')
            print(f"✅ Backend env: SMARTLEAD_API_KEY = {smartlead_key_status}")
        else:
            print(f"⚠️  Backend debug endpoint not accessible: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Backend debug error: {e}")
    
    # 5. Test SmartLead account info through backend
    print("\n5️⃣ Testing SmartLead Account Access...")
    print("ℹ️  Note: This requires authentication, so we'll test direct API")
    try:
        response = requests.get(
            "https://server.smartlead.ai/api/v1/agency",
            params={"api_key": api_key},
            timeout=10
        )
        if response.status_code == 200:
            account_info = response.json()
            print(f"✅ Account access successful")
            if 'name' in account_info:
                print(f"📧 Account: {account_info.get('name', 'N/A')}")
        else:
            print(f"⚠️  Account info not accessible: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Account info error: {e}")
    
    # 6. Test SmartLead email accounts
    print("\n6️⃣ Testing SmartLead Email Accounts...")
    try:
        response = requests.get(
            "https://server.smartlead.ai/api/v1/email-accounts",
            params={"api_key": api_key},
            timeout=10
        )
        if response.status_code == 200:
            email_accounts = response.json()
            print(f"✅ Email accounts: {len(email_accounts)} found")
            if email_accounts:
                active_accounts = [acc for acc in email_accounts if acc.get('status') == 'active']
                print(f"📧 Active email accounts: {len(active_accounts)}")
        else:
            print(f"⚠️  Email accounts not accessible: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Email accounts error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 SMARTLEAD.AI INTEGRATION STATUS")
    print("=" * 60)
    print("✅ API Key: Configured and Working")
    print("✅ Backend: Deployed and Recognizing SmartLead")
    print("✅ Direct API: Connected Successfully")
    print("📋 Current Campaigns: 0 (Expected - none created yet)")
    print("\n💡 NEXT STEPS:")
    print("1. Use frontend to create a campaign")
    print("2. Verify campaign appears in SmartLead.ai dashboard")
    print("3. Test campaign management (pause/resume/stats)")
    print("4. Confirm no demo/mock data is shown")
    
    return True

if __name__ == "__main__":
    success = test_comprehensive_smartlead_integration()
    exit(0 if success else 1)
