#!/usr/bin/env python3
"""
Test SmartLead.ai API key validation and campaign creation
This script will test if we can actually create campaigns through SmartLead
"""
import requests
import json
import time

def test_smartlead_creation():
    """Test actual campaign creation through SmartLead"""
    
    api_key = "de8d1c5e-1bb0-408e-a86e-1d320b721c92_zbkzree"
    base_url = "https://server.smartlead.ai/api/v1"
    
    print("🧪 TESTING SMARTLEAD CAMPAIGN CREATION")
    print("=" * 50)
    
    # Test 1: List current campaigns
    print("\n📋 Step 1: Listing current campaigns...")
    response = requests.get(
        f"{base_url}/campaigns/",
        params={"api_key": api_key}
    )
    
    if response.status_code == 200:
        current_campaigns = response.json()
        print(f"✅ Current campaigns: {len(current_campaigns)}")
        for i, campaign in enumerate(current_campaigns):
            print(f"   {i+1}. {campaign.get('name', 'Unnamed')} (ID: {campaign.get('id')})")
    else:
        print(f"❌ Failed to list campaigns: {response.status_code} - {response.text}")
        return False
    
    # Test 2: Try to create a test campaign
    print("\n🎯 Step 2: Creating test campaign...")
    
    test_campaign = {
        "name": f"COOGI Test Campaign {int(time.time())}"
    }
    
    response = requests.post(
        f"{base_url}/campaigns/create",
        params={"api_key": api_key},
        json=test_campaign
    )
    
    print(f"📡 Campaign creation response: {response.status_code}")
    print(f"📄 Response body: {response.text}")
    
    if response.status_code in [200, 201]:
        print("✅ Campaign creation successful!")
        campaign_data = response.json()
        campaign_id = campaign_data.get("id")
        print(f"🆔 Campaign ID: {campaign_id}")
        
        # Step 3: Verify campaign was created
        print("\n✅ Step 3: Verifying campaign was created...")
        time.sleep(2)  # Wait a bit
        
        response = requests.get(
            f"{base_url}/campaigns/",
            params={"api_key": api_key}
        )
        
        if response.status_code == 200:
            updated_campaigns = response.json()
            print(f"📊 Updated campaign count: {len(updated_campaigns)}")
            
            # Look for our campaign
            our_campaign = None
            for campaign in updated_campaigns:
                if campaign.get("id") == campaign_id:
                    our_campaign = campaign
                    break
            
            if our_campaign:
                print(f"🎉 SUCCESS! Campaign found: {our_campaign.get('name')}")
                return True
            else:
                print("⚠️  Campaign created but not found in list")
                return False
        else:
            print(f"❌ Failed to verify campaign: {response.status_code}")
            return False
    else:
        print(f"❌ Campaign creation failed: {response.status_code}")
        print(f"Error details: {response.text}")
        return False

if __name__ == "__main__":
    success = test_smartlead_creation()
    print(f"\n{'=' * 50}")
    if success:
        print("🎉 SMARTLEAD CAMPAIGN CREATION TEST: SUCCESS")
    else:
        print("❌ SMARTLEAD CAMPAIGN CREATION TEST: FAILED")
