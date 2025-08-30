#!/usr/bin/env python3
"""
Test SES Integration
Tests Amazon SES functionality for COOGI backend
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from utils.ses_manager import SESManager
from dotenv import load_dotenv

async def test_ses_integration():
    """Test SES manager functionality"""
    print("🧪 Testing Amazon SES Integration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if SES credentials are available
    aws_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not aws_key or not aws_secret:
        print("❌ SES credentials not found in environment")
        print("   Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return False
    
    print(f"✅ SES credentials found for region: {aws_region}")
    
    # Initialize SES Manager
    ses_manager = SESManager()
    
    if not ses_manager.ses_client:
        print("❌ Failed to initialize SES client")
        return False
    
    print("✅ SES client initialized successfully")
    
    # Test 1: Check SES reputation and quota
    print("\n📊 Checking SES account status...")
    reputation = ses_manager.check_reputation()
    
    if reputation.get("success"):
        print(f"✅ Daily quota: {reputation.get('daily_quota', 'N/A')}")
        print(f"✅ Sent last 24h: {reputation.get('sent_last_24h', 'N/A')}")
        print(f"✅ Send rate: {reputation.get('send_rate', 'N/A')} emails/second")
    else:
        print(f"⚠️  Could not retrieve SES status: {reputation.get('error', 'Unknown error')}")
    
    # Test 2: Get sending statistics
    print("\n📈 Getting send statistics...")
    stats = ses_manager.get_send_statistics()
    
    if stats.get("success"):
        data_points = stats.get("send_data_points", [])
        if data_points:
            latest = data_points[-1]
            print(f"✅ Recent bounce rate: {latest.get('Bounces', 0)}")
            print(f"✅ Recent complaint rate: {latest.get('Complaints', 0)}")
            print(f"✅ Recent delivery attempts: {latest.get('DeliveryAttempts', 0)}")
        else:
            print("ℹ️  No recent sending statistics available")
    else:
        print(f"⚠️  Could not retrieve send statistics: {stats.get('error', 'Unknown error')}")
    
    # Test 3: Test email template creation (optional)
    print("\n📧 Testing email template creation...")
    template_success = ses_manager.create_email_template(
        template_name="coogi_test_template",
        subject="COOGI Test Email - {{company}}",
        html_template="""
        <html>
        <body>
            <h2>Hello {{name}},</h2>
            <p>This is a test email from COOGI recruiting platform.</p>
            <p>Company: {{company}}</p>
            <p>Position: {{position}}</p>
            <br>
            <p>Best regards,<br>COOGI Team</p>
        </body>
        </html>
        """,
        text_template="""
        Hello {{name}},
        
        This is a test email from COOGI recruiting platform.
        Company: {{company}}
        Position: {{position}}
        
        Best regards,
        COOGI Team
        """
    )
    
    if template_success:
        print("✅ Test email template created successfully")
    else:
        print("⚠️  Could not create test template (may already exist)")
    
    print("\n🎉 SES integration test completed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_ses_integration())
