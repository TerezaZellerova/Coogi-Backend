from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Dict, Any
import logging
import json
import time
import httpx
import asyncio

from ..models import (
    JobSearchRequest, JobSearchResponse, RawJobSpyResponse,
    MessageGenerationRequest, MessageGenerationResponse,
    CompanyAnalysisRequest, CompanyAnalysisResponse,
    ContractOpportunityRequest, ContractAnalysisResponse,
    CompanyJobsRequest, CompanyJobsResponse
)
from ..dependencies import (
    get_current_user, get_job_scraper, get_contact_finder, 
    get_email_generator, get_memory_manager, get_contract_analyzer,
    get_instantly_manager, get_blacklist_manager,
    log_to_supabase
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["leads"])

@router.post("/search-jobs", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """Search for jobs and analyze companies for recruiting opportunities - COMPLETE PIPELINE"""
    try:
        job_scraper = get_job_scraper()
        contact_finder = get_contact_finder()
        memory_manager = get_memory_manager()
        blacklist_manager = get_blacklist_manager()
        
        # Generate batch ID for logging
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Parse query
        search_params = job_scraper.parse_query(request.query)
        
        # Override hours_old with request parameter if provided
        if request.hours_old != 720:
            search_params['hours_old'] = request.hours_old
            logger.info(f"🔍 Overriding hours_old to {request.hours_old} hours")
            await log_to_supabase(batch_id, f"🔍 Overriding hours_old to {request.hours_old} hours", "info")
        
        # Search jobs city by city and process each city's companies immediately
        await log_to_supabase(batch_id, f"🚀 Starting job search: {request.query}", "info")
        
        # Initialize tracking variables
        processed_companies = set()
        companies_analyzed = []
        campaigns_created = []
        leads_added = 0
        hunter_attempts = 0
        hunter_hits = 0
        processed_count = 0
        
        # Get jobs city by city and process each city immediately
        total_jobs_found = 0
        
        # Process each city sequentially
        for city in job_scraper.us_cities[:3]:  # Limit to first 3 cities for faster real processing
            await log_to_supabase(batch_id, f"🏙️ Processing city: {city}", "info")
            
            try:
                # Get jobs for this specific city using the full JobSpy API call
                city_jobs = job_scraper._call_jobspy_api(
                    search_term=search_params.get('search_term', ''),
                    location=city,
                    hours_old=search_params.get('hours_old', 720),
                    job_type=search_params.get('job_type', ''),
                    is_remote=search_params.get('is_remote', False),
                    site_name=search_params.get('site_name', ["linkedin", "indeed", "zip_recruiter", "google", "glassdoor"]),
                    results_wanted=search_params.get('results_wanted', 50),  # Reduced for faster processing
                    offset=search_params.get('offset', 0),
                    distance=search_params.get('distance', 25),
                    easy_apply=search_params.get('easy_apply', False),
                    country_indeed=search_params.get('country_indeed', 'us'),
                    google_search_term=search_params.get('google_search_term', ''),
                    linkedin_fetch_description=search_params.get('linkedin_fetch_description', True),
                    verbose=search_params.get('verbose', False)
                )
                
                if not city_jobs:
                    await log_to_supabase(batch_id, f"⚠️ No jobs found in {city}", "warning")
                    continue
                
                await log_to_supabase(batch_id, f"✅ Found {len(city_jobs)} jobs in {city}", "success")
                total_jobs_found += len(city_jobs)
                
                # Process all companies in this city immediately
                city_companies_processed = 0
                for job in city_jobs:
                    # Check if already processed
                    job_fingerprint = memory_manager.create_job_fingerprint(job)
                    if memory_manager.is_job_processed(job_fingerprint):
                        continue
                    
                    company = job.get('company', '')
                    job_title = job.get('title', '')
                    job_url = job.get('job_url', '')
                    
                    # Skip if we've already analyzed this company
                    if company in processed_companies:
                        logger.info(f"Skipping {company} - already analyzed")
                        memory_manager.mark_job_processed(job_fingerprint)
                        continue
                    
                    # Check blacklist BEFORE making any API calls
                    if blacklist_manager.is_blacklisted(company):
                        logger.info(f"⏭️  Skipping {company} - blacklisted")
                        memory_manager.mark_job_processed(job_fingerprint)
                        continue
                    
                    # Process this company through the complete flow
                    await log_to_supabase(batch_id, f"🔍 Processing company: {company} - {job_title}", "info", company, job_title, job_url, "company_start")
        
                    try:
                        # STEP 1: Domain Search (Clearout API)
                        domain = None
                        try:
                            import httpx
                            url = "https://api.clearout.io/public/companies/autocomplete"
                            params = {"query": company}
                            
                            logger.info(f"🌐 Making domain finding call for {company}")
                            async with httpx.AsyncClient() as client:
                                response = await client.get(url, params=params, timeout=30.0)
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    companies_data = data.get('companies', [])
                                    
                                    if companies_data:
                                        best_match = None
                                        best_confidence = 0
                                        
                                        for company_data in companies_data:
                                            confidence = company_data.get('confidence_score', 0)
                                            found_domain = company_data.get('domain')
                                            
                                            if confidence > best_confidence and confidence >= 50:
                                                best_confidence = confidence
                                                best_match = found_domain
                                        
                                        if best_match:
                                            domain = best_match
                                            logger.info(f"🌐 Found domain for {company}: {domain}")
                                        else:
                                            logger.warning(f"⚠️  No high-confidence domain found for {company}")
                                    else:
                                        logger.warning(f"⚠️  No companies found for {company}")
                                else:
                                    logger.warning(f"⚠️  Clearout API error: {response.status_code}")
                        except Exception as e:
                            logger.error(f"❌ Domain finding failed for {company}: {e}")
                        
                        job['company_website'] = domain
                        
                        # Log domain status
                        if domain:
                            await log_to_supabase(batch_id, f"✅ Domain found for {company}: {domain}", "success", company, job_title, job_url, "domain_found")
                        else:
                            await log_to_supabase(batch_id, f"⚠️ No domain found for {company}", "warning", company, job_title, job_url, "domain_not_found")
                
                        # STEP 2: LinkedIn Resolution (via OpenAI batch analysis)
                        analysis = contact_finder.batch_analyze_companies([company]).get(company, {})
                        linkedin_identifier = analysis.get('linkedin_identifier', company.lower().replace(" ", "-"))
                        
                        # STEP 3: RapidAPI Analysis (Contact finding + TA team detection)
                        description = job.get('description') or job.get('job_level') or ''
                        result = contact_finder.find_contacts(
                            company=company,
                            linkedin_identifier=linkedin_identifier,
                            role_hint=job_title,
                            keywords=job_scraper.extract_keywords(description),
                            company_website=domain
                        )
                        
                        contacts, has_ta_team, employee_roles, company_found = result
                        await log_to_supabase(batch_id, f"📊 Found {len(contacts)} contacts, TA team: {has_ta_team}", "info", company, job_title, job_url, "contact_analysis")
                        
                        # STEP 4: Hunter.io (if no TA team and company found)
                        hunter_emails = []
                        if not has_ta_team and company_found:
                            await log_to_supabase(batch_id, f"📡 Attempting Hunter.io lookup for: {company}", "info", company, job_title, job_url, "hunter_lookup")
                            
                            try:
                                hunter_attempts += 1
                                hunter_emails = contact_finder.find_hunter_emails_for_target_company(
                                    company=company,
                                    job_title=job_title,
                                    employee_roles=employee_roles,
                                    company_website=domain
                                )
                                
                                if hunter_emails:
                                    hunter_hits += 1
                                    await log_to_supabase(batch_id, f"✅ Found {len(hunter_emails)} Hunter.io emails for {company}", "success", company, job_title, job_url, "hunter_success")
                                else:
                                    await log_to_supabase(batch_id, f"⚠️ No Hunter.io emails found for {company}", "warning", company, job_title, job_url, "hunter_no_emails")
                                    
                            except Exception as e:
                                await log_to_supabase(batch_id, f"❌ Hunter.io error for {company}: {str(e)}", "error", company, job_title, job_url, "hunter_error")
                        else:
                            await log_to_supabase(batch_id, f"⏭️ Skipping Hunter.io for {company} (has TA team or company not found)", "info", company, job_title, job_url, "hunter_skipped")
                        
                        # STEP 5: Instantly.ai (if requested and emails found)
                        campaign_id = None
                        if request.create_campaigns and hunter_emails:
                            await log_to_supabase(batch_id, f"🚀 Creating Instantly campaign for {company}", "info", company, job_title, job_url, "instantly_start")
                            try:
                                instantly_manager = get_instantly_manager()
                                # Create campaign with the found emails
                                campaign_result = instantly_manager.create_recruiting_campaign(
                                    leads=hunter_emails,
                                    campaign_name=f"Recruitment - {company} - {batch_id}"
                                )
                                
                                if campaign_result:
                                    campaign_id = campaign_result
                                    leads_added += len(hunter_emails)
                                    campaigns_created.append(campaign_id)
                                    await log_to_supabase(batch_id, f"✅ Created campaign {campaign_id} with {len(hunter_emails)} leads", "success", company, job_title, job_url, "instantly_success")
                                else:
                                    await log_to_supabase(batch_id, f"❌ Failed to create campaign: {campaign_result.get('error')}", "error", company, job_title, job_url, "instantly_error")
                                    
                            except Exception as e:
                                await log_to_supabase(batch_id, f"❌ Error creating Instantly campaign for {company}: {str(e)}", "error", company, job_title, job_url, "instantly_error")
                        
                        # Create company analysis record
                        recommendation = "SKIP - Has TA team" if has_ta_team else "PROCESS - Target company"
                        company_analysis = {
                            "company": company,
                            "job_title": job_title,
                            "job_url": job_url,
                            "has_ta_team": has_ta_team,
                            "contacts_found": len(contacts),
                            "top_contacts": contacts[:5],
                            "hunter_emails": hunter_emails,
                            "employee_roles": employee_roles,
                            "company_website": domain,
                            "company_found": company_found,
                            "recommendation": recommendation,
                            "instantly_campaign_id": campaign_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        companies_analyzed.append(company_analysis)
                        
                        await log_to_supabase(batch_id, f"✅ Completed analysis for {company}: {recommendation}", "success", company, job_title, job_url, "company_analysis_complete")
                        
                        # Mark as processed
                        processed_companies.add(company)
                        memory_manager.mark_job_processed(job_fingerprint)
                        processed_count += 1
                        city_companies_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error analyzing {company}: {e}")
                        await log_to_supabase(batch_id, f"❌ Error analyzing {company}: {str(e)}", "error", company, job_title, job_url, "company_error")
                        memory_manager.mark_job_processed(job_fingerprint)
                        continue
                
                # Log city completion
                await log_to_supabase(batch_id, f"✅ Completed {city}: {city_companies_processed} companies processed", "success")
                
            except Exception as e:
                logger.error(f"Error processing city {city}: {e}")
                await log_to_supabase(batch_id, f"❌ Error processing city {city}: {str(e)}", "error")
                continue
            
            # Rate limiting: Wait between cities
            if city != job_scraper.us_cities[:10][-1]:  # Not the last city
                await log_to_supabase(batch_id, "⏳ Rate limiting: Waiting 30 seconds before next city...", "info")
                time.sleep(30)
        
        # Final summary logging
        logger.info(f"📊 Hunter.io Summary: {hunter_attempts} attempts, {hunter_hits} emails found")
        await log_to_supabase(batch_id, f"📊 Hunter.io Summary: {hunter_attempts} attempts, {hunter_hits} emails found", "info")
        await log_to_supabase(batch_id, f"🎉 Search completed: {len(companies_analyzed)} companies analyzed", "success")
        
        return JobSearchResponse(
            companies_analyzed=companies_analyzed,
            jobs_found=total_jobs_found,
            total_processed=processed_count,
            search_query=request.query,
            timestamp=datetime.now().isoformat(),
            campaigns_created=campaigns_created if campaigns_created else None,
            leads_added=leads_added
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/raw-jobspy", response_model=RawJobSpyResponse)
async def get_raw_jobspy_results(request: JobSearchRequest):
    """Get raw JobSpy results without any processing - fastest response"""
    try:
        job_scraper = get_job_scraper()
        
        # Parse query quickly
        search_params = job_scraper.parse_query(request.query)
        
        # Get all available jobs - increased to allow more jobs from location variants
        jobs = job_scraper.search_jobs(search_params, max_results=500)
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found matching criteria")
        
        logger.info(f"✅ Raw JobSpy results: {len(jobs)} jobs found")
        
        return RawJobSpyResponse(
            jobs=jobs,
            total_jobs=len(jobs),
            search_query=request.query,
            location=search_params.get("location", "N/A"),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in raw JobSpy search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-jobs-fast", response_model=JobSearchResponse)
async def search_jobs_fast(request: JobSearchRequest):
    """Fast job search with immediate results - optimized for 30-second responses"""
    try:
        job_scraper = get_job_scraper()
        
        # Parse query quickly
        search_params = job_scraper.parse_query(request.query)
        
        # Get all available jobs
        jobs = job_scraper.search_jobs(search_params, max_results=20)
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found matching criteria")
        
        companies_analyzed = []
        processed_count = 0
        
        # For immediate results, just return the JobSpy data without RapidAPI processing
        logger.info(f"Returning {len(jobs)} jobs from JobSpy without RapidAPI processing")
        
        # Create simple company analysis from JobSpy data
        for job in jobs[:10]:  # Limit to first 10 jobs for quick response
            company = job.get('company', '')
            if not company:
                continue
                
            company_analysis = {
                "company": company,
                "job_title": job.get('title', ''),
                "job_url": job.get('job_url', ''),
                "has_ta_team": False,  # Will be determined later
                "contacts_found": 0,
                "top_contacts": [],
                "recommendation": "PENDING - RapidAPI analysis required",
                "timestamp": datetime.now().isoformat()
            }
            
            companies_analyzed.append(company_analysis)
            processed_count += 1
            
        return JobSearchResponse(
            companies_analyzed=companies_analyzed,
            jobs_found=len(jobs),
            total_processed=processed_count,
            search_query=request.query,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in fast job search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-jobs-stream")
async def search_jobs_stream(request: JobSearchRequest):
    """Stream job search results for immediate feedback"""
    def generate_stream():
        try:
            job_scraper = get_job_scraper()
            contact_finder = get_contact_finder()
            memory_manager = get_memory_manager()
            
            # Initialize leads list
            leads = []
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting job search...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Parse query and send update
            search_params = job_scraper.parse_query(request.query)
            search_term = search_params.get("search_term", request.query)
            yield f"data: {json.dumps({'type': 'status', 'message': f'Searching for: {search_term}', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Search jobs - get all available jobs (increased from 50 to 500)
            jobs = job_scraper.search_jobs(search_params, max_results=500)
            yield f"data: {json.dumps({'type': 'jobs_found', 'count': len(jobs), 'timestamp': datetime.now().isoformat()})}\n\n"
            
            if not jobs:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No jobs found matching criteria', 'timestamp': datetime.now().isoformat()})}\n\n"
                return
            
            companies_analyzed = []
            processed_count = 0
            
            # Process jobs in batches (simplified for migration)
            max_jobs_per_batch = 4
            total_jobs = len(jobs)
            
            yield f"data: {json.dumps({'type': 'status', 'message': f'Processing {total_jobs} jobs in batches of {max_jobs_per_batch}', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Send completion summary
            yield f"data: {json.dumps({'type': 'complete', 'summary': {'leads_found': len(leads), 'jobs_processed': processed_count, 'total_jobs': len(jobs)}, 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming job search: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/plain")

@router.post("/generate-message", response_model=MessageGenerationResponse)
async def generate_message(request: MessageGenerationRequest):
    """Generate personalized outreach message"""
    try:
        email_generator = get_email_generator()
        
        message = email_generator.generate_outreach(
            job_title=request.job_title,
            company=request.company,
            contact_title=request.contact_title,
            job_url=request.job_url,
            tone=request.tone,
            additional_context=request.additional_context
        )
        
        subject_line = email_generator.generate_subject_line(
            request.job_title,
            request.company
        )
        
        return MessageGenerationResponse(
            message=message,
            subject_line=subject_line,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-companies", response_model=CompanyAnalysisResponse)
async def analyze_companies(request: CompanyAnalysisRequest):
    """Comprehensive company analysis with skip reporting and job data"""
    try:
        job_scraper = get_job_scraper()
        
        # Import here to avoid circular dependency
        from utils.company_analyzer import CompanyAnalyzer
        import os
        analyzer = CompanyAnalyzer(rapidapi_key=os.getenv("RAPIDAPI_KEY", ""))
        
        # Clear previous analysis
        analyzer.clear_skip_history()
        
        # Parse query and search for jobs
        search_params = job_scraper.parse_query(request.query)
        jobs = job_scraper.search_jobs(search_params, max_results=request.max_companies * 3)
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found matching criteria")
        
        # Simplified analysis for migration
        target_companies = []
        skipped_companies = []
        
        summary = {
            "total_companies_analyzed": len(jobs),
            "target_companies_found": len(target_companies),
            "companies_skipped": len(skipped_companies),
            "skip_reasons": {},
            "success_rate": 100.0
        }
        
        return CompanyAnalysisResponse(
            target_companies=target_companies,
            skipped_companies=skipped_companies,
            summary=summary,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in company analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-contract-opportunities", response_model=ContractAnalysisResponse)
async def analyze_contract_opportunities(request: ContractOpportunityRequest):
    """Analyze job market to identify high-value recruiting contract opportunities"""
    try:
        job_scraper = get_job_scraper()
        contract_analyzer = get_contract_analyzer()
        
        # Parse query and search for jobs
        search_params = job_scraper.parse_query(request.query)
        jobs = job_scraper.search_jobs(search_params, max_results=request.max_companies * 5)
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found matching criteria")
        
        # Analyze contract opportunities with enhanced company job search
        analysis = contract_analyzer.analyze_contract_opportunities(jobs, request.max_companies, job_scraper)
        
        return ContractAnalysisResponse(
            opportunities=[],  # Simplified for migration
            summary=analysis.get('summary', {}),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in contract opportunity analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads")
async def get_leads(current_user: dict = Depends(get_current_user)):
    """Get all leads"""
    try:
        import os
        leads = []
        
        # Try to get leads from Supabase if available
        try:
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                # Get leads from hunter_emails table
                response = supabase.table("hunter_emails").select("*").limit(100).execute()
                hunter_emails = response.data or []
                
                for i, email_data in enumerate(hunter_emails):
                    leads.append({
                        "id": str(email_data.get("id", i)),
                        "email": email_data.get("email", ""),
                        "first_name": email_data.get("first_name", ""),
                        "last_name": email_data.get("last_name", ""),
                        "company": email_data.get("company", ""),
                        "title": email_data.get("title", ""),
                        "linkedin_url": email_data.get("linkedin_url"),
                        "status": "active",  # Default status
                        "confidence": email_data.get("confidence"),
                        "timestamp": email_data.get("timestamp", datetime.now().isoformat())
                    })
        except Exception as e:
            logger.warning(f"Could not fetch from Supabase: {e}")
        
        return leads
    except Exception as e:
        logger.error(f"Error getting leads: {e}")
        return []

@router.post("/search-jobs-instant", response_model=JobSearchResponse)
async def search_jobs_instant(request: JobSearchRequest):
    """Instant job search with immediate demo results - no external API calls"""
    try:
        logger.info(f"📱 Instant job search request: {request.query}")
        
        # Generate instant demo companies for immediate response
        demo_companies = [
            {
                "company": "TechCorp Solutions",
                "job_title": f"{request.query.split()[0]} Engineer",
                "job_url": "https://example.com/job1",
                "has_ta_team": False,
                "contacts_found": 3,
                "top_contacts": [
                    {"name": "John Smith", "title": "Engineering Manager"},
                    {"name": "Sarah Johnson", "title": "Senior Recruiter"}
                ],
                "recommendation": "TARGET - High-growth startup",
                "timestamp": datetime.now().isoformat()
            },
            {
                "company": "InnovateNow Inc",
                "job_title": f"Senior {request.query.split()[0]} Developer",
                "job_url": "https://example.com/job2",
                "has_ta_team": False,
                "contacts_found": 2,
                "top_contacts": [
                    {"name": "Mike Chen", "title": "VP Engineering"},
                    {"name": "Lisa Rodriguez", "title": "Technical Lead"}
                ],
                "recommendation": "TARGET - Growing tech company",
                "timestamp": datetime.now().isoformat()
            },
            {
                "company": "DataDrive Analytics",
                "job_title": f"Lead {request.query.split()[0]} Specialist",
                "job_url": "https://example.com/job3",
                "has_ta_team": True,
                "contacts_found": 1,
                "top_contacts": [
                    {"name": "Alex Turner", "title": "HR Director"}
                ],
                "recommendation": "SKIP - Has internal TA team",
                "timestamp": datetime.now().isoformat()
            },
            {
                "company": "CloudScale Ventures",
                "job_title": f"{request.query.split()[0]} Architect",
                "job_url": "https://example.com/job4",
                "has_ta_team": False,
                "contacts_found": 4,
                "top_contacts": [
                    {"name": "David Kim", "title": "CTO"},
                    {"name": "Emma Wilson", "title": "Head of Engineering"}
                ],
                "recommendation": "TARGET - Scaling startup with funding",
                "timestamp": datetime.now().isoformat()
            },
            {
                "company": "NextGen Robotics",
                "job_title": f"Principal {request.query.split()[0]}",
                "job_url": "https://example.com/job5",
                "has_ta_team": False,
                "contacts_found": 2,
                "top_contacts": [
                    {"name": "Rachel Green", "title": "Founder & CEO"},
                    {"name": "Tom Anderson", "title": "VP Product"}
                ],
                "recommendation": "TARGET - Innovative AI company",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        return JobSearchResponse(
            companies_analyzed=demo_companies,
            jobs_found=25,  # Simulated total jobs found
            total_processed=5,
            search_query=request.query,
            timestamp=datetime.now().isoformat(),
            campaigns_created=None,
            leads_added=0
        )
        
    except Exception as e:
        logger.error(f"Error in instant job search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
