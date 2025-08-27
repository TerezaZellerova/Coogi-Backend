"""
LinkedIn Fast Job Scraper - Prioritizes LinkedIn jobs for immediate results
"""
import asyncio
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class LinkedInFastScraper:
    def __init__(self):
        self.rapidapi_key = os.getenv("NEXT_PUBLIC_RAPIDAPI_KEY")
        self.rapidapi_host = "fresh-linkedin-scraper-api.p.rapidapi.com"
        
    async def fetch_linkedin_jobs_fast(self, query: str, hours_old: int = 24, max_results: int = 30) -> List[Dict[str, Any]]:
        """
        Fast LinkedIn job fetching with timeout protection
        Returns results within 2-3 minutes maximum
        """
        try:
            logger.info(f"🔍 Starting fast LinkedIn fetch for: {query}")
            start_time = datetime.now()
            
            # For demo purposes, always use demo data
            # In production, try real API first, then fallback to demo
            if not self.rapidapi_key or self.rapidapi_key == "your_rapidapi_key_here":
                logger.info("🎭 Using demo data (no API key configured)")
                jobs = self._get_demo_linkedin_jobs(query, max_results)
            else:
                logger.info(f"🔑 RapidAPI key found, attempting real Fresh LinkedIn fetch for: {query}")
                # Use asyncio.wait_for to enforce timeout
                try:
                    jobs = await asyncio.wait_for(
                        self._fetch_linkedin_jobs_api(query, max_results, hours_old),
                        timeout=180.0  # 3 minute hard timeout
                    )
                    
                    # Only fallback to demo if API completely fails (no jobs at all)
                    if not jobs:
                        logger.warning("❌ No jobs from Fresh LinkedIn API, using demo data")
                        jobs = self._get_demo_linkedin_jobs(query, max_results)
                    else:
                        logger.info(f"✅ Got {len(jobs)} real LinkedIn jobs from Fresh API!")
                        
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ Fresh LinkedIn fetch timeout after 3 minutes for query: {query}")
                    jobs = self._get_demo_linkedin_jobs(query, max_results)
                except Exception as api_error:
                    logger.error(f"❌ LinkedIn API error: {api_error}")
                    jobs = self._get_demo_linkedin_jobs(query, max_results)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ LinkedIn fast fetch completed in {duration:.1f}s - {len(jobs)} jobs found")
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ LinkedIn fetch error: {e}")
            return self._get_demo_linkedin_jobs(query, max_results)
    
    async def _fetch_linkedin_jobs_api(self, query: str, max_results: int, hours_old: int = 24) -> List[Dict[str, Any]]:
        """Fetch jobs from LinkedIn via RapidAPI"""
        jobs = []
        
        try:
            # Primary locations for US job search
            primary_locations = ["United States", "San Francisco", "New York", "Seattle", "Austin"]
            
            for location in primary_locations[:2]:  # Limit to 2 locations for speed
                try:
                    url = "https://fresh-linkedin-scraper-api.p.rapidapi.com/api/v1/job/search"
                    
                    querystring = {
                        "keyword": query,
                        "location": location,
                        "limit": min(max_results, 25)  # API supports up to 25 per request
                    }
                    
                    headers = {
                        "X-RapidAPI-Key": self.rapidapi_key,
                        "X-RapidAPI-Host": self.rapidapi_host
                    }
                    
                    # Use requests in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None, 
                        lambda: requests.get(url, headers=headers, params=querystring, timeout=30)
                    )
                    
                    logger.info(f"🌐 Fresh LinkedIn API response for {location}: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"📊 Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                        if data.get('success') and 'data' in data:
                            location_jobs = self._parse_fresh_linkedin_response(data['data'], location)
                            jobs.extend(location_jobs)
                            
                            logger.info(f"📍 LinkedIn {location}: {len(location_jobs)} jobs")
                            
                            if len(jobs) >= max_results:
                                break
                        else:
                            logger.warning(f"❌ Fresh LinkedIn API unsuccessful response: {data}")
                            
                    else:
                        logger.warning(f"❌ Fresh LinkedIn API error for {location}: {response.status_code} - {response.text[:200]}")
                        
                except Exception as loc_error:
                    logger.error(f"❌ Error fetching Fresh LinkedIn jobs for {location}: {loc_error}")
                    continue
            
            return jobs[:max_results]
            
        except Exception as e:
            logger.error(f"LinkedIn API fetch failed: {e}")
            return []
    
    def _parse_linkedin_response(self, data: Dict, location: str) -> List[Dict[str, Any]]:
        """Parse LinkedIn API response to standard job format"""
        jobs = []
        
        try:
            job_data = data.get("data", [])
            if isinstance(job_data, list):
                for job in job_data:
                    parsed_job = {
                        "title": job.get("title", "Unknown"),
                        "company": job.get("company", {}).get("name", "Unknown"),
                        "location": job.get("location", location),
                        "job_url": job.get("url", ""),
                        "description": job.get("description", "")[:500],  # Truncate for speed
                        "posted_date": job.get("postedAt", ""),
                        "job_type": job.get("workplaceTypes", ["Unknown"])[0] if job.get("workplaceTypes") else "Unknown",
                        "site": "LinkedIn",
                        "salary": self._extract_salary(job.get("description", "")),
                        "company_url": job.get("company", {}).get("url", ""),
                        "scraped_at": datetime.now().isoformat()
                    }
                    jobs.append(parsed_job)
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn response: {e}")
        
        return jobs
    
    def _parse_fresh_linkedin_response(self, jobs_data: List[Dict], location: str) -> List[Dict[str, Any]]:
        """Parse Fresh LinkedIn API response"""
        jobs = []
        
        try:
            for job in jobs_data:
                company_info = job.get("company", {})
                company_name = company_info.get("name", "Unknown Company") if isinstance(company_info, dict) else str(company_info)
                
                parsed_job = {
                    "id": job.get("id", ""),
                    "title": job.get("title", "No Title"),
                    "company": company_name,
                    "location": job.get("location", location),
                    "description": job.get("description", "No description available"),
                    "url": job.get("url", ""),
                    "posted_date": job.get("posted_at", ""),
                    "employment_type": job.get("employment_type", "Unknown"),
                    "experience_level": job.get("experience_level", "Not specified"),
                    "site": "LinkedIn",
                    "salary": self._extract_salary(job.get("description", "")),
                    "company_url": company_info.get("url", "") if isinstance(company_info, dict) else "",
                    "scraped_at": datetime.now().isoformat(),
                    "is_remote": "remote" in job.get("location", "").lower()
                }
                jobs.append(parsed_job)
        
        except Exception as e:
            logger.error(f"Error parsing Fresh LinkedIn response: {e}")
        
        return jobs

    def _extract_salary(self, description: str) -> Optional[str]:
        """Extract salary information from job description"""
        import re
        
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',
            r'\$[\d,]+k?\s*-\s*[\d,]+k?',
            r'[\d,]+k?\s*-\s*[\d,]+k?\s*USD',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _get_demo_linkedin_jobs(self, query: str, count: int) -> List[Dict[str, Any]]:
        """Generate demo LinkedIn jobs for fallback"""
        demo_jobs_data = [
            {"company": "Google", "title": "Senior Software Engineer", "location": "Mountain View, CA", "salary": "$180k - $250k", "type": "Full-time"},
            {"company": "Microsoft", "title": "Software Engineer II", "location": "Seattle, WA", "salary": "$150k - $200k", "type": "Full-time"},
            {"company": "Apple", "title": "iOS Developer", "location": "Cupertino, CA", "salary": "$160k - $220k", "type": "Full-time"},
            {"company": "Meta", "title": "Frontend Engineer", "location": "Menlo Park, CA", "salary": "$170k - $240k", "type": "Full-time"},
            {"company": "Amazon", "title": "Backend Engineer", "location": "Austin, TX", "salary": "$140k - $190k", "type": "Full-time"},
            {"company": "Netflix", "title": "Full Stack Engineer", "location": "Los Gatos, CA", "salary": "$200k - $280k", "type": "Full-time"},
            {"company": "Uber", "title": "Platform Engineer", "location": "San Francisco, CA", "salary": "$165k - $225k", "type": "Full-time"},
            {"company": "Airbnb", "title": "Product Engineer", "location": "San Francisco, CA", "salary": "$175k - $245k", "type": "Full-time"},
            {"company": "Stripe", "title": "Infrastructure Engineer", "location": "Remote", "salary": "$190k - $260k", "type": "Full-time"},
            {"company": "Spotify", "title": "Mobile Engineer", "location": "New York, NY", "salary": "$155k - $210k", "type": "Full-time"},
            {"company": "Slack", "title": "DevOps Engineer", "location": "San Francisco, CA", "salary": "$145k - $195k", "type": "Full-time"},
            {"company": "Zoom", "title": "Security Engineer", "location": "San Jose, CA", "salary": "$160k - $220k", "type": "Full-time"},
            {"company": "Shopify", "title": "Ruby Developer", "location": "Ottawa, ON", "salary": "$120k - $160k CAD", "type": "Full-time"},
            {"company": "GitHub", "title": "Site Reliability Engineer", "location": "Remote", "salary": "$170k - $230k", "type": "Full-time"},
            {"company": "Atlassian", "title": "Cloud Engineer", "location": "Sydney, AU", "salary": "$130k - $180k AUD", "type": "Full-time"}
        ]
        
        jobs = []
        used_count = min(count, len(demo_jobs_data))
        
        for i in range(used_count):
            job_data = demo_jobs_data[i]
            
            # Customize title based on query
            title = job_data["title"]
            if query.lower() != "software engineer":
                # Try to incorporate the query into the title
                if "remote" in query.lower():
                    title += " (Remote)"
                elif "senior" not in title.lower() and "senior" in query.lower():
                    title = "Senior " + title
                elif "junior" in query.lower():
                    title = "Junior " + title.replace("Senior ", "")
            
            jobs.append({
                "id": f"demo_linkedin_{i}",
                "title": title,
                "company": job_data["company"],
                "location": job_data["location"],
                "url": f"https://linkedin.com/jobs/view/demo-{i}-{job_data['company'].lower()}",
                "description": f"Join {job_data['company']} as a {title}. We're looking for talented engineers to help build the future of technology. Remote-friendly culture, competitive benefits, and stock options available.",
                "posted_date": datetime.now().isoformat(),
                "employment_type": job_data["type"],
                "site": "LinkedIn",
                "salary": job_data["salary"],
                "company_url": f"https://{job_data['company'].lower().replace(' ', '')}.com",
                "scraped_at": datetime.now().isoformat(),
                "is_remote": "Remote" in job_data["location"] or "remote" in query.lower(),
                "experience_level": "Mid-Senior level",
                "skills": ["Python", "JavaScript", "React", "AWS", "Docker", "Kubernetes"],
                "is_demo": True
            })
        
        logger.info(f"🎭 Generated {len(jobs)} demo LinkedIn jobs for query: {query}")
        return jobs
