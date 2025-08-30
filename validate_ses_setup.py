#!/usr/bin/env python3
"""
SES Integration Validation
Validates that SES integration is properly configured
"""
import os
import sys
from pathlib import Path

def validate_ses_setup():
    """Validate SES integration setup"""
    print("🔍 Validating Amazon SES Integration Setup...")
    
    issues = []
    success_items = []
    
    # 1. Check if SES manager exists
    ses_manager_path = Path(__file__).parent / "utils" / "ses_manager.py"
    if ses_manager_path.exists():
        success_items.append("✅ SES Manager utility exists")
    else:
        issues.append("❌ SES Manager utility missing")
    
    # 2. Check if requirements.txt includes boto3
    requirements_path = Path(__file__).parent / "requirements.txt"
    if requirements_path.exists():
        requirements_content = requirements_path.read_text()
        if "boto3" in requirements_content and "botocore" in requirements_content:
            success_items.append("✅ AWS dependencies in requirements.txt")
        else:
            issues.append("❌ boto3/botocore missing from requirements.txt")
    else:
        issues.append("❌ requirements.txt not found")
    
    # 3. Check if SES endpoints are in campaigns router
    campaigns_path = Path(__file__).parent / "api" / "routers" / "campaigns.py"
    if campaigns_path.exists():
        campaigns_content = campaigns_path.read_text()
        if "ses/send-email" in campaigns_content and "get_ses_manager" in campaigns_content:
            success_items.append("✅ SES endpoints added to campaigns router")
        else:
            issues.append("❌ SES endpoints missing from campaigns router")
    else:
        issues.append("❌ Campaigns router not found")
    
    # 4. Check if SES models are defined
    models_path = Path(__file__).parent / "api" / "models.py"
    if models_path.exists():
        models_content = models_path.read_text()
        if "SESEmailRequest" in models_content and "SESCampaignRequest" in models_content:
            success_items.append("✅ SES models defined")
        else:
            issues.append("❌ SES models missing from models.py")
    else:
        issues.append("❌ Models file not found")
    
    # 5. Check if SES dependency is added
    dependencies_path = Path(__file__).parent / "api" / "dependencies.py"
    if dependencies_path.exists():
        dependencies_content = dependencies_path.read_text()
        if "get_ses_manager" in dependencies_content:
            success_items.append("✅ SES dependency function added")
        else:
            issues.append("❌ SES dependency function missing")
    else:
        issues.append("❌ Dependencies file not found")
    
    # 6. Check environment template
    env_template_path = Path(__file__).parent / "render-env-vars.template"
    if env_template_path.exists():
        env_content = env_template_path.read_text()
        if "AWS_ACCESS_KEY_ID" in env_content and "AWS_SECRET_ACCESS_KEY" in env_content:
            success_items.append("✅ SES environment variables in template")
        else:
            issues.append("❌ SES environment variables missing from template")
    else:
        issues.append("❌ Environment template not found")
    
    # 7. Check if integration guide exists
    guide_path = Path(__file__).parent / "SES_INTEGRATION_GUIDE.md"
    if guide_path.exists():
        success_items.append("✅ SES integration guide available")
    else:
        issues.append("❌ SES integration guide missing")
    
    # Print results
    print("\n📋 Validation Results:")
    print("=" * 50)
    
    if success_items:
        print("✅ SUCCESSFULLY CONFIGURED:")
        for item in success_items:
            print(f"   {item}")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    
    # Environment check (non-blocking)
    print("\n🌍 Environment Variables Check:")
    env_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * len(value)}")
        else:
            print(f"   ⚠️  {var}: Not set (required for runtime)")
    
    # Summary
    if not issues:
        print("\n🎉 SES INTEGRATION READY!")
        print("   All components are properly configured.")
        print("   Set environment variables and deploy to activate SES features.")
    else:
        print(f"\n⚠️  INTEGRATION INCOMPLETE: {len(issues)} issues found")
        print("   Please resolve the issues above before deploying.")
    
    print("\n📚 Next Steps:")
    print("   1. Set AWS SES credentials in your environment")
    print("   2. Verify your domain/email in AWS SES Console")
    print("   3. Test with: python test_ses_integration.py")
    print("   4. Deploy backend with new dependencies")
    
    return len(issues) == 0

if __name__ == "__main__":
    validate_ses_setup()
