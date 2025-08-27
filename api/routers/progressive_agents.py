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
            custom_tags=request.custom_tags
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
    """Run the LinkedIn fast fetch stage"""
    try:
        logger.info(f"🔍 Starting LinkedIn stage for agent {agent_id}")
        
        # Update stage status
        progressive_agent_manager.update_stage_status(
            agent_id, "linkedin_fetch", "running", 0
        )
        
        # Initialize LinkedIn scraper
        linkedin_scraper = LinkedInFastScraper()
        
        # Fetch LinkedIn jobs with progress updates
        progressive_agent_manager.update_stage_status(
            agent_id, "linkedin_fetch", "running", 25
        )
        
        linkedin_jobs = await linkedin_scraper.fetch_linkedin_jobs_fast(
            query=query,
            hours_old=hours_old,
            max_results=30
        )
        
        # Add results
        progressive_agent_manager.add_stage_results(
            agent_id, "linkedin_fetch", linkedin_jobs, "linkedin_jobs"
        )
        
        # Complete stage
        progressive_agent_manager.update_stage_status(
            agent_id, "linkedin_fetch", "completed", 100, len(linkedin_jobs)
        )
        
        logger.info(f"✅ LinkedIn stage completed for agent {agent_id} - {len(linkedin_jobs)} jobs")
        
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
    """Fetch jobs from other job boards"""
    try:
        logger.info(f"🔍 Starting other boards stage for agent {agent_id}")
        
        progressive_agent_manager.update_stage_status(
            agent_id, "other_boards", "running", 0
        )
        
        # Use existing job scraper for other boards
        job_scraper = get_job_scraper()
        
        # Get jobs from other sources (with timeout)
        other_jobs = await asyncio.wait_for(
            job_scraper.search_jobs_basic(
                query=request.query,
                limit=50,
                hours_old=request.hours_old,
                exclude_linkedin=True  # We already have LinkedIn jobs
            ),
            timeout=300.0  # 5 minute timeout
        )
        
        # Filter out LinkedIn jobs if any
        other_jobs = [job for job in other_jobs if job.get("site", "").lower() != "linkedin"]
        
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

async def run_contact_enrichment_stage(agent_id: str):
    """Run contact discovery and verification"""
    try:
        logger.info(f"👥 Starting contact enrichment for agent {agent_id}")
        
        progressive_agent_manager.update_stage_status(
            agent_id, "contact_enrichment", "running", 0
        )
        
        agent = progressive_agent_manager.get_agent(agent_id)
        if not agent:
            return
        
        contact_finder = get_contact_finder()
        all_contacts = []
        
        # Process all jobs for contacts
        all_jobs = agent.staged_results.linkedin_jobs + agent.staged_results.other_jobs
        total_jobs = len(all_jobs)
        
        for i, job in enumerate(all_jobs[:20]):  # Limit to 20 companies for speed
            try:
                # Find contacts for this company
                contacts = await contact_finder.find_contacts_for_company(
                    company=job.get("company", ""),
                    job_title=job.get("title", "")
                )
                
                if contacts.get("verified_emails"):
                    all_contacts.extend(contacts["verified_emails"])
                
                # Update progress
                progress = int((i + 1) / min(total_jobs, 20) * 100)
                progressive_agent_manager.update_stage_status(
                    agent_id, "contact_enrichment", "running", progress
                )
                
            except Exception as contact_error:
                logger.error(f"Error finding contacts for {job.get('company')}: {contact_error}")
                continue
        
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

async def run_campaign_creation_stage(agent_id: str, request: JobSearchRequest):
    """Create campaigns from verified contacts"""
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
        
        # Create campaigns (simplified for now)
        campaigns = [{
            "id": f"campaign_{agent_id}",
            "name": f"Campaign for {request.query}",
            "contacts_count": len(agent.staged_results.verified_contacts),
            "created_at": datetime.now().isoformat()
        }]
        
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
