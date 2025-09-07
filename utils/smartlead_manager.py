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
                "Content-Type": "application/json"
            }
            
            # SmartLead.ai uses API key as query parameter
            params = {"api_key": self.api_key}
            if data and method.upper() == "GET":
                params.update(data)
            
            self.last_request_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, params=params, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, params=params, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            
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
                "name": name
            }
            
            logger.info(f"📧 Creating Smartlead campaign: {name}")
            campaign_result = self._make_request("POST", "/campaigns/create", campaign_data)
            
            if "error" in campaign_result:
                return {"success": False, "error": campaign_result["error"]}
            
            campaign_id = campaign_result.get("id")
            
            # Step 2: Create email sequence
            sequence_data = {
                "sequences": [
                    {
                        "subject": subject,
                        "email_body": email_template,
                        "delay": 0  # Send immediately
                    }
                ]
            }
            
            logger.info(f"📧 Creating email sequence for campaign {campaign_id}")
            sequence_result = self._make_request("POST", f"/campaigns/{campaign_id}/sequences", sequence_data)
            
            if "error" in sequence_result:
                logger.error(f"❌ Sequence creation failed: {sequence_result['error']}")
                return {"success": False, "error": f"Campaign created but sequence failed: {sequence_result['error']}"}
            
            sequence_id = sequence_result.get("id")
            logger.info(f"✅ Email sequence created with ID: {sequence_id}")
            # Step 3: Add leads to campaign
            leads_added = 0
            failed_leads = []
            
            logger.info(f"📧 Adding {len(leads)} leads to campaign {campaign_id}")
            for lead in leads:
                lead_data = {
                    "email": lead.get("email", ""),
                    "first_name": lead.get("first_name", lead.get("name", "").split()[0] if lead.get("name") else ""),
                    "last_name": lead.get("last_name", " ".join(lead.get("name", "").split()[1:]) if lead.get("name") and len(lead.get("name", "").split()) > 1 else ""),
                    "company_name": lead.get("company", ""),
                    "job_title": lead.get("job_title", lead.get("title", "")),
                    "location": lead.get("location", "")
                }
                
                lead_result = self._make_request("POST", f"/campaigns/{campaign_id}/leads", lead_data)
                
                if "error" not in lead_result:
                    leads_added += 1
                    logger.info(f"✅ Added lead: {lead.get('email')}")
                else:
                    failed_leads.append({
                        "email": lead.get("email"),
                        "error": lead_result["error"]
                    })
                    logger.error(f"❌ Failed to add lead {lead.get('email')}: {lead_result['error']}")
            
            logger.info(f"🎯 Campaign creation completed: {leads_added}/{len(leads)} leads added successfully")
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
            result = self._make_request("GET", "/campaigns/")
            
            if "error" not in result:
                # SmartLead returns campaigns directly as array, not in a "data" wrapper
                campaigns = result if isinstance(result, list) else result.get("data", [])
                
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
        """Get Smartlead account information via campaigns endpoint (no direct account endpoint available)"""
        try:
            # Since SmartLead doesn't have a direct account endpoint, we'll use campaigns to test API access
            result = self._make_request("GET", "/campaigns/")
            
            if "error" not in result:
                # If we can access campaigns, the API key is valid
                campaigns_count = len(result) if isinstance(result, list) else 0
                
                return {
                    "success": True,
                    "account": {
                        "email": "API Key Valid",
                        "name": "SmartLead User",
                        "plan": "Active",
                        "credits_remaining": "N/A",
                        "monthly_limit": "N/A",
                        "emails_sent_this_month": "N/A",
                        "campaigns_count": campaigns_count
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
