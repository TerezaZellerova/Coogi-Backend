from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Dict, Any
import logging
import os

from ..models import InstantlyCampaignRequest, InstantlyCampaignResponse
from ..dependencies import (
    get_current_user, get_job_scraper, get_contact_finder, 
    get_instantly_manager
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["campaigns"])

@router.post("/create-instantly-campaign", response_model=InstantlyCampaignResponse)
async def create_instantly_campaign(request: InstantlyCampaignRequest):
    """Create an Instantly.ai campaign with leads (without sending emails)"""
    try:
        job_scraper = get_job_scraper()
        contact_finder = get_contact_finder()
        instantly_manager = get_instantly_manager()
        
        # Parse query and search for jobs
        search_params = job_scraper.parse_query(request.query)
        jobs = job_scraper.search_jobs(search_params, max_results=request.max_leads * 3)
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found matching criteria")
        
        leads = []
        processed_companies = set()
        
        # Process jobs to find leads
        for job in jobs:
            if len(leads) >= request.max_leads:
                break
                
            company = job.get('company', '')
            if company in processed_companies:
                continue
                
            processed_companies.add(company)
            
            # Find contacts and analyze company
            try:
                description = job.get('description') or job.get('job_level') or ''
                result = contact_finder.find_contacts(
                    company=company,
                    role_hint=job.get('title', ''),
                    keywords=job_scraper.extract_keywords(description),
                    company_website=job.get('company_website')
                )
                
                contacts, has_ta_team, employee_roles, company_found = result
                
                # Skip companies with TA teams
                if has_ta_team:
                    continue
                
                # Create leads from contacts
                for contact in contacts[:3]:  # Top 3 contacts
                    email = contact_finder.find_email(contact.get('title', ''), company)
                    if email:
                        score = contact_finder.calculate_lead_score(contact, job, has_ta_team)
                        if score >= request.min_score:
                            lead = {
                                "name": contact.get('name', ''),
                                "title": contact.get('title', ''),
                                "company": company,
                                "email": email,
                                "job_title": job.get('title', ''),
                                "job_url": job.get('job_url', ''),
                                "score": score,
                                "company_website": job.get('company_website', '')
                            }
                            leads.append(lead)
                        
            except Exception as e:
                logger.error(f"Error processing {company}: {e}")
                continue
        
        # Create Instantly campaign
        campaign_id = None
        status = "failed"
        
        if leads:
            campaign_id = instantly_manager.create_recruiting_campaign(
                leads=leads,
                campaign_name=request.campaign_name
            )
            status = "created" if campaign_id else "failed"
        else:
            status = "no_leads"
        
        return InstantlyCampaignResponse(
            campaign_id=campaign_id,
            campaign_name=request.campaign_name or f"Recruiting_Campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            leads_added=len(leads),
            total_leads_found=len(leads),
            status=status,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating Instantly campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lead-lists")
async def get_lead_lists():
    """Get all lead lists from Instantly"""
    try:
        instantly_manager = get_instantly_manager()
        lead_lists = instantly_manager.get_lead_lists()
        return {"lead_lists": lead_lists, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error getting lead lists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lead-lists/cleanup")
async def cleanup_lead_lists(days_old: int = 7):
    """Clean up old lead lists"""
    try:
        instantly_manager = get_instantly_manager()
        result = instantly_manager.cleanup_old_lead_lists(days_old)
        return {"message": "Lead lists cleaned up", "result": result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error cleaning up lead lists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns")
async def get_campaigns(current_user: dict = Depends(get_current_user)):
    """Get all campaigns"""
    try:
        campaigns = []
        
        # Try to get campaigns from Supabase if available
        try:
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                # Get campaigns from lead_lists table
                response = supabase.table("lead_lists").select("*").execute()
                lead_lists = response.data or []
                
                for i, lead_list in enumerate(lead_lists):
                    campaigns.append({
                        "id": lead_list.get("batch_id", f"campaign_{i}"),
                        "name": f"Campaign: {lead_list.get('query', 'Unknown')}",
                        "status": "active" if lead_list.get("email_count", 0) > 0 else "draft",
                        "leads_count": lead_list.get("email_count", 0),
                        "open_rate": 0.0,  # Placeholder - would come from email service
                        "reply_rate": 0.0,  # Placeholder - would come from email service
                        "created_at": lead_list.get("created_at", datetime.now().isoformat()),
                        "batch_id": lead_list.get("batch_id")
                    })
        except Exception as e:
            logger.warning(f"Could not fetch campaigns from Supabase: {e}")
        
        return campaigns
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}")
        return []

@router.post("/campaigns")
async def create_campaign(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new campaign"""
    try:
        campaign_name = request.get("name")
        lead_ids = request.get("lead_ids", [])
        
        if not campaign_name:
            raise HTTPException(status_code=400, detail="Campaign name is required")
        
        # For now, just create a simple campaign record
        # In production, this would integrate with email service
        campaign_id = f"campaign_{int(datetime.now().timestamp())}"
        
        campaign = {
            "id": campaign_id,
            "name": campaign_name,
            "status": "draft",
            "leads_count": len(lead_ids),
            "open_rate": 0.0,
            "reply_rate": 0.0,
            "created_at": datetime.now().isoformat(),
            "batch_id": campaign_id
        }
        
        return campaign
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))
