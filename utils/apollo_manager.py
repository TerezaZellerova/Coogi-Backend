"""
Apollo.io API Manager for COOGI
Handles candidate search through Apollo.io API
"""
import os
import requests
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ApolloManager:
    """Apollo.io API manager for candidate search"""
    
    def __init__(self):
        """Initialize Apollo.io API client"""
        self.api_key = os.getenv('APOLLO_API_KEY', '')
        self.base_url = "https://api.apollo.io/v1"
        
        # Rate limiting
        self.requests_per_second = 2
        self.last_request_time = 0
        
        if self.api_key:
            logger.info("✅ Apollo Manager initialized successfully")
        else:
            logger.warning("⚠️  Apollo Manager initialized without API key")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make rate-limited request to Apollo API"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < 0.5:  # 0.5 seconds between requests
                time.sleep(0.5 - time_since_last)
            
            url = f"{self.base_url}{endpoint}"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key
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
                logger.error(f"Apollo API error: {response.status_code} - {response.text}")
                return {"error": f"API request failed: {response.status_code}", "message": response.text}
                
        except Exception as e:
            logger.error(f"Apollo request failed: {e}")
            return {"error": str(e)}
    
    def search_candidates(
        self,
        job_title: str,
        location: Optional[str] = None,
        domain: Optional[str] = None,
        company_size: Optional[str] = None,
        limit: int = 10,
        require_email: bool = False
    ) -> Dict[str, Any]:
        """Search for job candidates using Apollo.io"""
        try:
            # Get optimized search terms for better results
            search_terms = self._get_optimized_search_terms(job_title)
            
            # Build search payload
            search_payload = {
                "page": 1,
                "per_page": min(limit, 25),  # Apollo.io max is 25 per page
                "person_titles": search_terms
            }
            
            # Optionally add email filters if higher quality results are needed
            if require_email:
                search_payload["contact_email_status"] = ["verified", "guessed"]
                logger.info("🔒 Email verification required - using stricter filters")
            
            # Add location filter if provided
            if location:
                search_payload["person_locations"] = [location]
            
            # Add company domain filter if provided
            if domain:
                search_payload["organization_domains"] = [domain]
            
            # Add company size filter if provided
            if company_size:
                # Map common company sizes to Apollo format
                size_mapping = {
                    "startup": "1,10",
                    "small": "11,50", 
                    "medium": "51,250",
                    "large": "251,1000",
                    "enterprise": "1001+"
                }
                if company_size.lower() in size_mapping:
                    search_payload["organization_num_employees_ranges"] = [size_mapping[company_size.lower()]]
            
            logger.info(f"🔍 Searching Apollo.io for: {job_title}")
            logger.info(f"🎯 Using search terms: {search_terms}")
            logger.info(f"📍 Location filter: {location}")
            logger.info(f"📦 Full search payload: {search_payload}")
            
            result = self._make_request("POST", "/mixed_people/search", search_payload)
            
            logger.info(f"📊 API Response: {result.get('pagination', {})} people found")
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            
            # Parse and standardize results
            candidates = []
            people = result.get("people", [])
            
            for person in people[:limit]:
                candidate = {
                    "name": person.get("name", "Unknown"),
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "email": person.get("email", ""),
                    "title": person.get("title", ""),
                    "company": person.get("organization", {}).get("name", "") if person.get("organization") else "",
                    "domain": person.get("organization", {}).get("primary_domain", "") if person.get("organization") else "",
                    "location": person.get("city", ""),
                    "linkedin_url": person.get("linkedin_url", ""),
                    "phone": person.get("phone", ""),
                    "seniority": person.get("seniority", ""),
                    "departments": person.get("departments", []),
                    "functions": person.get("functions", []),
                    "email_status": person.get("email_status", ""),
                    "apollo_id": person.get("id", ""),
                    "source": "apollo.io"
                }
                
                # Add candidates even without unlocked emails - we can process them later
                # Skip only if completely missing basic info
                if candidate["name"] and candidate["title"]:
                    candidates.append(candidate)
            
            logger.info(f"✅ Found {len(candidates)} candidates from Apollo.io")
            
            return {
                "success": True,
                "candidates": candidates,
                "total_found": len(candidates),
                "search_params": {
                    "job_title": job_title,
                    "location": location,
                    "domain": domain,
                    "company_size": company_size
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Apollo candidate search failed: {e}")
            return {"success": False, "error": str(e)}

    def search_candidates_with_emails(
        self,
        job_title: str,
        location: Optional[str] = None,
        domain: Optional[str] = None,
        company_size: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for job candidates with automatic email unlocking using professional account"""
        try:
            # Get optimized search terms for better results
            search_terms = self._get_optimized_search_terms(job_title)
            
            # Build search payload with reveal_email for professional accounts
            search_payload = {
                "page": 1,
                "per_page": min(limit, 25),  # Apollo.io max is 25 per page
                "person_titles": search_terms,
                "reveal_email": True  # Professional account feature
            }
            
            # Add location filter if provided
            if location:
                search_payload["person_locations"] = [location]
            
            # Add company domain filter if provided
            if domain:
                search_payload["organization_domains"] = [domain]
            
            # Add company size filter if provided
            if company_size:
                # Map common company sizes to Apollo format
                size_mapping = {
                    "startup": "1,10",
                    "small": "11,50", 
                    "medium": "51,250",
                    "large": "251,1000",
                    "enterprise": "1001+"
                }
                if company_size.lower() in size_mapping:
                    search_payload["organization_num_employees_ranges"] = [size_mapping[company_size.lower()]]
            
            logger.info(f"🔍 Searching Apollo.io with email reveal for: {job_title}")
            logger.info(f"🎯 Using search terms: {search_terms}")
            
            result = self._make_request("POST", "/mixed_people/search", search_payload)
            
            logger.info(f"📊 API Response: {result.get('pagination', {})} people found")
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            
            # Parse and standardize results
            candidates = []
            people = result.get("people", [])
            
            for person in people[:limit]:
                # Better organization parsing
                org = person.get("organization", {})
                company_name = ""
                if isinstance(org, dict):
                    company_name = org.get("name", "")
                elif isinstance(org, str):
                    company_name = org
                
                candidate = {
                    "id": person.get("id", f"apollo_{int(time.time())}"),
                    "name": person.get("name", "Unknown"),
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "email": person.get("email", ""),
                    "title": person.get("title", ""),
                    "company": company_name,
                    "organization": org,  # Keep full org data
                    "domain": org.get("primary_domain", "") if isinstance(org, dict) else "",
                    "location": person.get("city", ""),
                    "linkedin_url": person.get("linkedin_url", ""),
                    "phone": person.get("phone", ""),
                    "seniority": person.get("seniority", ""),
                    "departments": person.get("departments", []),
                    "functions": person.get("functions", []),
                    "email_status": person.get("email_status", ""),
                    "apollo_id": person.get("id", ""),
                    "source": "apollo.io",
                    "industry": org.get("industry", "") if isinstance(org, dict) else "",
                    "company_size": org.get("estimated_num_employees", "") if isinstance(org, dict) else "",
                    "contact_accuracy": person.get("contact_accuracy", "unknown")
                }
                
                # Add candidates even without unlocked emails - we can process them later
                # Skip only if completely missing basic info
                if candidate["name"] and candidate["title"]:
                    candidates.append(candidate)
            
            logger.info(f"✅ Found {len(candidates)} candidates from Apollo.io with email reveal")
            
            return {
                "success": True,
                "candidates": candidates,
                "total_found": len(candidates),
                "search_params": {
                    "job_title": job_title,
                    "location": location,
                    "domain": domain,
                    "company_size": company_size,
                    "email_reveal": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Apollo candidate search with emails failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_person_details(self, apollo_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific person"""
        try:
            result = self._make_request("GET", f"/people/{apollo_id}")
            
            if "error" not in result:
                person = result.get("person", {})
                return {
                    "success": True,
                    "person": person,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Apollo person details failed: {e}")
            return {"success": False, "error": str(e)}
    
    def test_api_connection(self) -> Dict[str, Any]:
        """Test Apollo API connection and key validity"""
        try:
            start_time = time.time()
            
            # Test with a simple search
            test_payload = {
                "q_keywords": "software engineer",
                "page": 1,
                "per_page": 1
            }
            
            result = self._make_request("POST", "/mixed_people/search", test_payload)
            response_time = time.time() - start_time
            
            if "error" not in result:
                return {
                    "status": "operational",
                    "api_key_valid": True,
                    "response_time_ms": round(response_time * 1000, 2),
                    "credits_used": result.get("pagination", {}).get("total_entries", 0),
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
            logger.error(f"Apollo API test failed: {e}")
            return {
                "status": "error",
                "api_key_valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_optimized_search_terms(self, job_title: str) -> List[str]:
        """Get optimized search terms based on job title for better Apollo results"""
        job_title_lower = job_title.lower().strip()
        
        # Optimized mappings based on successful cURL tests
        search_mappings = {
            # Veterinary professionals - use multiple variations
            "vet doctor": ["Veterinarian", "Vet Doctor", "Veterinary Doctor", "Doctor of Veterinary Medicine"],
            "veterinarian": ["Veterinarian", "Vet Doctor", "Veterinary Doctor", "DVM"],
            "vet": ["Veterinarian", "Vet Doctor", "Animal Care", "Animal Health"],
            
            # Medical professionals
            "doctor": ["Physician", "Doctor", "Medical Doctor", "MD"],
            "physician": ["Physician", "Doctor", "Medical Doctor", "MD"],
            "nurse": ["Registered Nurse", "Nurse", "RN", "Nursing"],
            "dentist": ["Dentist", "DDS", "Dental", "Oral Health"],
            "pharmacist": ["Pharmacist", "PharmD", "Pharmacy", "Pharmaceutical"],
            "therapist": ["Physical Therapist", "Therapist", "PT", "Rehabilitation"],
            "surgeon": ["Surgeon", "Surgery", "MD", "Surgical"],
            
            # Legal professionals  
            "lawyer": ["Attorney", "Lawyer", "Legal Counsel", "Esq"],
            "attorney": ["Attorney", "Lawyer", "Legal Counsel", "JD"],
            "paralegal": ["Paralegal", "Legal Assistant", "Legal Support"],
            
            # Tech professionals
            "software engineer": ["Software Engineer", "Developer", "Software Developer", "Engineer"],
            "developer": ["Developer", "Software Engineer", "Software Developer", "Programmer"],
            "programmer": ["Software Engineer", "Developer", "Programmer", "Coder"],
            "data scientist": ["Data Scientist", "Data Analyst", "Analytics", "Data"],
            "devops": ["DevOps Engineer", "Site Reliability Engineer", "Infrastructure"],
            "frontend": ["Frontend Developer", "Front-end Developer", "UI Developer"],
            "backend": ["Backend Developer", "Back-end Developer", "Server Developer"],
            "fullstack": ["Full Stack Developer", "Full-stack Developer", "Fullstack"],
            
            # Business professionals
            "sales": ["Sales Representative", "Sales", "Account Executive", "Business Development"],
            "marketing": ["Marketing Manager", "Marketing", "Brand Manager", "Digital Marketing"],
            "accountant": ["Accountant", "CPA", "Financial Analyst", "Accounting"],
            "hr": ["Human Resources", "HR Manager", "Recruiter", "People Operations"],
            "project manager": ["Project Manager", "PM", "Program Manager", "Scrum Master"],
            "consultant": ["Consultant", "Advisory", "Strategy", "Business Consultant"],
            
            # Education professionals
            "teacher": ["Teacher", "Educator", "Instructor", "Faculty"],
            "professor": ["Professor", "Assistant Professor", "Associate Professor", "PhD"],
            "principal": ["Principal", "School Administrator", "Education Leader"],
            
            # Finance professionals
            "financial advisor": ["Financial Advisor", "Wealth Manager", "Investment Advisor"],
            "banker": ["Banker", "Banking", "Commercial Banking", "Loan Officer"],
            "analyst": ["Financial Analyst", "Business Analyst", "Data Analyst", "Research Analyst"],
            
            # Healthcare specialists
            "physical therapist": ["Physical Therapist", "PT", "Rehabilitation", "Therapy"],
            "occupational therapist": ["Occupational Therapist", "OT", "Rehabilitation"],
            "speech therapist": ["Speech Therapist", "Speech Pathologist", "SLP"],
            
            # Engineering professionals
            "mechanical engineer": ["Mechanical Engineer", "Engineering", "ME", "Manufacturing"],
            "electrical engineer": ["Electrical Engineer", "EE", "Electronics", "Power Systems"],
            "civil engineer": ["Civil Engineer", "Structural Engineer", "Construction"],
            "chemical engineer": ["Chemical Engineer", "Process Engineer", "ChE"]
        }
        
        # Check for direct matches
        for key, terms in search_mappings.items():
            if key in job_title_lower:
                logger.info(f"🎯 Using optimized search terms for '{job_title}': {terms}")
                return terms
        
        # If no match, return original + some generic variations
        variations = [job_title]
        
        # Add common variations
        if " " in job_title:
            words = job_title.split()
            if len(words) >= 2:
                variations.append(words[-1])  # Last word (often the main role)
                variations.append(" ".join(words[:-1]))  # All but last word
        
        logger.info(f"🔍 Using default search terms for '{job_title}': {variations}")
        return variations
    
    def unlock_person_email(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Unlock person's email using Apollo professional credits via people/match"""
        try:
            # Extract person info for matching
            first_name = person_data.get("first_name", "")
            last_name = person_data.get("last_name", "")
            company_name = ""
            
            # Get company name from organization
            org = person_data.get("organization", {})
            if isinstance(org, dict):
                company_name = org.get("name", "")
            elif isinstance(org, str):
                company_name = org
            
            if not first_name or not last_name:
                return {"success": False, "error": "First and last name required"}
            
            logger.info(f"🔓 Unlocking email for {first_name} {last_name} at {company_name}")
            
            # Use people/match endpoint with reveal_email
            match_payload = {
                "first_name": first_name,
                "last_name": last_name,
                "reveal_email": True
            }
            
            # Add organization matching if available
            if company_name:
                match_payload["organization_name"] = company_name
            
            # Add domain if available
            if org and isinstance(org, dict) and org.get("primary_domain"):
                match_payload["domain"] = org.get("primary_domain")
            
            result = self._make_request("POST", "/people/match", match_payload)
            
            if "error" not in result:
                person = result.get("person", {})
                email = person.get("email", "")
                
                if email and "@" in email and "email_not_unlocked" not in email:
                    logger.info(f"✅ Email unlocked successfully: {email}")
                    return {
                        "success": True,
                        "email": email,
                        "person": person,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"⚠️ People/match returned invalid email: {email}")
                    return {"success": False, "error": "Invalid email returned"}
            else:
                logger.error(f"❌ People/match failed: {result['error']}")
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"❌ Email unlock exception: {e}")
            return {"success": False, "error": str(e)}

    async def unlock_emails_for_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Unlock emails for a list of candidates using Apollo professional account"""
        enhanced_candidates = []
        
        for candidate in candidates:
            try:
                current_email = candidate.get("email", "")
                
                # Try to unlock email if it's locked or missing
                if "email_not_unlocked" in str(current_email) or not current_email or "@" not in str(current_email):
                    unlock_result = self.unlock_person_email(candidate)
                    
                    if unlock_result.get("success"):
                        candidate["email"] = unlock_result["email"]
                        candidate["email_status"] = "unlocked"
                        candidate["verified"] = True
                        candidate["confidence_score"] = 0.9
                        
                        # Update person data from match result if available
                        if unlock_result.get("person"):
                            person = unlock_result["person"]
                            if person.get("organization"):
                                candidate["organization"] = person["organization"]
                                if isinstance(person["organization"], dict):
                                    candidate["company"] = person["organization"].get("name", candidate.get("company", ""))
                        
                        logger.info(f"✅ Unlocked email for {candidate.get('name', 'Unknown')}: {unlock_result['email']}")
                    else:
                        logger.warning(f"⚠️ Failed to unlock email for {candidate.get('name', 'Unknown')}: {unlock_result.get('error', 'Unknown error')}")
                else:
                    # Email already exists and is valid
                    candidate["email_status"] = "existing"
                    candidate["verified"] = True
                
                enhanced_candidates.append(candidate)
                
                # Rate limiting - Apollo allows 200 requests per minute for email unlocking
                await asyncio.sleep(0.3)  # ~200 per minute
                
            except Exception as e:
                logger.error(f"❌ Error processing candidate {candidate.get('name', 'Unknown')}: {e}")
                enhanced_candidates.append(candidate)
        
        unlocked_count = sum(1 for c in enhanced_candidates if c.get("email_status") == "unlocked")
        existing_count = sum(1 for c in enhanced_candidates if c.get("email_status") == "existing")
        logger.info(f"📧 Email processing complete: {unlocked_count} unlocked, {existing_count} existing emails")
        
        return enhanced_candidates
    
    def search_candidates_with_emails(
        self,
        job_title: str,
        location: Optional[str] = None,
        domain: Optional[str] = None,
        company_size: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for job candidates with automatic email unlocking using professional account"""
        try:
            # Get optimized search terms for better results
            search_terms = self._get_optimized_search_terms(job_title)
            
            # Build search payload with reveal_email for professional accounts
            search_payload = {
                "page": 1,
                "per_page": min(limit, 25),  # Apollo.io max is 25 per page
                "person_titles": search_terms,
                "reveal_email": True  # Professional account feature
            }
            
            # Add location filter if provided
            if location:
                search_payload["person_locations"] = [location]
            
            # Add company domain filter if provided
            if domain:
                search_payload["organization_domains"] = [domain]
            
            # Add company size filter if provided
            if company_size:
                # Map common company sizes to Apollo format
                size_mapping = {
                    "startup": "1,10",
                    "small": "11,50", 
                    "medium": "51,250",
                    "large": "251,1000",
                    "enterprise": "1001+"
                }
                if company_size.lower() in size_mapping:
                    search_payload["organization_num_employees_ranges"] = [size_mapping[company_size.lower()]]
            
            logger.info(f"🔍 Searching Apollo.io with email reveal for: {job_title}")
            logger.info(f"🎯 Using search terms: {search_terms}")
            logger.info(f"📦 Search payload: {search_payload}")
            
            result = self._make_request("POST", "/mixed_people/search", search_payload)
            
            logger.info(f"📊 API Response: {result.get('pagination', {})} people found")
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            
            # Parse and standardize results
            candidates = []
            people = result.get("people", [])
            
            for person in people[:limit]:
                # Better organization parsing
                org = person.get("organization", {})
                company_name = ""
                if isinstance(org, dict):
                    company_name = org.get("name", "")
                elif isinstance(org, str):
                    company_name = org
                
                candidate = {
                    "id": person.get("id", f"apollo_{int(time.time())}"),
                    "name": person.get("name", "Unknown"),
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "email": person.get("email", ""),
                    "title": person.get("title", ""),
                    "company": company_name,
                    "organization": org,  # Keep full org data
                    "domain": org.get("primary_domain", "") if isinstance(org, dict) else "",
                    "location": person.get("city", ""),
                    "linkedin_url": person.get("linkedin_url", ""),
                    "phone": person.get("phone", ""),
                    "seniority": person.get("seniority", ""),
                    "departments": person.get("departments", []),
                    "functions": person.get("functions", []),
                    "email_status": person.get("email_status", ""),
                    "apollo_id": person.get("id", ""),
                    "source": "apollo.io",
                    "industry": org.get("industry", "") if isinstance(org, dict) else "",
                    "company_size": org.get("estimated_num_employees", "") if isinstance(org, dict) else "",
                    "contact_accuracy": person.get("contact_accuracy", "unknown")
                }
                
                # Add candidates even without unlocked emails - we can process them later
                # Skip only if completely missing basic info
                if candidate["name"] and candidate["title"]:
                    candidates.append(candidate)
            
            logger.info(f"✅ Found {len(candidates)} candidates from Apollo.io with email reveal")
            
            return {
                "success": True,
                "candidates": candidates,
                "total_found": len(candidates),
                "search_params": {
                    "job_title": job_title,
                    "location": location,
                    "domain": domain,
                    "company_size": company_size,
                    "email_reveal": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Apollo candidate search with emails failed: {e}")
            return {"success": False, "error": str(e)}
