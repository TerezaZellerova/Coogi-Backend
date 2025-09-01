"""
Hunter.io Quota Management System
Tracks and optimizes Hunter.io API usage to stay within limits
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HunterQuotaManager:
    def __init__(self):
        self.quota_file = "hunter_quota_tracker.json"
        self.daily_limit = int(os.getenv("HUNTER_DAILY_LIMIT", "4000"))  # Your updated quota
        self.monthly_limit = int(os.getenv("HUNTER_MONTHLY_LIMIT", "4000"))
        self.load_quota_data()
    
    def load_quota_data(self):
        """Load quota tracking data from file"""
        try:
            if os.path.exists(self.quota_file):
                with open(self.quota_file, 'r') as f:
                    self.quota_data = json.load(f)
            else:
                self.quota_data = {
                    "daily_usage": 0,
                    "monthly_usage": 0,
                    "last_reset_date": datetime.now().isoformat(),
                    "requests_today": [],
                    "efficiency_stats": {
                        "total_requests": 0,
                        "successful_contacts": 0,
                        "success_rate": 0
                    }
                }
                self.save_quota_data()
        except Exception as e:
            logger.error(f"Error loading quota data: {e}")
            self.quota_data = {"daily_usage": 0, "monthly_usage": 0}
    
    def save_quota_data(self):
        """Save quota tracking data to file"""
        try:
            with open(self.quota_file, 'w') as f:
                json.dump(self.quota_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving quota data: {e}")
    
    def reset_daily_if_needed(self):
        """Reset daily usage if it's a new day"""
        try:
            last_reset = datetime.fromisoformat(self.quota_data.get("last_reset_date", datetime.now().isoformat()))
            now = datetime.now()
            
            if now.date() > last_reset.date():
                logger.info("🔄 Resetting daily Hunter.io quota usage")
                self.quota_data["daily_usage"] = 0
                self.quota_data["requests_today"] = []
                self.quota_data["last_reset_date"] = now.isoformat()
                self.save_quota_data()
        except Exception as e:
            logger.error(f"Error resetting daily quota: {e}")
    
    def can_make_request(self, estimated_cost: int = 1) -> bool:
        """Check if we can make a Hunter.io request without exceeding quota"""
        self.reset_daily_if_needed()
        
        current_daily = self.quota_data.get("daily_usage", 0)
        current_monthly = self.quota_data.get("monthly_usage", 0)
        
        can_request = (
            current_daily + estimated_cost <= self.daily_limit and
            current_monthly + estimated_cost <= self.monthly_limit
        )
        
        if not can_request:
            logger.warning(f"⚠️ Hunter.io quota exceeded. Daily: {current_daily}/{self.daily_limit}, Monthly: {current_monthly}/{self.monthly_limit}")
        
        return can_request
    
    def record_request(self, cost: int = 1, success: bool = True, contacts_found: int = 0):
        """Record a Hunter.io API request"""
        self.reset_daily_if_needed()
        
        self.quota_data["daily_usage"] = self.quota_data.get("daily_usage", 0) + cost
        self.quota_data["monthly_usage"] = self.quota_data.get("monthly_usage", 0) + cost
        
        # Track individual requests for analysis
        request_record = {
            "timestamp": datetime.now().isoformat(),
            "cost": cost,
            "success": success,
            "contacts_found": contacts_found
        }
        
        if "requests_today" not in self.quota_data:
            self.quota_data["requests_today"] = []
        
        self.quota_data["requests_today"].append(request_record)
        
        # Update efficiency stats
        stats = self.quota_data.get("efficiency_stats", {})
        stats["total_requests"] = stats.get("total_requests", 0) + 1
        if success:
            stats["successful_contacts"] = stats.get("successful_contacts", 0) + contacts_found
        stats["success_rate"] = (stats.get("successful_contacts", 0) / max(1, stats.get("total_requests", 0))) * 100
        
        self.quota_data["efficiency_stats"] = stats
        
        self.save_quota_data()
        
        logger.info(f"📊 Hunter.io usage: {self.quota_data['daily_usage']}/{self.daily_limit} daily, {contacts_found} contacts found")
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        self.reset_daily_if_needed()
        
        return {
            "daily_usage": self.quota_data.get("daily_usage", 0),
            "daily_limit": self.daily_limit,
            "daily_remaining": self.daily_limit - self.quota_data.get("daily_usage", 0),
            "monthly_usage": self.quota_data.get("monthly_usage", 0),
            "monthly_limit": self.monthly_limit,
            "monthly_remaining": self.monthly_limit - self.quota_data.get("monthly_usage", 0),
            "efficiency_stats": self.quota_data.get("efficiency_stats", {}),
            "requests_today": len(self.quota_data.get("requests_today", [])),
            "can_make_request": self.can_make_request()
        }
    
    def get_optimized_limits(self) -> Dict[str, int]:
        """Get optimized limits based on current quota"""
        status = self.get_quota_status()
        remaining = status["daily_remaining"]
        
        if remaining > 100:
            return {
                "contacts_per_company": 2,
                "companies_per_batch": 25,  # 50 total contacts
                "emails_per_domain": 2
            }
        elif remaining > 50:
            return {
                "contacts_per_company": 1,
                "companies_per_batch": 25,  # 25 total contacts
                "emails_per_domain": 1
            }
        elif remaining > 20:
            return {
                "contacts_per_company": 1,
                "companies_per_batch": 15,  # 15 total contacts
                "emails_per_domain": 1
            }
        else:
            return {
                "contacts_per_company": 1,
                "companies_per_batch": 5,   # 5 total contacts
                "emails_per_domain": 1
            }

# Global quota manager instance
hunter_quota_manager = HunterQuotaManager()
