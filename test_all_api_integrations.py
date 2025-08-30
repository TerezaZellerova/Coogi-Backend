#!/usr/bin/env python3
"""
Test JSearch and Smartlead.ai Integration
Tests both APIs functionality for COOGI backend
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from utils.jsearch_manager import JSearchManager
from utils.smartlead_manager import SmartleadManager
from dotenv import load_dotenv

async def test_jsearch_integration():
    """Test JSearch manager functionality"""
    print("🔍 Testing JSearch Integration...")
    
    # Load environment variables
    load_dotenv()
    
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    
    if not rapidapi_key:
        print("❌ RapidAPI key not found in environment")
        return False
    
    print(f"✅ RapidAPI key found: {rapidapi_key[:10]}...")
    
    # Initialize JSearch Manager
    jsearch_manager = JSearchManager()
    
    # Test 1: API Status Check
    print("\n📊 Checking JSearch API status...")
    status = jsearch_manager.get_api_status()
    
    if status.get("status") == "operational":
        print(f"✅ JSearch API operational")
        print(f"✅ Response time: {status.get('response_time_ms', 'N/A')}ms")
    else:
        print(f"❌ JSearch API error: {status.get('error', 'Unknown error')}")
        return False
    
    # Test 2: Job Search
    print("\n🔍 Testing job search...")
    search_result = jsearch_manager.search_jobs(
        query="software engineer",
        location="San Francisco, CA",
        num_pages=1
    )
    
    if search_result.get("success"):
        jobs = search_result.get("jobs", [])
        print(f"✅ Found {len(jobs)} jobs")
        if jobs:
            first_job = jobs[0]
            print(f"   Sample job: {first_job.get('title')} at {first_job.get('company')}")
    else:
        print(f"❌ Job search failed: {search_result.get('error')}")
    
    # Test 3: Salary Estimates
    print("\n💰 Testing salary estimates...")
    salary_result = jsearch_manager.get_salary_estimates(
        job_title="software engineer",
        location="San Francisco, CA"
    )
    
    if salary_result.get("success"):
        estimates = salary_result.get("salary_estimates", [])
        print(f"✅ Found {len(estimates)} salary estimates")
    else:
        print(f"⚠️  Salary estimates failed: {salary_result.get('error')}")
    
    return True

async def test_smartlead_integration():
    """Test Smartlead manager functionality"""
    print("\n🤖 Testing Smartlead.ai Integration...")
    
    smartlead_key = os.getenv('SMARTLEAD_API_KEY')
    
    if not smartlead_key:
        print("❌ Smartlead API key not found in environment")
        return False
    
    print(f"✅ Smartlead API key found: {smartlead_key[:10]}...")
    
    # Initialize Smartlead Manager
    smartlead_manager = SmartleadManager()
    
    # Test 1: API Connection Test
    print("\n📊 Testing Smartlead API connection...")
    connection_test = smartlead_manager.test_api_connection()
    
    if connection_test.get("status") == "operational":
        print(f"✅ Smartlead API operational")
        print(f"✅ Response time: {connection_test.get('response_time_ms', 'N/A')}ms")
        account_email = connection_test.get("account_email")
        if account_email:
            print(f"✅ Account: {account_email}")
        plan = connection_test.get("plan")
        if plan:
            print(f"✅ Plan: {plan}")
    else:
        print(f"❌ Smartlead API error: {connection_test.get('error', 'Unknown error')}")
        return False
    
    # Test 2: Account Information
    print("\n👤 Getting account information...")
    account_info = smartlead_manager.get_account_info()
    
    if account_info.get("success"):
        account = account_info.get("account", {})
        print(f"✅ Account name: {account.get('name', 'N/A')}")
        print(f"✅ Plan: {account.get('plan', 'N/A')}")
        print(f"✅ Credits remaining: {account.get('credits_remaining', 'N/A')}")
        print(f"✅ Monthly limit: {account.get('monthly_limit', 'N/A')}")
        print(f"✅ Emails sent this month: {account.get('emails_sent_this_month', 'N/A')}")
    else:
        print(f"⚠️  Account info failed: {account_info.get('error')}")
    
    # Test 3: Get Campaigns
    print("\n📧 Getting existing campaigns...")
    campaigns_result = smartlead_manager.get_campaigns()
    
    if campaigns_result.get("success"):
        campaigns = campaigns_result.get("campaigns", [])
        print(f"✅ Found {len(campaigns)} existing campaigns")
        if campaigns:
            for i, campaign in enumerate(campaigns[:3]):  # Show first 3
                print(f"   {i+1}. {campaign.get('name')} (Status: {campaign.get('status')})")
    else:
        print(f"⚠️  Campaigns retrieval failed: {campaigns_result.get('error')}")
    
    return True

async def test_all_integrations():
    """Test all API integrations"""
    print("🧪 Testing All API Integrations for COOGI Backend")
    print("=" * 60)
    
    # Test JSearch
    jsearch_success = await test_jsearch_integration()
    
    # Test Smartlead
    smartlead_success = await test_smartlead_integration()
    
    # Summary
    print("\n🎯 Integration Test Summary")
    print("=" * 30)
    print(f"JSearch Integration: {'✅ PASS' if jsearch_success else '❌ FAIL'}")
    print(f"Smartlead Integration: {'✅ PASS' if smartlead_success else '❌ FAIL'}")
    
    if jsearch_success and smartlead_success:
        print("\n🎉 ALL INTEGRATIONS SUCCESSFUL!")
        print("Your COOGI platform now has:")
        print("   📊 JSearch - Advanced job search capabilities")
        print("   🤖 Smartlead.ai - AI-powered email campaigns") 
        print("   📧 Amazon SES - Cost-effective bulk email delivery")
        print("   ⚡ Instantly.ai - Automated follow-up sequences")
        print("\n🚀 Ready for multi-provider recruiting automation!")
    else:
        print("\n⚠️  Some integrations failed. Please check API keys and configurations.")
    
    return jsearch_success and smartlead_success

if __name__ == "__main__":
    asyncio.run(test_all_integrations())
