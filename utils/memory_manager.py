import os
import logging
import json
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.memory_file = "memory.json"
        self.data = self._load_memory()
        
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load memory: {e}")
        return {
            "batches": {},
            "companies": {},
            "stats": {
                "total_batches": 0,
                "total_companies": 0,
                "total_jobs": 0
            }
        }
        
    def _save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save memory: {e}")
            
    def store_batch(self, batch_id: str, batch_data: Dict[str, Any]):
        """Store batch data"""
        self.data["batches"][batch_id] = {
            **batch_data,
            "timestamp": datetime.now().isoformat()
        }
        self.data["stats"]["total_batches"] += 1
        self._save_memory()
        logger.info(f"💾 Stored batch {batch_id}")
        
    def get_batch(self, batch_id: str) -> Dict[str, Any]:
        """Get batch data"""
        return self.data["batches"].get(batch_id, {})
        
    def get_all_batches(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all batches with pagination"""
        batches = list(self.data["batches"].values())
        return batches[offset:offset + limit]
        
    def store_company(self, company_name: str, company_data: Dict[str, Any]):
        """Store company data"""
        self.data["companies"][company_name] = {
            **company_data,
            "timestamp": datetime.now().isoformat()
        }
        self.data["stats"]["total_companies"] += 1
        self._save_memory()
        
    def get_company(self, company_name: str) -> Dict[str, Any]:
        """Get company data"""
        return self.data["companies"].get(company_name, {})
        
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return self.data["stats"]
        
    def create_job_fingerprint(self, job: Dict[str, Any]) -> str:
        """Create a unique fingerprint for a job"""
        # Create a unique identifier based on job title, company, and URL
        job_id = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('job_url', '')}"
        return job_id
        
    def is_job_processed(self, job_fingerprint: str) -> bool:
        """Check if a job has already been processed"""
        # Mock implementation - in real implementation this would check memory
        return False
        
    def mark_job_processed(self, job_fingerprint: str):
        """Mark a job as processed"""
        # Mock implementation - in real implementation this would store in memory
        logger.info(f"✅ Marked job {job_fingerprint} as processed")
        
    def is_email_contacted(self, email: str) -> bool:
        """Check if an email has already been contacted"""
        # Mock implementation - in real implementation this would check memory
        return False
        
    def clear_memory(self):
        """Clear all memory"""
        self.data = {
            "batches": {},
            "companies": {},
            "stats": {
                "total_batches": 0,
                "total_companies": 0,
                "total_jobs": 0
            }
        }
        self._save_memory()
        logger.info("🗑️  Memory cleared")
    
    def get_all_agent_data(self) -> List[Dict[str, Any]]:
        """Get all agent data from batches"""
        return list(self.data["batches"].values())
    
    def delete_agent_data(self, agent_id: str) -> bool:
        """Delete agent data by batch_id"""
        if agent_id in self.data["batches"]:
            del self.data["batches"][agent_id]
            self._save_memory()
            logger.info(f"🗑️  Deleted agent {agent_id}")
            return True
        return False
    
    def get_agent_data(self, batch_id: str) -> Dict[str, Any]:
        """Get agent data by batch_id"""
        return self.data["batches"].get(batch_id, {})
    
    def save_agent_data(self, batch_id: str, agent_data: Dict[str, Any]):
        """Save agent data by batch_id"""
        self.data["batches"][batch_id] = {
            **agent_data,
            "timestamp": datetime.now().isoformat()
        }
        self._save_memory()
        logger.info(f"💾 Saved agent data for {batch_id}")
