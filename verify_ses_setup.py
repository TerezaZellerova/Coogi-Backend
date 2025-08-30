#!/usr/bin/env python3
"""
AWS SES Setup Verification Script
Run this after completing AWS SES configuration to verify everything works
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment_variables():
    """Check if all required AWS SES environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION',
        'AWS_SES_FROM_EMAIL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"  ✅ {var}: Set")
    
    if missing_vars:
        print(f"  ❌ Missing variables: {', '.join(missing_vars)}")
        return False
    
    print("  🎉 All environment variables are set!")
    return True

def test_ses_connection():
    """Test AWS SES connection and basic functionality"""
    print("\n🔗 Testing AWS SES connection...")
    
    try:
        # Import the SES service
        sys.path.append(os.path.dirname(__file__))
        from utils.aws_ses_service import ses_service
        
        if not ses_service.ses_client:
            print("  ❌ Failed to initialize SES client")
            return False
        
        print("  ✅ SES client initialized successfully")
        
        # Test domain verification status
        print("\n📧 Checking domain verification...")
        domain_status = ses_service.verify_domain_status("coogi.com")
        
        if domain_status['success']:
            status = domain_status['verification_status']
            print(f"  📋 Domain: {domain_status['domain']}")
            print(f"  📊 Status: {status}")
            
            if status == 'Success':
                print("  🎉 Domain is verified!")
            elif status == 'Pending':
                print("  ⏳ Domain verification pending (check DNS records)")
            else:
                print(f"  ⚠️  Domain verification status: {status}")
        else:
            print(f"  ❌ Error checking domain: {domain_status.get('error')}")
        
        # Test sending quota
        print("\n📊 Checking sending quota...")
        quota_info = ses_service.get_send_quota()
        
        if quota_info['success']:
            print(f"  📈 Max 24-hour send: {quota_info['max_24_hour_send']}")
            print(f"  ⚡ Max send rate: {quota_info['max_send_rate']} emails/second")
            print(f"  📤 Sent last 24 hours: {quota_info['sent_last_24_hours']}")
            
            remaining = quota_info['max_24_hour_send'] - quota_info['sent_last_24_hours']
            print(f"  🎯 Remaining quota: {remaining}")
            
            if quota_info['max_24_hour_send'] > 200:
                print("  🎉 Production access approved!")
            else:
                print("  ⚠️  Still in sandbox mode (200 email limit)")
        else:
            print(f"  ❌ Error checking quota: {quota_info.get('error')}")
            
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("  💡 Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"  ❌ Connection error: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 AWS SES Setup Verification for coogi.com")
    print("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    if not env_ok:
        print("\n❌ Environment variables not properly configured")
        print("💡 Add AWS credentials to your .env file or Render environment")
        return False
    
    # Test SES connection
    ses_ok = test_ses_connection()
    
    if not ses_ok:
        print("\n❌ AWS SES connection failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 AWS SES Setup Verification Complete!")
    print("\nNext steps:")
    print("1. 📧 Send a test email: POST /email/test")
    print("2. 🚀 Start sending campaigns: POST /email/campaign")
    print("3. 📊 Monitor usage: GET /email/quota")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
