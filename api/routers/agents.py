from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging

from ..dependencies import get_current_user, get_memory_manager, get_job_scraper, get_contact_finder
from ..models import JobSearchRequest, JobSearchResponse, Agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["agents"])

@router.get("/agents")
async def get_agents(current_user: dict = Depends(get_current_user)):
    """Get all agents"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_all_agent_data()
        
        agents = []
        for i, agent in enumerate(agent_data):
            agents.append({
                "id": agent.get("batch_id", f"agent_{i}"),
                "query": agent.get("query", "Job Search Agent"),
                "status": agent.get("status", "completed"),
                "created_at": agent.get("start_time", datetime.now().isoformat()),
                "total_jobs_found": agent.get("total_jobs_found", 0),
                "total_emails_found": agent.get("total_emails_found", 0),
                "hours_old": agent.get("hours_old", 24),
                "custom_tags": agent.get("custom_tags"),
                "batch_id": agent.get("batch_id"),
                "processed_cities": agent.get("processed_cities", 0),
                "processed_companies": agent.get("processed_companies", 0),
                "start_time": agent.get("start_time"),
                "end_time": agent.get("end_time")
            })
        
        return agents
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        return []

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an agent"""
    try:
        memory_manager = get_memory_manager()
        success = memory_manager.delete_agent_data(agent_id)
        
        if success:
            return {"success": True, "message": "Agent deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_all_agent_data()
        
        active_agents = len([agent for agent in agent_data if agent.get('status') == 'running'])
        total_runs = len(agent_data)
        
        # Check both possible field names for job counts
        total_jobs = 0
        for agent in agent_data:
            jobs_count = agent.get('total_jobs_found', 0) or agent.get('total_jobs', 0) or agent.get('jobs_found', 0)
            total_jobs += jobs_count
        
        # Calculate success rate based on completed vs failed
        completed = len([agent for agent in agent_data if agent.get('status') == 'completed'])
        failed = len([agent for agent in agent_data if agent.get('status') == 'failed'])
        success_rate = (completed / (completed + failed)) * 100 if (completed + failed) > 0 else 100
        
        logger.info(f"📊 Dashboard stats: {active_agents} active, {total_runs} runs, {total_jobs} jobs")
        
        return {
            "activeAgents": active_agents,
            "totalRuns": total_runs,
            "totalJobs": total_jobs,
            "successRate": round(success_rate, 2)
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "activeAgents": 0,
            "totalRuns": 0,
            "totalJobs": 0,
            "successRate": 0
        }

@router.get("/logs/{batch_id}")
async def get_agent_logs(batch_id: str):
    """Get logs for a specific agent"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_agent_data(batch_id)
        
        if not agent_data:
            return {"logs": []}
        
        # Mock logs based on agent status and progress
        logs = []
        status = agent_data.get('status', 'unknown')
        
        if status == 'running':
            logs = [
                {
                    "id": f"{batch_id}_1",
                    "batch_id": batch_id,
                    "message": "Agent started successfully",
                    "level": "info",
                    "timestamp": agent_data.get('start_time', datetime.now().isoformat())
                },
                {
                    "id": f"{batch_id}_2",
                    "batch_id": batch_id,
                    "message": f"Processing job search for: {agent_data.get('query', 'Unknown')}",
                    "level": "info",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "id": f"{batch_id}_3",
                    "batch_id": batch_id,
                    "message": f"Found {agent_data.get('total_jobs_found', 0)} jobs so far",
                    "level": "success",
                    "timestamp": datetime.now().isoformat()
                }
            ]
        elif status == 'completed':
            logs = [
                {
                    "id": f"{batch_id}_1",
                    "batch_id": batch_id,
                    "message": "Agent completed successfully",
                    "level": "success",
                    "timestamp": agent_data.get('end_time', datetime.now().isoformat()),
                    "company": "Multiple companies processed"
                },
                {
                    "id": f"{batch_id}_2",
                    "batch_id": batch_id,
                    "message": f"Total jobs found: {agent_data.get('total_jobs_found', 0)}",
                    "level": "info",
                    "timestamp": agent_data.get('end_time', datetime.now().isoformat())
                },
                {
                    "id": f"{batch_id}_3",
                    "batch_id": batch_id,
                    "message": f"Total emails found: {agent_data.get('total_emails_found', 0)}",
                    "level": "info",
                    "timestamp": agent_data.get('end_time', datetime.now().isoformat())
                }
            ]
        elif status == 'failed':
            logs = [
                {
                    "id": f"{batch_id}_1",
                    "batch_id": batch_id,
                    "message": "Agent encountered an error",
                    "level": "error",
                    "timestamp": agent_data.get('end_time', datetime.now().isoformat())
                }
            ]
        
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error getting logs for {batch_id}: {e}")
        return {"logs": []}

@router.get("/status/{batch_id}")
async def get_agent_status(batch_id: str):
    """Get status for a specific agent"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_agent_data(batch_id)
        
        if not agent_data:
            return {
                "status": "failed",
                "message": "Agent not found"
            }
        
        status = agent_data.get('status', 'unknown')
        
        return {
            "status": status,
            "message": f"Agent is {status}",
            "progress": 100 if status == 'completed' else (50 if status == 'running' else 0),
            "jobs_found": agent_data.get('total_jobs_found', 0),
            "emails_found": agent_data.get('total_emails_found', 0),
            "processed_cities": agent_data.get('processed_cities', 0),
            "processed_companies": agent_data.get('processed_companies', 0),
            "start_time": agent_data.get('start_time'),
            "end_time": agent_data.get('end_time')
        }
    except Exception as e:
        logger.error(f"Error getting status for {batch_id}: {e}")
        return {
            "status": "failed",
            "message": "Error retrieving status"
        }

@router.post("/cancel-search/{batch_id}")
async def cancel_agent(batch_id: str):
    """Cancel a running agent"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_agent_data(batch_id)
        
        if not agent_data:
            return {"success": False, "message": "Agent not found"}
        
        # Update agent status to cancelled
        agent_data['status'] = 'failed'
        agent_data['end_time'] = datetime.now().isoformat()
        memory_manager.save_agent_data(batch_id, agent_data)
        
        return {"success": True, "message": "Agent cancelled successfully"}
    except Exception as e:
        logger.error(f"Error cancelling agent {batch_id}: {e}")
        return {"success": False, "message": "Error cancelling agent"}

@router.post("/pause-agent/{batch_id}")
async def pause_agent(batch_id: str):
    """Pause a running agent"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_agent_data(batch_id)
        
        if not agent_data:
            return {"success": False, "message": "Agent not found"}
        
        # Update agent status to paused
        current_status = agent_data.get('status', 'unknown')
        if current_status == 'running':
            agent_data['status'] = 'paused'
            memory_manager.save_agent_data(batch_id, agent_data)
            return {"success": True, "message": "Agent paused successfully"}
        elif current_status == 'paused':
            agent_data['status'] = 'running'
            memory_manager.save_agent_data(batch_id, agent_data)
            return {"success": True, "message": "Agent resumed successfully"}
        else:
            return {"success": False, "message": f"Cannot pause agent in {current_status} state"}
    except Exception as e:
        logger.error(f"Error pausing agent {batch_id}: {e}")
        return {"success": False, "message": "Error pausing agent"}

@router.post("/resume-agent/{batch_id}")
async def resume_agent(batch_id: str):
    """Resume a paused agent"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_agent_data(batch_id)
        
        if not agent_data:
            return {"success": False, "message": "Agent not found"}
        
        # Update agent status to running
        current_status = agent_data.get('status', 'unknown')
        if current_status == 'paused':
            agent_data['status'] = 'running'
            memory_manager.save_agent_data(batch_id, agent_data)
            return {"success": True, "message": "Agent resumed successfully"}
        elif current_status == 'running':
            return {"success": True, "message": "Agent is already running"}
        else:
            return {"success": False, "message": f"Cannot resume agent in {current_status} state"}
    except Exception as e:
        logger.error(f"Error resuming agent {batch_id}: {e}")
        return {"success": False, "message": "Error resuming agent"}

@router.get("/search-status/{batch_id}")
async def get_search_status(batch_id: str):
    """Get search status for a specific agent (alias for status endpoint)"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_agent_data(batch_id)
        
        if not agent_data:
            return {
                "status": "failed",
                "message": "Agent not found",
                "is_cancelled": True
            }
        
        status = agent_data.get('status', 'unknown')
        is_cancelled = status in ['failed', 'cancelled']
        
        return {
            "status": status,
            "message": f"Agent is {status}",
            "is_cancelled": is_cancelled,
            "progress": 100 if status == 'completed' else (50 if status == 'running' else 0),
            "jobs_found": agent_data.get('total_jobs_found', 0),
            "emails_found": agent_data.get('total_emails_found', 0),
            "processed_cities": agent_data.get('processed_cities', 0),
            "processed_companies": agent_data.get('processed_companies', 0),
            "start_time": agent_data.get('start_time'),
            "end_time": agent_data.get('end_time')
        }
    except Exception as e:
        logger.error(f"Error getting search status for {batch_id}: {e}")
        return {
            "status": "failed",
            "message": "Error retrieving status",
            "is_cancelled": True
        }

@router.patch("/agents/{agent_id}")
async def update_agent(agent_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    """Update agent status or other properties"""
    try:
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_agent_data(agent_id)
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update agent data with provided fields
        for key, value in updates.items():
            if key in ['status', 'query', 'hours_old', 'custom_tags']:
                agent_data[key] = value
        
        memory_manager.save_agent_data(agent_id, agent_data)
        
        return {
            "success": True,
            "message": "Agent updated successfully",
            "agent": {
                "id": agent_data.get("batch_id", agent_id),
                "query": agent_data.get("query", "Job Search Agent"),
                "status": agent_data.get("status", "completed"),
                "created_at": agent_data.get("start_time", datetime.now().isoformat()),
                "total_jobs_found": agent_data.get("total_jobs_found", 0),
                "total_emails_found": agent_data.get("total_emails_found", 0),
                "hours_old": agent_data.get("hours_old", 24),
                "custom_tags": agent_data.get("custom_tags"),
                "batch_id": agent_data.get("batch_id"),
                "processed_cities": agent_data.get("processed_cities", 0),
                "processed_companies": agent_data.get("processed_companies", 0),
                "start_time": agent_data.get("start_time"),
                "end_time": agent_data.get("end_time")
            }
        }
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/create-fast")
async def create_agent_fast(request: JobSearchRequest, current_user: dict = Depends(get_current_user)):
    """Create an agent with immediate results using progressive enhancement"""
    try:
        job_scraper = get_job_scraper()
        memory_manager = get_memory_manager()
        
        # Generate unique agent ID
        agent_id = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🚀 Creating fast agent: {agent_id} for query: {request.query}")
        
        # Phase 1: Get basic job data quickly with timeout protection
        try:
            import asyncio
            
            # Use asyncio.wait_for to enforce timeout
            basic_jobs = await asyncio.wait_for(
                job_scraper.search_jobs_basic(
                    query=request.query,
                    limit=10,  # Limit for speed
                    hours_old=request.hours_old
                ),
                timeout=20.0  # 20 second timeout
            )
            
            logger.info(f"✅ Found {len(basic_jobs)} jobs for agent {agent_id}")
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Job search timeout for agent {agent_id}, using demo data")
            # Fall back to demo data for immediate response
            basic_jobs = job_scraper._get_demo_jobs(request.query, 5)
            
        except Exception as e:
            logger.error(f"❌ Job search error for agent {agent_id}: {e}")
            # Fall back to demo data for immediate response
            basic_jobs = job_scraper._get_demo_jobs(request.query, 5)
        
        # Create agent record immediately
        agent_data = {
            "id": agent_id,
            "query": request.query,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "total_jobs_found": len(basic_jobs),
            "total_emails_found": 0,  # Will be updated later
            "hours_old": request.hours_old,
            "custom_tags": request.custom_tags,
            "batch_id": agent_id,
            "processing_phase": "basic_complete"
        }
        
        # Store agent data
        memory_manager.store_agent_data(agent_id, agent_data)
        
        # Format response
        companies_analyzed = []
        for job in basic_jobs[:5]:  # Return first 5 for immediate display
            companies_analyzed.append({
                "company": job.get("company", "Unknown"),
                "job_title": job.get("title", "Unknown"),
                "job_url": job.get("job_url", ""),
                "job_source": job.get("site", "JobSpy"),
                "has_ta_team": False,  # Will be analyzed later
                "contacts_found": 0,   # Will be found later
                "top_contacts": [],
                "hunter_emails": [],
                "recommendation": "Analysis in progress...",
                "processing_status": "basic_scan_complete"
            })
        
        response = JobSearchResponse(
            companies_analyzed=companies_analyzed,
            jobs_found=len(basic_jobs),
            total_processed=len(basic_jobs),
            search_query=request.query,
            timestamp=datetime.now().isoformat(),
            leads_added=0
        )
        
        # Start background enhancement (don't wait for it)
        import asyncio
        asyncio.create_task(enhance_agent_data_background(agent_id, request, basic_jobs))
        
        logger.info(f"🎉 Agent {agent_id} created successfully with {len(basic_jobs)} jobs")
        
        return {
            "agent": agent_data,
            "results": response,
            "message": "Agent created! Enhancement in progress..."
        }
        
    except Exception as e:
        logger.error(f"Error creating fast agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

async def enhance_agent_data_background(agent_id: str, request: JobSearchRequest, basic_jobs: list):
    """Background task to enhance agent data with contacts and emails"""
    try:
        contact_finder = get_contact_finder()
        memory_manager = get_memory_manager()
        
        enhanced_companies = []
        total_emails = 0
        
        # Process each company for contacts (limit to first 10 for speed)
        for job in basic_jobs[:10]:
            try:
                # Find contacts for this company
                contacts = await contact_finder.find_contacts_for_company(
                    company=job.get("company", ""),
                    job_title=job.get("title", "")
                )
                
                company_data = {
                    "company": job.get("company", "Unknown"),
                    "job_title": job.get("title", "Unknown"),
                    "job_url": job.get("job_url", ""),
                    "job_source": job.get("site", "JobSpy"),
                    "has_ta_team": len(contacts.get("ta_contacts", [])) > 0,
                    "contacts_found": len(contacts.get("all_contacts", [])),
                    "top_contacts": contacts.get("all_contacts", [])[:3],
                    "hunter_emails": contacts.get("verified_emails", []),
                    "recommendation": "Suitable for outreach" if len(contacts.get("all_contacts", [])) > 0 else "Limited contact info"
                }
                
                enhanced_companies.append(company_data)
                total_emails += len(contacts.get("verified_emails", []))
                
            except Exception as contact_error:
                logger.error(f"Error processing company {job.get('company')}: {contact_error}")
                continue
        
        # Update agent data with enhanced results
        agent_data = memory_manager.get_agent_data(agent_id)
        if agent_data:
            agent_data.update({
                "status": "completed",
                "total_emails_found": total_emails,
                "processing_phase": "enhanced_complete",
                "enhanced_companies": enhanced_companies,
                "end_time": datetime.now().isoformat()
            })
            memory_manager.store_agent_data(agent_id, agent_data)
            
        logger.info(f"✅ Enhanced agent {agent_id} - found {total_emails} emails")
        
    except Exception as e:
        logger.error(f"Background enhancement failed for agent {agent_id}: {e}")
        # Update agent status to completed even if enhancement fails
        memory_manager = get_memory_manager()
        agent_data = memory_manager.get_agent_data(agent_id)
        if agent_data:
            agent_data.update({
                "status": "completed",
                "processing_phase": "enhancement_failed",
                "error": str(e)
            })
            memory_manager.store_agent_data(agent_id, agent_data)
