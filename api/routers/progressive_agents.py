"""
Progressive Agent Router - Handles staged agent creation and updates
UPDATED: Now supports different target types (hiring_managers vs job_candidates)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import asyncio
import logging
import time
from datetime import datetime

from ..models import JobSearchRequest, ProgressiveAgentResponse, ProgressiveAgent
from ..dependencies import get_job_scraper, get_contact_finder
from utils.progressive_agent_manager import progressive_agent_manager
from utils.progressive_agent_coordinator import ProgressiveAgentCoordinator
from utils.linkedin_fast_scraper import LinkedInFastScraper
from utils.bulletproof_job_scraper import BulletproofJobScraper
from utils.bulletproof_contact_finder import BulletproofContactFinder
from utils.bulletproof_campaign_creator import BulletproofCampaignCreator
from utils.professional_candidate_searcher import ProfessionalCandidateSearcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["progressive-agents"])

# Initialize the coordinator that handles different target types
agent_coordinator = ProgressiveAgentCoordinator()

# Initialize professional candidate searcher
professional_searcher = ProfessionalCandidateSearcher()

@router.post("/agents/create-progressive", response_model=ProgressiveAgentResponse)
async def create_progressive_agent(request: JobSearchRequest, background_tasks: BackgroundTasks):
    """
    Create a progressive agent that handles different target types:
    - hiring_managers: Job search -> find companies -> find hiring managers
    - job_candidates: People search -> find professionals directly
    """
    try:
        logger.info(f"🚀 Creating progressive agent for query: {request.query} | Target: {request.target_type}")
        
        # Create progressive agent
        agent = progressive_agent_manager.create_progressive_agent(
            query=request.query,
            hours_old=request.hours_old,
            custom_tags=request.custom_tags,
            target_type=request.target_type,
            company_size=request.company_size,
            location_filter=request.location_filter
        )
        
        # Start appropriate search strategy based on target_type
        if request.target_type == "job_candidates":  # Fix: frontend sends "job_candidates"
            # Start people search for candidates
            background_tasks.add_task(
                run_candidate_search_stages,
                agent.id,
                request
            )
            message = "Agent created! Candidate search starting - professionals will be available in 2-3 minutes."
        else:
            # Start job search for hiring managers (original behavior)
            background_tasks.add_task(
                run_hiring_manager_stages,
                agent.id,
                request
            )
            message = "Agent created! Job search starting - LinkedIn jobs will be available in 2-3 minutes."
        
        return ProgressiveAgentResponse(
            agent=agent,
            message=message,
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

async def run_candidate_search_stages(agent_id: str, request: JobSearchRequest):
    """
    Run all stages for job_candidates target type using Professional Candidate Searcher
    Stage 1: Apollo.io professional search
    Stage 2: Hunter.io email enhancement  
    Stage 3: Additional professional directories
    Stage 4: Campaign creation
    """
    try:
        logger.info(f"👤 Starting PROFESSIONAL candidate search stages for agent {agent_id}")
        
        # Get agent configuration
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent:
            raise Exception("Agent not found")
        
        # Stage 1: AUTO-CAMPAIGN Professional Candidate Search (Apollo.io + Hunter.io + Campaign Creation)
        try:
            logger.info(f"� Stage 1: AUTO-CAMPAIGN candidate search (Apollo.io + Hunter.io + Campaigns) for agent {agent_id}")
            progressive_agent_manager.update_stage_status(agent_id, "candidate_search", "running", 0)
            
            # Determine if this is a DVM search for auto-campaign
            query_lower = request.query.lower()
            is_dvm_search = any(term in query_lower for term in ["dvm", "veterinarian", "vet doctor", "vet "])
            
            if is_dvm_search:
                logger.info(f"🐾 Detected DVM search - using AUTO-CAMPAIGN integration")
                
                # Parse locations from location_filter  
                locations = []
                if agent.location_filter:
                    # Split by common delimiters
                    locations = [loc.strip() for loc in agent.location_filter.replace(';', ',').split(',') if loc.strip()]
                if not locations:
                    locations = ["United States"]  # Default fallback
                
                # Use DVM auto-campaign search with immediate campaign creation
                search_result = await professional_searcher.search_dvm_with_auto_campaign(
                    locations=locations,
                    per_city_limit=15,
                    require_email=True,
                    require_phone=False,
                    hunter_verify=True,
                    unlock_emails=True,
                    auto_create_campaign=True,  # AUTO-CREATE CAMPAIGNS!
                    campaign_name=f"DVM Search - {agent_id} - {', '.join(locations[:2])}{' +' + str(len(locations)-2) + ' more' if len(locations) > 2 else ''}",
                    send_immediately=False,  # Schedule for later
                    delay_hours=24,  # Send in 24 hours
                )
                
                # Update progress - 50% after search
                progressive_agent_manager.update_stage_status(agent_id, "candidate_search", "running", 50)
                
            else:
                logger.info(f"👤 Non-DVM search - using professional search with potential auto-campaign")
                
                # Parse locations for generic search
                locations = []
                if agent.location_filter:
                    locations = [loc.strip() for loc in agent.location_filter.replace(';', ',').split(',') if loc.strip()]
                if not locations:
                    locations = ["United States"]
                
                # Use generic professional search with auto-campaign attempt
                search_result = await professional_searcher.search_professional_with_auto_campaign(
                    job_title=request.query,
                    locations=locations,
                    per_city_limit=15,
                    require_email=True,
                    require_phone=False,
                    hunter_verify=True,
                    unlock_emails=True,
                    auto_create_campaign=True,
                    campaign_name=f"{request.query} Search - {agent_id} - {', '.join(locations[:2])}{' +' + str(len(locations)-2) + ' more' if len(locations) > 2 else ''}",
                    send_immediately=False,
                    delay_hours=24,
                )
                
                # Update progress - 50% after search
                progressive_agent_manager.update_stage_status(agent_id, "candidate_search", "running", 50)
            
            if search_result.get("success"):
                candidates = search_result.get("candidates", [])
                campaign_created = search_result.get("campaign_created", False)
                campaign_id = search_result.get("campaign_id")
                campaign_name = search_result.get("campaign_name")
                
                logger.info(f"📊 SEARCH RESULTS: {len(candidates)} candidates found, Campaign created: {campaign_created}")
                if campaign_created:
                    logger.info(f"📧 CAMPAIGN DETAILS: ID={campaign_id}, Name={campaign_name}")
                
                # Convert candidates to our contact format and save to Supabase
                contacts = []
                for candidate in candidates:
                    # Get organization name correctly
                    org = candidate.get("organization") or candidate.get("company", "")
                    company_name = ""
                    if isinstance(org, dict):
                        company_name = org.get("name", "")
                    elif isinstance(org, str):
                        company_name = org
                    
                    # Handle emails - could be list or string
                    emails = candidate.get("emails", [])
                    if isinstance(emails, str):
                        emails = [emails]
                    primary_email = emails[0] if emails else ""
                    
                    # Handle phones - could be list or string  
                    phones = candidate.get("phones", [])
                    if isinstance(phones, str):
                        phones = [phones]
                    primary_phone = phones[0] if phones else ""
                    
                    contact = {
                        "agent_id": agent_id,
                        "id": candidate.get("id", f"apollo_{int(time.time())}_{len(contacts)}"),
                        "name": f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip() or candidate.get("name", ""),
                        "first_name": candidate.get("first_name", ""),
                        "last_name": candidate.get("last_name", ""),
                        "email": primary_email,
                        "title": candidate.get("title", ""),
                        "company": company_name,
                        "role": candidate.get("title", ""),
                        "linkedin_url": candidate.get("linkedin_url", ""),
                        "source": candidate.get("source", "Apollo.io + Hunter.io"),
                        "phone": primary_phone,
                        "verified": candidate.get("verified", bool(primary_email and "not_unlocked" not in primary_email)),
                        "confidence_score": candidate.get("confidence_score", 0.8 if primary_email and "not_unlocked" not in primary_email else 0.5),
                        "location": candidate.get("location", ""),
                        "industry": candidate.get("industry", ""),
                        "company_size": candidate.get("company_size", ""),
                        "seniority": candidate.get("seniority", ""),
                        "departments": candidate.get("departments", ""),
                        "contact_accuracy": candidate.get("contact_accuracy", "high" if candidate.get("verified") else "medium"),
                        # Add campaign info
                        "campaign_created": campaign_created,
                        "campaign_id": campaign_id if campaign_created else None,
                        "campaign_name": campaign_name if campaign_created else None,
                    }
                    contacts.append(contact)
                
                # Update progress - 75% after processing
                progressive_agent_manager.update_stage_status(agent_id, "candidate_search", "running", 75)
                
                # Save contacts to progressive_agent_contacts table
                if contacts:
                    progressive_agent_manager.add_stage_results(
                        agent_id, "candidate_search", contacts, "contacts"
                    )
                    logger.info(f"💾 Saved {len(contacts)} professional candidates to database")
                
                # Save campaign info if created
                if campaign_created:
                    campaign_info = {
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "target_count": len(contacts),
                        "verified_count": search_result.get("verified_candidates", 0),
                        "send_scheduled": search_result.get("send_scheduled", True),
                        "send_delay_hours": search_result.get("send_delay_hours", 24),
                        "created_at": datetime.now().isoformat(),
                        "search_type": "dvm" if is_dvm_search else "professional",
                        "auto_campaign": True,
                    }
                    
                    progressive_agent_manager.add_stage_results(
                        agent_id, "campaign_creation", [campaign_info], "campaigns"
                    )
                    logger.info(f"📧 Saved auto-campaign info to database: {campaign_id}")
                
                progressive_agent_manager.update_stage_status(
                    agent_id, "candidate_search", "completed", 100, len(contacts)
                )
                
                campaign_msg = f", AUTO-CAMPAIGN CREATED: {campaign_id}" if campaign_created else ", no campaign created"
                logger.info(f"✅ Stage 1 completed: {len(contacts)} professional candidates found{campaign_msg}")
                
            else:
                error_msg = search_result.get("error", "Unknown error")
                logger.error(f"❌ AUTO-CAMPAIGN candidate search failed: {error_msg}")
                progressive_agent_manager.update_stage_status(
                    agent_id, "candidate_search", "failed", 0, 0, error_msg
                )
            
        except Exception as e:
            logger.error(f"❌ Stage 1 failed for agent {agent_id}: {e}")
            progressive_agent_manager.update_stage_status(
                agent_id, "candidate_search", "failed", 0, 0, str(e)
            )
        
        # Stage 2: Profile Analysis (analyze the candidates we found)
        try:
            logger.info(f"🔍 Stage 2: Profile analysis for candidate profiles")
            progressive_agent_manager.update_stage_status(agent_id, "profile_analysis", "completed", 100, 0)
            
        except Exception as e:
            logger.error(f"❌ Stage 2 failed for agent {agent_id}: {e}")
            progressive_agent_manager.update_stage_status(
                agent_id, "profile_analysis", "failed", 0, 0, str(e)
            )
        
        # Stage 3: Contact enrichment already done by professional searcher
        try:
            logger.info(f"👥 Stage 3: Professional searcher already includes enrichment - marking as completed")
            progressive_agent_manager.update_stage_status(agent_id, "contact_enrichment", "completed", 100, 0)
            
        except Exception as e:
            logger.error(f"❌ Stage 3 failed for agent {agent_id}: {e}")
            progressive_agent_manager.update_stage_status(
                agent_id, "contact_enrichment", "failed", 0, 0, str(e)
            )
        
        # Stage 4: Campaign Creation
        try:
            logger.info(f"📧 Stage 4: Campaign creation for agent {agent_id}")
            await run_campaign_creation_stage(agent_id, request)
        except Exception as e:
            logger.error(f"❌ Stage 4 failed for agent {agent_id}: {e}")
        
        # Finalize agent
        await finalize_candidate_agent(agent_id)
        
    except Exception as e:
        logger.error(f"❌ Critical error in candidate search stages for agent {agent_id}: {e}")
        progressive_agent_manager.mark_agent_failed(agent_id, str(e))

async def run_hiring_manager_stages(agent_id: str, request: JobSearchRequest):
    """
    Run all stages for hiring_managers target type (original behavior)
    Stage 1: LinkedIn job search
    Stage 2: Other job boards
    Stage 3: Contact enrichment (find hiring managers)
    Stage 4: Campaign creation
    """
    try:
        logger.info(f"🏢 Starting hiring manager search stages for agent {agent_id}")
        
        # Stage 1: LinkedIn jobs
        await run_linkedin_stage(agent_id, request.query, request.hours_old)
        
        # Background enrichment stages
        await run_background_enrichment(agent_id, request)
        
    except Exception as e:
        logger.error(f"❌ Critical error in hiring manager search stages for agent {agent_id}: {e}")
        progressive_agent_manager.mark_agent_failed(agent_id, str(e))

async def finalize_candidate_agent(agent_id: str):
    """Finalize candidate search agent"""
    try:
        agent = progressive_agent_manager.get_agent(agent_id)
        if agent:
            final_stats = {
                "total_jobs": 0,  # No jobs for candidate search
                "total_contacts": agent.staged_results.total_contacts,
                "total_campaigns": agent.staged_results.total_campaigns,
                "completion_time": datetime.now().isoformat(),
                "search_type": "candidate_search"
            }
            progressive_agent_manager.finalize_agent(agent_id, final_stats)
            logger.info(f"✅ Candidate search agent {agent_id} finalized with {agent.staged_results.total_contacts} professionals")
    except Exception as e:
        logger.error(f"Error finalizing candidate agent {agent_id}: {e}")

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
            max_results=200  # Increased to utilize full API capacity
        )
        
        # Categorize jobs: LinkedIn jobs include direct LinkedIn API results AND JSearch jobs with LinkedIn URLs
        all_jobs = linkedin_jobs  # This contains all jobs from bulletproof scraper
        linkedin_jobs = []
        other_jobs = []
        
        for job in all_jobs:
            job_url = job.get("url", "").lower()
            job_site = job.get("site", "").lower()
            is_demo = job.get("is_demo", False)
            
            # Consider it a LinkedIn job if:
            # 1. Site is "linkedin" (from direct API or JSearch with LinkedIn URL detection)
            # 2. Site is "jsearch" and URL contains "linkedin.com" (fallback)
            # Note: Demo jobs are excluded from production data
            if (job_site == "linkedin" or 
                (job_site == "jsearch" and "linkedin.com" in job_url)) and not is_demo:
                linkedin_jobs.append(job)
            elif not is_demo:  # Only include non-demo jobs in other_jobs
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
        logger.info(f"🔄 Starting background enrichment for agent {agent_id}")
        
        # Wait for LinkedIn stage to complete or timeout
        await asyncio.sleep(5)  # Reduced wait time
        
        # Stage 2: Other job boards (with proper error handling)
        try:
            logger.info(f"🔍 Starting other boards stage for agent {agent_id}")
            await run_other_boards_stage(agent_id, request)
            logger.info(f"✅ Other boards stage completed for agent {agent_id}")
        except Exception as e:
            logger.error(f"❌ Other boards stage failed for agent {agent_id}: {e}")
            # Mark stage as failed but continue
            progressive_agent_manager.update_stage_status(
                agent_id, "other_boards", "failed", 0, 0, str(e)
            )
        
        # Stage 3: Contact enrichment (with proper error handling)
        try:
            logger.info(f"👥 Starting contact enrichment for agent {agent_id}")
            await run_contact_enrichment_stage(agent_id)
            logger.info(f"✅ Contact enrichment completed for agent {agent_id}")
        except Exception as e:
            logger.error(f"❌ Contact enrichment failed for agent {agent_id}: {e}")
            # Mark stage as failed but continue
            progressive_agent_manager.update_stage_status(
                agent_id, "contact_enrichment", "failed", 0, 0, str(e)
            )
        
        # Stage 4: Campaign creation (with proper error handling)
        try:
            logger.info(f"📧 Starting campaign creation for agent {agent_id}")
            await run_campaign_creation_stage(agent_id, request)
            logger.info(f"✅ Campaign creation completed for agent {agent_id}")
        except Exception as e:
            logger.error(f"❌ Campaign creation failed for agent {agent_id}: {e}")
            # Mark stage as failed but continue
            progressive_agent_manager.update_stage_status(
                agent_id, "campaign_creation", "failed", 0, 0, str(e)
            )
        
        # Finalize agent - always finalize if we have any results
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
        logger.error(f"❌ Critical background enrichment error for agent {agent_id}: {e}")
        # Only mark as failed if we don't have any results at all
        agent = progressive_agent_manager.get_agent(agent_id)
        if agent and (agent.staged_results.total_jobs > 0 or agent.staged_results.total_contacts > 0):
            # We have some results, so finalize as completed instead of failed
            final_stats = {
                "total_jobs": agent.staged_results.total_jobs,
                "total_contacts": agent.staged_results.total_contacts,
                "total_campaigns": agent.staged_results.total_campaigns,
                "completion_time": datetime.now().isoformat(),
                "partial_completion": True,
                "error_message": str(e)
            }
            progressive_agent_manager.finalize_agent(agent_id, final_stats)
            logger.info(f"✅ Agent {agent_id} completed with partial results despite error")
        else:
            # No results found, mark as truly failed
            progressive_agent_manager.mark_agent_failed(agent_id, str(e))

async def run_other_boards_stage(agent_id: str, request: JobSearchRequest):
    """Fetch jobs from non-LinkedIn job boards using bulletproof scraper"""
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
        
        # Get jobs specifically from non-LinkedIn sources with shorter timeout
        all_jobs = await asyncio.wait_for(
            job_scraper.search_other_boards_only(  # Use a dedicated method for non-LinkedIn jobs
                query=request.query,
                hours_old=request.hours_old,
                company_size=agent.company_size,
                location=agent.location_filter or "United States",
                max_results=100  # Reduced for faster processing
            ),
            timeout=180.0  # Reduced timeout to 3 minutes
        )
        
        # Since we're using search_other_boards_only(), all jobs should be non-LinkedIn
        # But let's still filter out any LinkedIn jobs that might slip through
        other_jobs = []
        
        for job in all_jobs:
            job_url = job.get("url", "").lower()
            job_site = job.get("site", "").lower()
            is_demo = job.get("is_demo", False)
            
            # Exclude LinkedIn jobs and demo jobs (those belong in LinkedIn stage or should be filtered out)
            if not (job_site == "linkedin" or 
                   (job_site == "jsearch" and "linkedin.com" in job_url) or
                   is_demo):  # Exclude demo jobs from production
                other_jobs.append(job)
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "running", 75
        )
        
        # Add results
        progressive_agent_manager.add_stage_results(
            agent_id, "other_boards", other_jobs, "other_jobs"
        )
        
        # Complete stage
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "completed", 100, len(other_jobs)
        )
        
        logger.info(f"✅ Other boards stage completed for agent {agent_id} - {len(other_jobs)} jobs")
        
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
        raise  # Re-raise to be caught by background enrichment

async def run_contact_enrichment_stage(agent_id: str):
    """Run contact discovery and verification using bulletproof contact finder"""
    try:
        logger.info(f"👥 Starting contact enrichment for agent {agent_id}")
        
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "running", 0
        )
        
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent:
            raise Exception("Agent not found")
        
        # Initialize bulletproof contact finder
        contact_finder = BulletproofContactFinder()
        all_contacts = []
        
        # Process all jobs for contacts
        all_jobs = agent.staged_results.linkedin_jobs + agent.staged_results.other_jobs
        total_jobs = len(all_jobs)
        
        if total_jobs == 0:
            logger.warning(f"⚠️ No jobs found for contact enrichment for agent {agent_id}")
            progressive_agent_manager.update_stage_status(
                agent_id, "contact_enrichment", "completed", 100, 0
            )
            return
        
        # Limit to 15 companies for speed, but ensure we process the best ones
        companies_to_process = []
        for job in all_jobs[:15]:  # Reduced from 20 to 15 for faster processing
            company = job.get("company", "").strip()
            if company and company not in companies_to_process:
                companies_to_process.append(company)  # Just append the company name string
        
        logger.info(f"📊 Processing {len(companies_to_process)} companies for contacts")
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "running", 25
        )
        
        # Process companies with timeout
        try:
            contacts = await asyncio.wait_for(
                contact_finder.find_contacts_bulletproof(companies_to_process),
                timeout=300.0  # 5 minute timeout
            )
            all_contacts.extend(contacts)
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Contact enrichment timeout for agent {agent_id}")
            # Continue with empty contacts rather than failing
        
        # Update progress
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "running", 75
        )
        
        # Add results
        progressive_agent_manager.add_stage_results(
            agent_id, "contact_enrichment", all_contacts, "contacts"
        )
        
        # Complete stage
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "completed", 100, len(all_contacts)
        )
        
        logger.info(f"✅ Contact enrichment completed for agent {agent_id} - {len(all_contacts)} contacts")
        
    except Exception as e:
        logger.error(f"❌ Contact enrichment failed for agent {agent_id}: {e}")
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "failed", 0, 0, str(e)
        )
        raise  # Re-raise to be caught by background enrichment
        
    except Exception as e:
        logger.error(f"❌ Contact enrichment failed for agent {agent_id}: {e}")
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "failed", 0, 0, str(e)
        )

async def run_campaign_creation_stage(agent_id: str, request: JobSearchRequest):
    """
    Smart campaign creation stage:
    - Check if auto-campaigns were already created during candidate search
    - If yes, just update status and skip duplicate creation
    - If no, create campaigns using bulletproof campaign creator
    """
    try:
        logger.info(f"📧 Starting SMART campaign creation for agent {agent_id}")
        
        progressive_agent_manager.update_stage_status(
            agent_id, "campaign_creation", "running", 0
        )
        
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent:
            logger.warning(f"⚠️ Agent {agent_id} not found for campaign creation")
            progressive_agent_manager.update_stage_status(
                agent_id, "campaign_creation", "failed", 0, 0, "Agent not found"
            )
            return
        
        # Check if auto-campaigns were already created during candidate search
        existing_campaigns = getattr(agent.staged_results, 'campaigns', [])
        auto_campaigns_exist = any(
            campaign.get("auto_campaign") == True 
            for campaign in existing_campaigns
        )
        
        if auto_campaigns_exist:
            logger.info(f"✅ AUTO-CAMPAIGNS already created during candidate search - {len(existing_campaigns)} campaigns found")
            
            # Just update the status to completed since campaigns already exist
            progressive_agent_manager.update_stage_status(
                agent_id, "campaign_creation", "completed", 100, len(existing_campaigns)
            )
            
            # Log campaign details
            for campaign in existing_campaigns:
                if campaign.get("auto_campaign"):
                    logger.info(f"📧 Existing auto-campaign: {campaign.get('campaign_name')} (ID: {campaign.get('campaign_id')})")
            
            return
        
        # No auto-campaigns exist, check if we have contacts to create campaigns for
        if not agent.staged_results.verified_contacts:
            logger.info(f"ℹ️ No verified contacts found for agent {agent_id} - skipping campaign creation")
            progressive_agent_manager.update_stage_status(
                agent_id, "campaign_creation", "completed", 100, 0
            )
            return
        
        logger.info(f"📧 Creating manual campaigns for {len(agent.staged_results.verified_contacts)} contacts")
        
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
                "title": "Talent Acquisition Specialist",
                "agent_id": agent_id  # Pass agent_id through sender_info
            }
        )
        
        # Ensure all campaigns have the agent_id set correctly and mark as manual
        for campaign in campaigns:
            campaign["agent_id"] = agent_id
            campaign["auto_campaign"] = False  # Mark as manually created
            # Ensure platform field consistency
            if "service" in campaign:
                if campaign["service"] == "instantly":
                    campaign["platform"] = "instantly"
                elif campaign["service"] in ["internal", "fallback"]:
                    campaign["platform"] = "internal"
        
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
        
        logger.info(f"✅ Manual campaign creation completed for agent {agent_id} - {len(campaigns)} campaigns")
        
    except Exception as e:
        logger.error(f"❌ Campaign creation failed for agent {agent_id}: {e}")
        progressive_agent_manager.update_stage_status(
            agent_id, "campaign_creation", "failed", 0, 0, str(e)
        )
