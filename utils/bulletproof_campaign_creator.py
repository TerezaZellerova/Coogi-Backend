"""
BULLETPROOF CAMPAIGN CREATOR - Robust Email Campaign System
Creates and manages email campaigns with multiple email service integrations
"""
import os
import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import random
import json
from .smartlead_manager import SmartleadManager

logger = logging.getLogger(__name__)

class BulletproofCampaignCreator:
    def __init__(self):
        self.instantly_api_key = os.getenv("INSTANTLY_API_KEY", "")
        self.smartlead_api_key = os.getenv("SMARTLEAD_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Initialize SmartLead manager
        self.smartlead_manager = SmartleadManager()
        
        # Campaign services with fallbacks
        self.campaign_services = {
            "instantly": {
                "base_url": "https://api.instantly.ai/api/v1",
                "headers": {
                    "Content-Type": "application/json"
                }
            },
            "smartlead": {
                "base_url": "https://server.smartlead.ai/api/v1",
                "headers": {
                    "Content-Type": "application/json"
                }
            }
        }
        
        # Campaign templates
        self.campaign_templates = {
            "hiring_managers": {
                "name_template": "Outreach to {company} - {job_title}",
                "subject_templates": [
                    "Re: {job_title} Position at {company}",
                    "Application for {job_title} Role",
                    "Interest in {job_title} Opportunity",
                    "{job_title} Candidate - {name}",
                    "Following up on {job_title} Position"
                ],
                "message_template": """Hi {contact_name},

I hope this email finds you well. I came across the {job_title} position at {company} and was immediately drawn to the opportunity.

With my background in {relevant_experience}, I believe I would be a strong fit for this role. I'm particularly excited about {company_specific_interest}.

I've attached my resume for your review and would welcome the opportunity to discuss how my skills align with your needs.

Thank you for your time and consideration.

Best regards,
{sender_name}

P.S. I'm available for a brief call at your convenience to discuss this opportunity further."""
            },
            "candidates": {
                "name_template": "Opportunity at {company} - {job_title}",
                "subject_templates": [
                    "Exciting {job_title} Opportunity at {company}",
                    "Your Next Career Move - {job_title}",
                    "Premium {job_title} Role at {company}",
                    "Confidential {job_title} Opportunity",
                    "Senior {job_title} Position - {company}"
                ],
                "message_template": """Hi {contact_name},

I hope you're doing well. I'm reaching out because I have an exciting {job_title} opportunity at {company} that I believe would be a perfect match for your background.

Here's what makes this role special:
• {benefit_1}
• {benefit_2}
• {benefit_3}

The position offers competitive compensation and the chance to work with cutting-edge technology in a fast-growing company.

Would you be open to a brief 10-15 minute conversation to learn more about this opportunity?

Best regards,
{sender_name}
{recruiter_title}

P.S. This is a confidential search, so your current employer won't be contacted without your explicit permission."""
            }
        }
    
    async def create_campaigns_bulletproof(self, 
                                         jobs: List[Dict[str, Any]], 
                                         contacts: List[Dict[str, Any]],
                                         campaign_type: str = "hiring_managers",
                                         sender_info: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        BULLETPROOF campaign creation with multiple service fallbacks
        """
        logger.info(f"🚀 BULLETPROOF campaign creation: {len(jobs)} jobs, {len(contacts)} contacts")
        
        if not sender_info:
            sender_info = {
                "name": "Alex Johnson",
                "email": "alex.johnson@example.com",
                "title": "Business Development Specialist"
            }
        
        all_campaigns = []
        
        # Group contacts by company for targeted campaigns
        company_groups = self._group_contacts_by_company(contacts, jobs)
        
        for company, company_data in company_groups.items():
            try:
                campaign = await self._create_company_campaign(
                    company=company,
                    jobs=company_data["jobs"],
                    contacts=company_data["contacts"],
                    campaign_type=campaign_type,
                    sender_info=sender_info
                )
                
                if campaign:
                    all_campaigns.append(campaign)
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Failed to create campaign for {company}: {e}")
                
                # Create fallback campaign
                fallback_campaign = self._create_fallback_campaign(
                    company, company_data["jobs"], company_data["contacts"], campaign_type
                )
                all_campaigns.append(fallback_campaign)
        
        logger.info(f"🎉 FINAL RESULT: {len(all_campaigns)} campaigns created")
        return all_campaigns
    
    async def _create_company_campaign(self, 
                                     company: str, 
                                     jobs: List[Dict], 
                                     contacts: List[Dict],
                                     campaign_type: str,
                                     sender_info: Dict) -> Optional[Dict[str, Any]]:
        """Create campaign for a specific company"""
        logger.info(f"📧 Creating campaign for: {company}")
        
        # Select primary job for campaign
        primary_job = jobs[0] if jobs else {"title": "Multiple Positions", "company": company}
        
        # Generate campaign content
        campaign_content = await self._generate_campaign_content(
            primary_job, contacts, campaign_type, sender_info
        )
        
        # Strategy 1: SmartLead.ai (Primary - Better features and reliability)
        try:
            smartlead_campaign = await self._create_smartlead_campaign(campaign_content, contacts)
            if smartlead_campaign:
                logger.info(f"✅ SmartLead.ai campaign created for {company}")
                return smartlead_campaign
        except Exception as e:
            logger.error(f"❌ SmartLead.ai failed for {company}: {e}")
        
        # Strategy 2: Instantly.ai (Fallback)
        try:
            instantly_campaign = await self._create_instantly_campaign(campaign_content, contacts)
            if instantly_campaign:
                logger.info(f"✅ Instantly.ai campaign created for {company}")
                return instantly_campaign
        except Exception as e:
            logger.error(f"❌ Instantly.ai failed for {company}: {e}")
        
        # Strategy 3: Internal campaign (fallback)
        internal_campaign = self._create_internal_campaign(campaign_content, contacts)
        logger.info(f"✅ Internal campaign created for {company}")
        return internal_campaign
    
    async def _generate_campaign_content(self, 
                                       job: Dict, 
                                       contacts: List[Dict],
                                       campaign_type: str,
                                       sender_info: Dict) -> Dict[str, Any]:
        """Generate personalized campaign content using AI"""
        
        template = self.campaign_templates.get(campaign_type, self.campaign_templates["hiring_managers"])
        
        # Basic template filling
        campaign_name = template["name_template"].format(
            company=job.get("company", "Unknown Company"),
            job_title=job.get("title", "Multiple Positions")
        )
        
        subject_line = random.choice(template["subject_templates"]).format(
            company=job.get("company", "Unknown Company"),
            job_title=job.get("title", "Multiple Positions"),
            name=sender_info.get("name", "")
        )
        
        # Generate AI-enhanced message if OpenAI is available
        try:
            if self.openai_api_key:
                enhanced_message = await self._generate_ai_message(job, campaign_type, sender_info)
            else:
                enhanced_message = self._generate_template_message(job, template, sender_info)
        except Exception as e:
            logger.error(f"AI message generation failed: {e}")
            enhanced_message = self._generate_template_message(job, template, sender_info)
        
        return {
            "name": campaign_name,
            "subject": subject_line,
            "message": enhanced_message,
            "job": job,
            "sender_info": sender_info,
            "campaign_type": campaign_type
        }
    
    async def _generate_ai_message(self, job: Dict, campaign_type: str, sender_info: Dict) -> str:
        """Generate AI-powered personalized message"""
        import openai
        
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        prompt = f"""
        Write a professional, personalized outreach email for a {campaign_type} campaign.
        
        Job Details:
        - Title: {job.get('title', 'Unknown')}
        - Company: {job.get('company', 'Unknown')}
        - Location: {job.get('location', 'Unknown')}
        
        Sender: {sender_info.get('name', 'Alex')} ({sender_info.get('title', 'Specialist')})
        
        Requirements:
        - Keep it under 150 words
        - Professional yet personable tone
        - Include specific value proposition
        - Clear call to action
        - No generic templates
        
        Make it compelling and personalized to the specific role and company.
        """
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_template_message(self, job: Dict, template: Dict, sender_info: Dict) -> str:
        """Generate message using templates"""
        message = template["message_template"]
        
        # Fill in placeholders
        placeholders = {
            "contact_name": "there",  # Will be personalized per contact
            "job_title": job.get("title", "the position"),
            "company": job.get("company", "your company"),
            "relevant_experience": "my relevant background",
            "company_specific_interest": f"the opportunity to contribute to {job.get('company', 'your organization')}",
            "sender_name": sender_info.get("name", "Alex Johnson"),
            "recruiter_title": sender_info.get("title", "Business Development Specialist"),
            "benefit_1": "Competitive compensation package",
            "benefit_2": "Opportunity for rapid career growth",
            "benefit_3": "Work with cutting-edge technology"
        }
        
        for key, value in placeholders.items():
            message = message.replace(f"{{{key}}}", value)
        
        return message
    
    async def _create_instantly_campaign(self, content: Dict, contacts: List[Dict]) -> Optional[Dict]:
        """Create campaign using Instantly.ai"""
        if not self.instantly_api_key:
            return None
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Create campaign
            campaign_data = {
                "campaign_name": content["name"],
                "from_email": content["sender_info"].get("email", "alex@example.com"),
                "reply_to_email": content["sender_info"].get("email", "alex@example.com"),
                "subject": content["subject"],
                "body_text": content["message"],
                "schedule_start_time": "now"
            }
            
            headers = {
                **self.campaign_services["instantly"]["headers"],
                "api_key": self.instantly_api_key
            }
            
            response = await client.post(
                f"{self.campaign_services['instantly']['base_url']}/campaigns",
                headers=headers,
                json=campaign_data
            )
            
            if response.status_code in [200, 201]:
                campaign_result = response.json()
                
                # Add contacts to campaign
                await self._add_contacts_to_instantly_campaign(
                    client, campaign_result.get("id"), contacts, headers
                )
                
                return {
                    "id": f"instantly_{campaign_result.get('id')}",
                    "name": content["name"],
                    "description": f"Instantly.ai campaign for {content['job']['company']}",
                    "status": "active",
                    "service": "instantly.ai",
                    "contacts": contacts,
                    "subject": content["subject"],
                    "message": content["message"],
                    "lead_count": len(contacts),
                    "created_at": datetime.now().isoformat(),
                    "external_id": campaign_result.get("id")
                }
            else:
                logger.error(f"Instantly.ai API error: {response.status_code}")
                return None
    
    async def _create_smartlead_campaign(self, content: Dict, contacts: List[Dict]) -> Optional[Dict]:
        """Create campaign using SmartLead.ai API"""
        if not self.smartlead_api_key:
            logger.warning("⚠️ SmartLead API key not configured")
            return None
        
        try:
            # Prepare SmartLead-compatible data
            campaign_name = content["name"]
            subject = content["subject"]
            message = content["message"]
            
            # Convert contacts to SmartLead format
            smartlead_leads = []
            for contact in contacts:
                lead = {
                    "email": contact.get("email", ""),
                    "first_name": contact.get("first_name", contact.get("name", "").split()[0] if contact.get("name") else ""),
                    "last_name": contact.get("last_name", " ".join(contact.get("name", "").split()[1:]) if contact.get("name") and len(contact.get("name", "").split()) > 1 else ""),
                    "company": contact.get("company", content["job"].get("company", "")),
                    "job_title": contact.get("title", ""),
                    "location": contact.get("location", "")
                }
                if lead["email"]:  # Only add contacts with valid emails
                    smartlead_leads.append(lead)
            
            if not smartlead_leads:
                logger.warning(f"⚠️ No valid email contacts for SmartLead campaign: {campaign_name}")
                return None
            
            # Create campaign using SmartLead manager
            logger.info(f"🚀 Creating SmartLead.ai campaign: {campaign_name} with {len(smartlead_leads)} leads")
            
            result = self.smartlead_manager.create_campaign(
                name=campaign_name,
                leads=smartlead_leads,
                email_template=message,
                subject=subject,
                from_email="noreply@coogi.ai",  # Use your verified domain
                from_name="Coogi Recruiting Team"
            )
            
            if result.get("success"):
                # Return standardized campaign format
                return {
                    "id": f"smartlead_{result.get('campaign_id', random.randint(1000, 9999))}",
                    "name": campaign_name,
                    "description": f"SmartLead.ai campaign for {content['job']['company']}",
                    "status": "active",
                    "service": "smartlead",
                    "platform": "SmartLead.ai",
                    "contacts": contacts,
                    "subject": subject,
                    "message": message,
                    "lead_count": len(smartlead_leads),
                    "leads_count": len(smartlead_leads),  # Alternative field name
                    "target_count": len(smartlead_leads),
                    "sent_count": 0,
                    "open_count": 0,
                    "reply_count": 0,
                    "open_rate": 0,
                    "reply_rate": 0,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "external_id": result.get("campaign_id"),
                    "batch_id": result.get("campaign_id"),
                    "agent_id": content.get("agent_id", ""),
                    "type": "outbound",
                    "job_details": content["job"],
                    "is_demo": False
                }
            else:
                logger.error(f"❌ SmartLead campaign creation failed: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ SmartLead campaign creation error: {e}")
            return None
    
    def _create_internal_campaign(self, content: Dict, contacts: List[Dict]) -> Dict[str, Any]:
        """Create internal campaign as fallback"""
        return {
            "id": f"internal_{random.randint(1000, 9999)}",
            "name": content["name"],
            "description": f"Internal campaign for {content['job']['company']}",
            "status": "draft",
            "service": "internal",
            "contacts": contacts,
            "subject": content["subject"],
            "message": content["message"],
            "lead_count": len(contacts),
            "created_at": datetime.now().isoformat(),
            "job_details": content["job"],
            "sender_info": content["sender_info"],
            "is_demo": False  # This is real campaign data, not demo
        }
    
    def _create_fallback_campaign(self, company: str, jobs: List[Dict], contacts: List[Dict], campaign_type: str) -> Dict[str, Any]:
        """Create fallback campaign when all services fail"""
        primary_job = jobs[0] if jobs else {"title": "Multiple Positions", "company": company}
        
        return {
            "id": f"fallback_{random.randint(1000, 9999)}",
            "name": f"Outreach to {company} - {primary_job.get('title', 'Multiple Positions')}",
            "description": f"Fallback campaign for {company}",
            "status": "draft",
            "service": "fallback",
            "contacts": contacts,
            "subject": f"Re: {primary_job.get('title', 'Position')} at {company}",
            "message": "Professional outreach message (generated via fallback)",
            "lead_count": len(contacts),
            "created_at": datetime.now().isoformat(),
            "is_demo": False  # This is real campaign data, not demo
        }
    
    def _group_contacts_by_company(self, contacts: List[Dict], jobs: List[Dict]) -> Dict[str, Dict]:
        """Group contacts by company with associated jobs"""
        company_groups = {}
        
        # Create job lookup by company
        jobs_by_company = {}
        for job in jobs:
            company = job.get("company", "Unknown Company")
            if company not in jobs_by_company:
                jobs_by_company[company] = []
            jobs_by_company[company].append(job)
        
        # Group contacts by company
        for contact in contacts:
            company = contact.get("company", "Unknown Company")
            
            if company not in company_groups:
                company_groups[company] = {
                    "contacts": [],
                    "jobs": jobs_by_company.get(company, [])
                }
            
            company_groups[company]["contacts"].append(contact)
        
        return company_groups
    
    async def _add_contacts_to_instantly_campaign(self, client, campaign_id: str, contacts: List[Dict], headers: Dict):
        """Add contacts to Instantly.ai campaign"""
        try:
            leads_data = []
            for contact in contacts:
                lead = {
                    "email": contact.get("email", ""),
                    "first_name": contact.get("name", "").split()[0] if contact.get("name") else "",
                    "last_name": " ".join(contact.get("name", "").split()[1:]) if contact.get("name") else "",
                    "company": contact.get("company", ""),
                    "title": contact.get("title", "")
                }
                leads_data.append(lead)
            
            response = await client.post(
                f"{self.campaign_services['instantly']['base_url']}/campaigns/{campaign_id}/leads",
                headers=headers,
                json={"leads": leads_data}
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Added {len(contacts)} contacts to Instantly campaign {campaign_id}")
            else:
                logger.error(f"❌ Failed to add contacts to Instantly campaign: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error adding contacts to Instantly campaign: {e}")

# Global instance
bulletproof_campaign_creator = BulletproofCampaignCreator()
