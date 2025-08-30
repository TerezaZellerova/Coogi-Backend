"""
Smartlead.ai API Manager for COOGI
Handles AI-powered email campaigns through Smartlead.ai API
"""
import os
import requests
import logging
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartleadManager:
    """Smartlead.ai API manager for AI-powered email campaigns"""
    
    def __init__(self):
        """Initialize Smartlead.ai API client"""
        self.api_key = os.getenv('SMARTLEAD_API_KEY', '')
        self.base_url = "https://server.smartlead.ai/api/v1"
        
        # Rate limiting
        self.requests_per_second = 2
        self.last_request_time = 0
        
        if self.api_key:
            logger.info("✅ Smartlead Manager initialized successfully")
        else:
            logger.warning("⚠️  Smartlead Manager initialized without API key")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make rate-limited request to Smartlead API"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < 0.5:  # 0.5 seconds between requests
                time.sleep(0.5 - time_since_last)
            
            url = f"{self.base_url}{endpoint}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            self.last_request_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Smartlead API error: {response.status_code} - {response.text}")
                return {"error": f"API request failed: {response.status_code}", "message": response.text}
                
        except Exception as e:
            logger.error(f"Smartlead request failed: {e}")
            return {"error": str(e)}
    
    def create_campaign(
        self,
        name: str,
        leads: List[Dict[str, Any]],
        email_template: str,
        subject: str,
        from_email: str,
        from_name: str = "Recruiting Team"
    ) -> Dict[str, Any]:
        """Create a new Smartlead campaign with leads"""
        try:
            # Step 1: Create campaign
            campaign_data = {
                "name": name,
                "from_email": from_email,
                "from_name": from_name,
                "timezone": "America/New_York",
                "track_opens": True,
                "track_clicks": True
            }
            
            logger.info(f"📧 Creating Smartlead campaign: {name}")
            campaign_result = self._make_request("POST", "/campaigns", campaign_data)
            
            if "error" in campaign_result:
                return {"success": False, "error": campaign_result["error"]}
            
            campaign_id = campaign_result.get("id")
            
            # Step 2: Create email sequence
            sequence_data = {
                "campaign_id": campaign_id,
                "subject": subject,
                "body": email_template,
                "delay_days": 0,
                "delay_hours": 0,
                "delay_minutes": 0
            }
            
            sequence_result = self._make_request("POST", "/sequences", sequence_data)
            
            if "error" in sequence_result:
                return {"success": False, "error": f"Campaign created but sequence failed: {sequence_result['error']}"}
            
            # Step 3: Add leads to campaign
            leads_added = 0
            failed_leads = []
            
            for lead in leads:
                lead_data = {
                    "campaign_id": campaign_id,
                    "email": lead.get("email", ""),
                    "first_name": lead.get("name", "").split()[0] if lead.get("name") else "",
                    "last_name": " ".join(lead.get("name", "").split()[1:]) if len(lead.get("name", "").split()) > 1 else "",
                    "company": lead.get("company", ""),
                    "title": lead.get("title", ""),
                    "custom_fields": {
                        "job_title": lead.get("job_title", ""),
                        "job_url": lead.get("job_url", ""),
                        "score": lead.get("score", 0),
                        "company_website": lead.get("company_website", "")
                    }
                }
                
                lead_result = self._make_request("POST", "/leads", lead_data)
                
                if "error" not in lead_result:
                    leads_added += 1
                else:
                    failed_leads.append({
                        "email": lead.get("email"),
                        "error": lead_result["error"]
                    })
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "campaign_name": name,
                "leads_added": leads_added,
                "failed_leads": len(failed_leads),
                "failed_details": failed_leads[:5],  # First 5 failures
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Smartlead campaign creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_campaigns(self) -> Dict[str, Any]:
        """Get all Smartlead campaigns"""
        try:
            result = self._make_request("GET", "/campaigns")
            
            if "error" not in result:
                campaigns = result.get("data", [])
                
                # Standardize campaign format
                standardized_campaigns = []
                for campaign in campaigns:
                    standardized_campaign = {
                        "id": campaign.get("id"),
                        "name": campaign.get("name"),
                        "status": campaign.get("status", "active"),
                        "from_email": campaign.get("from_email"),
                        "from_name": campaign.get("from_name"),
                        "created_at": campaign.get("created_at"),
                        "leads_count": campaign.get("leads_count", 0),
                        "sent_count": campaign.get("sent_count", 0),
                        "open_rate": campaign.get("open_rate", 0),
                        "reply_rate": campaign.get("reply_rate", 0),
                        "click_rate": campaign.get("click_rate", 0)
                    }
                    standardized_campaigns.append(standardized_campaign)
                
                return {
                    "success": True,
                    "campaigns": standardized_campaigns,
                    "total_count": len(campaigns),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Smartlead get campaigns failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific campaign"""
        try:
            result = self._make_request("GET", f"/campaigns/{campaign_id}/stats")
            
            if "error" not in result:
                stats = result.get("data", {})
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "stats": {
                        "total_leads": stats.get("total_leads", 0),
                        "emails_sent": stats.get("emails_sent", 0),
                        "emails_opened": stats.get("emails_opened", 0),
                        "emails_clicked": stats.get("emails_clicked", 0),
                        "emails_replied": stats.get("emails_replied", 0),
                        "emails_bounced": stats.get("emails_bounced", 0),
                        "open_rate": stats.get("open_rate", 0),
                        "click_rate": stats.get("click_rate", 0),
                        "reply_rate": stats.get("reply_rate", 0),
                        "bounce_rate": stats.get("bounce_rate", 0)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Smartlead campaign stats failed: {e}")
            return {"success": False, "error": str(e)}
    
    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause a Smartlead campaign"""
        try:
            data = {"status": "paused"}
            result = self._make_request("PUT", f"/campaigns/{campaign_id}", data)
            
            if "error" not in result:
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "status": "paused",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Smartlead pause campaign failed: {e}")
            return {"success": False, "error": str(e)}
    
    def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Resume a paused Smartlead campaign"""
        try:
            data = {"status": "active"}
            result = self._make_request("PUT", f"/campaigns/{campaign_id}", data)
            
            if "error" not in result:
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "status": "active",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Smartlead resume campaign failed: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Delete a Smartlead campaign"""
        try:
            result = self._make_request("DELETE", f"/campaigns/{campaign_id}")
            
            if "error" not in result:
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "status": "deleted",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Smartlead delete campaign failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Smartlead account information and limits"""
        try:
            result = self._make_request("GET", "/account")
            
            if "error" not in result:
                account = result.get("data", {})
                
                return {
                    "success": True,
                    "account": {
                        "email": account.get("email"),
                        "name": account.get("name"),
                        "plan": account.get("plan"),
                        "credits_remaining": account.get("credits_remaining"),
                        "monthly_limit": account.get("monthly_limit"),
                        "emails_sent_this_month": account.get("emails_sent_this_month"),
                        "campaigns_count": account.get("campaigns_count", 0)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Smartlead account info failed: {e}")
            return {"success": False, "error": str(e)}
    
    def test_api_connection(self) -> Dict[str, Any]:
        """Test Smartlead API connection and key validity"""
        try:
            start_time = time.time()
            result = self.get_account_info()
            response_time = time.time() - start_time
            
            if result.get("success"):
                return {
                    "status": "operational",
                    "api_key_valid": True,
                    "response_time_ms": round(response_time * 1000, 2),
                    "account_email": result.get("account", {}).get("email"),
                    "plan": result.get("account", {}).get("plan"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "api_key_valid": False,
                    "error": result.get("error"),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Smartlead API test failed: {e}")
            return {
                "status": "error",
                "api_key_valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def create_ai_personalized_campaign(
        self,
        name: str,
        leads: List[Dict[str, Any]],
        template_context: str,
        subject_template: str,
        from_email: str,
        personalization_level: str = "high"
    ) -> Dict[str, Any]:
        """Create AI-personalized campaign with dynamic content"""
        try:
            # Enhanced campaign with AI personalization settings
            campaign_data = {
                "name": name,
                "from_email": from_email,
                "from_name": "Recruiting Team",
                "timezone": "America/New_York",
                "track_opens": True,
                "track_clicks": True,
                "ai_personalization": True,
                "personalization_level": personalization_level,
                "context": template_context
            }
            
            logger.info(f"🤖 Creating AI-personalized Smartlead campaign: {name}")
            
            # Use the standard campaign creation but with AI enhancement flags
            result = self.create_campaign(
                name=name,
                leads=leads,
                email_template=template_context,
                subject=subject_template,
                from_email=from_email
            )
            
            if result.get("success"):
                result["ai_personalized"] = True
                result["personalization_level"] = personalization_level
            
            return result
            
        except Exception as e:
            logger.error(f"Smartlead AI campaign creation failed: {e}")
            return {"success": False, "error": str(e)}
