"""
Progressive Agent Router - Handles staged agent creation and updates
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import asyncio
import logging
from datetime import datetime

from ..models import JobSearchRequest, ProgressiveAgentResponse, ProgressiveAgent
from ..dependencies import get_job_scraper, get_contact_finder
from utils.progressive_agent_manager import progressive_agent_manager
from utils.linkedin_fast_scraper import LinkedInFastScraper
from utils.bulletproof_job_scraper import BulletproofJobScraper
from utils.bulletproof_contact_finder import BulletproofContactFinder
from utils.bulletproof_campaign_creator import BulletproofCampaignCreator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["progressive-agents"])

@router.post("/agents/create-progressive", response_model=ProgressiveAgentResponse)
async def create_progressive_agent(request: JobSearchRequest, background_tasks: BackgroundTasks):
    """
    Create a progressive agent that returns LinkedIn results fast while enriching in background
    Stage 1: LinkedIn jobs (2-3 minutes max)
    Stage 2-4: Background enrichment (other boards, contacts, campaigns)
    """
    try:
        logger.info(f"🚀 Creating progressive agent for query: {request.query}")
        
        # Create progressive agent
        agent = progressive_agent_manager.create_progressive_agent(
            query=request.query,
            hours_old=request.hours_old,
            custom_tags=request.custom_tags,
            target_type=request.target_type,
            company_size=request.company_size,
            location_filter=request.location_filter
        )
        
        # Start LinkedIn stage immediately
        background_tasks.add_task(
            run_linkedin_stage,
            agent.id,
            request.query,
            request.hours_old
        )
        
        # Start background enrichment stages
        background_tasks.add_task(
            run_background_enrichment,
            agent.id,
            request
        )
        
        return ProgressiveAgentResponse(
            agent=agent,
            message="Agent created! LinkedIn jobs will be available in 2-3 minutes.",
            next_update_in_seconds=30
        )
        
    except Exception as e:
        logger.error(f"Error creating progressive agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@router.get("/agents/progressive/{agent_id}", response_model=ProgressiveAgentResponse)
async def get_progressive_agent_status(agent_id: str):
    """Get current status and results for a progressive agent"""
    try:
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Determine next update interval based on status
        next_update = 30  # Default 30 seconds
        if agent.status == "completed":
            next_update = 0  # No more updates needed
        elif agent.status == "linkedin_stage":
            next_update = 15  # More frequent updates during active stage
        
        return ProgressiveAgentResponse(
            agent=agent,
            message=f"Agent status: {agent.status}",
            next_update_in_seconds=next_update
        )
        
    except Exception as e:
        logger.error(f"Error getting progressive agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/progressive", response_model=List[ProgressiveAgent])
async def get_all_progressive_agents():
    """Get all progressive agents"""
    try:
        agents = progressive_agent_manager.get_all_agents()
        return agents
    except Exception as e:
        logger.error(f"Error getting all progressive agents: {e}")
        return []

async def run_linkedin_stage(agent_id: str, query: str, hours_old: int):
    """Run the LinkedIn fast fetch stage using bulletproof job scraper"""
    try:
        logger.info(f"🔍 Starting LinkedIn stage for agent {agent_id}")
        
        # Update stage status
        progressive_agent_manager.update_stage_status(
            agent_id, "linkedin_fetch", "running", 0
        )
        
        # Get agent details for filtering
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent:
            raise Exception("Agent not found")
        
        # Initialize bulletproof job scraper
        job_scraper = BulletproofJobScraper()
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "linkedin_fetch", "running", 25
        )
        
        # Fetch LinkedIn jobs with company size filtering
        linkedin_jobs = await job_scraper.search_jobs_bulletproof(
            query=query,
            hours_old=hours_old,
            company_size=agent.company_size,
            location=agent.location_filter or "United States",
            max_results=30
        )
        
        # Categorize jobs: LinkedIn jobs include direct LinkedIn API results AND JSearch jobs with LinkedIn URLs
        all_jobs = linkedin_jobs  # This contains all jobs from bulletproof scraper
        linkedin_jobs = []
        other_jobs = []
        
        for job in all_jobs:
            job_url = job.get("url", "").lower()
            job_site = job.get("site", "").lower()
            
            # Consider it a LinkedIn job if:
            # 1. Site is "linkedin" (from direct API or JSearch with LinkedIn URL detection)
            # 2. Site is "jsearch" and URL contains "linkedin.com" (fallback)
            if (job_site == "linkedin" or 
                (job_site == "jsearch" and "linkedin.com" in job_url)):
                linkedin_jobs.append(job)
            else:
                other_jobs.append(job)
        
        # For this stage, we only want the LinkedIn jobs
        linkedin_jobs_only = linkedin_jobs
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "linkedin_fetch", "running", 75
        )
        
        # Add results
        progressive_agent_manager.add_stage_results(
            agent_id, "linkedin_fetch", linkedin_jobs_only, "linkedin_jobs"
        )
        
        # Complete stage
        progressive_agent_manager.update_stage_status(
            agent_id, "linkedin_fetch", "completed", 100, len(linkedin_jobs_only)
        )
        
        logger.info(f"✅ LinkedIn stage completed for agent {agent_id} - {len(linkedin_jobs_only)} LinkedIn jobs found")
        
    except Exception as e:
        logger.error(f"❌ LinkedIn stage failed for agent {agent_id}: {e}")
        progressive_agent_manager.update_stage_status(
            agent_id, "linkedin_fetch", "failed", 0, 0, str(e)
        )

async def run_background_enrichment(agent_id: str, request: JobSearchRequest):
    """Run background enrichment stages"""
    try:
        # Wait for LinkedIn stage to complete or timeout
        await asyncio.sleep(10)  # Give LinkedIn stage a head start
        
        # Stage 2: Other job boards
        await run_other_boards_stage(agent_id, request)
        
        # Stage 3: Contact enrichment
        await run_contact_enrichment_stage(agent_id)
        
        # Stage 4: Campaign creation
        if request.create_campaigns:
            await run_campaign_creation_stage(agent_id, request)
        
        # Finalize agent
        agent = progressive_agent_manager.get_agent(agent_id)
        if agent:
            final_stats = {
                "total_jobs": agent.staged_results.total_jobs,
                "total_contacts": agent.staged_results.total_contacts,
                "total_campaigns": agent.staged_results.total_campaigns,
                "completion_time": datetime.now().isoformat()
            }
            progressive_agent_manager.finalize_agent(agent_id, final_stats)
        
        logger.info(f"✅ Background enrichment completed for agent {agent_id}")
        
    except Exception as e:
        logger.error(f"❌ Background enrichment failed for agent {agent_id}: {e}")
        progressive_agent_manager.mark_agent_failed(agent_id, str(e))

async def run_other_boards_stage(agent_id: str, request: JobSearchRequest):
    """Fetch jobs from other job boards using bulletproof scraper"""
    try:
        logger.info(f"🔍 Starting other boards stage for agent {agent_id}")
        
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "running", 0
        )
        
        # Get agent details
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent:
            raise Exception("Agent not found")
        
        # Initialize bulletproof job scraper
        job_scraper = BulletproofJobScraper()
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "running", 25
        )
        
        # Get jobs from other sources and categorize them
        all_jobs = await asyncio.wait_for(
            job_scraper.search_jobs_bulletproof(
                query=request.query,
                hours_old=request.hours_old,
                company_size=agent.company_size,
                location=agent.location_filter or "United States",
                max_results=50
            ),
            timeout=300.0  # 5 minute timeout
        )
        
        # Categorize jobs: separate LinkedIn jobs from other sources
        linkedin_jobs = []
        other_jobs = []
        
        for job in all_jobs:
            job_url = job.get("url", "").lower()
            job_site = job.get("site", "").lower()
            
            # LinkedIn jobs: direct LinkedIn API OR JSearch with LinkedIn URLs
            if (job_site == "linkedin" or 
                (job_site == "jsearch" and "linkedin.com" in job_url)):
                linkedin_jobs.append(job)
            else:
                other_jobs.append(job)
        
        # For this stage, we only want the non-LinkedIn jobs
        other_jobs_only = other_jobs
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "running", 75
        )
        
        # Add results
        progressive_agent_manager.add_stage_results(
            agent_id, "other_boards", other_jobs_only, "other_jobs"
        )
        
        # Complete stage
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "completed", 100, len(other_jobs_only)
        )
        
        logger.info(f"✅ Other boards stage completed for agent {agent_id} - {len(other_jobs_only)} jobs")
        
    except asyncio.TimeoutError:
        logger.warning(f"⏰ Other boards stage timeout for agent {agent_id}")
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "completed", 100, 0
        )
    except Exception as e:
        logger.error(f"❌ Other boards stage failed for agent {agent_id}: {e}")
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "failed", 0, 0, str(e)
        )

async def run_contact_enrichment_stage(agent_id: str):
    """Run contact discovery and verification using bulletproof contact finder"""
    try:
        logger.info(f"👥 Starting contact enrichment for agent {agent_id}")
        
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "running", 0
        )
        
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent:
            return
        
        # Initialize bulletproof contact finder
        contact_finder = BulletproofContactFinder()
        all_contacts = []
        
        # Process all jobs for contacts
        all_jobs = agent.staged_results.linkedin_jobs + agent.staged_results.other_jobs
        total_jobs = len(all_jobs)
        
        # Limit to 20 companies for speed, but ensure we process the best ones
        companies_to_process = []
        for job in all_jobs[:20]:
            company = job.get("company", "").strip()
            if company and company not in [c.get("company") for c in companies_to_process]:
                companies_to_process.append({
                    "company": company,
                    "job_title": job.get("title", ""),
                    "job_url": job.get("url", ""),
                    "location": job.get("location", "")
                })
        
        logger.info(f"Processing {len(companies_to_process)} unique companies for contacts")
        
        for i, company_info in enumerate(companies_to_process):
            try:
                # Update progress
                progress = int((i / len(companies_to_process)) * 80)  # Reserve 20% for final processing
                progressive_agent_manager.update_stage_status(
                    agent_id, "contact_enrichment", "running", progress
                )
                
                # Find contacts for this company based on target type
                if agent.target_type == "hiring_managers":
                    target_roles = [
                        "Talent Acquisition Manager", "HR Manager", "Recruiter", 
                        "Head of Talent", "Recruiting Manager", "Head of People",
                        "Director of Talent", "VP of Talent", "Chief People Officer"
                    ]
                else:  # job_candidates
                    # Extract relevant roles from job title
                    job_title = company_info["job_title"].lower()
                    if "engineer" in job_title or "developer" in job_title or "software" in job_title:
                        target_roles = ["Software Engineer", "Senior Engineer", "Developer", "Tech Lead", "Engineering Manager"]
                    elif "marketing" in job_title:
                        target_roles = ["Marketing Manager", "Digital Marketing", "Product Marketing", "Growth Marketing"]
                    elif "sales" in job_title:
                        target_roles = ["Sales Manager", "Account Executive", "Business Development", "Sales Director"]
                    else:
                        target_roles = ["Manager", "Director", "Specialist", "Lead", "Senior"]
                
                contacts = await contact_finder.find_contacts_bulletproof(
                    companies=[company_info["company"]],
                    target_roles=target_roles,
                    max_contacts_per_company=3
                )
                
                if contacts:
                    # Enrich contacts with job context
                    for contact in contacts:
                        contact["source_job"] = company_info["job_title"]
                        contact["company"] = company_info["company"]
                        contact["job_url"] = company_info["job_url"]
                        contact["target_type"] = agent.target_type
                    
                    all_contacts.extend(contacts)
                    logger.info(f"Found {len(contacts)} contacts for {company_info['company']}")
                
            except Exception as contact_error:
                logger.error(f"Error finding contacts for {company_info['company']}: {contact_error}")
                continue
        
        # Final processing - deduplication and scoring
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "running", 90
        )
        
        # Remove duplicates based on email
        seen_emails = set()
        unique_contacts = []
        for contact in all_contacts:
            email = contact.get("email", "").lower()
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_contacts.append(contact)
        
        logger.info(f"Deduplicated to {len(unique_contacts)} unique contacts")
        
        # Add results
        progressive_agent_manager.add_stage_results(
            agent_id, "contact_enrichment", unique_contacts, "contacts"
        )
        
        # Complete stage
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "completed", 100, len(unique_contacts)
        )
        
        logger.info(f"✅ Contact enrichment completed for agent {agent_id} - {len(unique_contacts)} contacts")
        
    except Exception as e:
        logger.error(f"❌ Contact enrichment failed for agent {agent_id}: {e}")
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "failed", 0, 0, str(e)
        )

async def run_campaign_creation_stage(agent_id: str, request: JobSearchRequest):
    """Create campaigns from verified contacts using bulletproof campaign creator"""
    try:
        logger.info(f"📧 Starting campaign creation for agent {agent_id}")
        
        progressive_agent_manager.update_stage_status(
            agent_id, "campaign_creation", "running", 0
        )
        
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent or not agent.staged_results.verified_contacts:
            progressive_agent_manager.update_stage_status(
                agent_id, "campaign_creation", "completed", 100, 0
            )
            return
        
        # Initialize bulletproof campaign creator
        campaign_creator = BulletproofCampaignCreator()
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "campaign_creation", "running", 25
        )
        
        # Prepare campaign data
        campaign_name = request.campaign_name or f"Agent {agent_id} - {request.query}"
        contacts = agent.staged_results.verified_contacts
        jobs = agent.staged_results.linkedin_jobs + agent.staged_results.other_jobs
        
        logger.info(f"Creating campaigns for {len(contacts)} contacts from {len(jobs)} jobs")
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "campaign_creation", "running", 50
        )
        
        # Create campaigns using bulletproof campaign creator
        campaigns = await campaign_creator.create_campaigns_bulletproof(
            jobs=jobs,
            contacts=contacts,
            campaign_type=agent.target_type,
            sender_info={
                "name": "Talent Acquisition Team",
                "email": "talent@company.com",
                "title": "Talent Acquisition Specialist"
            }
        )
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "campaign_creation", "running", 90
        )
        
        # Add results
        progressive_agent_manager.add_stage_results(
            agent_id, "campaign_creation", campaigns, "campaigns"
        )
        
        # Complete stage
        progressive_agent_manager.update_stage_status(
            agent_id, "campaign_creation", "completed", 100, len(campaigns)
        )
        
        logger.info(f"✅ Campaign creation completed for agent {agent_id} - {len(campaigns)} campaigns")
        
    except Exception as e:
        logger.error(f"❌ Campaign creation failed for agent {agent_id}: {e}")
        progressive_agent_manager.update_stage_status(
            agent_id, "campaign_creation", "failed", 0, 0, str(e)
        )
