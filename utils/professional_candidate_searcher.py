"""
PROFESSIONAL GRADE CANDIDATE SEARCH SYSTEM
Real Apollo.io + Hunter.io integration for direct candidate discovery
NO MOCKS, NO DEMOS, REAL DATA ONLY
"""
import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils.apollo_manager import ApolloManager
from utils.bulletproof_contact_finder import BulletproofContactFinder

logger = logging.getLogger(__name__)

class ProfessionalCandidateSearcher:
    """Professional grade candidate search - Apollo.io + Hunter.io integration"""
    
    def __init__(self):
        """Initialize real API integrations"""
        self.apollo = ApolloManager()
        self.contact_finder = BulletproofContactFinder()
        logger.info("🚀 Professional Candidate Searcher initialized")
    
    async def search_candidates_direct(
        self,
        query: str,
        location_filter: Optional[str] = None,
        company_size: str = "all",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        DIRECT CANDIDATE SEARCH - NO JOB ROUTING
        Uses Apollo.io to find real professionals directly
        """
        try:
            logger.info(f"🎯 DIRECT CANDIDATE SEARCH: '{query}' | Location: {location_filter} | Size: {company_size}")
            
            results = {
                "candidates": [],
                "total_found": 0,
                "sources": [],
                "search_summary": {
                    "query": query,
                    "location": location_filter,
                    "company_size": company_size,
                    "started_at": datetime.now().isoformat()
                }
            }
            
            # STAGE 1: Apollo.io Professional Search
            logger.info("🔍 Stage 1: Apollo.io Professional Search")
            apollo_candidates = await self._search_apollo_candidates(
                query, location_filter, company_size, limit
            )
            
            if apollo_candidates.get("success"):
                candidates = apollo_candidates.get("candidates", [])
                
                # STAGE 1.5: Apollo Email Unlocking (Professional Account)
                logger.info(f"🔓 Stage 1.5: Unlocking emails for {len(candidates)} Apollo candidates")
                unlocked_candidates = await self.apollo.unlock_emails_for_candidates(candidates)
                
                results["candidates"].extend(unlocked_candidates)
                results["sources"].append(f"Apollo.io: {len(unlocked_candidates)} candidates")
                logger.info(f"✅ Apollo.io: {len(unlocked_candidates)} candidates found and processed")
            
            # STAGE 2: Hunter.io Email Enhancement
            logger.info("🔍 Stage 2: Hunter.io Email Enhancement") 
            enhanced_candidates = await self._enhance_with_hunter(results["candidates"])
            results["candidates"] = enhanced_candidates
            
            # STAGE 3: RapidAPI Professional Search
            logger.info("🔍 Stage 3: RapidAPI Professional Search")
            rapidapi_candidates = await self._search_rapidapi_professionals(
                query, location_filter, limit // 2
            )
            if rapidapi_candidates:
                results["candidates"].extend(rapidapi_candidates)
                results["sources"].append(f"RapidAPI: {len(rapidapi_candidates)} candidates")
            
            # STAGE 4: Clearout Email Verification
            logger.info("🔍 Stage 4: Email Verification via Clearout")
            verified_candidates = await self._verify_emails_with_clearout(results["candidates"])
            results["candidates"] = verified_candidates
            
            # STAGE 5: LinkedIn Profile Enhancement
            logger.info("🔍 Stage 5: LinkedIn Profile Enhancement")
            enriched_candidates = await self._enhance_linkedin_profiles(results["candidates"])
            results["candidates"] = enriched_candidates
            
            # Final processing
            results["total_found"] = len(results["candidates"])
            results["search_summary"]["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"🎉 CANDIDATE SEARCH COMPLETE: {results['total_found']} professionals found")
            return {
                "success": True,
                "data": results
            }
            
        except Exception as e:
            logger.error(f"❌ Candidate search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"candidates": [], "total_found": 0}
            }
    
    async def _search_apollo_candidates(
        self,
        query: str,
        location: Optional[str],
        company_size: str,
        limit: int
    ) -> Dict[str, Any]:
        """Search Apollo.io for real candidates with professional account email reveal"""
        try:
            # Parse job title from query with intelligent mapping
            job_title = self._extract_job_title(query)
            
            # Strategy 1: Direct search with email reveal (professional account)
            logger.info(f"🎯 Strategy 1: Searching Apollo.io with email reveal for '{job_title}'")
            result = self.apollo.search_candidates(
                job_title=job_title,
                location=location,
                company_size=company_size if company_size != "all" else None,
                limit=limit,
                require_email=True,
                unlock_emails=True,
                hunter_verify=True
            )
            
            candidates = []
            if result.get("success") and result.get("candidates"):
                candidates.extend(result.get("candidates", []))
                logger.info(f"✅ Strategy 1: Found {len(candidates)} candidates with emails")
            
            # Strategy 2: If no results, try broader keyword search
            if len(candidates) == 0:
                logger.info(f"🎯 Strategy 2: Trying broader keyword search")
                broader_terms = self._get_broader_search_terms(job_title)
                
                for term in broader_terms:
                    result = self.apollo.search_candidates(
                        job_title=term,
                        location=location,
                        company_size=company_size if company_size != "all" else None,
                        limit=limit//len(broader_terms) if len(broader_terms) > 1 else limit,
                        require_email=True,
                        unlock_emails=True,
                        hunter_verify=True
                    )
                    
                    if result.get("success") and result.get("candidates"):
                        new_candidates = result.get("candidates", [])
                        candidates.extend(new_candidates)
                        logger.info(f"✅ Strategy 2 ('{term}'): Found {len(new_candidates)} additional candidates")
                        
                        # Stop if we have enough candidates
                        if len(candidates) >= limit:
                            break
            
            # Strategy 3: If still no results, try industry-specific search
            if len(candidates) == 0:
                logger.info(f"🎯 Strategy 3: Trying industry-specific search")
                industry_terms = self._get_industry_keywords(job_title)
                
                for term in industry_terms:
                    result = self.apollo.search_candidates(
                        job_title=term,
                        location=location,
                        company_size=company_size if company_size != "all" else None,
                        limit=limit//len(industry_terms) if len(industry_terms) > 1 else limit,
                        require_email=True,
                        unlock_emails=True,
                        hunter_verify=True
                    )
                    
                    if result.get("success") and result.get("candidates"):
                        new_candidates = result.get("candidates", [])
                        candidates.extend(new_candidates)
                        logger.info(f"✅ Strategy 3 ('{term}'): Found {len(new_candidates)} additional candidates")
                        
                        if len(candidates) >= limit:
                            break
            
            if len(candidates) == 0:
                logger.warning(f"❌ All Apollo.io search strategies failed for '{query}'")
                return {"success": False, "candidates": []}
            
            # Standardize candidate data
            standardized_candidates = []
            for candidate in candidates[:limit]:  # Limit results
                standardized = self._standardize_candidate_data(candidate, "Apollo.io")
                if standardized:
                    standardized_candidates.append(standardized)
            
            logger.info(f"🎉 Total Apollo.io candidates found: {len(standardized_candidates)}")
            return {
                "success": True,
                "candidates": standardized_candidates
            }
            
        except Exception as e:
            logger.error(f"Apollo.io search error: {e}")
            return {"success": False, "candidates": []}
    
    def _get_broader_search_terms(self, job_title: str) -> List[str]:
        """Get broader search terms for fallback searches"""
        job_title_lower = job_title.lower()
        
        broader_terms_map = {
            "veterinarian": ["Animal Care", "Veterinary", "Animal Health"],
            "physician": ["Doctor", "Medical", "Healthcare"],
            "attorney": ["Legal", "Law", "Counsel"],
            "teacher": ["Education", "Instructor", "Academic"],
            "software engineer": ["Developer", "Engineer", "Programmer"],
            "data scientist": ["Analyst", "Data", "Research"],
            "nurse": ["Healthcare", "Medical", "Nursing"],
            "accountant": ["Finance", "Accounting", "Financial"],
            "sales representative": ["Sales", "Business Development", "Account"],
            "marketing manager": ["Marketing", "Brand", "Digital Marketing"]
        }
        
        for key, broader_terms in broader_terms_map.items():
            if key in job_title_lower:
                return broader_terms
        
        # Default broader terms
        return [job_title.split()[0]] if " " in job_title else []
    
    def _get_industry_keywords(self, job_title: str) -> List[str]:
        """Get industry-specific keywords for targeted searches"""
        job_title_lower = job_title.lower()
        
        industry_keywords_map = {
            "veterinarian": ["Animal Hospital", "Veterinary Clinic", "Pet Care"],
            "physician": ["Hospital", "Medical Center", "Clinic"],
            "attorney": ["Law Firm", "Legal Services", "Corporate Legal"],
            "teacher": ["School", "University", "Education"],
            "software engineer": ["Technology", "Software", "Tech"],
            "data scientist": ["Analytics", "Data Science", "Research"],
            "nurse": ["Hospital", "Healthcare", "Medical"],
            "accountant": ["Accounting Firm", "Finance", "CPA"],
            "sales representative": ["Sales", "Business Development"],
            "marketing manager": ["Marketing Agency", "Brand Management"]
        }
        
        for key, keywords in industry_keywords_map.items():
            if key in job_title_lower:
                return keywords
        
        return []
    
    async def _enhance_with_hunter(self, candidates: List[Dict]) -> List[Dict]:
        """Enhance candidate emails using Hunter.io"""
        enhanced = []
        
        for candidate in candidates:
            try:
                if not candidate.get("email") and candidate.get("company"):
                    # Use Hunter.io to find email
                    company_domain = self._extract_domain(candidate["company"])
                    if company_domain:
                        hunter_result = await self._search_hunter_for_person(
                            candidate.get("first_name", ""),
                            candidate.get("last_name", ""),
                            company_domain
                        )
                        
                        if hunter_result.get("email"):
                            candidate["email"] = hunter_result["email"]
                            candidate["email_verified"] = True
                            candidate["source"] += " + Hunter.io"
                
                enhanced.append(candidate)
                
            except Exception as e:
                logger.warning(f"Hunter enhancement failed for candidate: {e}")
                enhanced.append(candidate)
        
        return enhanced
    
    async def _search_additional_sources(
        self,
        query: str,
        location: Optional[str],
        company_size: str
    ) -> List[Dict]:
        """Search additional professional sources"""
        # This could include RocketReach, ZoomInfo, etc.
        # For now, return empty list - can be expanded
        return []
    
    def _extract_job_title(self, query: str) -> str:
        """Extract and normalize job title from search query for better API results"""
        query_lower = query.lower().strip()
        
        # Professional title mappings for better API results
        title_mappings = {
            # Medical/Healthcare professionals
            "dvm": "Veterinarian",
            "vet doctor": "Veterinarian",
            "veterinarian": "Veterinarian", 
            "vet": "Veterinarian",
            "doctor": "Physician",
            "physician": "Physician",
            "nurse": "Registered Nurse",
            "dentist": "Dentist",
            "pharmacist": "Pharmacist",
            "therapist": "Physical Therapist",
            
            # Legal professionals
            "lawyer": "Attorney",
            "attorney": "Attorney",
            "legal counsel": "Attorney",
            
            # Education
            "teacher": "Teacher",
            "professor": "Professor",
            "educator": "Teacher",
            
            # Finance
            "accountant": "Accountant",
            "cpa": "Certified Public Accountant",
            "financial advisor": "Financial Advisor",
            
            # Tech variations
            "programmer": "Software Engineer",
            "coder": "Software Engineer",
            "developer": "Software Engineer",
            "data scientist": "Data Scientist",
            "analyst": "Data Analyst",
            
            # Sales/Marketing
            "salesperson": "Sales Representative",
            "marketer": "Marketing Manager",
            "sales rep": "Sales Representative",
            
            # Operations
            "manager": "Manager",
            "supervisor": "Supervisor",
            "director": "Director",
            "executive": "Executive"
        }
        
        # Check for direct mappings first
        for key, mapped_title in title_mappings.items():
            if key in query_lower:
                logger.info(f"🔄 Mapped '{query}' to '{mapped_title}' for better API results")
                return mapped_title
        
        # Remove location information for cleaner searches
        location_indicators = [" in ", " at ", " near ", " from "]
        clean_query = query
        for indicator in location_indicators:
            if indicator in query_lower:
                clean_query = query[:query_lower.index(indicator)]
                break
        
        return clean_query.strip()
    
    def _extract_domain(self, company_name: str) -> Optional[str]:
        """Extract domain from company name"""
        # Simple domain extraction - could be enhanced with company database
        company_clean = company_name.lower().replace(" ", "").replace(",", "").replace("inc", "").replace("llc", "")
        return f"{company_clean}.com"
    
    async def _search_hunter_for_person(
        self,
        first_name: str,
        last_name: str,
        domain: str
    ) -> Dict[str, Any]:
        """Search Hunter.io for specific person"""
        try:
            # Use the existing bulletproof contact finder
            results = await asyncio.to_thread(
                self.contact_finder.find_person_email,
                first_name,
                last_name,
                domain
            )
            return results
        except:
            return {}
    
    async def _search_rapidapi_professionals(
        self,
        query: str,
        location: Optional[str],
        limit: int
    ) -> List[Dict]:
        """Search for professionals using RapidAPI sources"""
        try:
            job_title = self._extract_job_title(query)
            logger.info(f"🔍 RapidAPI search for: {job_title} in {location}")
            
            candidates = []
            
            # RapidAPI LinkedIn People Search
            rapidapi_key = os.getenv("RAPIDAPI_KEY")
            if rapidapi_key:
                linkedin_candidates = await self._search_linkedin_via_rapidapi(
                    job_title, location, rapidapi_key, limit // 2
                )
                candidates.extend(linkedin_candidates)
                logger.info(f"✅ RapidAPI LinkedIn: {len(linkedin_candidates)} candidates")
            
            # RapidAPI Contact Finder (ZoomInfo alternative)
            if rapidapi_key and len(candidates) < limit:
                contact_candidates = await self._search_contacts_via_rapidapi(
                    job_title, location, rapidapi_key, limit - len(candidates)
                )
                candidates.extend(contact_candidates)
                logger.info(f"✅ RapidAPI Contacts: {len(contact_candidates)} candidates")
            
            return candidates[:limit]
            
        except Exception as e:
            logger.error(f"RapidAPI search error: {e}")
            return []
    
    async def _verify_emails_with_clearout(self, candidates: List[Dict]) -> List[Dict]:
        """Verify email addresses using Clearout API"""
        verified_candidates = []
        clearout_key = os.getenv("CLEAROUT_API_KEY")
        
        for candidate in candidates:
            try:
                email = candidate.get("email", "")
                
                # Skip obviously fake emails
                if "email_not_unlocked" in email or not email or "@" not in email:
                    candidate["email_verified"] = False
                    candidate["email_quality"] = "invalid"
                    verified_candidates.append(candidate)
                    continue
                
                # Use Clearout API if available
                if clearout_key:
                    verification_result = await self._clearout_verify_email(email, clearout_key)
                    candidate["email_verified"] = verification_result.get("is_valid", False)
                    candidate["email_quality"] = verification_result.get("quality", "unknown")
                    candidate["clearout_score"] = verification_result.get("score", 0)
                else:
                    # Basic email validation if no Clearout API
                    candidate["email_verified"] = self._basic_email_validation(email)
                    candidate["email_quality"] = "basic_check"
                
                verified_candidates.append(candidate)
                
            except Exception as e:
                logger.warning(f"Email verification failed for candidate: {e}")
                candidate["email_verified"] = False
                candidate["email_quality"] = "error"
                verified_candidates.append(candidate)
        
        logger.info(f"📧 Email verification: {sum(1 for c in verified_candidates if c.get('email_verified'))} verified emails")
        return verified_candidates
    
    async def _enhance_linkedin_profiles(self, candidates: List[Dict]) -> List[Dict]:
        """Enhance candidates with additional LinkedIn profile data"""
        enhanced_candidates = []
        rapidapi_key = os.getenv("RAPIDAPI_KEY")
        
        for candidate in candidates:
            try:
                linkedin_url = candidate.get("linkedin_url", "")
                
                if linkedin_url and rapidapi_key:
                    # Extract LinkedIn profile data via RapidAPI
                    profile_data = await self._scrape_linkedin_profile(linkedin_url, rapidapi_key)
                    
                    if profile_data:
                        candidate.update({
                            "has_linkedin": True,
                            "profile_complete": True,
                            "linkedin_summary": profile_data.get("summary", ""),
                            "linkedin_experience": profile_data.get("experience", []),
                            "linkedin_education": profile_data.get("education", []),
                            "linkedin_skills": profile_data.get("skills", []),
                            "linkedin_connections": profile_data.get("connections", 0),
                            "profile_quality_score": self._calculate_profile_score(profile_data)
                        })
                        logger.debug(f"✅ Enhanced LinkedIn profile for {candidate.get('name', 'Unknown')}")
                    else:
                        candidate["has_linkedin"] = True
                        candidate["profile_complete"] = False
                elif linkedin_url:
                    candidate["has_linkedin"] = True
                    candidate["profile_complete"] = False
                else:
                    candidate["has_linkedin"] = False
                    candidate["profile_complete"] = False
                
                enhanced_candidates.append(candidate)
                
            except Exception as e:
                logger.warning(f"LinkedIn enhancement failed for candidate: {e}")
                candidate["has_linkedin"] = bool(candidate.get("linkedin_url"))
                candidate["profile_complete"] = False
                enhanced_candidates.append(candidate)
        
        enhanced_count = sum(1 for c in enhanced_candidates if c.get("profile_complete"))
        logger.info(f"🔗 LinkedIn enhancement: {enhanced_count} profiles enhanced")
        return enhanced_candidates
    
    def _standardize_candidate_data(self, raw_candidate: Dict, source: str) -> Optional[Dict]:
        """Standardize candidate data format"""
        try:
            # Handle organization data properly
            org = raw_candidate.get("organization", {})
            company_name = ""
            if isinstance(org, dict):
                company_name = org.get("name", "")
            elif isinstance(org, str):
                company_name = org
            elif raw_candidate.get("company"):
                company_name = raw_candidate.get("company", "")
            
            return {
                "contact_id": raw_candidate.get("id", f"apollo_{int(datetime.now().timestamp())}"),
                "first_name": raw_candidate.get("first_name", ""),
                "last_name": raw_candidate.get("last_name", ""),
                "name": f"{raw_candidate.get('first_name', '')} {raw_candidate.get('last_name', '')}".strip(),
                "email": raw_candidate.get("email", ""),
                "title": raw_candidate.get("title", ""),
                "company": company_name,
                "organization": org,  # Keep full organization data
                "linkedin_url": raw_candidate.get("linkedin_url", ""),
                "phone": raw_candidate.get("phone", ""),
                "verified": bool(raw_candidate.get("email") and "@" in str(raw_candidate.get("email", ""))),
                "source": source,
                "confidence_score": 0.8 if raw_candidate.get("email") else 0.5,
                "created_at": datetime.now().isoformat(),
                "location": raw_candidate.get("location", ""),
                "industry": org.get("industry", "") if isinstance(org, dict) else "",
                "company_size": org.get("estimated_num_employees", "") if isinstance(org, dict) else "",
                "seniority": raw_candidate.get("seniority", ""),
                "departments": raw_candidate.get("departments", ""),
                "contact_accuracy": raw_candidate.get("contact_accuracy", "unknown")
            }
        except Exception as e:
            logger.warning(f"Failed to standardize candidate data: {e}")
            return None

    async def _search_linkedin_via_rapidapi(
        self,
        job_title: str,
        location: Optional[str],
        rapidapi_key: str,
        limit: int
    ) -> List[Dict]:
        """Search LinkedIn professionals via RapidAPI"""
        try:
            # This is a placeholder for RapidAPI LinkedIn search
            # In a real implementation, you would use a RapidAPI LinkedIn service
            logger.info(f"🔍 RapidAPI LinkedIn search for {job_title} (placeholder)")
            
            # For now, return empty list since we're focusing on Apollo.io
            # You can implement this later with actual RapidAPI LinkedIn services
            return []
            
        except Exception as e:
            logger.error(f"RapidAPI LinkedIn search error: {e}")
            return []

    async def _search_contacts_via_rapidapi(
        self,
        job_title: str,
        location: Optional[str],
        rapidapi_key: str,
        limit: int
    ) -> List[Dict]:
        """Search contacts via RapidAPI (ZoomInfo alternative)"""
        try:
            # This is a placeholder for RapidAPI contact search
            logger.info(f"🔍 RapidAPI contact search for {job_title} (placeholder)")
            
            # For now, return empty list since we're focusing on Apollo.io + Hunter.io
            return []
            
        except Exception as e:
            logger.error(f"RapidAPI contact search error: {e}")
            return []

    async def _clearout_verify_email(self, email: str, clearout_key: str) -> Dict[str, Any]:
        """Verify email using Clearout API"""
        try:
            import requests
            
            url = "https://api.clearout.io/v2/email_verify/instant"
            headers = {
                "Authorization": f"Bearer {clearout_key}",
                "Content-Type": "application/json"
            }
            
            payload = {"email": email}
            
            response = await asyncio.to_thread(
                requests.post, url, headers=headers, json=payload, timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "is_valid": result.get("status") == "valid",
                    "quality": result.get("status", "unknown"),
                    "score": result.get("confidence_score", 0),
                    "details": result
                }
            else:
                logger.warning(f"Clearout API error: {response.status_code}")
                return {"is_valid": False, "quality": "api_error", "score": 0}
                
        except Exception as e:
            logger.error(f"Clearout verification error: {e}")
            return {"is_valid": False, "quality": "error", "score": 0}

    def _basic_email_validation(self, email: str) -> bool:
        """Basic email validation without external API"""
        try:
            import re
            
            # Basic email regex
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
            
        except Exception:
            return False

    async def _scrape_linkedin_profile(self, linkedin_url: str, rapidapi_key: str) -> Optional[Dict]:
        """Scrape LinkedIn profile data via RapidAPI"""
        try:
            # This is a placeholder for LinkedIn profile scraping
            logger.info(f"🔍 LinkedIn profile scraping for {linkedin_url} (placeholder)")
            
            # For now, return None since this requires specific RapidAPI LinkedIn scrapers
            # You can implement this later with actual RapidAPI LinkedIn profile services
            return None
            
        except Exception as e:
            logger.error(f"LinkedIn profile scraping error: {e}")
            return None

    def _calculate_profile_score(self, profile_data: Dict) -> float:
        """Calculate profile quality score"""
        try:
            score = 0.0
            
            # Basic scoring based on profile completeness
            if profile_data.get("summary"):
                score += 0.2
            if profile_data.get("experience"):
                score += 0.3
            if profile_data.get("education"):
                score += 0.2
            if profile_data.get("skills"):
                score += 0.2
            if profile_data.get("connections", 0) > 50:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5

# Initialize global instance
professional_candidate_searcher = ProfessionalCandidateSearcher()
