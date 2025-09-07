import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

from .aws_ses_service import ses_service
from .email_generator import EmailGenerator

logger = logging.getLogger(__name__)

class EmailCampaignService:
    def __init__(self):
        """Initialize email campaign service"""
        self.email_generator = EmailGenerator()
        self.ses_service = ses_service
        
    async def send_outreach_campaign(self, 
                                   contacts: List[Dict[str, Any]], 
                                   job_data: Dict[str, Any],
                                   campaign_name: str) -> Dict[str, Any]:
        """
        Send outreach emails to a list of contacts for a specific job
        
        Args:
            contacts: List of contact dictionaries with email, name, title
            job_data: Job information including title, company, url
            campaign_name: Name of the campaign
            
        Returns:
            Dict with campaign results
        """
        logger.info(f"🚀 Starting email campaign '{campaign_name}' for {len(contacts)} contacts")
        
        if not contacts:
            return {"success": False, "error": "No contacts provided"}
            
        job_title = job_data.get('title', 'Unknown Position')
        company = job_data.get('company', 'Unknown Company')
        job_url = job_data.get('url', '')
        
        campaign_results = []
        successful_sends = 0
        failed_sends = 0
        
        for contact in contacts:
            try:
                # Extract contact info
                contact_email = contact.get('email', '')
                contact_name = contact.get('name', 'Hiring Manager')
                contact_title = contact.get('title', 'Hiring Manager')
                
                if not contact_email:
                    logger.warning(f"⚠️ Skipping contact {contact_name} - no email provided")
                    failed_sends += 1
                    continue
                
                # Generate personalized message
                message_data = self.email_generator.generate_message(
                    job_title=job_title,
                    company=company,
                    contact_title=contact_title,
                    job_url=job_url,
                    tone="professional"
                )
                
                # Send email via AWS SES
                send_result = self.ses_service.send_campaign_email(
                    to_email=contact_email,
                    contact_name=contact_name,
                    job_title=job_title,
                    company=company,
                    message=message_data['message'],
                    campaign_name=campaign_name
                )
                
                # Track result
                campaign_result = {
                    "contact_email": contact_email,
                    "contact_name": contact_name,
                    "contact_title": contact_title,
                    "job_title": job_title,
                    "company": company,
                    "sent_at": datetime.utcnow().isoformat(),
                    "success": send_result['success'],
                    "message_id": send_result.get('message_id'),
                    "error": send_result.get('error')
                }
                
                campaign_results.append(campaign_result)
                
                if send_result['success']:
                    successful_sends += 1
                    logger.info(f"✅ Email sent to {contact_email} (MessageId: {send_result.get('message_id')})")
                else:
                    failed_sends += 1
                    logger.error(f"❌ Failed to send email to {contact_email}: {send_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing contact {contact.get('email', 'unknown')}: {e}")
                failed_sends += 1
                campaign_results.append({
                    "contact_email": contact.get('email', 'unknown'),
                    "success": False,
                    "error": str(e),
                    "sent_at": datetime.utcnow().isoformat()
                })
        
        # Campaign summary
        campaign_summary = {
            "success": failed_sends == 0,
            "campaign_name": campaign_name,
            "job_title": job_title,
            "company": company,
            "total_contacts": len(contacts),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "success_rate": (successful_sends / len(contacts)) * 100 if contacts else 0,
            "campaign_started_at": datetime.utcnow().isoformat(),
            "results": campaign_results
        }
        
        logger.info(f"""
📊 Campaign '{campaign_name}' completed:
   • Total contacts: {len(contacts)}
   • Successful sends: {successful_sends}
   • Failed sends: {failed_sends}
   • Success rate: {campaign_summary['success_rate']:.1f}%
        """)
        
        return campaign_summary
    
    async def send_test_email(self, test_email: str) -> Dict[str, Any]:
        """
        Send a test email to verify SES configuration
        
        Args:
            test_email: Email address to send test to
            
        Returns:
            Dict with test result
        """
        logger.info(f"🧪 Sending test email to {test_email}")
        
        test_subject = "Coogi Platform - AWS SES Test Email"
        test_message = """
Hello!

This is a test email from the Coogi AI-powered lead generation platform.

If you're receiving this email, it means:
✅ AWS SES is properly configured
✅ Domain verification is working
✅ Email sending is functional

Best regards,
The Coogi Team

---
Powered by Coogi - AI Lead Generation Platform
        """.strip()
        
        # Send test email
        result = self.ses_service.send_email(
            to_email=test_email,
            subject=test_subject,
            body_text=test_message,
            body_html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2563eb;">🚀 Coogi Platform - Test Email</h2>
                        <p>Hello!</p>
                        <p>This is a test email from the <strong>Coogi AI-powered lead generation platform</strong>.</p>
                        
                        <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>If you're receiving this email, it means:</strong></p>
                            <ul style="margin: 10px 0;">
                                <li>✅ AWS SES is properly configured</li>
                                <li>✅ Domain verification is working</li>
                                <li>✅ Email sending is functional</li>
                            </ul>
                        </div>
                        
                        <p>Best regards,<br><strong>The Coogi Team</strong></p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                        <p style="font-size: 12px; color: #666;">
                            Powered by <strong>Coogi</strong> - AI Lead Generation Platform
                        </p>
                    </div>
                </body>
            </html>
            """
        )
        
        if result['success']:
            logger.info(f"✅ Test email sent successfully to {test_email}")
        else:
            logger.error(f"❌ Test email failed: {result.get('error')}")
            
        return result
    
    def get_campaign_stats(self) -> Dict[str, Any]:
        """
        Get SES sending statistics and quota information
        
        Returns:
            Dict with SES stats
        """
        logger.info("📈 Fetching SES campaign statistics")
        
        # Get SES quota and stats
        quota_info = self.ses_service.get_send_quota()
        domain_status = self.ses_service.verify_domain_status("coogi.com")
        
        return {
            "ses_quota": quota_info,
            "domain_verification": domain_status,
            "from_email": self.ses_service.from_email,
            "aws_region": self.ses_service.region
        }

# Initialize global instance
email_campaign_service = EmailCampaignService()
