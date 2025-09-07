#!/usr/bin/env python3
"""
Coogi Domain Email Integration with Amazon SES
Complete solution for @coogi.com email processing with GPT auto-tagging
"""
import boto3
import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .email_intelligence import EmailIntelligenceEngine, EmailIntelligencePipeline
from .aws_ses_service import AWSSESService

logger = logging.getLogger(__name__)

class CoogiDomainEmailProcessor:
    """
    Complete @coogi.com email processing system
    - Receives emails via SES + S3
    - Processes with GPT auto-tagging
    - Sends smart replies via SES
    """
    
    def __init__(self, intelligence_engine: EmailIntelligenceEngine):
        """Initialize with existing SES configuration"""
        self.intelligence_pipeline = EmailIntelligencePipeline(intelligence_engine)
        self.ses_service = AWSSESService()
        
        # AWS clients
        self.s3_client = boto3.client('s3')
        self.ses_client = boto3.client('ses')
        
        # Configuration from environment
        self.domain = "coogi.com"
        self.incoming_bucket = os.getenv("SES_S3_BUCKET", "coogi-incoming-emails")
        self.from_email = os.getenv("COOGI_FROM_EMAIL", "ai-assistant@coogi.com")
        
    def setup_ses_email_receiving(self) -> Dict[str, Any]:
        """
        Set up SES to receive emails for @coogi.com domain
        This configures SES to store incoming emails in S3
        """
        try:
            # Create S3 bucket for incoming emails if it doesn't exist
            try:
                self.s3_client.head_bucket(Bucket=self.incoming_bucket)
                logger.info(f"✅ S3 bucket exists: {self.incoming_bucket}")
            except:
                self.s3_client.create_bucket(Bucket=self.incoming_bucket)
                logger.info(f"✅ Created S3 bucket: {self.incoming_bucket}")
            
            # Set up SES receipt rule
            rule_set_name = "coogi-incoming-emails"
            rule_name = "coogi-domain-processor"
            
            # Create receipt rule to store emails in S3
            receipt_rule = {
                'Name': rule_name,
                'Enabled': True,
                'Recipients': [
                    f"support@{self.domain}",
                    f"sales@{self.domain}",
                    f"contact@{self.domain}",
                    f"hello@{self.domain}"
                ],
                'Actions': [
                    {
                        'S3Action': {
                            'BucketName': self.incoming_bucket,
                            'ObjectKeyPrefix': 'incoming/',
                        }
                    }
                ]
            }
            
            # Apply the rule
            try:
                self.ses_client.create_receipt_rule(
                    RuleSetName=rule_set_name,
                    Rule=receipt_rule
                )
                logger.info(f"✅ Created SES receipt rule: {rule_name}")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"✅ SES receipt rule already exists: {rule_name}")
                else:
                    raise
            
            return {
                "success": True,
                "message": "SES email receiving configured successfully",
                "domain": self.domain,
                "s3_bucket": self.incoming_bucket,
                "supported_emails": [
                    f"support@{self.domain}",
                    f"sales@{self.domain}", 
                    f"contact@{self.domain}",
                    f"hello@{self.domain}"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ SES setup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_incoming_emails_from_s3(self, hours: int = 24) -> Dict[str, Any]:
        """
        Process incoming emails stored in S3 by SES
        
        Args:
            hours: How many hours back to process emails
            
        Returns:
            Processing results with GPT analysis and smart replies
        """
        try:
            logger.info(f"🚀 Processing @{self.domain} emails from S3")
            
            # List recent email objects in S3
            since_time = datetime.now() - timedelta(hours=hours)
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.incoming_bucket,
                Prefix='incoming/'
            )
            
            if 'Contents' not in response:
                return {
                    "success": True,
                    "message": "No emails found in S3",
                    "emails_processed": 0
                }
            
            # Filter recent emails
            recent_emails = []
            for obj in response['Contents']:
                if obj['LastModified'].replace(tzinfo=None) > since_time:
                    recent_emails.append(obj)
            
            logger.info(f"📧 Found {len(recent_emails)} recent emails")
            
            # Process each email
            processed_emails = []
            auto_tagged = 0
            smart_replies_generated = 0
            auto_replies_sent = 0
            
            for email_obj in recent_emails:
                try:
                    # Download email from S3
                    email_content = self.s3_client.get_object(
                        Bucket=self.incoming_bucket,
                        Key=email_obj['Key']
                    )
                    
                    # Parse email
                    raw_email = email_content['Body'].read()
                    parsed_email = self._parse_s3_email(raw_email, email_obj['Key'])
                    
                    # Process with GPT intelligence
                    result = self.intelligence_pipeline.process_email(
                        email_data=parsed_email,
                        auto_reply=True  # Enable auto-replies for @coogi.com
                    )
                    
                    # Send smart reply if appropriate
                    reply_sent = False
                    if result["actions"]["auto_reply_eligible"]:
                        reply_sent = self._send_smart_reply_via_ses(
                            parsed_email, 
                            result["smart_reply"]
                        )
                    
                    processed_emails.append({
                        "email": parsed_email,
                        "analysis": result["analysis"],
                        "smart_reply": result["smart_reply"],
                        "actions": result["actions"],
                        "reply_sent": reply_sent
                    })
                    
                    # Update counters
                    if result["actions"]["auto_tagged"]:
                        auto_tagged += 1
                    if result["smart_reply"]["suggested_text"]:
                        smart_replies_generated += 1
                    if reply_sent:
                        auto_replies_sent += 1
                    
                    logger.info(f"✅ Processed: {parsed_email['subject'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing email {email_obj['Key']}: {e}")
                    continue
            
            return {
                "success": True,
                "domain": self.domain,
                "emails_found": len(recent_emails),
                "emails_processed": len(processed_emails),
                "auto_tagged": auto_tagged,
                "smart_replies_generated": smart_replies_generated,
                "auto_replies_sent": auto_replies_sent,
                "processed_emails": processed_emails,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ S3 email processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_s3_email(self, raw_email: bytes, s3_key: str) -> Dict[str, Any]:
        """Parse email stored in S3 by SES"""
        try:
            email_msg = email.message_from_bytes(raw_email)
            
            # Extract headers
            subject = email_msg.get('Subject', 'No Subject')
            from_email = email_msg.get('From', '')
            to_email = email_msg.get('To', '')
            date = email_msg.get('Date', '')
            message_id = email_msg.get('Message-ID', f"s3_{s3_key}")
            
            # Extract body
            body = ""
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8')
                            break
                        except:
                            continue
            else:
                try:
                    body = email_msg.get_payload(decode=True).decode('utf-8')
                except:
                    body = str(email_msg.get_payload())
            
            return {
                "id": s3_key,
                "message_id": message_id,
                "subject": subject,
                "from_email": from_email,
                "to_email": to_email,
                "body": body,
                "timestamp": date,
                "email_provider": "ses_s3",
                "s3_key": s3_key
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing S3 email: {e}")
            return {}
    
    def _send_smart_reply_via_ses(self, original_email: Dict[str, Any], smart_reply: Dict[str, Any]) -> bool:
        """Send smart reply using existing SES service"""
        try:
            # Extract original sender
            from_addr = original_email['from_email']
            if '<' in from_addr:
                # Extract email from "Name <email@domain.com>" format
                from_addr = from_addr.split('<')[1].split('>')[0]
            
            # Create reply subject
            original_subject = original_email['subject']
            if not original_subject.startswith('Re:'):
                reply_subject = f"Re: {original_subject}"
            else:
                reply_subject = original_subject
            
            # Send via SES
            result = self.ses_service.send_email(
                to_emails=[from_addr],
                subject=reply_subject,
                body_html=f"<p>{smart_reply['suggested_text']}</p>",
                body_text=smart_reply['suggested_text'],
                from_email=self.from_email
            )
            
            if result.get('success'):
                logger.info(f"📤 Smart reply sent via SES to {from_addr}")
                return True
            else:
                logger.error(f"❌ SES reply failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending SES reply: {e}")
            return False
    
    def get_coogi_email_stats(self) -> Dict[str, Any]:
        """Get statistics for @coogi.com email processing"""
        try:
            # Get SES sending stats
            ses_stats = self.ses_client.get_send_statistics()
            
            # Get S3 email count
            s3_response = self.s3_client.list_objects_v2(
                Bucket=self.incoming_bucket,
                Prefix='incoming/'
            )
            
            total_emails = len(s3_response.get('Contents', []))
            
            # Recent emails (last 24 hours)
            recent_count = 0
            if 'Contents' in s3_response:
                since_time = datetime.now() - timedelta(hours=24)
                for obj in s3_response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) > since_time:
                        recent_count += 1
            
            return {
                "success": True,
                "domain": self.domain,
                "total_emails_received": total_emails,
                "emails_last_24h": recent_count,
                "ses_sending_stats": ses_stats,
                "s3_bucket": self.incoming_bucket,
                "supported_addresses": [
                    f"support@{self.domain}",
                    f"sales@{self.domain}",
                    f"contact@{self.domain}",
                    f"hello@{self.domain}"
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Configuration for @coogi.com domain
COOGI_EMAIL_CONFIG = {
    "domain": "coogi.com",
    "supported_emails": [
        "support@coogi.com",    # Customer support
        "sales@coogi.com",      # Sales inquiries  
        "contact@coogi.com",    # General contact
        "hello@coogi.com",      # Friendly contact
        "info@coogi.com",       # Information requests
        "demo@coogi.com",       # Demo requests
        "partnership@coogi.com" # Business partnerships
    ],
    "s3_bucket": "coogi-incoming-emails",
    "from_email": "ai-assistant@coogi.com",
    "auto_reply_enabled": True,
    "gpt_processing": True
}

def setup_coogi_domain_email(intelligence_engine: EmailIntelligenceEngine) -> CoogiDomainEmailProcessor:
    """Set up complete @coogi.com email processing system"""
    processor = CoogiDomainEmailProcessor(intelligence_engine)
    
    # Configure SES receiving
    setup_result = processor.setup_ses_email_receiving()
    
    if setup_result["success"]:
        logger.info("✅ @coogi.com email system ready!")
        logger.info(f"📧 Supported emails: {setup_result['supported_emails']}")
    else:
        logger.error(f"❌ Setup failed: {setup_result['error']}")
    
    return processor
