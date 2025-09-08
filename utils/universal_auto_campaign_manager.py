"""
Universal Auto-Campaign Manager
Supports auto-campaign creation for all professional roles with role-specific templates
ENHANCED: Now includes live email sending integration
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from utils.apollo_manager import ApolloManager
from utils.live_email_campaign_service import live_email_service
from utils.campaign_analytics_service import campaign_analytics

logger = logging.getLogger(__name__)

class UniversalAutoCampaignManager:
    """Universal auto-campaign manager for all professional roles with live email integration"""
    
    def __init__(self):
        """Initialize the universal auto-campaign manager"""
        self.apollo = ApolloManager()
        logger.info("🚀 Universal Auto-Campaign Manager initialized with live email integration")
    
    async def search_professionals_with_auto_campaign(
        self,
        job_title: str,
        locations: List[str],
        *,
        per_city_limit: int = 15,
        require_email: bool = True,
        require_phone: bool = False,
        hunter_verify: bool = True,
        unlock_emails: bool = True,
        auto_create_campaign: bool = True,
        campaign_name: Optional[str] = None,
        send_immediately: bool = False,
        delay_hours: int = 24,
        company_size: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Universal professional search with auto-campaign creation
        
        Supports all roles:
        - Medical: DVM, Physician, Nurse, Dentist, Pharmacist
        - Legal: Attorney, Lawyer, Legal Counsel
        - Tech: Software Engineer, Data Scientist, Developer
        - Business: Sales, Marketing, Finance, HR
        - Education: Teacher, Professor, Principal
        - And many more...
        """
        try:
            logger.info(f"🚀 UNIVERSAL AUTO-CAMPAIGN SEARCH: {job_title} in {locations}")
            
            # Normalize and detect role category
            role_info = self._analyze_role(job_title)
            normalized_title = role_info["normalized_title"]
            role_category = role_info["category"]
            industry_keywords = role_info["industry_keywords"]
            
            logger.info(f"📋 Role analysis: {job_title} → {normalized_title} (category: {role_category})")
            
            # Check if this is a DVM search (use existing specialized DVM method)
            if role_category == "veterinary":
                logger.info("🐾 Detected veterinary role - using specialized DVM auto-campaign")
                return await self.apollo.search_dvm_with_auto_campaign(
                    locations=locations,
                    per_city_limit=per_city_limit,
                    require_email=require_email,
                    require_phone=require_phone,
                    hunter_verify=hunter_verify,
                    unlock_emails=unlock_emails,
                    auto_create_campaign=auto_create_campaign,
                    campaign_name=campaign_name or f"{normalized_title} Outreach - {', '.join(locations[:2])}{' +' + str(len(locations)-2) + ' more' if len(locations) > 2 else ''}",
                    send_immediately=send_immediately,
                    delay_hours=delay_hours,
                )
            
            # For all other roles, use universal search
            logger.info(f"👤 Using universal auto-campaign for {role_category} role")
            
            # Step 1: Search candidates across locations
            all_candidates = []
            search_summary = {
                "locations_searched": [],
                "candidates_per_location": {},
                "total_api_calls": 0,
                "search_strategies_used": []
            }
            
            for location in locations:
                logger.info(f"🔍 Searching {normalized_title} in {location}")
                
                # Try multiple search strategies for better coverage
                location_candidates = await self._search_location_with_strategies(
                    normalized_title, location, per_city_limit, role_info, company_size
                )
                
                if location_candidates:
                    all_candidates.extend(location_candidates)
                    search_summary["candidates_per_location"][location] = len(location_candidates)
                    search_summary["locations_searched"].append(location)
                else:
                    search_summary["candidates_per_location"][location] = 0
                
                search_summary["total_api_calls"] += 1
            
            logger.info(f"📊 Search complete: {len(all_candidates)} candidates across {len(locations)} locations")
            
            # Step 2: Unlock emails and enhance candidates
            if unlock_emails and all_candidates:
                logger.info(f"🔓 Unlocking emails for {len(all_candidates)} candidates")
                all_candidates = await self.apollo.unlock_emails_for_candidates(all_candidates)
            
            # Step 3: Filter by requirements
            verified_candidates = []
            for candidate in all_candidates:
                # Email requirement
                if require_email and not candidate.get("emails"):
                    continue
                
                # Phone requirement
                if require_phone and not candidate.get("phones"):
                    continue
                
                # Mark as verified if has email
                candidate["verified"] = bool(candidate.get("emails"))
                verified_candidates.append(candidate)
            
            logger.info(f"✅ Found {len(verified_candidates)} verified candidates")
            
            # Step 4: Auto-create campaign if enabled and candidates found
            campaign_created = False
            campaign_details = {}
            
            if auto_create_campaign and verified_candidates:
                logger.info(f"📧 Creating auto-campaign for {len(verified_candidates)} {normalized_title} candidates")
                
                campaign_result = await self._create_universal_campaign(
                    job_title=normalized_title,
                    role_category=role_category,
                    candidates=verified_candidates,
                    campaign_name=campaign_name or f"{normalized_title} Outreach - {', '.join(locations[:2])}{' +' + str(len(locations)-2) + ' more' if len(locations) > 2 else ''}",
                    send_immediately=send_immediately,
                    delay_hours=delay_hours,
                    locations=locations,
                    industry_keywords=industry_keywords
                )
                
                campaign_created = campaign_result.get("success", False)
                campaign_details = campaign_result
            
            # Step 5: Return comprehensive results
            result = {
                "success": True,
                "job_title": job_title,
                "normalized_title": normalized_title,
                "role_category": role_category,
                "total_found": len(all_candidates),
                "verified_candidates": len(verified_candidates),
                "candidates": verified_candidates,
                "campaign_created": campaign_created,
                "campaign_id": campaign_details.get("campaign_id"),
                "campaign_name": campaign_details.get("campaign_name"),
                "campaign_details": campaign_details,
                "search_summary": search_summary,
                "locations_searched": locations,
                "search_timestamp": datetime.now().isoformat(),
                "auto_campaign_enabled": auto_create_campaign,
                "send_scheduled": not send_immediately if campaign_created else None,
                "send_delay_hours": delay_hours if not send_immediately and campaign_created else None,
                "integration_type": "universal_auto_campaign",
                "professional_features_used": [
                    "apollo_universal_search",
                    "email_unlocking" if unlock_emails else None,
                    "hunter_verification" if hunter_verify else None,
                    "auto_campaign_creation" if auto_create_campaign else None,
                ],
            }
            
            # Log success
            logger.info(f"🎉 UNIVERSAL AUTO-CAMPAIGN COMPLETE:")
            logger.info(f"   Role: {normalized_title} ({role_category})")
            logger.info(f"   Locations: {len(locations)}")
            logger.info(f"   Candidates: {len(verified_candidates)}")
            logger.info(f"   Campaign: {'✅ Created' if campaign_created else '❌ Not created'}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Universal auto-campaign search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "job_title": job_title,
                "locations_searched": locations,
                "candidates": [],
                "total_found": 0,
                "campaign_created": False,
                "search_timestamp": datetime.now().isoformat(),
            }
    
    def _analyze_role(self, job_title: str) -> Dict[str, Any]:
        """Analyze job title and return normalized info"""
        title_lower = job_title.lower().strip()
        
        # Role category mappings
        role_categories = {
            # Medical/Healthcare
            "veterinary": {
                "keywords": ["dvm", "veterinarian", "vet doctor", "vet", "animal doctor"],
                "normalized_titles": {"dvm": "Veterinarian", "veterinarian": "Veterinarian", "vet": "Veterinarian"},
                "industry_keywords": ["Animal Hospital", "Veterinary Clinic", "Pet Care", "Animal Health"]
            },
            "medical": {
                "keywords": ["doctor", "physician", "md", "nurse", "dentist", "pharmacist", "therapist", "medical"],
                "normalized_titles": {"doctor": "Physician", "physician": "Physician", "md": "Physician", "nurse": "Registered Nurse", "dentist": "Dentist"},
                "industry_keywords": ["Hospital", "Medical Center", "Clinic", "Healthcare", "Medical Practice"]
            },
            
            # Legal
            "legal": {
                "keywords": ["attorney", "lawyer", "legal counsel", "counsel", "legal advisor", "paralegal"],
                "normalized_titles": {"attorney": "Attorney", "lawyer": "Attorney", "legal counsel": "Legal Counsel"},
                "industry_keywords": ["Law Firm", "Legal Services", "Corporate Legal", "Legal Department"]
            },
            
            # Technology
            "technology": {
                "keywords": ["software engineer", "developer", "programmer", "data scientist", "devops", "tech", "engineer"],
                "normalized_titles": {"software engineer": "Software Engineer", "developer": "Software Developer", "programmer": "Software Engineer", "data scientist": "Data Scientist"},
                "industry_keywords": ["Technology", "Software", "Tech Company", "Startup", "SaaS"]
            },
            
            # Business/Sales/Marketing
            "business": {
                "keywords": ["sales", "marketing", "business development", "account executive", "sales rep", "marketer"],
                "normalized_titles": {"sales": "Sales Representative", "marketing": "Marketing Manager", "business development": "Business Development"},
                "industry_keywords": ["Sales", "Marketing", "Business Development", "Account Management"]
            },
            
            # Finance/Accounting
            "finance": {
                "keywords": ["accountant", "cpa", "financial advisor", "finance", "accounting", "controller", "cfo"],
                "normalized_titles": {"accountant": "Accountant", "cpa": "Certified Public Accountant", "financial advisor": "Financial Advisor"},
                "industry_keywords": ["Accounting Firm", "Finance", "Financial Services", "Investment"]
            },
            
            # Education
            "education": {
                "keywords": ["teacher", "professor", "educator", "principal", "instructor", "academic"],
                "normalized_titles": {"teacher": "Teacher", "professor": "Professor", "educator": "Educator"},
                "industry_keywords": ["School", "University", "Education", "Academic Institution"]
            },
            
            # Operations/Management
            "operations": {
                "keywords": ["manager", "director", "supervisor", "executive", "operations", "coo", "ceo"],
                "normalized_titles": {"manager": "Manager", "director": "Director", "supervisor": "Supervisor", "executive": "Executive"},
                "industry_keywords": ["Management", "Operations", "Corporate", "Administration"]
            },
            
            # HR/Recruiting
            "human_resources": {
                "keywords": ["hr", "human resources", "recruiter", "talent acquisition", "hr manager", "people ops"],
                "normalized_titles": {"hr": "HR Manager", "recruiter": "Recruiter", "talent acquisition": "Talent Acquisition Specialist"},
                "industry_keywords": ["Human Resources", "Recruiting", "Talent Acquisition", "People Operations"]
            }
        }
        
        # Find best matching category
        best_category = "general"
        best_match_count = 0
        normalized_title = job_title.title()
        industry_keywords = []
        
        for category, info in role_categories.items():
            match_count = sum(1 for keyword in info["keywords"] if keyword in title_lower)
            if match_count > best_match_count:
                best_match_count = match_count
                best_category = category
                industry_keywords = info["industry_keywords"]
                
                # Find best normalized title
                for keyword, norm_title in info["normalized_titles"].items():
                    if keyword in title_lower:
                        normalized_title = norm_title
                        break
        
        return {
            "original_title": job_title,
            "normalized_title": normalized_title,
            "category": best_category,
            "industry_keywords": industry_keywords,
            "confidence": best_match_count
        }
    
    async def _search_location_with_strategies(
        self, 
        job_title: str, 
        location: str, 
        limit: int, 
        role_info: Dict[str, Any],
        company_size: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search a location using multiple strategies for better coverage"""
        try:
            candidates = []
            
            # Strategy 1: Direct title search
            result = self.apollo.search_candidates(
                job_title=job_title,
                location=location,
                limit=limit,
                require_email=False,  # Filter later after unlocking
                company_size=company_size,
                unlock_emails=False   # Do this at the end for all candidates
            )
            
            if result.get("success") and result.get("candidates"):
                strategy_candidates = result.get("candidates", [])
                for candidate in strategy_candidates:
                    candidate["search_strategy"] = "direct_title"
                    candidate["search_location"] = location
                candidates.extend(strategy_candidates)
                logger.info(f"✅ Strategy 1 (direct): {len(strategy_candidates)} candidates in {location}")
            
            # Strategy 2: Industry keyword search (if we don't have enough)
            if len(candidates) < limit and role_info.get("industry_keywords"):
                for keyword in role_info["industry_keywords"][:2]:  # Try top 2 keywords
                    result = self.apollo.search_candidates(
                        job_title=keyword,
                        location=location,
                        limit=max(5, limit - len(candidates)),
                        require_email=False,
                        company_size=company_size,
                        unlock_emails=False
                    )
                    
                    if result.get("success") and result.get("candidates"):
                        strategy_candidates = result.get("candidates", [])
                        for candidate in strategy_candidates:
                            candidate["search_strategy"] = f"industry_keyword_{keyword}"
                            candidate["search_location"] = location
                        candidates.extend(strategy_candidates)
                        logger.info(f"✅ Strategy 2 ({keyword}): {len(strategy_candidates)} additional candidates")
                        
                        if len(candidates) >= limit:
                            break
            
            # Remove duplicates based on email/LinkedIn
            seen = set()
            unique_candidates = []
            for candidate in candidates:
                # Create dedup key
                emails = candidate.get("emails", [])
                linkedin = candidate.get("linkedin_url", "")
                name = candidate.get("name", "")
                
                key = None
                if emails:
                    key = emails[0]
                elif linkedin:
                    key = linkedin
                else:
                    key = f"{name}_{candidate.get('company', '')}"
                
                if key and key not in seen:
                    seen.add(key)
                    unique_candidates.append(candidate)
            
            return unique_candidates[:limit]
            
        except Exception as e:
            logger.error(f"❌ Location search failed for {location}: {e}")
            return []
    
    async def _create_universal_campaign(
        self,
        job_title: str,
        role_category: str,
        candidates: List[Dict[str, Any]],
        campaign_name: str,
        send_immediately: bool,
        delay_hours: int,
        locations: List[str],
        industry_keywords: List[str]
    ) -> Dict[str, Any]:
        """Create universal campaign with role-specific templates"""
        try:
            campaign_id = f"universal_campaign_{int(datetime.now().timestamp())}"
            
            # Get role-specific email templates
            email_templates = self._get_role_templates(job_title, role_category, locations, industry_keywords)
            
            # Create campaign data
            campaign_data = {
                "id": campaign_id,
                "name": campaign_name,
                "type": f"{role_category}_outreach",
                "status": "ready" if send_immediately else "scheduled",
                "target_audience": f"{job_title} professionals",
                "job_title": job_title,
                "role_category": role_category,
                "locations": locations,
                "candidates": candidates,
                "verified_count": len([c for c in candidates if c.get("verified", True)]),
                "email_templates": email_templates,
                "send_immediately": send_immediately,
                "delay_hours": delay_hours,
                "scheduled_send_time": None if send_immediately else self._calculate_send_time(delay_hours),
                "created_at": datetime.now().isoformat(),
                "platform": "ses",  # Default platform
                "from_email": os.getenv("CAMPAIGN_FROM_EMAIL", "outreach@coogi.ai"),
                "from_name": os.getenv("CAMPAIGN_FROM_NAME", "Coogi Talent Team"),
                "unsubscribe_url": os.getenv("UNSUBSCRIBE_URL", "https://coogi.ai/unsubscribe"),
                "tracking_enabled": True,
                "personalization_enabled": True,
                "industry_keywords": industry_keywords,
                "auto_campaign": True,
            }
            
            # Save campaign data
            await self._save_campaign_data(campaign_data)
            
            # Create campaign metrics in analytics
            await campaign_analytics.create_campaign_metrics(
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                platform="ses",
                total_recipients=len(candidates),
                campaign_type=f"{role_category}_outreach",
                target_audience=f"{job_title} professionals"
            )
            
            # Add recipients to analytics
            for candidate in candidates:
                emails = candidate.get("emails", [])
                if emails:
                    await campaign_analytics.add_recipient_activity(
                        campaign_id=campaign_id,
                        recipient_email=emails[0],
                        recipient_name=candidate.get("name", "Unknown"),
                        company=candidate.get("company", "Unknown"),
                        title=candidate.get("title", "Unknown"),
                        status="added"
                    )
            
            # Execute immediately if requested
            if send_immediately:
                execution_result = await live_email_service.execute_campaign(campaign_data)
                campaign_data["execution_result"] = execution_result
                campaign_data["status"] = "sent" if execution_result.get("success") else "failed"
                
                # Update analytics with execution results
                if execution_result.get("success"):
                    sent_count = execution_result.get("sent_count", 0)
                    await campaign_analytics.update_campaign_metrics(
                        campaign_id=campaign_id,
                        emails_sent=sent_count,
                        executed_at=datetime.now().isoformat()
                    )
            
            logger.info(f"✅ Universal campaign created: {campaign_id}")
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "job_title": job_title,
                "role_category": role_category,
                "candidates_count": len(candidates),
                "verified_count": campaign_data["verified_count"],
                "status": campaign_data["status"],
                "scheduled_send_time": campaign_data["scheduled_send_time"],
                "email_templates_count": len(email_templates),
                "platform": campaign_data["platform"],
                "campaign_data": campaign_data,
                "execution_result": campaign_data.get("execution_result")
            }
            
        except Exception as e:
            logger.error(f"❌ Universal campaign creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": None,
            }
    
    def _get_role_templates(self, job_title: str, role_category: str, locations: List[str], industry_keywords: List[str]) -> List[Dict[str, Any]]:
        """Get role-specific email templates"""
        
        location_text = f" in {', '.join(locations[:2])}" if locations else ""
        if len(locations) > 2:
            location_text += f" and {len(locations)-2} other locations"
        
        # Role-specific template variations
        role_templates = {
            "medical": {
                "subject_prefix": "Healthcare Opportunity",
                "role_specific_benefits": [
                    "Competitive salary packages with comprehensive benefits",
                    "State-of-the-art medical facilities and equipment",
                    "Continuing medical education support and CME allowances",
                    "Flexible scheduling options and work-life balance",
                    "Malpractice insurance coverage and legal support"
                ],
                "role_context": "healthcare practice"
            },
            "legal": {
                "subject_prefix": "Legal Career Opportunity",
                "role_specific_benefits": [
                    "Competitive compensation with partnership track opportunities",
                    "Access to cutting-edge legal technology and research tools",
                    "Professional development and CLE support",
                    "Collaborative team environment with experienced attorneys",
                    "Diverse practice areas and high-profile client base"
                ],
                "role_context": "law firm"
            },
            "technology": {
                "subject_prefix": "Tech Opportunity",
                "role_specific_benefits": [
                    "Competitive salary with equity opportunities",
                    "Latest technology stack and development tools",
                    "Remote work flexibility and modern office spaces",
                    "Professional development budget for conferences and training",
                    "Collaborative team culture with growth opportunities"
                ],
                "role_context": "technology company"
            },
            "finance": {
                "subject_prefix": "Finance Opportunity",
                "role_specific_benefits": [
                    "Competitive compensation with performance bonuses",
                    "Professional development and certification support",
                    "Access to financial planning tools and resources",
                    "Career advancement opportunities and mentorship",
                    "Comprehensive benefits package"
                ],
                "role_context": "financial services"
            },
            "education": {
                "subject_prefix": "Education Opportunity",
                "role_specific_benefits": [
                    "Competitive salary with tenure opportunities",
                    "Professional development and conference attendance",
                    "Research support and sabbatical opportunities",
                    "Collaborative academic environment",
                    "Comprehensive benefits and retirement planning"
                ],
                "role_context": "educational institution"
            }
        }
        
        # Get role-specific template data or use default
        template_data = role_templates.get(role_category, {
            "subject_prefix": "Professional Opportunity",
            "role_specific_benefits": [
                "Competitive compensation package",
                "Professional development opportunities",
                "Excellent work-life balance",
                "Collaborative team environment",
                "Growth and advancement opportunities"
            ],
            "role_context": "organization"
        })
        
        benefits_text = "\n".join([f"• {benefit}" for benefit in template_data["role_specific_benefits"]])
        
        templates = [
            {
                "step": 1,
                "delay_days": 0,
                "subject": f"{template_data['subject_prefix']}{location_text} - {job_title} Position",
                "body": f"""Hi {{{{first_name}}}},

I hope this message finds you well! I came across your profile and was impressed by your expertise in {job_title.lower()}.

We're currently working with several top-tier {template_data['role_context']}s{location_text} that are looking for talented {job_title} professionals like yourself. These positions offer:

{benefits_text}

Would you be open to a brief conversation about these opportunities? I'd love to learn more about your career goals and see if there's a good match.

Best regards,
{{{{from_name}}}}
{{{{from_email}}}}

P.S. Even if you're not actively looking, I'd be happy to keep you in mind for future opportunities that might be a perfect fit.""",
                "personalization_fields": ["first_name", "company", "location", "title"],
                "tracking_enabled": True,
            },
            {
                "step": 2,
                "delay_days": 3,
                "subject": f"Quick follow-up - {job_title} positions still available",
                "body": f"""Hi {{{{first_name}}}},

I wanted to follow up on my previous message about {job_title} opportunities{location_text}.

I understand how busy things can get in {role_category}, so I'll keep this brief.

Our clients are specifically looking for experienced {job_title} professionals, and based on your background at {{{{company}}}}, I think you'd be a great fit for several positions we're currently filling.

Would you have 10 minutes this week for a quick call? I can share more details about:
• Specific {template_data['role_context']} types and specializations available
• Compensation ranges and benefits packages
• Locations and {template_data['role_context']} cultures

No pressure at all - just wanted to make sure you had the opportunity to learn more.

Best,
{{{{from_name}}}}""",
                "personalization_fields": ["first_name", "company", "location"],
                "tracking_enabled": True,
            },
            {
                "step": 3,
                "delay_days": 7,
                "subject": "Last note - thought you might find this interesting",
                "body": f"""Hi {{{{first_name}}}},

I hope you don't mind one last follow-up. I wanted to share something that might interest you as a {job_title}.

We just had a {job_title} join one of our client {template_data['role_context']}s{location_text}, and they mentioned how refreshing it was to find a workplace that truly values:
• Professional growth and development
• Work-life balance and flexibility
• Modern tools and technology
• Supportive team environment

If any of this resonates with you, I'd still love to chat. Sometimes the best opportunities come when we're not actively looking.

Feel free to reach out anytime - my contact info is below.

Wishing you all the best in your {job_title} career,
{{{{from_name}}}}
{{{{from_email}}}}

P.S. If you know any other great {job_title} professionals who might be interested, referrals are always appreciated!""",
                "personalization_fields": ["first_name", "location"],
                "tracking_enabled": True,
            }
        ]
        
        return templates
    
    def _calculate_send_time(self, delay_hours: int) -> str:
        """Calculate scheduled send time based on delay"""
        send_time = datetime.now() + timedelta(hours=delay_hours)
        return send_time.isoformat()
    
    async def _save_campaign_data(self, campaign_data: Dict[str, Any]) -> bool:
        """Save campaign data for tracking and execution"""
        try:
            # Ensure campaigns directory exists
            Path("campaigns").mkdir(exist_ok=True)
            
            campaign_file = f"campaigns/{campaign_data['id']}.json"
            with open(campaign_file, 'w', encoding='utf-8') as f:
                json.dump(campaign_data, f, indent=2, default=str)
            
            logger.info(f"💾 Universal campaign data saved: {campaign_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save campaign data: {e}")
            return False

# Global instance
universal_campaign_manager = UniversalAutoCampaignManager()
