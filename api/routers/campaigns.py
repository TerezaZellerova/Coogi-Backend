from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Dict, Any
import logging
import os

from ..models import (
    InstantlyCampaignRequest, InstantlyCampaignResponse,
    SESCampaignRequest, SESCampaignResponse, SESEmailRequest,
    SESBulkEmailRequest, SESTemplateRequest, EmailProviderStats,
    JSearchJobRequest, JSearchJobResponse, JSearchSalaryRequest, JSearchSalaryResponse,
    SmartleadCampaignRequest, SmartleadAICampaignRequest, SmartleadCampaignResponse, 
    SmartleadStatsResponse, SmartleadAccountResponse
)
from ..dependencies import (
    get_current_user, get_job_scraper, get_contact_finder, 
    get_instantly_manager, get_ses_manager, get_jsearch_manager, 
    get_smartlead_manager
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
                response = supabase.table("lead_lists").select("*").order("created_at", desc=True).execute()
                lead_lists = response.data or []
                
                for i, lead_list in enumerate(lead_lists):
                    # Use campaign_name if available, otherwise fall back to query
                    campaign_name = lead_list.get("campaign_name") or f"Campaign: {lead_list.get('query', 'Unknown')}"
                    
                    campaigns.append({
                        "id": lead_list.get("batch_id", f"campaign_{i}"),
                        "name": campaign_name,
                        "status": lead_list.get("status", "active") if lead_list.get("email_count", 0) > 0 else "draft",
                        "leads_count": lead_list.get("lead_count", 0) or lead_list.get("email_count", 0),
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
        
        # Create a simple campaign record
        campaign_id = f"campaign_{int(datetime.now().timestamp())}"
        campaign_data = {
            "id": campaign_id,
            "name": campaign_name,
            "status": "draft",
            "leads_count": len(lead_ids),
            "open_rate": 0.0,
            "reply_rate": 0.0,
            "created_at": datetime.now().isoformat(),
            "batch_id": campaign_id
        }
        
        # Try to save to Supabase
        try:
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                
                # Create a simplified record in lead_lists for campaign tracking
                lead_list_record = {
                    "batch_id": campaign_id,
                    "query": campaign_name,
                    "location": "general",
                    "lead_count": len(lead_ids),
                    "email_count": 0,  # Will be updated when emails are sent
                    "created_at": datetime.now().isoformat(),
                    "company_size": "all",
                    "campaign_name": campaign_name,
                    "status": "draft"
                }
                
                result = supabase.table("lead_lists").insert(lead_list_record).execute()
                logger.info(f"Campaign saved to database: {campaign_id}")
                
        except Exception as e:
            logger.warning(f"Could not save campaign to database: {e}")
            # Continue anyway - campaign creation doesn't depend on database storage
        
        return campaign_data
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SES Email Endpoints
@router.post("/ses/send-email")
async def send_ses_email(
    request: SESEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send single email via Amazon SES"""
    try:
        ses_manager = get_ses_manager()
        result = ses_manager.send_email(
            to_emails=request.to_emails,
            subject=request.subject,
            body_html=request.body_html,
            body_text=request.body_text,
            from_email=request.from_email,
            reply_to=request.reply_to
        )
        return result
    except Exception as e:
        logger.error(f"Error sending SES email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ses/send-bulk-email")
async def send_ses_bulk_email(
    request: SESBulkEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send bulk personalized emails via SES templates"""
    try:
        ses_manager = get_ses_manager()
        result = ses_manager.send_bulk_emails(
            emails_data=request.emails_data,
            template_name=request.template_name,
            from_email=request.from_email
        )
        return result
    except Exception as e:
        logger.error(f"Error sending bulk SES emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ses/create-template")
async def create_ses_template(
    request: SESTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create email template in SES"""
    try:
        ses_manager = get_ses_manager()
        success = ses_manager.create_email_template(
            template_name=request.template_name,
            subject=request.subject,
            html_template=request.html_template,
            text_template=request.text_template
        )
        return {
            "success": success,
            "template_name": request.template_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating SES template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ses/stats")
async def get_ses_stats(current_user: dict = Depends(get_current_user)):
    """Get SES account statistics and reputation"""
    try:
        ses_manager = get_ses_manager()
        
        # Get reputation and quota info
        reputation_data = ses_manager.check_reputation()
        stats_data = ses_manager.get_send_statistics()
        
        if reputation_data.get("success"):
            return EmailProviderStats(
                provider="amazon_ses",
                daily_quota=reputation_data.get("daily_quota", 0),
                sent_last_24h=reputation_data.get("sent_last_24h", 0),
                send_rate=reputation_data.get("send_rate", 0),
                reputation_score=reputation_data.get("reputation", {}).get("ReputationForLastDelivery", {}).get("Percentage"),
                timestamp=datetime.now().isoformat()
            )
        else:
            return {"error": "Failed to get SES stats", "timestamp": datetime.now().isoformat()}
            
    except Exception as e:
        logger.error(f"Error getting SES stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ses/create-campaign", response_model=SESCampaignResponse)
async def create_ses_campaign(
    request: SESCampaignRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create SES-powered recruiting campaign with leads"""
    try:
        job_scraper = get_job_scraper()
        contact_finder = get_contact_finder()
        ses_manager = get_ses_manager()
        
        # Parse query and search for jobs
        search_params = job_scraper.parse_query(request.query)
        jobs = job_scraper.search_jobs(search_params, max_results=request.max_leads * 3)
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found matching criteria")
        
        leads = []
        processed_companies = set()
        
        # Process jobs to find leads (same logic as Instantly)
        for job in jobs:
            if len(leads) >= request.max_leads:
                break
                
            company = job.get('company', '')
            if company in processed_companies:
                continue
                
            processed_companies.add(company)
            
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
        
        # Create campaign ID and name
        campaign_id = f"ses_campaign_{int(datetime.now().timestamp())}"
        campaign_name = request.campaign_name or f"SES_Recruiting_Campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        emails_sent = 0
        email_failures = 0
        message_ids = []
        
        # Send emails if requested
        if request.send_immediately and leads:
            for lead in leads:
                try:
                    # Personalize email content
                    personalized_template = request.email_template.replace(
                        "{name}", lead.get("name", "")
                    ).replace(
                        "{company}", lead.get("company", "")
                    ).replace(
                        "{job_title}", lead.get("job_title", "")
                    ).replace(
                        "{title}", lead.get("title", "")
                    )
                    
                    # Send via SES
                    result = ses_manager.send_email(
                        to_emails=[lead["email"]],
                        subject=request.subject,
                        body_html=personalized_template,
                        body_text=personalized_template,  # Strip HTML for text version
                        from_email=request.from_email
                    )
                    
                    if result.get("success"):
                        emails_sent += 1
                        message_ids.append(result.get("message_id", ""))
                    else:
                        email_failures += 1
                        
                except Exception as e:
                    logger.error(f"Failed to send email to {lead['email']}: {e}")
                    email_failures += 1
        
        # Determine status
        if not leads:
            status = "no_leads"
        elif request.send_immediately:
            status = "sent" if emails_sent > 0 else "send_failed"
        else:
            status = "created"
        
        return SESCampaignResponse(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            leads_added=len(leads),
            total_leads_found=len(leads),
            emails_sent=emails_sent,
            email_failures=email_failures,
            status=status,
            provider="amazon_ses",
            message_ids=message_ids,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating SES campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ses/bounce-complaint")
async def handle_ses_notification(notification: dict):
    """Handle SES bounce/complaint notifications (webhook endpoint)"""
    try:
        ses_manager = get_ses_manager()
        result = ses_manager.handle_bounce_complaint(notification)
        return {"processed": result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error handling SES notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# JSearch Job Search Endpoints
@router.post("/jsearch/search-jobs", response_model=JSearchJobResponse)
async def search_jobs_jsearch(
    request: JSearchJobRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search for jobs using JSearch RapidAPI"""
    try:
        jsearch_manager = get_jsearch_manager()
        result = jsearch_manager.search_jobs(
            query=request.query,
            location=request.location,
            employment_types=request.employment_types,
            remote_jobs_only=request.remote_jobs_only,
            date_posted=request.date_posted,
            num_pages=request.num_pages
        )
        
        if result.get("success"):
            return JSearchJobResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "JSearch request failed"))
            
    except Exception as e:
        logger.error(f"Error searching JSearch jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jsearch/job-details/{job_id}")
async def get_jsearch_job_details(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific job from JSearch"""
    try:
        jsearch_manager = get_jsearch_manager()
        result = jsearch_manager.get_job_details(job_id)
        return result
    except Exception as e:
        logger.error(f"Error getting JSearch job details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jsearch/salary-estimates", response_model=JSearchSalaryResponse)
async def get_jsearch_salary_estimates(
    request: JSearchSalaryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get salary estimates for a job title/location using JSearch"""
    try:
        jsearch_manager = get_jsearch_manager()
        result = jsearch_manager.get_salary_estimates(
            job_title=request.job_title,
            location=request.location
        )
        
        if result.get("success"):
            return JSearchSalaryResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Salary estimates request failed"))
            
    except Exception as e:
        logger.error(f"Error getting JSearch salary estimates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jsearch/trending-jobs")
async def get_jsearch_trending_jobs(
    location: str = "United States",
    current_user: dict = Depends(get_current_user)
):
    """Get trending/popular job searches from JSearch"""
    try:
        jsearch_manager = get_jsearch_manager()
        result = jsearch_manager.search_trending_jobs(location=location)
        return result
    except Exception as e:
        logger.error(f"Error getting JSearch trending jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jsearch/company/{company_name}")
async def search_jsearch_company_jobs(
    company_name: str,
    location: str = "United States",
    current_user: dict = Depends(get_current_user)
):
    """Search for jobs at a specific company using JSearch"""
    try:
        jsearch_manager = get_jsearch_manager()
        result = jsearch_manager.search_by_company(
            company_name=company_name,
            location=location
        )
        return result
    except Exception as e:
        logger.error(f"Error searching JSearch company jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jsearch/status")
async def get_jsearch_status(current_user: dict = Depends(get_current_user)):
    """Check JSearch API status and quota"""
    try:
        jsearch_manager = get_jsearch_manager()
        result = jsearch_manager.get_api_status()
        return result
    except Exception as e:
        logger.error(f"Error checking JSearch status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Smartlead.ai Campaign Endpoints
@router.post("/smartlead/create-campaign", response_model=SmartleadCampaignResponse)
async def create_smartlead_campaign(
    request: SmartleadCampaignRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new Smartlead.ai campaign"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.create_campaign(
            name=request.name,
            leads=request.leads,
            email_template=request.email_template,
            subject=request.subject,
            from_email=request.from_email,
            from_name=request.from_name
        )
        
        if result.get("success"):
            return SmartleadCampaignResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Smartlead campaign creation failed"))
            
    except Exception as e:
        logger.error(f"Error creating Smartlead campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/smartlead/create-ai-campaign", response_model=SmartleadCampaignResponse)
async def create_smartlead_ai_campaign(
    request: SmartleadAICampaignRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create AI-personalized Smartlead.ai campaign"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.create_ai_personalized_campaign(
            name=request.name,
            leads=request.leads,
            template_context=request.template_context,
            subject_template=request.subject_template,
            from_email=request.from_email,
            personalization_level=request.personalization_level
        )
        
        if result.get("success"):
            return SmartleadCampaignResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Smartlead AI campaign creation failed"))
            
    except Exception as e:
        logger.error(f"Error creating Smartlead AI campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smartlead/campaigns")
async def get_smartlead_campaigns(current_user: dict = Depends(get_current_user)):
    """Get all Smartlead.ai campaigns"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.get_campaigns()
        return result
    except Exception as e:
        logger.error(f"Error getting Smartlead campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smartlead/campaign/{campaign_id}/stats", response_model=SmartleadStatsResponse)
async def get_smartlead_campaign_stats(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed statistics for a Smartlead campaign"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.get_campaign_stats(campaign_id)
        
        if result.get("success"):
            return SmartleadStatsResponse(**result)
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "Campaign not found"))
            
    except Exception as e:
        logger.error(f"Error getting Smartlead campaign stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/smartlead/campaign/{campaign_id}/pause")
async def pause_smartlead_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Pause a Smartlead campaign"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.pause_campaign(campaign_id)
        return result
    except Exception as e:
        logger.error(f"Error pausing Smartlead campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/smartlead/campaign/{campaign_id}/resume")
async def resume_smartlead_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resume a paused Smartlead campaign"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.resume_campaign(campaign_id)
        return result
    except Exception as e:
        logger.error(f"Error resuming Smartlead campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/smartlead/campaign/{campaign_id}")
async def delete_smartlead_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a Smartlead campaign"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.delete_campaign(campaign_id)
        return result
    except Exception as e:
        logger.error(f"Error deleting Smartlead campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smartlead/account", response_model=SmartleadAccountResponse)
async def get_smartlead_account_info(current_user: dict = Depends(get_current_user)):
    """Get Smartlead account information and limits"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.get_account_info()
        
        if result.get("success"):
            return SmartleadAccountResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get account info"))
            
    except Exception as e:
        logger.error(f"Error getting Smartlead account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smartlead/status")
async def get_smartlead_status(current_user: dict = Depends(get_current_user)):
    """Test Smartlead API connection and key validity"""
    try:
        smartlead_manager = get_smartlead_manager()
        result = smartlead_manager.test_api_connection()
        return result
    except Exception as e:
        logger.error(f"Error checking Smartlead status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
