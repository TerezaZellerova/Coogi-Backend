"""
Amazon SES Email Manager for COOGI
Handles email sending, bounce/complaint tracking, and delivery optimization
"""
import boto3
import json
import logging
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class SESManager:
    """Amazon SES email delivery manager"""
    
    def __init__(self):
        """Initialize SES client"""
        try:
            self.ses_client = boto3.client(
                'ses',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            logger.info("✅ SES Manager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SES client: {e}")
            self.ses_client = None
    
    def verify_email_address(self, email: str) -> bool:
        """Verify an email address with SES"""
        try:
            if not self.ses_client:
                return False
                
            response = self.ses_client.verify_email_identity(EmailAddress=email)
            logger.info(f"✅ Email verification initiated for: {email}")
            return True
        except ClientError as e:
            logger.error(f"❌ Failed to verify email {email}: {e}")
            return False
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: str,
        from_email: str,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SES"""
        try:
            if not self.ses_client:
                return {"success": False, "error": "SES client not initialized"}
            
            destination = {
                'ToAddresses': to_emails
            }
            
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'},
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'}
                }
            }
            
            kwargs = {
                'Source': from_email,
                'Destination': destination,
                'Message': message
            }
            
            if reply_to:
                kwargs['ReplyToAddresses'] = [reply_to]
            
            response = self.ses_client.send_email(**kwargs)
            
            return {
                "success": True,
                "message_id": response['MessageId'],
                "timestamp": datetime.now().isoformat()
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"❌ SES send error [{error_code}]: {error_msg}")
            
            return {
                "success": False,
                "error": f"{error_code}: {error_msg}",
                "timestamp": datetime.now().isoformat()
            }
    
    def send_bulk_emails(
        self,
        emails_data: List[Dict[str, Any]],
        template_name: str,
        from_email: str
    ) -> Dict[str, Any]:
        """Send bulk personalized emails using SES templates"""
        try:
            if not self.ses_client:
                return {"success": False, "error": "SES client not initialized"}
            
            destinations = []
            for email_data in emails_data:
                destination = {
                    'Destination': {
                        'ToAddresses': [email_data['email']]
                    },
                    'ReplacementTemplateData': json.dumps(email_data.get('template_data', {}))
                }
                destinations.append(destination)
            
            response = self.ses_client.send_bulk_templated_email(
                Source=from_email,
                Template=template_name,
                DefaultTemplateData='{}',
                Destinations=destinations
            )
            
            return {
                "success": True,
                "message_ids": [status['MessageId'] for status in response['Status']],
                "sent_count": len([s for s in response['Status'] if s['Status'] == 'Success']),
                "failed_count": len([s for s in response['Status'] if s['Status'] != 'Success']),
                "timestamp": datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"❌ Bulk email send error: {e}")
            return {"success": False, "error": str(e)}
    
    def create_email_template(
        self,
        template_name: str,
        subject: str,
        html_template: str,
        text_template: str
    ) -> bool:
        """Create an email template in SES"""
        try:
            if not self.ses_client:
                return False
            
            template = {
                'TemplateName': template_name,
                'Subject': subject,
                'HtmlPart': html_template,
                'TextPart': text_template
            }
            
            self.ses_client.create_template(Template=template)
            logger.info(f"✅ Email template '{template_name}' created successfully")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Failed to create template '{template_name}': {e}")
            return False
    
    def get_send_statistics(self) -> Dict[str, Any]:
        """Get SES sending statistics"""
        try:
            if not self.ses_client:
                return {"error": "SES client not initialized"}
            
            response = self.ses_client.get_send_statistics()
            
            return {
                "success": True,
                "send_data_points": response['SendDataPoints'],
                "timestamp": datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"❌ Failed to get send statistics: {e}")
            return {"success": False, "error": str(e)}
    
    def check_reputation(self) -> Dict[str, Any]:
        """Check SES account reputation"""
        try:
            if not self.ses_client:
                return {"error": "SES client not initialized"}
            
            reputation = self.ses_client.get_reputation()
            quota = self.ses_client.get_send_quota()
            
            return {
                "success": True,
                "reputation": reputation,
                "daily_quota": quota['Max24HourSend'],
                "sent_last_24h": quota['SentLast24Hours'],
                "send_rate": quota['MaxSendRate'],
                "timestamp": datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"❌ Failed to check reputation: {e}")
            return {"success": False, "error": str(e)}

    def handle_bounce_complaint(self, notification: Dict[str, Any]) -> bool:
        """Handle SES bounce/complaint notifications"""
        try:
            notification_type = notification.get('notificationType')
            
            if notification_type == 'Bounce':
                bounce_type = notification['bounce']['bounceType']
                bounced_recipients = notification['bounce']['bouncedRecipients']
                
                for recipient in bounced_recipients:
                    email = recipient['emailAddress']
                    logger.warning(f"⚠️  Email bounced ({bounce_type}): {email}")
                    # Add to suppression list or mark in database
                    
            elif notification_type == 'Complaint':
                complained_recipients = notification['complaint']['complainedRecipients']
                
                for recipient in complained_recipients:
                    email = recipient['emailAddress']
                    logger.warning(f"⚠️  Spam complaint received: {email}")
                    # Add to suppression list immediately
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling bounce/complaint: {e}")
            return False
