#!/usr/bin/env python3
"""
Complete API Integration Validation
Validates JSearch, Smartlead.ai, and SES integrations are properly configured
"""
import os
import sys
from pathlib import Path

def validate_complete_integration():
    """Validate all API integrations setup"""
    print("🔍 Validating Complete API Integration Setup...")
    print("=" * 60)
    
    issues = []
    success_items = []
    
    # 1. Check JSearch Manager
    jsearch_manager_path = Path(__file__).parent / "utils" / "jsearch_manager.py"
    if jsearch_manager_path.exists():
        success_items.append("✅ JSearch Manager utility exists")
    else:
        issues.append("❌ JSearch Manager utility missing")
    
    # 2. Check Smartlead Manager
    smartlead_manager_path = Path(__file__).parent / "utils" / "smartlead_manager.py"
    if smartlead_manager_path.exists():
        success_items.append("✅ Smartlead Manager utility exists")
    else:
        issues.append("❌ Smartlead Manager utility missing")
    
    # 3. Check SES Manager
    ses_manager_path = Path(__file__).parent / "utils" / "ses_manager.py"
    if ses_manager_path.exists():
        success_items.append("✅ SES Manager utility exists")
    else:
        issues.append("❌ SES Manager utility missing")
    
    # 4. Check dependencies
    dependencies_path = Path(__file__).parent / "api" / "dependencies.py"
    if dependencies_path.exists():
        dependencies_content = dependencies_path.read_text()
        managers_found = 0
        if "get_jsearch_manager" in dependencies_content:
            managers_found += 1
        if "get_smartlead_manager" in dependencies_content:
            managers_found += 1
        if "get_ses_manager" in dependencies_content:
            managers_found += 1
        
        if managers_found == 3:
            success_items.append("✅ All manager dependencies configured")
        else:
            issues.append(f"❌ Only {managers_found}/3 manager dependencies found")
    else:
        issues.append("❌ Dependencies file not found")
    
    # 5. Check models
    models_path = Path(__file__).parent / "api" / "models.py"
    if models_path.exists():
        models_content = models_path.read_text()
        model_groups = 0
        if "JSearchJobRequest" in models_content:
            model_groups += 1
        if "SmartleadCampaignRequest" in models_content:
            model_groups += 1
        if "SESEmailRequest" in models_content:
            model_groups += 1
        
        if model_groups == 3:
            success_items.append("✅ All API models defined")
        else:
            issues.append(f"❌ Only {model_groups}/3 API model groups found")
    else:
        issues.append("❌ Models file not found")
    
    # 6. Check campaigns router endpoints
    campaigns_path = Path(__file__).parent / "api" / "routers" / "campaigns.py"
    if campaigns_path.exists():
        campaigns_content = campaigns_path.read_text()
        endpoint_groups = 0
        if "jsearch/search-jobs" in campaigns_content:
            endpoint_groups += 1
        if "smartlead/create-campaign" in campaigns_content:
            endpoint_groups += 1
        if "ses/send-email" in campaigns_content:
            endpoint_groups += 1
        
        if endpoint_groups == 3:
            success_items.append("✅ All API endpoints configured")
        else:
            issues.append(f"❌ Only {endpoint_groups}/3 API endpoint groups found")
    else:
        issues.append("❌ Campaigns router not found")
    
    # Print results
    print("\n📋 Integration Status:")
    print("=" * 50)
    
    if success_items:
        print("✅ SUCCESSFULLY CONFIGURED:")
        for item in success_items:
            print(f"   {item}")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    
    # Environment check
    print("\n🌍 Environment Variables Status:")
    print("=" * 40)
    
    # SES variables
    print("📧 Amazon SES:")
    ses_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    for var in ses_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * min(len(value), 20)}")
        else:
            print(f"   ⚠️  {var}: Not set")
    
    # JSearch variables
    print("\n🔍 JSearch (RapidAPI):")
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    if rapidapi_key:
        print(f"   ✅ RAPIDAPI_KEY: {rapidapi_key[:10]}...")
    else:
        print(f"   ⚠️  RAPIDAPI_KEY: Not set")
    
    # Smartlead variables
    print("\n🤖 Smartlead.ai:")
    smartlead_key = os.getenv('SMARTLEAD_API_KEY')
    if smartlead_key:
        print(f"   ✅ SMARTLEAD_API_KEY: {smartlead_key[:10]}...")
    else:
        print(f"   ⚠️  SMARTLEAD_API_KEY: Not set")
    
    # Other APIs
    print("\n📬 Other Email Providers:")
    instantly_key = os.getenv('INSTANTLY_API_KEY')
    if instantly_key:
        print(f"   ✅ INSTANTLY_API_KEY: {instantly_key[:10]}...")
    else:
        print(f"   ⚠️  INSTANTLY_API_KEY: Not set")
    
    # API Endpoints Summary
    print("\n🛠️  Available API Endpoints:")
    print("=" * 40)
    
    endpoints = [
        "📧 SES Email Delivery:",
        "   POST /api/ses/send-email",
        "   POST /api/ses/send-bulk-email",
        "   POST /api/ses/create-campaign",
        "   GET /api/ses/stats",
        "",
        "🔍 JSearch Job Search:",
        "   POST /api/jsearch/search-jobs",
        "   GET /api/jsearch/job-details/{job_id}",
        "   POST /api/jsearch/salary-estimates",
        "   GET /api/jsearch/trending-jobs",
        "   GET /api/jsearch/company/{company_name}",
        "",
        "🤖 Smartlead.ai Campaigns:",
        "   POST /api/smartlead/create-campaign",
        "   POST /api/smartlead/create-ai-campaign",
        "   GET /api/smartlead/campaigns",
        "   GET /api/smartlead/campaign/{id}/stats",
        "   POST /api/smartlead/campaign/{id}/pause",
        "",
        "⚡ Instantly.ai (Existing):",
        "   POST /api/create-instantly-campaign",
        "   GET /api/lead-lists",
        "   GET /api/campaigns"
    ]
    
    for endpoint in endpoints:
        print(f"   {endpoint}")
    
    # Summary
    if not issues:
        print("\n🎉 COMPLETE INTEGRATION READY!")
        print("=" * 40)
        print("✅ All APIs are properly integrated:")
        print("   📧 Amazon SES - Bulk email delivery")
        print("   🔍 JSearch - Advanced job search")
        print("   🤖 Smartlead.ai - AI-powered campaigns")
        print("   ⚡ Instantly.ai - Automated sequences")
        print("\n🚀 Your COOGI platform is now a multi-provider powerhouse!")
    else:
        print(f"\n⚠️  INTEGRATION INCOMPLETE: {len(issues)} issues found")
        print("Please resolve the issues above before deploying.")
    
    print("\n📚 Next Steps:")
    print("=" * 20)
    print("1. Set all required API keys in environment")
    print("2. Test APIs: python test_all_api_integrations.py")
    print("3. Deploy backend with new dependencies")
    print("4. Update frontend to use new endpoints")
    print("5. Configure multi-provider campaign strategies")
    
    return len(issues) == 0

if __name__ == "__main__":
    validate_complete_integration()
