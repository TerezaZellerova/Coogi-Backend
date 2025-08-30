"""
Progressive Agent Database Manager - Handles persistence of agent results to Supabase
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Use service role key for write operations, fallback to anon key
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    key_type = "SERVICE_ROLE" if SUPABASE_SERVICE_ROLE_KEY else "ANON"
    logger.info(f"✅ Supabase client initialized for progressive agents (using {key_type} key)")
else:
    supabase = None
    logger.warning("❌ Supabase credentials not found - database persistence disabled")

class ProgressiveAgentDB:
    """Manages database operations for progressive agents"""
    
    def __init__(self):
        self.supabase = supabase
    
    async def save_agent_metadata(self, agent_id: str, query: str, status: str, **kwargs):
        """Save or update agent metadata"""
        if not self.supabase:
            logger.warning("No Supabase client - skipping agent metadata save")
            return
        
        try:
            agent_data = {
                "agent_id": agent_id,
                "query": query,
                "status": status,
                "updated_at": datetime.now().isoformat(),
                **kwargs
            }
            
            # Try to update first, if not exists then insert
            result = self.supabase.table("progressive_agents").select("id").eq("agent_id", agent_id).execute()
            
            if result.data:
                # Update existing
                self.supabase.table("progressive_agents").update(agent_data).eq("agent_id", agent_id).execute()
                logger.info(f"📊 Updated agent metadata: {agent_id}")
            else:
                # Insert new
                agent_data["created_at"] = datetime.now().isoformat()
                self.supabase.table("progressive_agents").insert(agent_data).execute()
                logger.info(f"📊 Created agent metadata: {agent_id}")
                
        except Exception as e:
            logger.error(f"❌ Error saving agent metadata for {agent_id}: {e}")
    
    async def save_jobs(self, agent_id: str, jobs: List[Dict[str, Any]]):
        """Save jobs to database"""
        if not self.supabase:
            logger.warning("No Supabase client - skipping job save")
            return
            
        if not jobs:
            logger.info(f"No jobs to save for agent {agent_id}")
            return
        
        try:
            job_records = []
            for job in jobs:
                job_record = {
                    "agent_id": agent_id,
                    "job_id": job.get("id"),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location"),
                    "url": job.get("url"),
                    "description": job.get("description", "")[:1000],  # Truncate for db
                    "posted_date": job.get("posted_date"),
                    "employment_type": job.get("employment_type"),
                    "experience_level": job.get("experience_level"),
                    "salary": job.get("salary"),
                    "site": job.get("site", "LinkedIn"),
                    "company_url": job.get("company_url"),
                    "is_remote": job.get("is_remote", False),
                    "skills": job.get("skills", []),
                    "is_demo": job.get("is_demo", False),
                    "scraped_at": job.get("scraped_at", datetime.now().isoformat()),
                    "created_at": datetime.now().isoformat()
                }
                job_records.append(job_record)
            
            # Batch insert jobs
            logger.info(f"💼 Attempting to save {len(job_records)} jobs for agent {agent_id}")
            result = self.supabase.table("progressive_agent_jobs").insert(job_records).execute()
            
            if result.data:
                logger.info(f"✅ Successfully saved {len(result.data)} jobs for agent {agent_id}")
            else:
                logger.warning(f"⚠️ No data returned after saving jobs for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"❌ Error saving jobs for agent {agent_id}: {e}")
            logger.error(f"   First job sample: {jobs[0] if jobs else 'No jobs'}")
            import traceback
            traceback.print_exc()
    
    async def save_contacts(self, agent_id: str, contacts: List[Dict[str, Any]]):
        """Save contacts to database"""
        if not self.supabase:
            logger.warning("No Supabase client - skipping contact save")
            return
            
        if not contacts:
            logger.info(f"No contacts to save for agent {agent_id}")
            return
        
        try:
            contact_records = []
            for contact in contacts:
                contact_record = {
                    "agent_id": agent_id,
                    "contact_id": contact.get("id"),
                    "name": contact.get("name"),
                    "first_name": contact.get("first_name"),
                    "last_name": contact.get("last_name"),
                    "email": contact.get("email"),
                    "company": contact.get("company"),
                    "role": contact.get("role"),
                    "title": contact.get("title"),
                    "linkedin_url": contact.get("linkedin_url"),
                    "phone": contact.get("phone"),
                    "verified": bool(contact.get("email")),
                    "source": contact.get("source", "Hunter"),
                    "confidence_score": contact.get("confidence_score"),
                    "created_at": datetime.now().isoformat()
                }
                contact_records.append(contact_record)
            
            # Batch insert contacts
            logger.info(f"👥 Attempting to save {len(contact_records)} contacts for agent {agent_id}")
            result = self.supabase.table("progressive_agent_contacts").insert(contact_records).execute()
            
            if result.data:
                logger.info(f"✅ Successfully saved {len(result.data)} contacts for agent {agent_id}")
            else:
                logger.warning(f"⚠️ No data returned after saving contacts for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"❌ Error saving contacts for agent {agent_id}: {e}")
            logger.error(f"   First contact sample: {contacts[0] if contacts else 'No contacts'}")
            import traceback
            traceback.print_exc()
    
    async def save_campaigns(self, agent_id: str, campaigns: List[Dict[str, Any]]):
        """Save campaigns to database"""
        if not self.supabase or not campaigns:
            return
        
        try:
            campaign_records = []
            for campaign in campaigns:
                campaign_record = {
                    "agent_id": agent_id,
                    "campaign_id": campaign.get("id"),
                    "name": campaign.get("name", ""),
                    "type": campaign.get("type", "Email Campaign"),
                    "status": campaign.get("status", "Ready"),
                    "subject": campaign.get("subject"),
                    "content": campaign.get("content"),
                    "target_count": campaign.get("target_count", 0),
                    "sent_count": campaign.get("sent_count", 0),
                    "open_count": campaign.get("open_count", 0),
                    "reply_count": campaign.get("reply_count", 0),
                    "platform": campaign.get("platform", "Instantly"),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                campaign_records.append(campaign_record)
            
            # Batch insert campaigns
            self.supabase.table("progressive_agent_campaigns").insert(campaign_records).execute()
            logger.info(f"📧 Saved {len(campaign_records)} campaigns for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"❌ Error saving campaigns for agent {agent_id}: {e}")
    
    async def get_agent_jobs(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs from database"""
        if not self.supabase:
            return []
        
        try:
            query = self.supabase.table("progressive_agent_jobs").select("*").order("created_at", desc=True).limit(limit)
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting jobs: {e}")
            return []
    
    async def get_agent_contacts(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get contacts from database"""
        if not self.supabase:
            return []
        
        try:
            query = self.supabase.table("progressive_agent_contacts").select("*").order("created_at", desc=True).limit(limit)
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting contacts: {e}")
            return []
    
    async def get_agent_campaigns(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get campaigns from database"""
        if not self.supabase:
            return []
        
        try:
            query = self.supabase.table("progressive_agent_campaigns").select("*").order("created_at", desc=True).limit(limit)
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting campaigns: {e}")
            return []
    
    async def get_all_agents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all progressive agents"""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table("progressive_agents").select("*").order("created_at", desc=True).limit(limit).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting agents: {e}")
            return []
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        if not self.supabase:
            return {"total_jobs": 0, "total_contacts": 0, "total_campaigns": 0, "active_agents": 0}
        
        try:
            # Get counts from each table
            jobs_result = self.supabase.table("progressive_agent_jobs").select("id", count="exact").execute()
            contacts_result = self.supabase.table("progressive_agent_contacts").select("id", count="exact").execute()
            campaigns_result = self.supabase.table("progressive_agent_campaigns").select("id", count="exact").execute()
            agents_result = self.supabase.table("progressive_agents").select("id", count="exact").neq("status", "completed").execute()
            
            return {
                "total_jobs": jobs_result.count or 0,
                "total_contacts": contacts_result.count or 0,
                "total_campaigns": campaigns_result.count or 0,
                "active_agents": agents_result.count or 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard stats: {e}")
            return {"total_jobs": 0, "total_contacts": 0, "total_campaigns": 0, "active_agents": 0}

# Global instance
progressive_agent_db = ProgressiveAgentDB()
