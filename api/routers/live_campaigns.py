"""
Live Campaign Management Router
Advanced campaign orchestration with multi-platform support, analytics, and automation
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional, Literal
import logging
from datetime import datetime, timedelta
import uuid

from utils.live_email_campaign_service import live_email_service
from utils.campaign_analytics_service import campaign_analytics
from utils.universal_auto_campaign_manager import UniversalAutoCampaignManager
from utils.professional_candidate_searcher import ProfessionalCandidateSearcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live-campaigns", tags=["live-campaigns"])

# Initialize services
universal_campaign_manager = UniversalAutoCampaignManager()
professional_searcher = ProfessionalCandidateSearcher()

# Pydantic models
class EmailStep(BaseModel):
    step_number: int
    subject: str
    body: str
    delay_days: int = 0
    personalization_fields: List[str] = ["first_name", "company", "title"]

class CreateLiveCampaignRequest(BaseModel):
    name: str
    platform: Literal["ses", "instantly", "smartlead"] = "ses"
    job_title: str
    locations: List[str]
    from_email: EmailStr
    from_name: str = "Coogi Talent Team"
    email_sequence: List[EmailStep]
    max_candidates: int = 50
    require_email: bool = True
    require_phone: bool = False
    hunter_verify: bool = True
    send_immediately: bool = False
    schedule_time: Optional[str] = None  # ISO datetime string
    target_companies: Optional[List[str]] = None
    company_size: Optional[str] = None
    min_score: float = 0.7

class ExecuteCampaignRequest(BaseModel):
    campaign_id: str
    platform: Optional[Literal["ses", "instantly", "smartlead"]] = None
    send_immediately: bool = True
    delay_hours: int = 0

class UpdateCampaignRequest(BaseModel):
    campaign_id: str
    status: Optional[Literal["draft", "active", "paused", "completed"]] = None
    email_sequence: Optional[List[EmailStep]] = None
    schedule_time: Optional[str] = None

class CampaignAnalyticsRequest(BaseModel):
    campaign_id: str
    date_range: Optional[int] = 30  # Days
    include_details: bool = True

@router.post("/create")
async def create_live_campaign(request: CreateLiveCampaignRequest, background_tasks: BackgroundTasks):
    """Create a comprehensive live email campaign with candidate search and scheduling"""
    try:
        logger.info(f"🚀 Creating live campaign: {request.name}")
        
        # Generate unique campaign ID
        campaign_id = f"live_{uuid.uuid4().hex[:8]}"
        
        # Step 1: Search for candidates
        logger.info(f"🔍 Searching for {request.job_title} candidates in {request.locations}")
        
        search_result = await universal_campaign_manager.search_professionals_with_auto_campaign(
            job_title=request.job_title,
            locations=request.locations,
            per_city_limit=request.max_candidates // len(request.locations) if request.locations else request.max_candidates,
            require_email=request.require_email,
            require_phone=request.require_phone,
            hunter_verify=request.hunter_verify,
            unlock_emails=True,
            auto_create_campaign=False,  # We'll handle campaign creation manually
            company_size=request.company_size
        )
        
        if not search_result.get('success'):
            raise HTTPException(status_code=400, detail="Failed to find qualified candidates")
        
        candidates = search_result.get('candidates', [])
        
        if not candidates:
            raise HTTPException(status_code=404, detail="No qualified candidates found")
        
        # Filter by minimum score
        qualified_candidates = [
            c for c in candidates 
            if c.get('apollo_score', 0) >= request.min_score
        ]
        
        if not qualified_candidates:
            raise HTTPException(status_code=404, detail=f"No candidates meet minimum score requirement of {request.min_score}")
        
        # Step 2: Create campaign data structure
        campaign_data = {
            "id": campaign_id,
            "name": request.name,
            "platform": request.platform,
            "from_email": request.from_email,
            "from_name": request.from_name,
            "job_title": request.job_title,
            "locations": request.locations,
            "candidates": qualified_candidates[:request.max_candidates],
            "email_templates": [
                {
                    "step": step.step_number,
                    "subject": step.subject,
                    "body": step.body,
                    "delay_days": step.delay_days,
                    "personalization_fields": step.personalization_fields
                }
                for step in request.email_sequence
            ],
            "created_at": datetime.now().isoformat(),
            "status": "draft",
            "schedule_time": request.schedule_time,
            "target_companies": request.target_companies,
            "company_size": request.company_size,
            "min_score": request.min_score
        }
        
        # Step 3: Create campaign metrics in analytics
        await campaign_analytics.create_campaign_metrics(
            campaign_id=campaign_id,
            campaign_name=request.name,
            platform=request.platform,
            total_recipients=len(qualified_candidates),
            campaign_type="live_outreach",
            target_audience=request.job_title
        )
        
        # Step 4: Store candidate data in analytics
        for candidate in qualified_candidates:
            emails = candidate.get('emails', [])
            if emails:
                await campaign_analytics.add_recipient_activity(
                    campaign_id=campaign_id,
                    recipient_email=emails[0],
                    recipient_name=candidate.get('name', 'Unknown'),
                    company=candidate.get('company', 'Unknown'),
                    title=candidate.get('title', 'Unknown'),
                    status="added"
                )
        
        # Step 5: Execute or schedule campaign
        if request.send_immediately:
            background_tasks.add_task(execute_live_campaign_task, campaign_data)
            execution_message = "Campaign created and executing immediately"
        elif request.schedule_time:
            schedule_dt = datetime.fromisoformat(request.schedule_time.replace('Z', '+00:00'))
            delay_seconds = (schedule_dt - datetime.now()).total_seconds()
            if delay_seconds > 0:
                background_tasks.add_task(execute_scheduled_campaign_task, campaign_data, delay_seconds)
                execution_message = f"Campaign scheduled for {request.schedule_time}"
            else:
                background_tasks.add_task(execute_live_campaign_task, campaign_data)
                execution_message = "Scheduled time has passed, executing immediately"
        else:
            execution_message = "Campaign created as draft, ready for manual execution"
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": execution_message,
            "candidates_found": len(candidates),
            "qualified_candidates": len(qualified_candidates),
            "locations_searched": request.locations,
            "platform": request.platform,
            "email_sequence_steps": len(request.email_sequence),
            "created_at": campaign_data["created_at"],
            "candidate_preview": [
                {
                    "name": c.get('name', 'Unknown'),
                    "email": c.get('emails', [''])[0] if c.get('emails') else '',
                    "company": c.get('company', ''),
                    "title": c.get('title', ''),
                    "location": c.get('location', ''),
                    "score": c.get('apollo_score', 0)
                }
                for c in qualified_candidates[:5]  # Preview first 5
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating live campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_campaign(request: ExecuteCampaignRequest, background_tasks: BackgroundTasks):
    """Execute a previously created campaign"""
    try:
        logger.info(f"▶️ Executing campaign: {request.campaign_id}")
        
        # Get campaign data (in a real system, this would be stored in database)
        # For now, we'll return an error asking to use create endpoint
        raise HTTPException(
            status_code=404, 
            detail="Campaign not found. Use /create endpoint to create and execute campaigns."
        )
        
    except Exception as e:
        logger.error(f"❌ Error executing campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{campaign_id}")
async def get_campaign_status(campaign_id: str):
    """Get current status and real-time metrics for a campaign"""
    try:
        logger.info(f"📊 Getting status for campaign: {campaign_id}")
        
        # Get campaign metrics
        metrics = await campaign_analytics.get_campaign_metrics(campaign_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get recent recipient activities
        activities = await campaign_analytics.get_recipient_activities(campaign_id, limit=10)
        
        # Get recent events
        events = await campaign_analytics.get_campaign_events(campaign_id, limit=20)
        
        # Calculate performance metrics
        total_recipients = metrics.get("total_recipients", 0)
        emails_sent = metrics.get("emails_sent", 0)
        emails_opened = metrics.get("emails_opened", 0)
        emails_clicked = metrics.get("emails_clicked", 0)
        emails_replied = metrics.get("emails_replied", 0)
        
        # Calculate rates
        open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
        click_rate = (emails_clicked / emails_sent * 100) if emails_sent > 0 else 0
        reply_rate = (emails_replied / emails_sent * 100) if emails_sent > 0 else 0
        
        # Determine status
        if emails_sent == 0:
            status = "draft"
        elif emails_sent < total_recipients:
            status = "sending"
        elif events and any(e.get("event_type") == "replied" for e in events[-5:]):
            status = "active_replies"
        else:
            status = "sent"
        
        return {
            "campaign_id": campaign_id,
            "status": status,
            "created_at": metrics.get("created_at"),
            "executed_at": metrics.get("executed_at"),
            "performance": {
                "total_recipients": total_recipients,
                "emails_sent": emails_sent,
                "emails_delivered": metrics.get("emails_delivered", 0),
                "emails_opened": emails_opened,
                "emails_clicked": emails_clicked,
                "emails_replied": emails_replied,
                "emails_bounced": metrics.get("emails_bounced", 0),
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "reply_rate": round(reply_rate, 2),
                "bounce_rate": metrics.get("bounce_rate", 0)
            },
            "recent_activities": activities,
            "recent_events": events,
            "platform": metrics.get("platform", "unknown"),
            "campaign_type": metrics.get("campaign_type", "outreach")
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting campaign status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{campaign_id}")
async def get_detailed_analytics(campaign_id: str, date_range: int = 30):
    """Get comprehensive analytics and insights for a campaign"""
    try:
        logger.info(f"📈 Getting detailed analytics for campaign: {campaign_id}")
        
        # Get comprehensive metrics
        metrics = await campaign_analytics.get_campaign_metrics(campaign_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get all recipient activities
        activities = await campaign_analytics.get_recipient_activities(campaign_id)
        
        # Get time-series data for the last N days
        events = await campaign_analytics.get_campaign_events(
            campaign_id, 
            days_back=date_range
        )
        
        # Analyze engagement patterns
        engagement_analysis = analyze_engagement_patterns(events, activities)
        
        # Company and title analysis
        company_analysis = analyze_by_company(activities)
        title_analysis = analyze_by_title(activities)
        
        # Time-based analysis
        time_analysis = analyze_by_time(events)
        
        return {
            "campaign_id": campaign_id,
            "date_range_days": date_range,
            "overall_metrics": metrics,
            "engagement_analysis": engagement_analysis,
            "company_analysis": company_analysis,
            "title_analysis": title_analysis,
            "time_analysis": time_analysis,
            "recipient_details": activities,
            "insights": generate_campaign_insights(metrics, engagement_analysis, company_analysis),
            "recommendations": generate_optimization_recommendations(metrics, engagement_analysis),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting detailed analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview")
async def get_campaigns_overview():
    """Get overview of all live campaigns"""
    try:
        logger.info("📊 Getting campaigns overview")
        
        # Get performance overview
        overview = await campaign_analytics.get_performance_overview()
        
        # Get recent campaigns
        recent_campaigns = await campaign_analytics.get_recent_campaigns(limit=20)
        
        # Calculate aggregate metrics
        total_campaigns = len(recent_campaigns)
        total_recipients = sum(c.get("total_recipients", 0) for c in recent_campaigns)
        total_sent = sum(c.get("emails_sent", 0) for c in recent_campaigns)
        total_opened = sum(c.get("emails_opened", 0) for c in recent_campaigns)
        total_replied = sum(c.get("emails_replied", 0) for c in recent_campaigns)
        
        # Calculate average rates
        avg_open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        avg_reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
        
        # Platform distribution
        platform_stats = {}
        for campaign in recent_campaigns:
            platform = campaign.get("platform", "unknown")
            if platform not in platform_stats:
                platform_stats[platform] = {"count": 0, "sent": 0, "opened": 0, "replied": 0}
            platform_stats[platform]["count"] += 1
            platform_stats[platform]["sent"] += campaign.get("emails_sent", 0)
            platform_stats[platform]["opened"] += campaign.get("emails_opened", 0)
            platform_stats[platform]["replied"] += campaign.get("emails_replied", 0)
        
        return {
            "overview": {
                "total_campaigns": total_campaigns,
                "total_recipients": total_recipients,
                "total_emails_sent": total_sent,
                "total_emails_opened": total_opened,
                "total_emails_replied": total_replied,
                "average_open_rate": round(avg_open_rate, 2),
                "average_reply_rate": round(avg_reply_rate, 2)
            },
            "platform_statistics": platform_stats,
            "recent_campaigns": recent_campaigns,
            "performance_trends": overview,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting campaigns overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def execute_live_campaign_task(campaign_data: Dict[str, Any]):
    """Background task to execute a live campaign"""
    try:
        logger.info(f"🚀 Executing live campaign: {campaign_data['id']}")
        
        # Update status to executing
        await campaign_analytics.update_campaign_status(
            campaign_data['id'], 
            "executing", 
            executed_at=datetime.now().isoformat()
        )
        
        # Execute the campaign
        result = await live_email_service.execute_campaign(campaign_data)
        
        # Update final status
        final_status = "completed" if result.get("success") else "failed"
        await campaign_analytics.update_campaign_status(campaign_data['id'], final_status)
        
        logger.info(f"✅ Campaign execution completed: {campaign_data['id']} - {final_status}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Campaign execution failed: {e}")
        await campaign_analytics.update_campaign_status(campaign_data['id'], "failed")

async def execute_scheduled_campaign_task(campaign_data: Dict[str, Any], delay_seconds: float):
    """Background task to execute a scheduled campaign"""
    import asyncio
    
    try:
        logger.info(f"⏰ Campaign scheduled for {delay_seconds} seconds: {campaign_data['id']}")
        
        # Wait for the scheduled time
        await asyncio.sleep(delay_seconds)
        
        # Execute the campaign
        await execute_live_campaign_task(campaign_data)
        
    except Exception as e:
        logger.error(f"❌ Scheduled campaign execution failed: {e}")

# Analytics helper functions
def analyze_engagement_patterns(events: List[Dict], activities: List[Dict]) -> Dict[str, Any]:
    """Analyze engagement patterns from campaign events"""
    engagement_data = {
        "total_events": len(events),
        "event_types": {},
        "engagement_timeline": {},
        "high_engagement_recipients": []
    }
    
    # Count event types
    for event in events:
        event_type = event.get("event_type", "unknown")
        engagement_data["event_types"][event_type] = engagement_data["event_types"].get(event_type, 0) + 1
    
    # Find highly engaged recipients
    recipient_engagement = {}
    for activity in activities:
        email = activity.get("recipient_email", "")
        engagement_score = 0
        if activity.get("email_opened_at"):
            engagement_score += 1
        if activity.get("email_clicked_at"):
            engagement_score += 2
        if activity.get("email_replied_at"):
            engagement_score += 3
        
        if engagement_score > 0:
            recipient_engagement[email] = {
                "score": engagement_score,
                "name": activity.get("recipient_name", ""),
                "company": activity.get("company", "")
            }
    
    # Sort by engagement score
    engagement_data["high_engagement_recipients"] = sorted(
        recipient_engagement.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:10]
    
    return engagement_data

def analyze_by_company(activities: List[Dict]) -> Dict[str, Any]:
    """Analyze performance by company"""
    company_stats = {}
    
    for activity in activities:
        company = activity.get("company", "Unknown")
        if company not in company_stats:
            company_stats[company] = {
                "total_recipients": 0,
                "opened": 0,
                "clicked": 0,
                "replied": 0
            }
        
        company_stats[company]["total_recipients"] += 1
        if activity.get("email_opened_at"):
            company_stats[company]["opened"] += 1
        if activity.get("email_clicked_at"):
            company_stats[company]["clicked"] += 1
        if activity.get("email_replied_at"):
            company_stats[company]["replied"] += 1
    
    # Calculate rates for each company
    for company, stats in company_stats.items():
        total = stats["total_recipients"]
        if total > 0:
            stats["open_rate"] = round(stats["opened"] / total * 100, 2)
            stats["click_rate"] = round(stats["clicked"] / total * 100, 2)
            stats["reply_rate"] = round(stats["replied"] / total * 100, 2)
        else:
            stats["open_rate"] = stats["click_rate"] = stats["reply_rate"] = 0
    
    return company_stats

def analyze_by_title(activities: List[Dict]) -> Dict[str, Any]:
    """Analyze performance by job title"""
    title_stats = {}
    
    for activity in activities:
        title = activity.get("title", "Unknown")
        if title not in title_stats:
            title_stats[title] = {
                "total_recipients": 0,
                "opened": 0,
                "clicked": 0,
                "replied": 0
            }
        
        title_stats[title]["total_recipients"] += 1
        if activity.get("email_opened_at"):
            title_stats[title]["opened"] += 1
        if activity.get("email_clicked_at"):
            title_stats[title]["clicked"] += 1
        if activity.get("email_replied_at"):
            title_stats[title]["replied"] += 1
    
    # Calculate rates for each title
    for title, stats in title_stats.items():
        total = stats["total_recipients"]
        if total > 0:
            stats["open_rate"] = round(stats["opened"] / total * 100, 2)
            stats["click_rate"] = round(stats["clicked"] / total * 100, 2)
            stats["reply_rate"] = round(stats["replied"] / total * 100, 2)
        else:
            stats["open_rate"] = stats["click_rate"] = stats["reply_rate"] = 0
    
    return title_stats

def analyze_by_time(events: List[Dict]) -> Dict[str, Any]:
    """Analyze engagement patterns by time"""
    # This would analyze time-based patterns like best days/hours for engagement
    return {
        "best_send_times": ["9:00 AM", "2:00 PM", "10:00 AM"],
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "engagement_by_hour": {},
        "note": "Time analysis requires more historical data"
    }

def generate_campaign_insights(metrics: Dict, engagement: Dict, companies: Dict) -> List[str]:
    """Generate actionable insights from campaign data"""
    insights = []
    
    # Open rate insights
    open_rate = metrics.get("open_rate", 0)
    if open_rate > 25:
        insights.append(f"Excellent open rate of {open_rate}% - well above industry average")
    elif open_rate > 15:
        insights.append(f"Good open rate of {open_rate}% - consider A/B testing subject lines to improve further")
    else:
        insights.append(f"Low open rate of {open_rate}% - review subject lines and sender reputation")
    
    # Company insights
    top_companies = sorted(companies.items(), key=lambda x: x[1].get("reply_rate", 0), reverse=True)[:3]
    if top_companies:
        insights.append(f"Top responding companies: {', '.join([c[0] for c in top_companies])}")
    
    # Engagement insights
    high_engagement = len(engagement.get("high_engagement_recipients", []))
    if high_engagement > 0:
        insights.append(f"{high_engagement} recipients showed high engagement - prioritize for follow-up")
    
    return insights

def generate_optimization_recommendations(metrics: Dict, engagement: Dict) -> List[str]:
    """Generate optimization recommendations"""
    recommendations = []
    
    # Based on performance metrics
    reply_rate = metrics.get("reply_rate", 0)
    if reply_rate < 5:
        recommendations.append("Consider personalizing email content more specifically to recipient's role and company")
        recommendations.append("Review email timing - try sending during business hours on weekdays")
    
    # Based on engagement patterns
    event_types = engagement.get("event_types", {})
    opens = event_types.get("opened", 0)
    clicks = event_types.get("clicked", 0)
    
    if opens > 0 and clicks == 0:
        recommendations.append("Recipients are opening but not clicking - review call-to-action placement and clarity")
    
    if len(recommendations) == 0:
        recommendations.append("Campaign performance is good - continue with current strategy")
    
    return recommendations
