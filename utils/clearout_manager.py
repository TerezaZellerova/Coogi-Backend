"""
ClearOut API Integration for Email Verification and Domain Finding
Supports email validation, bulk verification, and company domain discovery
"""
import os
import requests
import logging
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

class ClearOutManager:
    def __init__(self):
        self.api_key = os.getenv('CLEAROUT_API_KEY')
        self.base_url = "https://api.clearout.io"
        
        if not self.api_key:
            logger.warning("⚠️  CLEAROUT_API_KEY not found in environment variables")
    
    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify a single email address using ClearOut API
        Returns detailed verification results
        """
        if not self.api_key:
            return {"error": "ClearOut API key not configured"}
        
        try:
            url = f"{self.base_url}/public/verify/{email}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"📧 Verifying email: {email}")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Email verification successful for {email}")
                return {
                    "email": email,
                    "status": data.get("status", "unknown"),
                    "result": data.get("result", "unknown"),
                    "reason": data.get("reason", ""),
                    "confidence": data.get("confidence", 0),
                    "is_valid": data.get("status") == "valid",
                    "is_deliverable": data.get("result") == "deliverable",
                    "domain_valid": data.get("domain_valid", False),
                    "mx_found": data.get("mx_found", False),
                    "smtp_valid": data.get("smtp_valid", False)
                }
            else:
                logger.warning(f"⚠️  ClearOut email verification failed: {response.status_code}")
                return {"error": f"API request failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Error verifying email {email}: {str(e)}")
            return {"error": str(e)}
    
    def bulk_verify_emails(self, emails: List[str]) -> Dict[str, Any]:
        """
        Verify multiple emails in bulk using ClearOut API
        More efficient for large lists
        """
        if not self.api_key:
            return {"error": "ClearOut API key not configured"}
        
        if not emails:
            return {"error": "No emails provided"}
        
        try:
            url = f"{self.base_url}/public/bulk/verify"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "emails": emails,
                "webhook_url": None  # Optional webhook for async processing
            }
            
            logger.info(f"📧 Bulk verifying {len(emails)} emails")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Bulk verification initiated for {len(emails)} emails")
                return {
                    "job_id": data.get("job_id"),
                    "status": "processing",
                    "total_emails": len(emails),
                    "estimated_time": data.get("estimated_time", "unknown")
                }
            else:
                logger.warning(f"⚠️  ClearOut bulk verification failed: {response.status_code}")
                return {"error": f"API request failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Error in bulk email verification: {str(e)}")
            return {"error": str(e)}
    
    def get_bulk_results(self, job_id: str) -> Dict[str, Any]:
        """
        Get results from a bulk verification job
        """
        if not self.api_key:
            return {"error": "ClearOut API key not configured"}
        
        try:
            url = f"{self.base_url}/public/bulk/status/{job_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"📋 Checking bulk verification status: {job_id}")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "job_id": job_id,
                    "status": data.get("status", "unknown"),
                    "progress": data.get("progress", 0),
                    "results": data.get("results", []),
                    "completed": data.get("status") == "completed"
                }
            else:
                logger.warning(f"⚠️  ClearOut job status check failed: {response.status_code}")
                return {"error": f"API request failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Error checking bulk verification status: {str(e)}")
            return {"error": str(e)}
    
    def find_company_domain(self, company_name: str) -> Optional[str]:
        """
        Find company website domain using ClearOut API
        """
        if not self.api_key:
            logger.warning("⚠️  ClearOut API key not configured")
            return None
        
        try:
            url = f"{self.base_url}/public/companies/autocomplete"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "name": company_name,
                "limit": 5
            }
            
            logger.info(f"🔍 Finding domain for company: {company_name}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    companies = data["data"]
                    for company in companies:
                        if company.get("domain"):
                            domain = company["domain"]
                            logger.info(f"✅ Found domain for {company_name}: {domain}")
                            return domain
                    
                    logger.warning(f"⚠️  No domain found for {company_name}")
                    return None
                else:
                    logger.warning(f"⚠️  ClearOut API failed for {company_name}: {data.get('message', 'Unknown error')}")
                    return None
            else:
                logger.warning(f"⚠️  ClearOut API error for {company_name}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error finding domain for {company_name}: {str(e)}")
            return None
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get ClearOut account information and credits
        """
        if not self.api_key:
            return {"error": "ClearOut API key not configured"}
        
        try:
            url = f"{self.base_url}/public/account/info"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "account_id": data.get("account_id"),
                    "email": data.get("email"),
                    "credits_remaining": data.get("credits_remaining", 0),
                    "plan": data.get("plan", "unknown"),
                    "status": "active"
                }
            else:
                return {"error": f"API request failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Error getting account info: {str(e)}")
            return {"error": str(e)}

# Global instance
clearout_manager = ClearOutManager()
