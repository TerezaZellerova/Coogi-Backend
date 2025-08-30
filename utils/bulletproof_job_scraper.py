"""
BULLETPROOF JOB SCRAPER - End-to-End Robust Implementation
Handles all company sizes (1-100, 100-1000, all) with multiple fallbacks
"""
import os
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import random

logger = logging.getLogger(__name__)

class BulletproofJobScraper:
    def __init__(self):
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
        self.apify_key = os.getenv("APIFY_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Multiple fallback APIs
        self.job_apis = {
            "jsearch": {
                "url": "https://jsearch.p.rapidapi.com/search",
                "headers": {
                    "X-RapidAPI-Key": self.rapidapi_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                }
            },
            "linkedin_api": {
                "url": "https://linkedin-jobs-search.p.rapidapi.com/jobs",
                "headers": {
                    "X-RapidAPI-Key": self.rapidapi_key,
                    "X-RapidAPI-Host": "linkedin-jobs-search.p.rapidapi.com"
                }
            }
        }
        
        # Company size filters
        self.company_size_filters = {
            "small": {
                "keywords": ["startup", "small business", "boutique", "growing company"],
                "employee_range": [1, 100],
                "exclude_keywords": ["enterprise", "corporation", "multinational", "fortune 500"]
            },
            "medium": {
                "keywords": ["medium-sized", "mid-market", "growing", "established"],
                "employee_range": [100, 1000],
                "exclude_keywords": ["startup", "small business", "enterprise", "multinational"]
            },
            "all": {
                "keywords": [],
                "employee_range": [1, 999999],
                "exclude_keywords": []
            }
        }
    
    async def search_jobs_bulletproof(self, 
                                    query: str, 
                                    hours_old: int = 24,
                                    company_size: str = "all",
                                    location: str = "United States",
                                    max_results: int = 100) -> List[Dict[str, Any]]:
        """
        BULLETPROOF job search with multiple fallbacks and company size filtering
        """
        logger.info(f"🚀 BULLETPROOF job search: '{query}' | Size: {company_size} | Location: {location}")
        
        all_jobs = []
        
        # Strategy 1: JSearch API (Primary)
        try:
            jsearch_jobs = await self._search_jsearch(query, location, max_results // 2)
            all_jobs.extend(jsearch_jobs)
            logger.info(f"✅ JSearch: {len(jsearch_jobs)} jobs found")
        except Exception as e:
            logger.error(f"❌ JSearch failed: {e}")
        
        # Strategy 2: LinkedIn API (Secondary)
        try:
            linkedin_jobs = await self._search_linkedin_api(query, location, max_results // 2)
            all_jobs.extend(linkedin_jobs)
            logger.info(f"✅ LinkedIn API: {len(linkedin_jobs)} jobs found")
        except Exception as e:
            logger.error(f"❌ LinkedIn API failed: {e}")
        
        # Strategy 3: JobSpy Fallback (Tertiary)
        if len(all_jobs) < 10:
            try:
                jobspy_jobs = await self._search_jobspy_fallback(query, location, max_results)
                all_jobs.extend(jobspy_jobs)
                logger.info(f"✅ JobSpy fallback: {len(jobspy_jobs)} jobs found")
            except Exception as e:
                logger.error(f"❌ JobSpy fallback failed: {e}")
        
        # Strategy 4: Demo Data (Last Resort)
        if len(all_jobs) < 5:
            demo_jobs = self._generate_demo_jobs(query, company_size, location)
            all_jobs.extend(demo_jobs)
            logger.warning(f"⚠️ Using demo data: {len(demo_jobs)} jobs")
        
        # Filter by company size
        filtered_jobs = self._filter_by_company_size(all_jobs, company_size)
        
        # Remove duplicates
        unique_jobs = self._remove_duplicates(filtered_jobs)
        
        # Sort by relevance and date
        sorted_jobs = self._sort_jobs_by_relevance(unique_jobs, query)
        
        logger.info(f"🎯 FINAL RESULT: {len(sorted_jobs)} jobs after filtering and deduplication")
        return sorted_jobs[:max_results]
    
    async def _search_jsearch(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Search using JSearch API"""
        import httpx
        
        params = {
            "query": query,
            "page": "1",
            "num_pages": "3",
            "date_posted": "today" if limit < 50 else "week",
        }
        
        if location and location.lower() != "united states":
            params["location"] = location
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.job_apis["jsearch"]["url"],
                headers=self.job_apis["jsearch"]["headers"],
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("data", [])
                
                return [self._normalize_jsearch_job(job) for job in jobs[:limit]]
            else:
                logger.error(f"JSearch API error: {response.status_code}")
                return []
    
    async def _search_linkedin_api(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Search using LinkedIn Jobs API"""
        import httpx
        
        params = {
            "keywords": query,
            "locationId": "92000000",  # US
            "dateSincePosted": "past-24-hours",
            "sort": "recent"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.job_apis["linkedin_api"]["url"],
                headers=self.job_apis["linkedin_api"]["headers"],
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("data", [])
                
                return [self._normalize_linkedin_job(job) for job in jobs[:limit]]
            else:
                logger.error(f"LinkedIn API error: {response.status_code}")
                return []
    
    async def _search_jobspy_fallback(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback using JobSpy library"""
        try:
            from jobspy import scrape_jobs
            
            # Use JobSpy as fallback
            jobs_df = await asyncio.to_thread(
                scrape_jobs,
                site_name=["indeed", "glassdoor", "zip_recruiter"],
                search_term=query,
                location=location,
                results_wanted=limit,
                hours_old=48,
                country_indeed="us"
            )
            
            if jobs_df is not None and not jobs_df.empty:
                return [self._normalize_jobspy_job(row) for _, row in jobs_df.iterrows()]
            
        except Exception as e:
            logger.error(f"JobSpy error: {e}")
        
        return []
    
    def _normalize_jsearch_job(self, job: Dict) -> Dict[str, Any]:
        """Normalize JSearch job data"""
        return {
            "id": job.get("job_id", f"jsearch_{random.randint(1000, 9999)}"),
            "title": job.get("job_title", "Unknown Title"),
            "company": job.get("employer_name", "Unknown Company"),
            "location": job.get("job_city", "") + ", " + job.get("job_state", ""),
            "url": job.get("job_apply_link", ""),
            "description": job.get("job_description", "")[:500],
            "posted_date": job.get("job_posted_at_datetime_utc", ""),
            "employment_type": job.get("job_employment_type", ""),
            "salary": self._parse_salary(job.get("job_salary", "")),
            "site": "JSearch",
            "company_url": job.get("employer_company_type", ""),
            "is_remote": "remote" in job.get("job_title", "").lower() or "remote" in job.get("job_description", "").lower(),
            "skills": self._extract_skills(job.get("job_description", "")),
            "scraped_at": datetime.now().isoformat()
        }
    
    def _normalize_linkedin_job(self, job: Dict) -> Dict[str, Any]:
        """Normalize LinkedIn job data"""
        return {
            "id": job.get("id", f"linkedin_{random.randint(1000, 9999)}"),
            "title": job.get("title", "Unknown Title"),
            "company": job.get("company", "Unknown Company"),
            "location": job.get("location", ""),
            "url": job.get("url", ""),
            "description": job.get("description", "")[:500],
            "posted_date": job.get("posted_at", ""),
            "employment_type": job.get("type", ""),
            "salary": self._parse_salary(job.get("salary", "")),
            "site": "LinkedIn",
            "company_url": "",
            "is_remote": job.get("is_remote", False),
            "skills": self._extract_skills(job.get("description", "")),
            "scraped_at": datetime.now().isoformat()
        }
    
    def _normalize_jobspy_job(self, row) -> Dict[str, Any]:
        """Normalize JobSpy job data"""
        return {
            "id": f"jobspy_{random.randint(1000, 9999)}",
            "title": str(row.get("title", "Unknown Title")),
            "company": str(row.get("company", "Unknown Company")),
            "location": str(row.get("location", "")),
            "url": str(row.get("job_url", "")),
            "description": str(row.get("description", ""))[:500],
            "posted_date": str(row.get("date_posted", "")),
            "employment_type": str(row.get("job_type", "")),
            "salary": self._parse_salary(str(row.get("salary", ""))),
            "site": str(row.get("site", "JobSpy")),
            "company_url": "",
            "is_remote": "remote" in str(row.get("title", "")).lower(),
            "skills": self._extract_skills(str(row.get("description", ""))),
            "scraped_at": datetime.now().isoformat()
        }
    
    def _filter_by_company_size(self, jobs: List[Dict], company_size: str) -> List[Dict]:
        """Filter jobs by company size"""
        if company_size == "all":
            return jobs
        
        size_config = self.company_size_filters.get(company_size, self.company_size_filters["all"])
        filtered_jobs = []
        
        for job in jobs:
            company_name = job.get("company", "").lower()
            description = job.get("description", "").lower()
            combined_text = f"{company_name} {description}"
            
            # Check for size indicators
            size_match = False
            
            # Look for size keywords
            for keyword in size_config["keywords"]:
                if keyword in combined_text:
                    size_match = True
                    break
            
            # Check for exclusions
            exclude_match = False
            for exclude_keyword in size_config["exclude_keywords"]:
                if exclude_keyword in combined_text:
                    exclude_match = True
                    break
            
            # If no specific indicators, include in medium/all categories
            if not size_match and not exclude_match:
                if company_size in ["medium", "all"]:
                    size_match = True
            
            if size_match and not exclude_match:
                filtered_jobs.append(job)
        
        logger.info(f"🎯 Company size filter '{company_size}': {len(filtered_jobs)}/{len(jobs)} jobs match")
        return filtered_jobs
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        logger.info(f"🔄 Removed {len(jobs) - len(unique_jobs)} duplicate jobs")
        return unique_jobs
    
    def _sort_jobs_by_relevance(self, jobs: List[Dict], query: str) -> List[Dict]:
        """Sort jobs by relevance to query"""
        query_words = query.lower().split()
        
        def relevance_score(job):
            title = job.get("title", "").lower()
            description = job.get("description", "").lower()
            
            score = 0
            for word in query_words:
                if word in title:
                    score += 10
                if word in description:
                    score += 1
            
            # Bonus for recent posts
            if "today" in job.get("posted_date", "").lower():
                score += 5
            
            return score
        
        return sorted(jobs, key=relevance_score, reverse=True)
    
    def _generate_demo_jobs(self, query: str, company_size: str, location: str) -> List[Dict]:
        """Generate realistic demo jobs when APIs fail"""
        demo_companies = {
            "small": ["TechStart Inc", "Innovation Labs", "GrowthCorp", "StartupXYZ", "AgileTeam"],
            "medium": ["MidScale Solutions", "Regional Corp", "GrowthTech", "ExpandCo", "ScaleUp Inc"],
            "all": ["Global Corp", "Enterprise Solutions", "MegaTech", "Industry Leader", "Fortune Company"]
        }
        
        companies = demo_companies.get(company_size, demo_companies["all"])
        
        jobs = []
        for i in range(5):
            job = {
                "id": f"demo_{random.randint(10000, 99999)}",
                "title": f"{query.title()} {['Specialist', 'Manager', 'Director', 'Lead', 'Senior'][i]}",
                "company": companies[i % len(companies)],
                "location": location if location != "United States" else "New York, NY",
                "url": f"https://demo-job-{i}.example.com",
                "description": f"We are looking for a skilled {query} to join our {company_size} team...",
                "posted_date": "1 day ago",
                "employment_type": "fulltime",
                "salary": f"${random.randint(60, 150)}k - ${random.randint(160, 200)}k",
                "site": "Demo",
                "company_url": "",
                "is_remote": random.choice([True, False]),
                "skills": query.split() + ["teamwork", "communication"],
                "scraped_at": datetime.now().isoformat(),
                "is_demo": True
            }
            jobs.append(job)
        
        return jobs
    
    def _parse_salary(self, salary_text: str) -> Optional[str]:
        """Parse salary information"""
        if not salary_text or salary_text.lower() in ["", "null", "none"]:
            return None
        return str(salary_text)
    
    def _extract_skills(self, description: str) -> List[str]:
        """Extract skills from job description"""
        if not description:
            return []
        
        common_skills = [
            "python", "javascript", "react", "node.js", "sql", "aws", "docker",
            "kubernetes", "git", "agile", "scrum", "leadership", "communication",
            "teamwork", "problem-solving", "analytical", "management"
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in common_skills:
            if skill in description_lower:
                found_skills.append(skill)
        
        return found_skills[:10]  # Limit to 10 skills

# Global instance
bulletproof_job_scraper = BulletproofJobScraper()
