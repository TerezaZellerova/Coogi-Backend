import boto3
import os
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AWSSESService:
    def __init__(self):
        """Initialize AWS SES client"""
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.from_email = os.getenv("AWS_SES_FROM_EMAIL", "noreply@coogi.com")
        
        # Initialize SES client
        try:
            self.ses_client = boto3.client(
                'ses',
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            logger.info(f"✅ AWS SES client initialized for region: {self.region}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AWS SES client: {e}")
            self.ses_client = None
    
    def send_email(self, 
                   to_email: str, 
                   subject: str, 
                   body_text: str, 
                   body_html: Optional[str] = None,
                   from_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Send email using AWS SES
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text email body
            body_html: HTML email body (optional)
            from_email: Sender email (optional, uses default)
            
        Returns:
            Dict with success status and message ID or error
        """
        if not self.ses_client:
            return {"success": False, "error": "SES client not initialized"}
            
        sender = from_email or self.from_email
        
        try:
            # Prepare email content
            email_content = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'}
                }
            }
            
            # Add HTML body if provided
            if body_html:
                email_content['Body']['Html'] = {'Data': body_html, 'Charset': 'UTF-8'}
            
            # Send email
            response = self.ses_client.send_email(
                Source=sender,
                Destination={'ToAddresses': [to_email]},
                Message=email_content
            )
            
            message_id = response['MessageId']
            logger.info(f"✅ Email sent successfully to {to_email}, MessageId: {message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "to_email": to_email,
                "from_email": sender
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"❌ AWS SES error [{error_code}]: {error_message}")
            
            return {
                "success": False,
                "error": f"SES Error: {error_message}",
                "error_code": error_code
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def send_bulk_emails(self, emails: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Send multiple emails
        
        Args:
            emails: List of email dicts with 'to_email', 'subject', 'body_text', 'body_html'
            
        Returns:
            Dict with overall success status and individual results
        """
        if not self.ses_client:
            return {"success": False, "error": "SES client not initialized"}
            
        results = []
        successful_sends = 0
        failed_sends = 0
        
        for email_data in emails:
            result = self.send_email(
                to_email=email_data['to_email'],
                subject=email_data['subject'],
                body_text=email_data['body_text'],
                body_html=email_data.get('body_html'),
                from_email=email_data.get('from_email')
            )
            
            results.append(result)
            
            if result['success']:
                successful_sends += 1
            else:
                failed_sends += 1
        
        logger.info(f"📊 Bulk email results: {successful_sends} successful, {failed_sends} failed")
        
        return {
            "success": failed_sends == 0,
            "total_emails": len(emails),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "results": results
        }
    
    def send_campaign_email(self, 
                           to_email: str, 
                           contact_name: str,
                           job_title: str, 
                           company: str, 
                           message: str,
                           campaign_name: str) -> Dict[str, Any]:
        """
        Send campaign outreach email
        
        Args:
            to_email: Contact email
            contact_name: Contact name
            job_title: Job title being applied for
            company: Company name
            message: Generated message content
            campaign_name: Campaign identifier
            
        Returns:
            Dict with send result
        """
        subject = f"Re: {job_title} Position at {company}"
        
        # Create HTML version of the email
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    {message.replace('\n', '<br>')}
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    
                    <p style="font-size: 12px; color: #666;">
                        This email was sent as part of campaign: <strong>{campaign_name}</strong><br>
                        Powered by Coogi - AI-Powered Lead Generation
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body_text=message,
            body_html=html_body
        )
    
    def verify_domain_status(self, domain: str = "coogi.com") -> Dict[str, Any]:
        """
        Check domain verification status
        
        Args:
            domain: Domain to check (default: coogi.com)
            
        Returns:
            Dict with verification status
        """
        if not self.ses_client:
            return {"success": False, "error": "SES client not initialized"}
            
        try:
            response = self.ses_client.get_identity_verification_attributes(
                Identities=[domain]
            )
            
            verification_attrs = response.get('VerificationAttributes', {})
            domain_attrs = verification_attrs.get(domain, {})
            
            verification_status = domain_attrs.get('VerificationStatus', 'NotStarted')
            verification_token = domain_attrs.get('VerificationToken', '')
            
            logger.info(f"📧 Domain {domain} verification status: {verification_status}")
            
            return {
                "success": True,
                "domain": domain,
                "verification_status": verification_status,
                "verification_token": verification_token,
                "is_verified": verification_status == 'Success'
            }
            
        except ClientError as e:
            logger.error(f"❌ Error checking domain verification: {e}")
            return {"success": False, "error": str(e)}
    
    def get_send_quota(self) -> Dict[str, Any]:
        """
        Get current sending quota and statistics
        
        Returns:
            Dict with quota information
        """
        if not self.ses_client:
            return {"success": False, "error": "SES client not initialized"}
            
        try:
            quota_response = self.ses_client.get_send_quota()
            stats_response = self.ses_client.get_send_statistics()
            
            return {
                "success": True,
                "max_24_hour_send": quota_response['Max24HourSend'],
                "max_send_rate": quota_response['MaxSendRate'],
                "sent_last_24_hours": quota_response['SentLast24Hours'],
                "send_statistics": stats_response.get('SendDataPoints', [])
            }
            
        except ClientError as e:
            logger.error(f"❌ Error getting send quota: {e}")
            return {"success": False, "error": str(e)}

# Initialize global instance
ses_service = AWSSESService()
