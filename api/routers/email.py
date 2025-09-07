from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import logging
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.email_campaign_service import email_campaign_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])

# Pydantic models
class TestEmailRequest(BaseModel):
    test_email: EmailStr

class CampaignEmailRequest(BaseModel):
    campaign_name: str
    job_title: str
    company: str
    job_url: Optional[str] = ""
    contacts: List[Dict[str, Any]]  # List of contacts with email, name, title

class BulkEmailRequest(BaseModel):
    emails: List[Dict[str, str]]  # List with to_email, subject, body_text

@router.post("/test")
async def send_test_email(request: TestEmailRequest):
    """
    Send a test email to verify AWS SES configuration
    """
    try:
        logger.info(f"📧 Test email request for: {request.test_email}")
        
        result = await email_campaign_service.send_test_email(request.test_email)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Test email sent successfully to {request.test_email}",
                "message_id": result.get('message_id')
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to send test email: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Test email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaign")
async def send_campaign_emails(request: CampaignEmailRequest, background_tasks: BackgroundTasks):
    """
    Send outreach emails for a campaign
    """
    try:
        logger.info(f"🚀 Campaign email request: {request.campaign_name}")
        
        if not request.contacts:
            raise HTTPException(status_code=400, detail="No contacts provided")
        
        # Prepare job data
        job_data = {
            "title": request.job_title,
            "company": request.company,
            "url": request.job_url
        }
        
        # Send campaign emails
        result = await email_campaign_service.send_outreach_campaign(
            contacts=request.contacts,
            job_data=job_data,
            campaign_name=request.campaign_name
        )
        
        return {
            "success": result['success'],
            "campaign_name": result['campaign_name'],
            "total_contacts": result['total_contacts'],
            "successful_sends": result['successful_sends'],
            "failed_sends": result['failed_sends'],
            "success_rate": result['success_rate'],
            "campaign_started_at": result['campaign_started_at'],
            "message": f"Campaign completed: {result['successful_sends']}/{result['total_contacts']} emails sent successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Campaign email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_email_stats():
    """
    Get AWS SES statistics and domain verification status
    """
    try:
        logger.info("📊 Fetching email statistics")
        
        stats = email_campaign_service.get_campaign_stats()
        
        return {
            "success": True,
            "aws_region": stats['aws_region'],
            "from_email": stats['from_email'],
            "domain_verification": stats['domain_verification'],
            "ses_quota": stats['ses_quota']
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domain-status")
async def check_domain_verification():
    """
    Check domain verification status for coogi.com
    """
    try:
        logger.info("🔍 Checking domain verification status")
        
        result = email_campaign_service.ses_service.verify_domain_status("coogi.com")
        
        if result['success']:
            return {
                "success": True,
                "domain": result['domain'],
                "verification_status": result['verification_status'],
                "is_verified": result['is_verified'],
                "verification_token": result.get('verification_token', '')
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to check domain status: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Domain status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quota")
async def get_sending_quota():
    """
    Get current AWS SES sending quota and usage
    """
    try:
        logger.info("📈 Fetching SES sending quota")
        
        result = email_campaign_service.ses_service.get_send_quota()
        
        if result['success']:
            return {
                "success": True,
                "max_24_hour_send": result['max_24_hour_send'],
                "max_send_rate": result['max_send_rate'],
                "sent_last_24_hours": result['sent_last_24_hours'],
                "remaining_quota": result['max_24_hour_send'] - result['sent_last_24_hours'],
                "quota_usage_percent": (result['sent_last_24_hours'] / result['max_24_hour_send']) * 100
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get quota: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Quota error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
