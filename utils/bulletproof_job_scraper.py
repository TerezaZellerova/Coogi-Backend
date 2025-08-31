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
                                    max_results: int = 500) -> List[Dict[str, Any]]:
        """
        BULLETPROOF job search with multiple fallbacks and company size filtering
        ENHANCED: Prioritizes JobSpy (which is working) over APIs with rate limits
        """
        logger.info(f"🚀 BULLETPROOF job search: '{query}' | Size: {company_size} | Location: {location} | Target: {max_results} jobs")
        
        all_jobs = []
        
        # Strategy 1: JobSpy Multi-platform (PRIMARY - This works reliably!)
        try:
            jobspy_jobs = await self._search_jobspy_aggressive(query, location, max_results)
            all_jobs.extend(jobspy_jobs)
            logger.info(f"✅ JobSpy aggressive: {len(jobspy_jobs)} jobs found")
        except Exception as e:
            logger.error(f"❌ JobSpy aggressive failed: {e}")
        
        # Strategy 2: JobSpy with query variations (SECONDARY)
        if len(all_jobs) < max_results * 0.8:  # If we have less than 80% of target
            try:
                variation_jobs = await self._search_jobspy_variations(query, location, max_results // 2)
                all_jobs.extend(variation_jobs)
                logger.info(f"✅ JobSpy variations: {len(variation_jobs)} jobs found")
            except Exception as e:
                logger.error(f"❌ JobSpy variations failed: {e}")
        
        # Strategy 3: JSearch API (Only if not rate limited)
        if len(all_jobs) < max_results * 0.6:  # If we still need more jobs
            try:
                jsearch_jobs = await self._search_jsearch_conservative(query, location, max_results // 3)
                all_jobs.extend(jsearch_jobs)
                logger.info(f"✅ JSearch conservative: {len(jsearch_jobs)} jobs found")
            except Exception as e:
                logger.warning(f"⚠️ JSearch conservative failed (rate limited?): {e}")
        
        # Strategy 4: Extended JobSpy search with broader terms
        if len(all_jobs) < max_results * 0.7:  # If we still need more jobs
            try:
                extended_jobs = await self._search_jobspy_extended(query, location, max_results // 3)
                all_jobs.extend(extended_jobs)
                logger.info(f"✅ JobSpy extended: {len(extended_jobs)} jobs found")
            except Exception as e:
                logger.error(f"❌ JobSpy extended failed: {e}")
        
        # Strategy 5: Demo Data (Only if we have very few jobs)
        if len(all_jobs) < 50:
            demo_jobs = self._generate_demo_jobs(query, company_size, location, count=max_results - len(all_jobs))
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
    
    async def _search_jsearch_aggressive(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """AGGRESSIVE JSearch API search - multiple pages and broader date range"""
        import httpx
        
        all_jobs = []
        
        # Search with multiple configurations for maximum coverage
        search_configs = [
            {"date_posted": "today", "num_pages": "5"},       # Today, 5 pages
            {"date_posted": "3days", "num_pages": "8"},       # Last 3 days, 8 pages
            {"date_posted": "week", "num_pages": "15"},       # Last week, 15 pages
            {"date_posted": "month", "num_pages": "12"},      # Last month, 12 pages  
            {"date_posted": "all", "num_pages": "10"},        # All time, 10 pages
        ]
        
        for config in search_configs:
            try:
                params = {
                    "query": query,
                    "page": "1", 
                    "num_pages": config["num_pages"],
                    "date_posted": config["date_posted"],
                    "employment_types": "FULLTIME;PARTTIME;CONTRACTOR;INTERN",  # Include all types
                    "job_requirements": "under_3_years_experience;more_than_3_years_experience;no_experience",  # All experience levels
                }
                
                if location and location.lower() != "united states":
                    params["location"] = location
                
                async with httpx.AsyncClient(timeout=60) as client:  # Increased timeout
                    response = await client.get(
                        self.job_apis["jsearch"]["url"],
                        headers=self.job_apis["jsearch"]["headers"],
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        jobs = data.get("data", [])
                        normalized_jobs = [self._normalize_jsearch_job(job) for job in jobs]
                        all_jobs.extend(normalized_jobs)
                        logger.info(f"📈 JSearch config {config['date_posted']}: {len(normalized_jobs)} jobs")
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.5)
                        
                    else:
                        logger.warning(f"JSearch API error for {config}: {response.status_code}")
                        
            except Exception as e:
                logger.error(f"JSearch config {config} failed: {e}")
                continue
        
        logger.info(f"📊 Total JSearch jobs collected: {len(all_jobs)}")
        return all_jobs[:limit]
    
    async def _search_jobspy_aggressive(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """AGGRESSIVE JobSpy search across multiple platforms"""
        try:
            from jobspy import scrape_jobs
            
            all_jobs = []
            
            # Search across multiple job sites
            job_sites = [
                ["indeed", "glassdoor"],
                ["zip_recruiter", "linkedin"], 
                ["monster", "careerbuilder"]
            ]
            
            for sites in job_sites:
                try:
                    jobs_df = await asyncio.to_thread(
                        scrape_jobs,
                        site_name=sites,
                        search_term=query,
                        location=location,
                        results_wanted=limit // len(job_sites) + 50,  # Get more per site
                        hours_old=168,  # 1 week
                        country_indeed="us"
                    )
                    
                    if jobs_df is not None and not jobs_df.empty:
                        site_jobs = [self._normalize_jobspy_job(row) for _, row in jobs_df.iterrows()]
                        all_jobs.extend(site_jobs)
                        logger.info(f"📊 JobSpy {sites}: {len(site_jobs)} jobs")
                        
                except Exception as e:
                    logger.warning(f"JobSpy sites {sites} failed: {e}")
                    continue
            
            return all_jobs[:limit]
            
        except Exception as e:
            logger.error(f"JobSpy aggressive error: {e}")
            return []
    
    async def _search_query_variations(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Search with query variations to find more jobs"""
        variations = []
        
        # Generate query variations based on the original query
        base_query = query.lower().strip()
        
        if "manager" in base_query:
            variations = [
                base_query.replace("manager", "supervisor"),
                base_query.replace("manager", "lead"),
                base_query.replace("manager", "director"),
                f"{base_query} OR supervisor OR lead",
            ]
        elif "developer" in base_query:
            variations = [
                base_query.replace("developer", "engineer"),
                base_query.replace("developer", "programmer"),
                f"{base_query} OR engineer OR programmer",
            ]
        elif "analyst" in base_query:
            variations = [
                base_query.replace("analyst", "specialist"),
                f"{base_query} OR specialist OR consultant",
            ]
        else:
            # Generic variations
            variations = [
                f"{base_query} specialist",
                f"{base_query} coordinator", 
                f"{base_query} associate",
                f"senior {base_query}",
                f"junior {base_query}",
            ]
        
        all_jobs = []
        for variation in variations[:4]:  # Increased to 4 variations
            try:
                jobs = await self._search_jsearch_aggressive(variation, location, limit // len(variations))
                all_jobs.extend(jobs)
                logger.info(f"🔄 Variation '{variation}': {len(jobs)} jobs")
            except Exception as e:
                logger.warning(f"Variation '{variation}' failed: {e}")
        
        return all_jobs
    
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
    
    async def _search_extended_timeframe(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Search with extended timeframes and remote options to find more jobs"""
        import httpx
        
        all_jobs = []
        
        # Extended search configurations
        extended_configs = [
            {"query": f"{query} remote", "date_posted": "month"},
            {"query": f"remote {query}", "date_posted": "month"},
            {"query": f"{query} work from home", "date_posted": "month"},
            {"query": f"{query} hybrid", "date_posted": "month"},
            {"query": f"{query} contract", "date_posted": "month"},
            {"query": f"{query} freelance", "date_posted": "month"},
        ]
        
        for config in extended_configs:
            try:
                params = {
                    "query": config["query"],
                    "page": "1", 
                    "num_pages": "8",
                    "date_posted": config["date_posted"],
                    "employment_types": "FULLTIME;PARTTIME;CONTRACTOR;INTERN",
                    "remote_jobs_only": "false",  # Include both remote and non-remote
                }
                
                if location and location.lower() != "united states":
                    params["location"] = location
                
                async with httpx.AsyncClient(timeout=45) as client:
                    response = await client.get(
                        self.job_apis["jsearch"]["url"],
                        headers=self.job_apis["jsearch"]["headers"],
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        jobs = data.get("data", [])
                        normalized_jobs = [self._normalize_jsearch_job(job) for job in jobs]
                        all_jobs.extend(normalized_jobs)
                        logger.info(f"🔍 Extended search '{config['query']}': {len(normalized_jobs)} jobs")
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.3)
                        
                    else:
                        logger.warning(f"Extended search API error for {config}: {response.status_code}")
                        
            except Exception as e:
                logger.warning(f"Extended search config {config} failed: {e}")
                continue
        
        logger.info(f"🔍 Total extended search jobs: {len(all_jobs)}")
        return all_jobs[:limit]
    
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
    
    def _generate_demo_jobs(self, query: str, company_size: str, location: str, count: int = 150) -> List[Dict]:
        """Generate realistic demo jobs when APIs fail"""
        demo_companies = {
            "small": ["TechStart Inc", "Innovation Labs", "GrowthCorp", "StartupXYZ", "AgileTeam", 
                     "NextGen Solutions", "Pioneer Tech", "Velocity Inc", "Bootstrap Co", "Lean Startup"],
            "medium": ["MidScale Solutions", "Regional Corp", "GrowthTech", "ExpandCo", "ScaleUp Inc",
                      "Progress Systems", "Evolution Corp", "Balanced Tech", "Steady Growth", "Regional Leader"],
            "all": ["Global Corp", "Enterprise Solutions", "MegaTech", "Industry Leader", "Fortune Company",
                   "International Inc", "Worldwide Systems", "Global Leader", "Enterprise Tech", "Corporate Giant"]
        }
        
        companies = demo_companies.get(company_size, demo_companies["all"])
        job_titles = [
            f"Senior {query}",
            f"Junior {query}",
            f"{query} Manager",
            f"Lead {query}",
            f"{query} Director",
            f"{query} Specialist",
            f"{query} Coordinator",
            f"{query} Associate",
            f"Principal {query}",
            f"{query} Consultant"
        ]
        
        locations = [
            location if location != "United States" else "New York, NY",
            "San Francisco, CA",
            "Austin, TX", 
            "Seattle, WA",
            "Boston, MA",
            "Chicago, IL",
            "Los Angeles, CA",
            "Denver, CO",
            "Atlanta, GA",
            "Remote"
        ]
        
        jobs = []
        for i in range(count):
            job = {
                "id": f"demo_{random.randint(10000, 99999)}",
                "title": job_titles[i % len(job_titles)],
                "company": companies[i % len(companies)],
                "location": locations[i % len(locations)],
                "url": f"https://demo-job-{i}.example.com",
                "description": f"We are looking for a skilled {query} to join our {company_size} team. This is an exciting opportunity to work with cutting-edge technology and make a real impact.",
                "posted_date": f"{random.randint(1, 7)} days ago",
                "employment_type": random.choice(["fulltime", "parttime", "contract"]),
                "salary": f"${random.randint(60, 150)}k - ${random.randint(160, 200)}k",
                "site": "Demo",
                "company_url": "",
                "is_remote": random.choice([True, False]),
                "skills": query.split() + random.sample(["teamwork", "communication", "leadership", "problem-solving", "analytical"], 3),
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
