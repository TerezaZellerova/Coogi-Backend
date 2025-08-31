"""
Progressive Agent Manager - Handles staged agent creation with real-time updates
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from api.models import ProgressiveAgent, AgentStage, StagedResults, ProgressiveAgentResponse
from .progressive_agent_db import progressive_agent_db

logger = logging.getLogger(__name__)

class ProgressiveAgentManager:
    def __init__(self):
        self.active_agents: Dict[str, ProgressiveAgent] = {}
        self.stage_definitions = {
            "linkedin_fetch": {
                "name": "LinkedIn Job Fetching",
                "timeout": 180,  # 3 minutes max
                "weight": 40  # 40% of total progress
            },
            "other_boards": {
                "name": "Other Job Boards",
                "timeout": 300,  # 5 minutes max
                "weight": 30  # 30% of total progress
            },
            "contact_enrichment": {
                "name": "Contact Discovery & Verification",
                "timeout": 600,  # 10 minutes max
                "weight": 20  # 20% of total progress
            },
            "campaign_creation": {
                "name": "Campaign Creation",
                "timeout": 120,  # 2 minutes max
                "weight": 10  # 10% of total progress
            }
        }
    
    def create_progressive_agent(self, query: str, hours_old: int = 24, custom_tags: Optional[List[str]] = None, target_type: str = "hiring_managers", company_size: str = "all", location_filter: Optional[str] = None) -> ProgressiveAgent:
        """Create a new progressive agent with initial stages"""
        agent_id = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Initialize stages
        stages = {}
        for stage_key, stage_config in self.stage_definitions.items():
            stages[stage_key] = AgentStage(
                name=stage_config["name"],
                status="pending",
                progress=0
            )
        
        agent = ProgressiveAgent(
            id=agent_id,
            query=query,
            status="initializing",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            total_progress=0,
            stages=stages,
            staged_results=StagedResults(),
            hours_old=hours_old,
            custom_tags=custom_tags,
            target_type=target_type,
            company_size=company_size,
            location_filter=location_filter
        )
        
        self.active_agents[agent_id] = agent
        
        # Save to database
        asyncio.create_task(progressive_agent_db.save_agent_metadata(
            agent_id=agent_id,
            query=query,
            status="initializing",
            hours_old=hours_old,
            custom_tags=custom_tags or [],
            total_progress=0,
            target_type=target_type,
            company_size=company_size,
            location_filter=location_filter
        ))
        
        logger.info(f"🚀 Created progressive agent: {agent_id} (target: {target_type}, size: {company_size})")
        return agent
    
    def update_stage_status(self, agent_id: str, stage_key: str, status: str, progress: int = 0, results_count: int = 0, error_message: Optional[str] = None):
        """Update the status of a specific stage"""
        if agent_id not in self.active_agents:
            logger.warning(f"Agent {agent_id} not found for stage update")
            return
        
        agent = self.active_agents[agent_id]
        if stage_key not in agent.stages:
            logger.warning(f"Stage {stage_key} not found for agent {agent_id}")
            return
        
        stage = agent.stages[stage_key]
        stage.status = status
        stage.progress = progress
        stage.results_count = results_count
        stage.error_message = error_message
        
        if status == "running" and stage.started_at is None:
            stage.started_at = datetime.now().isoformat()
        elif status in ["completed", "failed"]:
            stage.completed_at = datetime.now().isoformat()
        
        # Update overall progress
        self._calculate_total_progress(agent_id)
        agent.updated_at = datetime.now().isoformat()
        
        logger.info(f"📊 Agent {agent_id} - Stage {stage_key}: {status} ({progress}%)")
    
    def add_stage_results(self, agent_id: str, stage_key: str, results: List[Dict], result_type: str):
        """Add results from a specific stage"""
        if agent_id not in self.active_agents:
            return
        
        agent = self.active_agents[agent_id]
        
        if result_type == "linkedin_jobs":
            agent.staged_results.linkedin_jobs.extend(results)
            # Save jobs to database
            asyncio.create_task(self._save_jobs_safely(agent_id, results))
        elif result_type == "other_jobs":
            agent.staged_results.other_jobs.extend(results)
            # Save jobs to database
            asyncio.create_task(self._save_jobs_safely(agent_id, results))
        elif result_type == "contacts":
            agent.staged_results.verified_contacts.extend(results)
            # Save contacts to database
            asyncio.create_task(self._save_contacts_safely(agent_id, results))
        elif result_type == "campaigns":
            agent.staged_results.campaigns.extend(results)
            # Save campaigns to database
            asyncio.create_task(self._save_campaigns_safely(agent_id, results))
        
        # Update totals
        agent.staged_results.total_jobs = len(agent.staged_results.linkedin_jobs) + len(agent.staged_results.other_jobs)
        agent.staged_results.total_contacts = len(agent.staged_results.verified_contacts)
        agent.staged_results.total_campaigns = len(agent.staged_results.campaigns)
        
        # Update stage results count
        if stage_key in agent.stages:
            agent.stages[stage_key].results_count = len(results)
        
        agent.updated_at = datetime.now().isoformat()
        
        # Update agent metadata in database
        asyncio.create_task(progressive_agent_db.save_agent_metadata(
            agent_id=agent_id,
            query=agent.query,
            status=agent.status,
            total_progress=agent.total_progress,
            total_jobs=agent.staged_results.total_jobs,
            total_contacts=agent.staged_results.total_contacts,
            total_campaigns=agent.staged_results.total_campaigns
        ))
        
        logger.info(f"➕ Agent {agent_id} - Added {len(results)} {result_type} from {stage_key}")
    
    def _calculate_total_progress(self, agent_id: str):
        """Calculate total progress based on stage weights"""
        agent = self.active_agents[agent_id]
        total_progress = 0
        
        for stage_key, stage in agent.stages.items():
            if stage_key in self.stage_definitions:
                weight = self.stage_definitions[stage_key]["weight"]
                stage_progress = stage.progress / 100
                total_progress += weight * stage_progress
        
        agent.total_progress = int(total_progress)
        
        # Update overall status with improved logic
        if agent.total_progress == 100:
            agent.status = "completed"
        else:
            # Check if critical stages failed
            critical_stages = ["linkedin_fetch"]  # Only LinkedIn stage is truly critical
            critical_failed = all(
                agent.stages[stage].status == "failed" 
                for stage in critical_stages 
                if stage in agent.stages
            )
            
            # Check if we have enough data to consider it successful
            total_jobs = sum(stage.results_count for stage in agent.stages.values() if stage.results_count)
            
            if critical_failed and total_jobs == 0:
                # Only mark as failed if critical stages failed AND we have no results
                agent.status = "failed"
            elif total_jobs > 0:
                # We have some results, consider it successful even if some stages are incomplete
                if agent.total_progress >= 80:  # If we're 80% done and have results, call it completed
                    agent.status = "completed"
                    agent.total_progress = 100
                else:
                    agent.status = "enrichment_stage"
            elif any(stage.status == "running" for stage in agent.stages.values()):
                if agent.stages["linkedin_fetch"].status in ["completed", "failed"]:
                    agent.status = "enrichment_stage"
                else:
                    agent.status = "linkedin_stage"
            else:
                # Default to enrichment stage if stages are done but not failed
                agent.status = "enrichment_stage"
    
    def get_agent(self, agent_id: str) -> Optional[ProgressiveAgent]:
        """Get an agent by ID"""
        return self.active_agents.get(agent_id)
    
    def get_all_agents(self) -> List[ProgressiveAgent]:
        """Get all active agents"""
        return list(self.active_agents.values())
    
    def mark_agent_failed(self, agent_id: str, error_message: str):
        """Mark an agent as failed with error message"""
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            agent.status = "failed"
            agent.updated_at = datetime.now().isoformat()
            
            # Mark any running stages as failed
            for stage in agent.stages.values():
                if stage.status == "running":
                    stage.status = "failed"
                    stage.error_message = error_message
                    stage.completed_at = datetime.now().isoformat()
            
            # Update in database
            asyncio.create_task(progressive_agent_db.save_agent_metadata(
                agent_id=agent_id,
                query=agent.query,
                status="failed",
                total_progress=agent.total_progress
            ))
            
            logger.error(f"❌ Agent {agent_id} marked as failed: {error_message}")
    
    def finalize_agent(self, agent_id: str, final_stats: Dict):
        """Finalize an agent with final statistics"""
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            agent.final_stats = final_stats
            agent.status = "completed"
            agent.total_progress = 100
            agent.updated_at = datetime.now().isoformat()
            
            # Update in database
            asyncio.create_task(progressive_agent_db.save_agent_metadata(
                agent_id=agent_id,
                query=agent.query,
                status="completed",
                total_progress=100,
                total_jobs=agent.staged_results.total_jobs,
                total_contacts=agent.staged_results.total_contacts,
                total_campaigns=agent.staged_results.total_campaigns,
                completed_at=datetime.now().isoformat()
            ))
            
            # Also save to memory manager for dashboard stats
            from utils.memory_manager import get_memory_manager
            memory_manager = get_memory_manager()
            
            agent_data = {
                "batch_id": agent_id,
                "query": agent.query,
                "status": "completed",
                "start_time": agent.created_at,
                "end_time": agent.updated_at,
                "total_jobs_found": agent.staged_results.total_jobs,
                "total_jobs": agent.staged_results.total_jobs,  # Also set this for compatibility
                "total_emails_found": agent.staged_results.total_contacts,
                "total_contacts": agent.staged_results.total_contacts,
                "total_campaigns": agent.staged_results.total_campaigns,
                "jobs_found": agent.staged_results.total_jobs,  # Alternative field name
                "final_stats": final_stats,
                "hours_old": getattr(agent, 'hours_old', 24),
                "custom_tags": getattr(agent, 'custom_tags', None),
                "target_type": getattr(agent, 'target_type', 'hiring_managers'),
                "company_size": getattr(agent, 'company_size', 'all'),
                "location_filter": getattr(agent, 'location_filter', None)
            }
            
            memory_manager.save_agent_data(agent_id, agent_data)
            
            logger.info(f"✅ Agent {agent_id} finalized with stats: {final_stats}")
            logger.info(f"💾 Agent {agent_id} saved to memory manager with {agent.staged_results.total_jobs} jobs")
    
    async def _save_jobs_safely(self, agent_id: str, jobs: List[Dict[str, Any]]):
        """Safely save jobs to database with error handling"""
        try:
            await progressive_agent_db.save_jobs(agent_id, jobs)
            logger.info(f"💼 Saved {len(jobs)} jobs for agent {agent_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save jobs for agent {agent_id}: {e}")
    
    async def _save_contacts_safely(self, agent_id: str, contacts: List[Dict[str, Any]]):
        """Safely save contacts to database with error handling"""
        try:
            await progressive_agent_db.save_contacts(agent_id, contacts)
            logger.info(f"👥 Saved {len(contacts)} contacts for agent {agent_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save contacts for agent {agent_id}: {e}")
    
    async def _save_campaigns_safely(self, agent_id: str, campaigns: List[Dict[str, Any]]):
        """Safely save campaigns to database with error handling"""
        try:
            await progressive_agent_db.save_campaigns(agent_id, campaigns)
            logger.info(f"📧 Saved {len(campaigns)} campaigns for agent {agent_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save campaigns for agent {agent_id}: {e}")

# Global instance
progressive_agent_manager = ProgressiveAgentManager()
