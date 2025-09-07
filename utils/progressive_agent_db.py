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
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        key_type = "SERVICE_ROLE" if SUPABASE_SERVICE_ROLE_KEY else "ANON"
        logger.info(f"✅ Supabase client initialized for progressive agents (using {key_type} key)")
        
        # Test the connection immediately
        try:
            test_result = supabase.table("progressive_agents").select("id").limit(1).execute()
            logger.info("✅ Supabase connection test successful")
        except Exception as e:
            logger.warning(f"⚠️ Supabase connection test failed: {e}")
            # If service role key fails, try with anon key
            if SUPABASE_SERVICE_ROLE_KEY and SUPABASE_ANON_KEY:
                logger.info("🔄 Retrying with ANON key...")
                supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                test_result = supabase.table("progressive_agents").select("id").limit(1).execute()
                logger.info("✅ Supabase connection successful with ANON key")
            else:
                raise e
                
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase client: {e}")
        supabase = None
else:
    supabase = None
    logger.warning("❌ Supabase credentials not found - database persistence disabled")

class ProgressiveAgentDB:
    """Manages database operations for progressive agents with fallback to in-memory storage"""
    
    def __init__(self):
        self.supabase = supabase
        # In-memory fallback storage
        self.memory_storage = {
            "agents": {},
            "jobs": [],
            "contacts": [],
            "campaigns": []
        }
        self.use_memory_fallback = not bool(supabase)
        
        if self.use_memory_fallback:
            logger.warning("📦 Using in-memory storage as Supabase fallback")
        else:
            logger.info("💾 Using Supabase database for persistence")
    
    async def save_agent_metadata(self, agent_id: str, query: str, status: str, **kwargs):
        """Save or update agent metadata with memory fallback"""
        if self.use_memory_fallback:
            # Use in-memory storage
            agent_data = {
                "agent_id": agent_id,
                "query": query,
                "status": status,
                "updated_at": datetime.now().isoformat(),
                **kwargs
            }
            self.memory_storage["agents"][agent_id] = agent_data
            logger.info(f"📦 Saved agent metadata to memory: {agent_id}")
            return
        
        if not self.supabase:
            logger.warning("No Supabase client - skipping agent metadata save")
            return
        
        max_retries = 3
        for attempt in range(max_retries):
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
                
                return  # Success, exit retry loop
                
            except Exception as e:
                logger.error(f"❌ Error saving agent metadata for {agent_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Failed to save agent metadata after {max_retries} attempts - falling back to memory")
                    # Fall back to memory storage
                    agent_data = {
                        "agent_id": agent_id,
                        "query": query,
                        "status": status,
                        "updated_at": datetime.now().isoformat(),
                        **kwargs
                    }
                    self.memory_storage["agents"][agent_id] = agent_data
                    logger.info(f"📦 Saved agent metadata to memory fallback: {agent_id}")
                else:
                    import time
                    time.sleep(1)  # Wait 1 second before retry
    
    async def save_jobs(self, agent_id: str, jobs: List[Dict[str, Any]]):
        """Save jobs to database with memory fallback"""
        if not jobs:
            logger.info(f"No jobs to save for agent {agent_id}")
            return
            
        if self.use_memory_fallback:
            # Use in-memory storage
            for job in jobs:
                job_record = {
                    "agent_id": agent_id,
                    "job_id": job.get("id"),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location"),
                    "url": job.get("url"),
                    "description": job.get("description", "")[:1000],
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
                self.memory_storage["jobs"].append(job_record)
            logger.info(f"📦 Saved {len(jobs)} jobs to memory for agent {agent_id}")
            return
            
        if not self.supabase:
            logger.warning("No Supabase client - skipping job save")
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
            # Fall back to memory storage
            for job in jobs:
                job_record = {
                    "agent_id": agent_id,
                    "job_id": job.get("id"),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location"),
                    "url": job.get("url"),
                    "description": job.get("description", "")[:1000],
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
                self.memory_storage["jobs"].append(job_record)
            logger.info(f"📦 Saved {len(jobs)} jobs to memory fallback for agent {agent_id}")
            import traceback
            traceback.print_exc()
    
    async def save_contacts(self, agent_id: str, contacts: List[Dict[str, Any]]):
        """Save contacts to database with memory fallback"""
        if not contacts:
            logger.info(f"No contacts to save for agent {agent_id}")
            return
            
        if self.use_memory_fallback:
            # Use in-memory storage
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
                self.memory_storage["contacts"].append(contact_record)
            logger.info(f"📦 Saved {len(contacts)} contacts to memory for agent {agent_id}")
            return
            
        if not self.supabase:
            logger.warning("No Supabase client - skipping contact save")
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
            # Fall back to memory storage
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
                self.memory_storage["contacts"].append(contact_record)
            logger.info(f"📦 Saved {len(contacts)} contacts to memory fallback for agent {agent_id}")
            import traceback
            traceback.print_exc()
    
    async def save_campaigns(self, agent_id: str, campaigns: List[Dict[str, Any]]):
        """Save campaigns to database with retry logic"""
        if not self.supabase or not campaigns:
            return
        
        max_retries = 3
        for attempt in range(max_retries):
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
                return  # Success, exit retry loop
                
            except Exception as e:
                logger.error(f"❌ Error saving campaigns for agent {agent_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Failed to save campaigns after {max_retries} attempts")
                else:
                    import time
                    time.sleep(1)  # Wait 1 second before retry
    
    async def get_agent_jobs(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs from database or memory"""
        if self.use_memory_fallback:
            # Use in-memory storage
            jobs = self.memory_storage["jobs"]
            if agent_id:
                jobs = [job for job in jobs if job.get("agent_id") == agent_id]
            # Sort by created_at desc and limit
            jobs = sorted(jobs, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
            logger.info(f"📦 Retrieved {len(jobs)} jobs from memory")
            return jobs
            
        if not self.supabase:
            logger.error("❌ No Supabase client - cannot fetch jobs")
            raise Exception("Database connection not available")
        
        try:
            query = self.supabase.table("progressive_agent_jobs").select("*").order("created_at", desc=True).limit(limit)
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            
            result = query.execute()
            logger.info(f"📋 Retrieved {len(result.data or [])} jobs from database")
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting jobs: {e}")
            raise Exception(f"Failed to fetch jobs: {str(e)}")

    async def get_agent_contacts(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get contacts from database or memory"""
        if self.use_memory_fallback:
            # Use in-memory storage
            contacts = self.memory_storage["contacts"]
            if agent_id:
                contacts = [contact for contact in contacts if contact.get("agent_id") == agent_id]
            # Sort by created_at desc and limit
            contacts = sorted(contacts, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
            logger.info(f"📦 Retrieved {len(contacts)} contacts from memory")
            return contacts
            
        if not self.supabase:
            logger.error("❌ No Supabase client - cannot fetch contacts")
            raise Exception("Database connection not available")
        
        try:
            query = self.supabase.table("progressive_agent_contacts").select("*").order("created_at", desc=True).limit(limit)
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            
            result = query.execute()
            logger.info(f"👥 Retrieved {len(result.data or [])} contacts from database")
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting contacts: {e}")
            raise Exception(f"Failed to fetch contacts: {str(e)}")
    
    async def get_agent_campaigns(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get campaigns from database"""
        if not self.supabase:
            logger.error("❌ No Supabase client - cannot fetch campaigns")
            raise Exception("Database connection not available")
        
        try:
            query = self.supabase.table("progressive_agent_campaigns").select("*").order("created_at", desc=True).limit(limit)
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            
            result = query.execute()
            logger.info(f"📧 Retrieved {len(result.data or [])} campaigns from database")
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting campaigns: {e}")
            raise Exception(f"Failed to fetch campaigns: {str(e)}")
    
    async def get_all_agents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all progressive agents with retry logic"""
        if not self.supabase:
            return []

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.supabase.table("progressive_agents").select("*").order("created_at", desc=True).limit(limit).execute()
                return result.data or []

            except Exception as e:
                logger.error(f"❌ Error getting agents (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Failed to get agents after {max_retries} attempts")
                    return []
                else:
                    import time
                    time.sleep(1)  # Wait 1 second before retry
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics with improved error handling"""
        if not self.supabase:
            return {"total_jobs": 0, "total_contacts": 0, "total_campaigns": 0, "active_agents": 0}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get counts from each table with timeout
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
                logger.error(f"❌ Error getting dashboard stats (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Failed to get dashboard stats after {max_retries} attempts")
                    return {"total_jobs": 0, "total_contacts": 0, "total_campaigns": 0, "active_agents": 0}
                else:
                    import time
                    time.sleep(1)  # Wait 1 second before retry

    # ===================================
    # 🚀 PRODUCTION CAMPAIGN METHODS
    # ===================================
    
    async def save_campaign_metadata(self, campaign_id: str, campaign_data: Dict[str, Any]):
        """Save campaign metadata to database"""
        if not self.supabase:
            logger.warning("No Supabase client - skipping campaign metadata save")
            return
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Insert new campaign
                self.supabase.table("production_campaigns").insert(campaign_data).execute()
                logger.info(f"📧 Created campaign metadata: {campaign_id}")
                return
                
            except Exception as e:
                logger.error(f"❌ Error saving campaign metadata for {campaign_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Failed to save campaign metadata after {max_retries} attempts")
                else:
                    import time
                    time.sleep(1)
    
    async def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get single campaign by ID"""
        if not self.supabase:
            logger.warning("No Supabase client - skipping campaign get")
            return None
        
        try:
            result = self.supabase.table("production_campaigns").select("*").eq("campaign_id", campaign_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ Error getting campaign {campaign_id}: {e}")
            return None
    
    async def get_campaigns(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all campaigns"""
        if not self.supabase:
            logger.warning("No Supabase client - skipping campaigns get")
            return []
        
        try:
            query = self.supabase.table("production_campaigns").select("*").order("created_at", desc=True)
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Error getting campaigns: {e}")
            return []
    
    async def update_campaign_status(self, campaign_id: str, status: str, additional_data: Optional[Dict] = None):
        """Update campaign status"""
        if not self.supabase:
            logger.warning("No Supabase client - skipping campaign status update")
            return
        
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            if additional_data:
                update_data.update(additional_data)
            
            self.supabase.table("production_campaigns").update(update_data).eq("campaign_id", campaign_id).execute()
            logger.info(f"📊 Updated campaign {campaign_id} status to {status}")
            
        except Exception as e:
            logger.error(f"❌ Error updating campaign status for {campaign_id}: {e}")
    
    async def update_campaign_metadata(self, campaign_id: str, updates: Dict[str, Any]):
        """Update campaign metadata"""
        if not self.supabase:
            logger.warning("No Supabase client - skipping campaign metadata update")
            return
        
        try:
            updates["updated_at"] = datetime.now().isoformat()
            self.supabase.table("production_campaigns").update(updates).eq("campaign_id", campaign_id).execute()
            logger.info(f"📊 Updated campaign metadata for {campaign_id}")
            
        except Exception as e:
            logger.error(f"❌ Error updating campaign metadata for {campaign_id}: {e}")
    
    def get_contact_count(self, agent_id: str) -> int:
        """Get total contact count for an agent"""
        if not self.supabase:
            return 0
        
        try:
            result = self.supabase.table("progressive_agent_contacts").select("id").eq("agent_id", agent_id).execute()
            return len(result.data)
        except Exception as e:
            logger.error(f"❌ Error getting contact count for agent {agent_id}: {e}")
            return 0
    
    def get_campaign_count(self, agent_id: str) -> int:
        """Get total campaign count for an agent"""
        if not self.supabase:
            return 0
        
        try:
            result = self.supabase.table("progressive_agent_campaigns").select("id").eq("agent_id", agent_id).execute()
            return len(result.data)
        except Exception as e:
            logger.error(f"❌ Error getting campaign count for agent {agent_id}: {e}")
            return 0
    
    def get_job_count(self, agent_id: str) -> int:
        """Get total job count for an agent"""
        if not self.supabase:
            return 0
        
        try:
            result = self.supabase.table("progressive_agent_jobs").select("id").eq("agent_id", agent_id).execute()
            return len(result.data)
        except Exception as e:
            logger.error(f"❌ Error getting job count for agent {agent_id}: {e}")
            return 0

# Global instance
progressive_agent_db = ProgressiveAgentDB()
