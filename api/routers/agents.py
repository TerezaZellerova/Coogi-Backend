from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging

from ..dependencies import get_current_user, get_memory_manager

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
        total_jobs = sum(agent.get('total_jobs_found', 0) for agent in agent_data)
        
        # Calculate success rate based on completed vs failed
        completed = len([agent for agent in agent_data if agent.get('status') == 'completed'])
        failed = len([agent for agent in agent_data if agent.get('status') == 'failed'])
        success_rate = (completed / (completed + failed)) * 100 if (completed + failed) > 0 else 100
        
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
