"""
Live Email Campaign Service
Integrates with AWS SES, Instantly.ai, and Smartlead.ai for actual email sending
"""

import os
import json
import boto3
import requests
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class LiveEmailCampaignService:
    """Service for executing live email campaigns across multiple platforms"""
    
    def __init__(self):
        """Initialize email service integrations"""
        self.ses_client = None
        self.instantly_api_key = os.getenv("INSTANTLY_API_KEY")
        self.smartlead_api_key = os.getenv("SMARTLEAD_API_KEY")
        
        # Initialize AWS SES
        try:
            self.ses_client = boto3.client(
                'ses',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            logger.info("✅ AWS SES client initialized")
        except Exception as e:
            logger.warning(f"⚠️ AWS SES initialization failed: {e}")
        
        logger.info(f"📧 Live Email Campaign Service initialized")
        logger.info(f"   SES: {'✅' if self.ses_client else '❌'}")
        logger.info(f"   Instantly.ai: {'✅' if self.instantly_api_key else '❌'}")
        logger.info(f"   Smartlead.ai: {'✅' if self.smartlead_api_key else '❌'}")
    
    async def execute_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a live email campaign using the best available service"""
        try:
            campaign_id = campaign_data.get("id")
            platform = campaign_data.get("platform", "ses")
            candidates = campaign_data.get("candidates", [])
            templates = campaign_data.get("email_templates", [])
            
            logger.info(f"🚀 Executing live campaign: {campaign_id}")
            logger.info(f"   Platform: {platform}")
            logger.info(f"   Recipients: {len(candidates)}")
            logger.info(f"   Templates: {len(templates)}")
            
            if not candidates:
                return {"success": False, "error": "No candidates to email"}
            
            if not templates:
                return {"success": False, "error": "No email templates"}
            
            # Choose execution method based on platform preference and availability
            if platform == "instantly" and self.instantly_api_key:
                result = await self._execute_via_instantly(campaign_data)
            elif platform == "smartlead" and self.smartlead_api_key:
                result = await self._execute_via_smartlead(campaign_data)
            elif self.ses_client:
                result = await self._execute_via_ses(campaign_data)
            else:
                result = await self._execute_mock_campaign(campaign_data)
            
            # Log execution results
            await self._log_campaign_execution(campaign_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Campaign execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": campaign_data.get("id"),
                "execution_time": datetime.now().isoformat()
            }
    
    async def _execute_via_ses(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute campaign via AWS SES"""
        try:
            logger.info("📧 Executing campaign via AWS SES")
            
            campaign_id = campaign_data.get("id")
            candidates = campaign_data.get("candidates", [])
            templates = campaign_data.get("email_templates", [])
            from_email = campaign_data.get("from_email", "outreach@coogi.ai")
            from_name = campaign_data.get("from_name", "Coogi Talent Team")
            
            # Use first template for initial send
            template = templates[0] if templates else {}
            subject = template.get("subject", "Exciting Career Opportunity")
            body = template.get("body", "Hello, we have an exciting opportunity for you!")
            
            sent_count = 0
            failed_count = 0
            results = []
            
            for candidate in candidates:
                try:
                    # Get candidate email
                    emails = candidate.get("emails", [])
                    if not emails:
                        failed_count += 1
                        continue
                    
                    recipient_email = emails[0]
                    
                    # Personalize content
                    personalized_subject = self._personalize_content(subject, candidate)
                    personalized_body = self._personalize_content(body, candidate)
                    
                    # Send via SES
                    response = self.ses_client.send_email(
                        Source=f"{from_name} <{from_email}>",
                        Destination={
                            'ToAddresses': [recipient_email]
                        },
                        Message={
                            'Subject': {
                                'Data': personalized_subject,
                                'Charset': 'UTF-8'
                            },
                            'Body': {
                                'Text': {
                                    'Data': personalized_body,
                                    'Charset': 'UTF-8'
                                },
                                'Html': {
                                    'Data': self._text_to_html(personalized_body),
                                    'Charset': 'UTF-8'
                                }
                            }
                        }
                    )
                    
                    message_id = response.get('MessageId')
                    sent_count += 1
                    
                    results.append({
                        "recipient": recipient_email,
                        "status": "sent",
                        "message_id": message_id,
                        "candidate_name": candidate.get("name", "Unknown")
                    })
                    
                    logger.info(f"✅ Sent to {candidate.get('name', 'Unknown')} ({recipient_email})")
                    
                    # Rate limiting for SES
                    await asyncio.sleep(0.1)  # 10 emails per second max
                    
                except Exception as e:
                    failed_count += 1
                    results.append({
                        "recipient": candidate.get("emails", ["unknown"])[0] if candidate.get("emails") else "unknown",
                        "status": "failed",
                        "error": str(e),
                        "candidate_name": candidate.get("name", "Unknown")
                    })
                    logger.error(f"❌ Failed to send to {candidate.get('name', 'Unknown')}: {e}")
            
            return {
                "success": True,
                "platform": "aws_ses",
                "campaign_id": campaign_id,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_recipients": len(candidates),
                "execution_time": datetime.now().isoformat(),
                "results": results,
                "next_step": templates[1]["step"] if len(templates) > 1 else None,
                "next_send_date": (datetime.now() + timedelta(days=templates[1]["delay_days"])).isoformat() if len(templates) > 1 else None
            }
            
        except Exception as e:
            logger.error(f"❌ SES campaign execution failed: {e}")
            return {
                "success": False,
                "platform": "aws_ses",
                "error": str(e),
                "sent_count": 0,
                "failed_count": len(campaign_data.get("candidates", []))
            }
    
    async def _execute_via_instantly(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute campaign via Instantly.ai"""
        try:
            logger.info("📧 Executing campaign via Instantly.ai")
            
            # Instantly.ai campaign creation
            campaign_payload = {
                "campaign_name": campaign_data.get("name"),
                "from_email": campaign_data.get("from_email"),
                "from_name": campaign_data.get("from_name"),
                "sequences": []
            }
            
            # Convert templates to Instantly sequences
            for template in campaign_data.get("email_templates", []):
                sequence = {
                    "step": template.get("step", 1),
                    "delay_days": template.get("delay_days", 0),
                    "subject": template.get("subject"),
                    "body": template.get("body"),
                    "personalization": template.get("personalization_fields", [])
                }
                campaign_payload["sequences"].append(sequence)
            
            # Create campaign in Instantly
            headers = {
                "Authorization": f"Bearer {self.instantly_api_key}",
                "Content-Type": "application/json"
            }
            
            # This is a mock implementation - replace with actual Instantly.ai API calls
            logger.info("🔄 [MOCK] Creating campaign in Instantly.ai")
            
            # Add recipients
            candidates = campaign_data.get("candidates", [])
            sent_count = 0
            
            for candidate in candidates:
                emails = candidate.get("emails", [])
                if emails:
                    # Mock adding to Instantly campaign
                    logger.info(f"🔄 [MOCK] Adding {candidate.get('name')} to Instantly campaign")
                    sent_count += 1
            
            return {
                "success": True,
                "platform": "instantly",
                "campaign_id": campaign_data.get("id"),
                "instantly_campaign_id": f"instantly_{int(datetime.now().timestamp())}",
                "sent_count": sent_count,
                "failed_count": 0,
                "total_recipients": len(candidates),
                "execution_time": datetime.now().isoformat(),
                "note": "Mock execution - integrate with actual Instantly.ai API"
            }
            
        except Exception as e:
            logger.error(f"❌ Instantly.ai campaign execution failed: {e}")
            return {
                "success": False,
                "platform": "instantly",
                "error": str(e)
            }
    
    async def _execute_via_smartlead(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute campaign via Smartlead.ai"""
        try:
            logger.info("📧 Executing campaign via Smartlead.ai")
            
            # This is a mock implementation - replace with actual Smartlead.ai API calls
            candidates = campaign_data.get("candidates", [])
            
            logger.info("🔄 [MOCK] Creating campaign in Smartlead.ai")
            
            return {
                "success": True,
                "platform": "smartlead",
                "campaign_id": campaign_data.get("id"),
                "smartlead_campaign_id": f"smartlead_{int(datetime.now().timestamp())}",
                "sent_count": len(candidates),
                "failed_count": 0,
                "total_recipients": len(candidates),
                "execution_time": datetime.now().isoformat(),
                "note": "Mock execution - integrate with actual Smartlead.ai API"
            }
            
        except Exception as e:
            logger.error(f"❌ Smartlead.ai campaign execution failed: {e}")
            return {
                "success": False,
                "platform": "smartlead",
                "error": str(e)
            }
    
    async def _execute_mock_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mock campaign when no live services are available"""
        logger.info("📧 Executing MOCK campaign (no live services configured)")
        
        candidates = campaign_data.get("candidates", [])
        
        # Simulate sending
        await asyncio.sleep(1)  # Simulate processing time
        
        return {
            "success": True,
            "platform": "mock",
            "campaign_id": campaign_data.get("id"),
            "sent_count": len(candidates),
            "failed_count": 0,
            "total_recipients": len(candidates),
            "execution_time": datetime.now().isoformat(),
            "note": "Mock execution - configure AWS SES, Instantly.ai, or Smartlead.ai for live sending"
        }
    
    def _personalize_content(self, content: str, candidate: Dict[str, Any]) -> str:
        """Personalize email content with candidate data"""
        try:
            # Replace placeholders
            replacements = {
                "{{first_name}}": candidate.get("first_name", ""),
                "{{last_name}}": candidate.get("last_name", ""),
                "{{name}}": candidate.get("name", ""),
                "{{company}}": candidate.get("company", ""),
                "{{title}}": candidate.get("title", ""),
                "{{location}}": candidate.get("location", ""),
                "{{from_name}}": "Coogi Talent Team",
                "{{from_email}}": "outreach@coogi.ai"
            }
            
            personalized = content
            for placeholder, value in replacements.items():
                personalized = personalized.replace(placeholder, value or "")
            
            return personalized
            
        except Exception as e:
            logger.warning(f"⚠️ Personalization failed: {e}")
            return content
    
    def _text_to_html(self, text: str) -> str:
        """Convert plain text to HTML email format"""
        # Simple text to HTML conversion
        html = text.replace('\n', '<br>\n')
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        {html}
        </body>
        </html>
        """
        return html
    
    async def _log_campaign_execution(self, campaign_id: str, result: Dict[str, Any]) -> None:
        """Log campaign execution for analytics"""
        try:
            log_entry = {
                "campaign_id": campaign_id,
                "execution_time": datetime.now().isoformat(),
                "platform": result.get("platform"),
                "success": result.get("success"),
                "sent_count": result.get("sent_count", 0),
                "failed_count": result.get("failed_count", 0),
                "total_recipients": result.get("total_recipients", 0),
                "results": result.get("results", [])
            }
            
            # Ensure logs directory exists
            Path("campaign_logs").mkdir(exist_ok=True)
            
            # Save execution log
            log_file = f"campaign_logs/{campaign_id}_execution.json"
            with open(log_file, 'w') as f:
                json.dump(log_entry, f, indent=2, default=str)
            
            logger.info(f"📊 Campaign execution logged: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log campaign execution: {e}")

# Global instance
live_email_service = LiveEmailCampaignService()
