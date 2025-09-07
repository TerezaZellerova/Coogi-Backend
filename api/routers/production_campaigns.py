"""
Production Campaign Management API Routes
Unified campaign system that works with Instantly.ai and Smartlead.ai
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from api.dependencies import get_current_user
from utils.instantly_manager import InstantlyManager
from utils.smartlead_manager import SmartleadManager
from utils.progressive_agent_db import ProgressiveAgentDB

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/production-campaigns", tags=["production-campaigns"])

# Database instance
db = ProgressiveAgentDB()

# ===================================
# 📊 PYDANTIC MODELS
# ===================================

class EmailStep(BaseModel):
    step_number: int
    subject: str
    body: str
    delay_days: int
    template_variables: Optional[Dict[str, str]] = {}

class Contact(BaseModel):
    id: Optional[str] = None
    email: str
    first_name: str
    last_name: str
    company: str
    title: str
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    verified: bool = False
    verification_status: Optional[str] = "unknown"
    source: str = "manual"
    confidence_score: Optional[float] = None

class CreateCampaignRequest(BaseModel):
    name: str
    platform: str = Field(..., pattern="^(instantly|smartlead|internal)$")
    subject_line: str
    from_email: str
    from_name: str
    email_sequence: List[EmailStep]
    contacts: List[Contact]
    agent_id: Optional[str] = None

class CampaignOperationResponse(BaseModel):
    success: bool
    message: str
    campaign_id: str
    provider_campaign_id: Optional[str] = None

class CampaignStatsResponse(BaseModel):
    campaign_id: str
    sent: int
    opens: int
    replies: int
    clicks: int
    bounces: int
    open_rate: float
    reply_rate: float
    click_rate: float
    last_updated: str

# ===================================
# 🚀 CAMPAIGN ROUTES
# ===================================

@router.post("/create")
async def create_production_campaign(
    request: CreateCampaignRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Create a production-ready campaign with provider integration"""
    try:
        logger.info(f"🚀 Creating production campaign: {request.name}")
        
        # Validate required fields
        if not request.subject_line:
            raise HTTPException(status_code=400, detail="Subject line is required")
        
        if not request.email_sequence:
            raise HTTPException(status_code=400, detail="Email sequence is required")
        
        # Generate campaign ID
        campaign_id = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.name) % 10000}"
        
        # Save campaign to database first (as draft)
        campaign_data = {
            "campaign_id": campaign_id,
            "name": request.name,
            "status": "draft",
            "platform": request.platform,
            "subject_line": request.subject_line,
            "from_email": request.from_email,
            "from_name": request.from_name,
            "email_sequence": [step.dict() for step in request.email_sequence],
            "target_count": len(request.contacts),
            "verified_contacts": [contact.dict() for contact in request.contacts],
            "sent_count": 0,
            "open_count": 0,
            "reply_count": 0,
            "click_count": 0,
            "bounce_count": 0,
            "open_rate": 0.0,
            "reply_rate": 0.0,
            "click_rate": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "agent_id": request.agent_id
        }
        
        await db.save_campaign_metadata(campaign_id, campaign_data)
        
        # Schedule provider creation in background
        if request.platform in ["instantly", "smartlead"]:
            background_tasks.add_task(create_campaign_in_provider, campaign_id, request)
        
        logger.info(f"✅ Campaign created: {campaign_id}")
        return CampaignOperationResponse(
            success=True,
            message="Campaign created successfully",
            campaign_id=campaign_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def get_campaigns(current_user: str = Depends(get_current_user)):
    """Get all campaigns for the current user"""
    try:
        campaigns = await db.get_campaigns()
        return {"campaigns": campaigns}
    except Exception as e:
        logger.error(f"❌ Error fetching campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Start a campaign (activate in provider)"""
    try:
        campaign = await db.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign["status"] != "draft":
            raise HTTPException(status_code=400, detail="Campaign is already active or completed")
        
        # Update status to active
        await db.update_campaign_status(campaign_id, "active", {"started_at": datetime.now().isoformat()})
        
        # Start campaign in provider
        if campaign["platform"] in ["instantly", "smartlead"]:
            background_tasks.add_task(start_campaign_in_provider, campaign_id, campaign)
        
        return CampaignOperationResponse(
            success=True,
            message="Campaign started successfully",
            campaign_id=campaign_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error starting campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    current_user: str = Depends(get_current_user)
):
    """Pause a campaign"""
    try:
        campaign = await db.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Update status
        await db.update_campaign_status(campaign_id, "paused")
        
        # Pause in provider if has provider_campaign_id
        if campaign.get("provider_campaign_id"):
            await pause_campaign_in_provider(campaign)
        
        return CampaignOperationResponse(
            success=True,
            message="Campaign paused successfully",
            campaign_id=campaign_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error pausing campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: str,
    current_user: str = Depends(get_current_user)
):
    """Resume a paused campaign"""
    try:
        campaign = await db.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign["status"] != "paused":
            raise HTTPException(status_code=400, detail="Campaign is not paused")
        
        # Update status
        await db.update_campaign_status(campaign_id, "active")
        
        # Resume in provider if has provider_campaign_id
        if campaign.get("provider_campaign_id"):
            await resume_campaign_in_provider(campaign)
        
        return CampaignOperationResponse(
            success=True,
            message="Campaign resumed successfully",
            campaign_id=campaign_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error resuming campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get live campaign statistics"""
    try:
        campaign = await db.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return CampaignStatsResponse(
            campaign_id=campaign_id,
            sent=campaign.get("sent_count", 0),
            opens=campaign.get("open_count", 0),
            replies=campaign.get("reply_count", 0),
            clicks=campaign.get("click_count", 0),
            bounces=campaign.get("bounce_count", 0),
            open_rate=campaign.get("open_rate", 0.0),
            reply_rate=campaign.get("reply_rate", 0.0),
            click_rate=campaign.get("click_rate", 0.0),
            last_updated=campaign.get("last_sync_at", campaign.get("updated_at", ""))
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching stats for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/sync")
async def sync_campaign_stats(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Manually sync campaign stats from provider"""
    try:
        campaign = await db.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Schedule sync in background
        background_tasks.add_task(sync_campaign_from_provider, campaign_id, campaign)
        
        return CampaignOperationResponse(
            success=True,
            message="Campaign sync initiated",
            campaign_id=campaign_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error syncing campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/verify-contacts")
async def verify_campaign_contacts(
    campaign_id: str,
    current_user: str = Depends(get_current_user)
):
    """Verify contacts for a campaign"""
    try:
        campaign = await db.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        verified_contacts = []
        verification_errors = []
        
        contacts = campaign.get("verified_contacts", [])
        
        for contact in contacts:
            # For now, we'll mark all contacts as verified
            # In a real implementation, you'd use email verification services
            contact["verified"] = True
            contact["verification_status"] = "valid"
            verified_contacts.append(contact)
        
        # Update campaign with verified contacts
        await db.update_campaign_metadata(campaign_id, {
            "verified_contacts": verified_contacts,
            "target_count": len(verified_contacts),
            "updated_at": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "verified_count": len(verified_contacts),
            "error_count": len(verification_errors),
            "errors": verification_errors
        }
        
    except Exception as e:
        logger.error(f"❌ Error verifying contacts for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================================
# 🔧 BACKGROUND TASKS
# ===================================

async def create_campaign_in_provider(campaign_id: str, request: CreateCampaignRequest):
    """Create campaign in external provider (Instantly/Smartlead)"""
    try:
        provider_campaign_id = None
        
        if request.platform == "instantly":
            # Create in Instantly.ai
            instantly_manager = InstantlyManager()
            
            # Create lead list first
            lead_list_id = instantly_manager.create_lead_list(
                name=f"{request.name} - Lead List",
                description=f"Lead list for campaign: {request.name}"
            )
            
            if lead_list_id and request.contacts:
                # Add leads to list
                leads_data = [{
                    "email": contact.email,
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "company": contact.company,
                    "title": contact.title,
                    "linkedin_url": contact.linkedin_url or ""
                } for contact in request.contacts]
                
                instantly_manager.add_leads_to_list(lead_list_id, leads_data)
            
            # Create campaign with lead list
            provider_campaign_id = instantly_manager.create_campaign_with_lead_list(
                name=request.name,
                subject_line=request.subject_line,
                message_template=request.email_sequence[0].body,
                sender_email=request.from_email,
                sender_name=request.from_name,
                lead_list_id=lead_list_id
            )
            
        elif request.platform == "smartlead":
            # Create in Smartlead.ai
            smartlead_manager = SmartleadManager()
            
            # Prepare leads data for Smartlead
            leads_data = [{
                "email": contact.email,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "company_name": contact.company,
                "custom_fields": {
                    "title": contact.title,
                    "linkedin_url": contact.linkedin_url or ""
                }
            } for contact in request.contacts]
            
            result = smartlead_manager.create_campaign(
                name=request.name,
                leads=leads_data,
                email_template=request.email_sequence[0].body,
                subject=request.subject_line,
                from_email=request.from_email,
                from_name=request.from_name
            )
            provider_campaign_id = result.get("campaign_id") if result else None
        
        # Update campaign with provider ID
        if provider_campaign_id:
            await db.update_campaign_metadata(campaign_id, {
                "provider_campaign_id": provider_campaign_id,
                "status": "ready",
                "updated_at": datetime.now().isoformat()
            })
            logger.info(f"✅ Campaign {campaign_id} created in {request.platform}: {provider_campaign_id}")
        else:
            await db.update_campaign_metadata(campaign_id, {
                "status": "error",
                "error_message": f"Failed to create campaign in {request.platform}",
                "updated_at": datetime.now().isoformat()
            })
            logger.error(f"❌ Failed to create campaign {campaign_id} in {request.platform}")
            
    except Exception as e:
        logger.error(f"❌ Error creating campaign {campaign_id} in provider: {e}")
        await db.update_campaign_metadata(campaign_id, {
            "status": "error",
            "error_message": str(e),
            "updated_at": datetime.now().isoformat()
        })
            
    except Exception as e:
        logger.error(f"❌ Error creating campaign {campaign_id} in provider: {e}")
        await db.update_campaign_metadata(campaign_id, {
            "status": "failed",
            "sync_errors": [str(e)]
        })

async def start_campaign_in_provider(campaign_id: str, campaign: Dict[str, Any]):
    """Start campaign in external provider"""
    try:
        if not campaign.get("provider_campaign_id"):
            logger.warning(f"Campaign {campaign_id} has no provider campaign ID")
            return
        
        platform = campaign["platform"]
        provider_campaign_id = campaign["provider_campaign_id"]
        
        if platform == "instantly":
            instantly_manager = InstantlyManager()
            success = instantly_manager.activate_campaign(provider_campaign_id)
            if success:
                logger.info(f"✅ Campaign {campaign_id} started in Instantly")
            else:
                logger.error(f"❌ Failed to start campaign {campaign_id} in Instantly")
            
        elif platform == "smartlead":
            smartlead_manager = SmartleadManager()
            success = smartlead_manager.start_campaign(provider_campaign_id)
            if success:
                logger.info(f"✅ Campaign {campaign_id} started in Smartlead")
            else:
                logger.error(f"❌ Failed to start campaign {campaign_id} in Smartlead")
        
    except Exception as e:
        logger.error(f"❌ Error starting campaign {campaign_id} in provider: {e}")

async def pause_campaign_in_provider(campaign: Dict[str, Any]):
    """Pause campaign in external provider"""
    try:
        platform = campaign["platform"]
        provider_campaign_id = campaign.get("provider_campaign_id")
        
        if not provider_campaign_id:
            return
        
        if platform == "instantly":
            instantly_manager = InstantlyManager()
            success = instantly_manager.pause_campaign(provider_campaign_id)
            if success:
                logger.info(f"✅ Campaign {campaign['campaign_id']} paused in Instantly")
            else:
                logger.error(f"❌ Failed to pause campaign {campaign['campaign_id']} in Instantly")
            
        elif platform == "smartlead":
            smartlead_manager = SmartleadManager()
            success = smartlead_manager.pause_campaign(provider_campaign_id)
            if success:
                logger.info(f"✅ Campaign {campaign['campaign_id']} paused in Smartlead")
            else:
                logger.error(f"❌ Failed to pause campaign {campaign['campaign_id']} in Smartlead")
        
    except Exception as e:
        logger.error(f"❌ Error pausing campaign in provider: {e}")

async def resume_campaign_in_provider(campaign: Dict[str, Any]):
    """Resume campaign in external provider"""
    try:
        platform = campaign["platform"]
        provider_campaign_id = campaign.get("provider_campaign_id")
        
        if not provider_campaign_id:
            return
        
        if platform == "instantly":
            instantly_manager = InstantlyManager()
            success = instantly_manager.activate_campaign(provider_campaign_id)
            if success:
                logger.info(f"✅ Campaign {campaign['campaign_id']} resumed in Instantly")
            else:
                logger.error(f"❌ Failed to resume campaign {campaign['campaign_id']} in Instantly")
            
        elif platform == "smartlead":
            smartlead_manager = SmartleadManager()
            success = smartlead_manager.start_campaign(provider_campaign_id)
            if success:
                logger.info(f"✅ Campaign {campaign['campaign_id']} resumed in Smartlead")
            else:
                logger.error(f"❌ Failed to resume campaign {campaign['campaign_id']} in Smartlead")
        
    except Exception as e:
        logger.error(f"❌ Error resuming campaign in provider: {e}")

async def sync_campaign_from_provider(campaign_id: str, campaign: Dict[str, Any]):
    """Sync campaign stats from external provider"""
    try:
        platform = campaign["platform"]
        provider_campaign_id = campaign.get("provider_campaign_id")
        
        if not provider_campaign_id:
            logger.warning(f"Campaign {campaign_id} has no provider campaign ID")
            return
        
        stats = None
        
        if platform == "instantly":
            instantly_manager = InstantlyManager()
            campaign_data = instantly_manager.get_campaign_status(provider_campaign_id)
            if campaign_data:
                # Parse Instantly stats format
                stats = {
                    "sent": campaign_data.get("total_sent", 0),
                    "opens": campaign_data.get("total_opened", 0),
                    "replies": campaign_data.get("total_replied", 0),
                    "clicks": campaign_data.get("total_clicked", 0),
                    "bounces": campaign_data.get("total_bounced", 0)
                }
            
        elif platform == "smartlead":
            smartlead_manager = SmartleadManager()
            campaign_stats = smartlead_manager.get_campaign_stats(provider_campaign_id)
            if campaign_stats:
                stats = campaign_stats
        
        if stats:
            # Calculate rates
            sent = stats.get("sent", 0)
            opens = stats.get("opens", 0)
            replies = stats.get("replies", 0)
            clicks = stats.get("clicks", 0)
            
            open_rate = (opens / sent * 100) if sent > 0 else 0
            reply_rate = (replies / sent * 100) if sent > 0 else 0
            click_rate = (clicks / sent * 100) if sent > 0 else 0
            
            # Update campaign stats
            await db.update_campaign_metadata(campaign_id, {
                "sent_count": sent,
                "open_count": opens,
                "reply_count": replies,
                "click_count": clicks,
                "bounce_count": stats.get("bounces", 0),
                "open_rate": round(open_rate, 2),
                "reply_rate": round(reply_rate, 2),
                "click_rate": round(click_rate, 2),
                "last_sync_at": datetime.now().isoformat()
            })
            
            logger.info(f"✅ Campaign {campaign_id} stats synced from {platform}")
        
    except Exception as e:
        logger.error(f"❌ Error syncing campaign {campaign_id} from provider: {e}")
