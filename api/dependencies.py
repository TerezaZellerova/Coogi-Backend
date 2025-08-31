"""
Shared dependencies for the API
"""
import os
import logging
from typing import Optional
from fastapi import Header, HTTPException

# Configure logging
logger = logging.getLogger(__name__)

# Test users for development
TEST_USERS = {
    "test@coogi.dev": {
        "password": "coogi123",
        "name": "Test User",
        "role": "admin"
    },
    "chuck@liacgroupllc.com": {
        "password": "Newyork2024$",
        "name": "Chuck Cole",
        "role": "admin"
    },
    "cole@liacgroupllc.com": {
        "password": "Newyork2024$",
        "name": "Cole Admin",
        "role": "super_admin",
        "permissions": {
            "unlimited_agents": True,
            "unlimited_searches": True,
            "no_subscription_required": True,
            "access_all_features": True,
            "bypass_rate_limits": True,
            "full_admin_access": True
        }
    }
}

# User authentication
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Simple token validation for development
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            
            # Extract email from token (format: test_token_{email_with_underscores})
            if token.startswith("test_token_"):
                email_part = token.replace("test_token_", "")
                email = email_part.replace("_", ".")
                # Handle @ symbol
                if "_" in email:
                    parts = email.split("_")
                    if len(parts) >= 2:
                        email = f"{parts[0]}@{'.'.join(parts[1:])}"
                
                # Find user in TEST_USERS
                user_data = None
                for test_email, data in TEST_USERS.items():
                    if test_email.replace("@", "_").replace(".", "_") in token:
                        user_data = data
                        email = test_email
                        break
                
                if user_data:
                    user_info = {
                        "email": email,
                        "name": user_data["name"],
                        "role": user_data["role"]
                    }
                    
                    # Add permissions for super_admin
                    if "permissions" in user_data:
                        user_info["permissions"] = user_data["permissions"]
                    
                    return user_info
                else:
                    raise HTTPException(status_code=401, detail="Invalid user token")
            else:
                raise HTTPException(status_code=401, detail="Invalid token format")
        else:
            raise HTTPException(status_code=401, detail="Invalid authorization format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Helper functions for user permissions
def is_admin_user(user_info: dict) -> bool:
    """Check if user has admin or super_admin role"""
    role = user_info.get("role", "user")
    return role in ["admin", "super_admin"]

def has_unlimited_access(user_info: dict) -> bool:
    """Check if user has unlimited access (super_admin with permissions)"""
    if user_info.get("role") == "super_admin":
        permissions = user_info.get("permissions", {})
        return permissions.get("unlimited_agents", False) and permissions.get("no_subscription_required", False)
    return False

def can_bypass_limitations(user_info: dict) -> bool:
    """Check if user can bypass rate limits and subscription requirements"""
    if user_info.get("role") == "super_admin":
        permissions = user_info.get("permissions", {})
        return permissions.get("bypass_rate_limits", False) and permissions.get("full_admin_access", False)
    return False

# Get services instances (REAL implementations - not mocked)
def get_job_scraper():
    from utils.job_scraper import JobScraper
    return JobScraper()

def get_contact_finder():
    from utils.contact_finder import ContactFinder
    return ContactFinder()

def get_email_generator():
    from utils.email_generator import EmailGenerator
    return EmailGenerator()

def get_memory_manager():
    from utils.memory_manager import MemoryManager
    return MemoryManager()

def get_contract_analyzer():
    from utils.contract_analyzer import ContractAnalyzer
    return ContractAnalyzer()

def get_instantly_manager():
    from utils.instantly_manager import InstantlyManager
    return InstantlyManager()

def get_blacklist_manager():
    from utils.blacklist_manager import BlacklistManager
    return BlacklistManager()

def get_ses_manager():
    """Get SES manager for email delivery"""
    from utils.ses_manager import SESManager
    return SESManager()

def get_jsearch_manager():
    """Get JSearch manager for job searching"""
    from utils.jsearch_manager import JSearchManager
    return JSearchManager()

def get_smartlead_manager():
    """Get Smartlead.ai manager for AI-powered email campaigns"""
    from utils.smartlead_manager import SmartleadManager
    return SmartleadManager()

# Logging function
async def log_to_supabase(batch_id: str, message: str, level: str = "info", company: str = None, 
                          job_title: str = None, job_url: str = None, processing_stage: str = None):
    """Send log message directly to Supabase in real-time"""
    try:
        # Log locally first for immediate feedback
        logger.info(f"📝 [{level.upper()}] {batch_id}: {message}")
        
        # ✅ ENABLED: Supabase logging with service role key
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for backend operations
        
        if supabase_url and supabase_key:
            supabase = create_client(supabase_url, supabase_key)
            
            log_data = {
                "batch_id": batch_id,
                "message": message,
                "level": level,
                "company": company,
                "job_title": job_title,
                "job_url": job_url,
                "processing_stage": processing_stage
            }
            
            # Insert log to Supabase
            result = supabase.table("agent_logs").insert(log_data).execute()
            logger.info(f"📝 Logged to Supabase: {message}")
        else:
            logger.warning(f"⚠️  Supabase not configured - logging locally only: {message}")
    except Exception as e:
        logger.error(f"❌ Failed to log to Supabase: {e} - Message: {message}")
