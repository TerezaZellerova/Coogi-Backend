"""
JSearch API Manager for COOGI
Handles job search through JSearch RapidAPI for comprehensive job data
"""
import os
import requests
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JSearchManager:
    """JSearch RapidAPI job search manager"""
    
    def __init__(self):
        """Initialize JSearch API client"""
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY', '')
        self.base_url = "https://jsearch.p.rapidapi.com"
        
        # Rate limiting
        self.requests_per_minute = 60
        self.last_request_time = 0
        
        if self.rapidapi_key:
            logger.info("✅ JSearch Manager initialized successfully")
        else:
            logger.warning("⚠️  JSearch Manager initialized without RapidAPI key")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make rate-limited request to JSearch API"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < 1:  # 1 second between requests
                time.sleep(1 - time_since_last)
            
            url = f"{self.base_url}{endpoint}"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            
            self.last_request_time = time.time()
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"JSearch API error: {response.status_code} - {response.text}")
                return {"error": f"API request failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"JSearch request failed: {e}")
            return {"error": str(e)}
    
    def search_jobs(
        self,
        query: str,
        location: str = "United States",
        employment_types: str = "FULLTIME",
        remote_jobs_only: bool = False,
        date_posted: str = "month",
        num_pages: int = 1
    ) -> Dict[str, Any]:
        """Search for jobs using JSearch API"""
        try:
            params = {
                "query": query,
                "location": location,
                "page": "1",
                "num_pages": str(num_pages),
                "date_posted": date_posted,
                "employment_types": employment_types
            }
            
            if remote_jobs_only:
                params["remote_jobs_only"] = "true"
            
            logger.info(f"🔍 Searching JSearch for: {query} in {location}")
            result = self._make_request("/search", params)
            
            if "error" not in result:
                jobs = result.get("data", [])
                logger.info(f"✅ JSearch found {len(jobs)} jobs")
                
                # Standardize job format for COOGI
                standardized_jobs = []
                for job in jobs:
                    standardized_job = self._standardize_job_format(job)
                    standardized_jobs.append(standardized_job)
                
                return {
                    "success": True,
                    "jobs": standardized_jobs,
                    "total_found": len(jobs),
                    "query": query,
                    "location": location,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"JSearch search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _standardize_job_format(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSearch job format to COOGI standard format"""
        return {
            "title": job.get("job_title", ""),
            "company": job.get("employer_name", ""),
            "location": job.get("job_city", "") + ", " + job.get("job_state", ""),
            "description": job.get("job_description", ""),
            "job_url": job.get("job_apply_link", ""),
            "company_website": job.get("employer_website", ""),
            "salary_min": job.get("job_min_salary"),
            "salary_max": job.get("job_max_salary"),
            "salary_currency": job.get("job_salary_currency", "USD"),
            "employment_type": job.get("job_employment_type", ""),
            "date_posted": job.get("job_posted_at_datetime_utc", ""),
            "remote": job.get("job_is_remote", False),
            "job_level": job.get("job_required_experience", {}).get("required_experience_in_months"),
            "benefits": job.get("job_benefits"),
            "highlights": job.get("job_highlights", {}),
            "requirements": job.get("job_required_skills"),
            "job_source": "JSearch",
            "job_id": job.get("job_id", ""),
            "company_type": job.get("employer_company_type", ""),
            "logo_url": job.get("employer_logo", "")
        }
    
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific job"""
        try:
            params = {"job_id": job_id}
            result = self._make_request("/job-details", params)
            
            if "error" not in result:
                job_details = result.get("data", [])
                if job_details:
                    return {
                        "success": True,
                        "job": self._standardize_job_format(job_details[0]),
                        "timestamp": datetime.now().isoformat()
                    }
            
            return {"success": False, "error": "Job not found"}
            
        except Exception as e:
            logger.error(f"JSearch job details failed: {e}")
            return {"success": False, "error": str(e)}
    
    def search_by_company(self, company_name: str, location: str = "United States") -> Dict[str, Any]:
        """Search for jobs at a specific company"""
        try:
            query = f"company:{company_name}"
            return self.search_jobs(query=query, location=location)
            
        except Exception as e:
            logger.error(f"JSearch company search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_salary_estimates(self, job_title: str, location: str = "United States") -> Dict[str, Any]:
        """Get salary estimates for a job title/location"""
        try:
            params = {
                "job_title": job_title,
                "location": location
            }
            
            result = self._make_request("/estimated-salary", params)
            
            if "error" not in result:
                salary_data = result.get("data", [])
                if salary_data:
                    return {
                        "success": True,
                        "salary_estimates": salary_data,
                        "job_title": job_title,
                        "location": location,
                        "timestamp": datetime.now().isoformat()
                    }
            
            return {"success": False, "error": "No salary data found"}
            
        except Exception as e:
            logger.error(f"JSearch salary estimates failed: {e}")
            return {"success": False, "error": str(e)}
    
    def search_trending_jobs(self, location: str = "United States") -> Dict[str, Any]:
        """Get trending/popular job searches"""
        try:
            # Search for high-demand roles
            trending_queries = [
                "software engineer",
                "data scientist", 
                "product manager",
                "sales representative",
                "marketing manager",
                "business analyst",
                "project manager",
                "customer success"
            ]
            
            all_trending = []
            
            for query in trending_queries[:3]:  # Limit to avoid rate limits
                result = self.search_jobs(
                    query=query,
                    location=location,
                    date_posted="week",
                    num_pages=1
                )
                
                if result.get("success"):
                    jobs = result.get("jobs", [])[:5]  # Top 5 per category
                    for job in jobs:
                        job["trending_category"] = query
                    all_trending.extend(jobs)
            
            return {
                "success": True,
                "trending_jobs": all_trending,
                "location": location,
                "categories_searched": trending_queries[:3],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"JSearch trending jobs failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_api_status(self) -> Dict[str, Any]:
        """Check JSearch API status and quota"""
        try:
            # Make a minimal request to check status
            params = {
                "query": "test",
                "location": "United States",
                "page": "1",
                "num_pages": "1"
            }
            
            start_time = time.time()
            result = self._make_request("/search", params)
            response_time = time.time() - start_time
            
            if "error" not in result:
                return {
                    "status": "operational",
                    "response_time_ms": round(response_time * 1000, 2),
                    "api_key_valid": True,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": result["error"],
                    "api_key_valid": False,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"JSearch status check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "api_key_valid": False,
                "timestamp": datetime.now().isoformat()
            }
