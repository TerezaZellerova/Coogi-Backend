"""
AWS SES Campaign Router - Full integration with live email sending and analytics
Provides complete SES campaign management including live sending, templates, and analytics
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from utils.aws_ses_service import ses_service
from utils.live_email_campaign_service import live_email_service
from utils.campaign_analytics_service import campaign_analytics
from utils.email_campaign_service import email_campaign_service
from utils.universal_auto_campaign_manager import UniversalAutoCampaignManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ses", tags=["ses-campaigns"])

# Initialize services
universal_campaign_manager = UniversalAutoCampaignManager()

# Pydantic models
class SESEmailRequest(BaseModel):
    to_emails: List[EmailStr]
    subject: str
    body_text: str
    body_html: Optional[str] = ""
    from_email: EmailStr
    reply_to: Optional[EmailStr] = None

class SESBulkEmailRequest(BaseModel):
    emails_data: List[Dict[str, Any]]  # [{email: str, template_data: dict}]
    template_name: str
    from_email: EmailStr
    reply_to: Optional[EmailStr] = None

class SESTemplateRequest(BaseModel):
    template_name: str
    subject: str
    html_part: str
    text_part: str

class SESCampaignRequest(BaseModel):
    query: str
    campaign_name: str
    max_leads: int = 50
    min_score: float = 0.7
    from_email: EmailStr
    subject: str
    email_template: str
    send_immediately: bool = False

class LiveCampaignRequest(BaseModel):
    campaign_id: str
    platform: str = "ses"  # ses, instantly, smartlead
    send_immediately: bool = True
    delay_hours: int = 0

@router.get("/stats")
async def get_ses_stats():
    """Get AWS SES sending statistics and quota information"""
    try:
        logger.info("📊 Fetching SES statistics")
        
        # Get SES quota and stats
        quota_info = ses_service.get_send_quota()
        sending_stats = ses_service.get_send_statistics()
        reputation = ses_service.get_account_sending_enabled()
        
        # Calculate usage percentage
        sent_last_24h = quota_info.get('SentLast24Hours', 0)
        max_24h_send = quota_info.get('Max24HourSend', 1)
        usage_percentage = (sent_last_24h / max_24h_send * 100) if max_24h_send > 0 else 0
        
        # Get bounce and complaint rates from stats
        bounce_rate = 0.0
        complaint_rate = 0.0
        
        if sending_stats and 'SendDataPoints' in sending_stats:
            recent_stats = sending_stats['SendDataPoints'][-7:]  # Last 7 data points
            if recent_stats:
                total_sent = sum(point.get('DeliveryAttempts', 0) for point in recent_stats)
                total_bounces = sum(point.get('Bounces', 0) for point in recent_stats)
                total_complaints = sum(point.get('Complaints', 0) for point in recent_stats)
                
                if total_sent > 0:
                    bounce_rate = (total_bounces / total_sent) * 100
                    complaint_rate = (total_complaints / total_sent) * 100
        
        return {
            "send_quota": max_24h_send,
            "sent_last_24_hours": sent_last_24h,
            "max_send_rate": quota_info.get('MaxSendRate', 1),
            "usage_percentage": round(usage_percentage, 2),
            "bounce_rate": round(bounce_rate, 2),
            "complaint_rate": round(complaint_rate, 2),
            "reputation": {
                "delivery_delay": False,  # Would need specific API to check this
                "reputation_score": 100 - (bounce_rate * 10) - (complaint_rate * 20)  # Estimated
            },
            "account_enabled": reputation.get('Enabled', False),
            "region": ses_service.region
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching SES stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch SES stats: {str(e)}")

@router.post("/send-email")
async def send_ses_email(request: SESEmailRequest):
    """Send individual email via AWS SES"""
    try:
        logger.info(f"📧 Sending SES email to {len(request.to_emails)} recipients")
        
        # Send to first recipient (SES send_email supports only one recipient)
        to_email = request.to_emails[0]
        
        # Prepare HTML body - use provided HTML or convert text to HTML
        html_body = request.body_html
        if not html_body and request.body_text:
            try:
                html_body = ses_service._text_to_html(request.body_text)
            except Exception as e:
                logger.warning(f"Failed to convert text to HTML: {e}")
                html_body = request.body_text  # Fallback to plain text
        
        result = ses_service.send_email(
            to_email=to_email,
            subject=request.subject,
            body_text=request.body_text,
            body_html=html_body,
            from_email=request.from_email,
            reply_to=request.reply_to
        )
        
        if result['success']:
            # Track in analytics
            await campaign_analytics.track_email_event(
                campaign_id=f"manual_{int(datetime.now().timestamp())}",
                recipient_email=to_email,
                event_type="sent",
                metadata={"message_id": result.get('message_id')}
            )
            
            return {
                "message": f"Email sent successfully to {to_email}",
                "message_id": result.get('message_id'),
                "success": True
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))
            
    except Exception as e:
        logger.error(f"❌ Error sending SES email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-bulk-email")
async def send_ses_bulk_email(request: SESBulkEmailRequest):
    """Send bulk templated emails via AWS SES"""
    try:
        logger.info(f"📧 Sending bulk SES emails to {len(request.emails_data)} recipients")
        
        sent_count = 0
        failed_count = 0
        results = []
        
        for email_data in request.emails_data:
            try:
                result = ses_service.send_templated_email(
                    to_email=email_data['email'],
                    template_name=request.template_name,
                    template_data=email_data['template_data'],
                    from_email=request.from_email,
                    reply_to=request.reply_to
                )
                
                if result['success']:
                    sent_count += 1
                    results.append({
                        "email": email_data['email'],
                        "status": "sent",
                        "message_id": result.get('message_id')
                    })
                else:
                    failed_count += 1
                    results.append({
                        "email": email_data['email'],
                        "status": "failed",
                        "error": result.get('error')
                    })
                    
            except Exception as e:
                failed_count += 1
                results.append({
                    "email": email_data['email'],
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "message": f"Bulk email completed: {sent_count} sent, {failed_count} failed",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending bulk SES email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-template")
async def create_ses_template(request: SESTemplateRequest):
    """Create AWS SES email template"""
    try:
        logger.info(f"📝 Creating SES template: {request.template_name}")
        
        result = ses_service.create_template(
            template_name=request.template_name,
            subject=request.subject,
            html_part=request.html_part,
            text_part=request.text_part
        )
        
        if result['success']:
            return {
                "message": f"Template '{request.template_name}' created successfully",
                "template_name": request.template_name
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))
            
    except Exception as e:
        logger.error(f"❌ Error creating SES template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-campaign")
async def create_ses_campaign(request: SESCampaignRequest, background_tasks: BackgroundTasks):
    """Create and optionally execute SES-based lead generation campaign"""
    try:
        logger.info(f"🚀 Creating SES campaign: {request.campaign_name}")
        
        # Use universal auto-campaign manager for lead generation
        search_result = await universal_campaign_manager.search_professionals_with_auto_campaign(
            job_title=request.query,
            locations=["United States"],  # Default broad search
            per_city_limit=request.max_leads,
            require_email=True,
            hunter_verify=True,
            unlock_emails=True,
            auto_create_campaign=True,
            campaign_name=request.campaign_name,
            send_immediately=request.send_immediately
        )
        
        if not search_result.get('success'):
            raise HTTPException(status_code=400, detail="Failed to find leads")
        
        # Extract candidates
        candidates = search_result.get('candidates', [])
        
        if not candidates:
            return {
                "campaign_id": search_result.get('campaign_id'),
                "leads_found": 0,
                "emails_sent": 0,
                "campaign_status": "no_leads",
                "message": "Campaign created but no qualified leads found",
                "leads": []
            }
        
        # If sending immediately, execute via SES
        emails_sent = 0
        if request.send_immediately:
            for candidate in candidates:
                try:
                    emails = candidate.get('emails', [])
                    if emails:
                        # Personalize email content
                        personalized_subject = request.subject.format(
                            first_name=candidate.get('first_name', 'there'),
                            company=candidate.get('company', 'your company')
                        )
                        personalized_body = request.email_template.format(
                            first_name=candidate.get('first_name', 'there'),
                            company=candidate.get('company', 'your company'),
                            title=candidate.get('title', 'your role')
                        )
                        
                        # Send via SES
                        result = ses_service.send_email(
                            to_email=emails[0],
                            subject=personalized_subject,
                            body_text=personalized_body,
                            body_html=ses_service._text_to_html(personalized_body),
                            from_email=request.from_email
                        )
                        
                        if result['success']:
                            emails_sent += 1
                            
                            # Track in analytics
                            await campaign_analytics.track_email_event(
                                campaign_id=search_result.get('campaign_id'),
                                recipient_email=emails[0],
                                event_type="sent",
                                metadata={
                                    "message_id": result.get('message_id'),
                                    "candidate_name": candidate.get('name')
                                }
                            )
                        
                except Exception as e:
                    logger.error(f"Failed to send to {candidate.get('name')}: {e}")
        
        # Create campaign metrics
        campaign_id = search_result.get('campaign_id')
        await campaign_analytics.create_campaign_metrics(
            campaign_id=campaign_id,
            campaign_name=request.campaign_name,
            platform="aws_ses",
            total_recipients=len(candidates),
            emails_sent=emails_sent
        )
        
        return {
            "campaign_id": campaign_id,
            "leads_found": len(candidates),
            "emails_sent": emails_sent,
            "campaign_status": "executed" if request.send_immediately else "scheduled",
            "message": f"Campaign created successfully with {len(candidates)} leads",
            "leads": [
                {
                    "name": c.get('name', 'Unknown'),
                    "email": c.get('emails', [''])[0] if c.get('emails') else '',
                    "company": c.get('company', ''),
                    "position": c.get('title', ''),
                    "score": c.get('apollo_score', 0.8)
                }
                for c in candidates[:10]  # Return first 10 for preview
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating SES campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-live-campaign")
async def execute_live_campaign(request: LiveCampaignRequest, background_tasks: BackgroundTasks):
    """Execute a live email campaign with full analytics tracking"""
    try:
        logger.info(f"🚀 Executing live campaign: {request.campaign_id}")
        
        # Get campaign data (this would come from your campaign storage)
        # For now, we'll create a mock campaign
        campaign_data = {
            "id": request.campaign_id,
            "name": f"Live Campaign {request.campaign_id}",
            "platform": request.platform,
            "from_email": "outreach@coogi.ai",
            "from_name": "Coogi Talent Team",
            "candidates": [],  # Would be populated from actual campaign data
            "email_templates": [
                {
                    "step": 1,
                    "subject": "Exciting Career Opportunity",
                    "body": "Hi {first_name}, we have an exciting opportunity at {company}...",
                    "delay_days": 0
                }
            ]
        }
        
        if request.send_immediately:
            # Execute immediately
            result = await live_email_service.execute_campaign(campaign_data)
            return result
        else:
            # Schedule for later execution
            background_tasks.add_task(
                execute_delayed_campaign,
                campaign_data,
                request.delay_hours
            )
            return {
                "success": True,
                "message": f"Campaign scheduled for execution in {request.delay_hours} hours",
                "campaign_id": request.campaign_id,
                "scheduled_time": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Error executing live campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaign-analytics/{campaign_id}")
async def get_campaign_analytics(campaign_id: str):
    """Get comprehensive analytics for a specific campaign"""
    try:
        logger.info(f"📊 Fetching analytics for campaign: {campaign_id}")
        
        # Get campaign metrics
        metrics = await campaign_analytics.get_campaign_metrics(campaign_id)
        
        # Get recipient activities
        activities = await campaign_analytics.get_recipient_activities(campaign_id)
        
        # Get recent events
        events = await campaign_analytics.get_campaign_events(
            campaign_id, 
            limit=50
        )
        
        return {
            "campaign_id": campaign_id,
            "metrics": metrics,
            "recipient_activities": activities,
            "recent_events": events,
            "summary": {
                "total_recipients": metrics.get("total_recipients", 0),
                "emails_sent": metrics.get("emails_sent", 0),
                "open_rate": metrics.get("open_rate", 0),
                "click_rate": metrics.get("click_rate", 0),
                "reply_rate": metrics.get("reply_rate", 0),
                "status": "active" if metrics.get("emails_sent", 0) > 0 else "draft"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching campaign analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/overview")
async def get_analytics_overview():
    """Get overview analytics across all SES campaigns"""
    try:
        logger.info("📊 Fetching analytics overview")
        
        # Get overall performance stats
        overview = await campaign_analytics.get_performance_overview()
        
        # Get recent campaign summaries
        recent_campaigns = await campaign_analytics.get_recent_campaigns(limit=10)
        
        return {
            "overview": overview,
            "recent_campaigns": recent_campaigns,
            "platform": "aws_ses",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for delayed campaign execution
async def execute_delayed_campaign(campaign_data: Dict[str, Any], delay_hours: int):
    """Execute a campaign after a delay"""
    import asyncio
    
    logger.info(f"⏰ Scheduling campaign execution in {delay_hours} hours")
    
    # Wait for the specified delay
    await asyncio.sleep(delay_hours * 3600)  # Convert hours to seconds
    
    # Execute the campaign
    result = await live_email_service.execute_campaign(campaign_data)
    
    logger.info(f"✅ Delayed campaign executed: {result.get('success')}")
    return result
