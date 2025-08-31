from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Dict, Any
import logging
import json
import time
import httpx
import asyncio
import os
from supabase import create_client

from ..models import (
    JobSearchRequest, JobSearchResponse, RawJobSpyResponse,
    MessageGenerationRequest, MessageGenerationResponse,
    CompanyAnalysisRequest, CompanyAnalysisResponse,
    ContractOpportunityRequest, ContractAnalysisResponse,
    CompanyJobsRequest, CompanyJobsResponse, Agent
)
from ..dependencies import (
    get_current_user, get_job_scraper, get_contact_finder, 
    get_email_generator, get_memory_manager, get_contract_analyzer,
    get_instantly_manager, get_blacklist_manager,
    log_to_supabase
)
from utils.clearout_manager import clearout_manager
from utils.progressive_agent_db import progressive_agent_db
from utils.progressive_agent_manager import progressive_agent_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["leads"])

# Initialize Supabase client for direct queries
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") 
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        for city in job_scraper.us_cities[:10]:  # Increased to 10 cities for better coverage while maintaining performance
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
                    results_wanted=search_params.get('results_wanted', 200),  # Increased for better job coverage
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
                    job_source = job.get('site', 'unknown')  # Get the site/source (linkedin, indeed, etc.)
                    
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
                        
                        # STEP 4: Hunter.io (for all found companies)
                        hunter_emails = []
                        if company_found:
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
                            await log_to_supabase(batch_id, f"⏭️ Skipping Hunter.io for {company} (company not found)", "info", company, job_title, job_url, "hunter_skipped")
                        
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
                            "job_source": job_source,  # Add source information (linkedin, indeed, etc.)
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
        
        # Save agent data to memory for persistence
        agent_data = {
            "batch_id": batch_id,
            "query": request.query,
            "status": "completed",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_jobs_found": total_jobs_found,
            "total_emails_found": sum(len(comp.get('hunter_emails', [])) for comp in companies_analyzed),
            "hours_old": request.hours_old,
            "custom_tags": getattr(request, 'custom_tags', None),
            "processed_cities": 10,  # We now process first 10 cities
            "processed_companies": len(companies_analyzed),
            "companies_analyzed": companies_analyzed,
            "campaigns_created": campaigns_created,
            "leads_added": leads_added
        }
        memory_manager.save_agent_data(batch_id, agent_data)
        logger.info(f"💾 Agent {batch_id} saved to memory")
        
        return JobSearchResponse(
            success=True,
            batch_id=batch_id,
            message=f"Job search completed: {len(companies_analyzed)} companies analyzed",
            estimated_jobs=total_jobs_found,
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
        contact_finder = get_contact_finder()
        
        # Parse query and search for jobs
        search_params = job_scraper.parse_query(request.query)
        jobs = job_scraper.search_jobs(search_params, max_results=request.max_companies * 3)
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found matching criteria")
        
        # Perform basic company analysis using existing contact finder
        target_companies = []
        skipped_companies = []
        
        for job in jobs[:request.max_companies]:
            company = job.get('company', '')
            if not company:
                continue
                
            try:
                # Use existing contact finder to check for TA team
                result = contact_finder.find_contacts(
                    company=company,
                    linkedin_identifier=company.lower().replace(" ", "-"),
                    role_hint=job.get('title', ''),
                    keywords=job_scraper.extract_keywords(job.get('description', '')),
                    company_website=None
                )
                
                contacts, has_ta_team, employee_roles, company_found = result
                
                if has_ta_team:
                    skipped_companies.append({
                        "company": company,
                        "reason": "Has internal TA team",
                        "job_title": job.get('title', ''),
                        "contacts_found": len(contacts)
                    })
                else:
                    target_companies.append({
                        "company": company,
                        "job_title": job.get('title', ''),
                        "job_url": job.get('url', ''),
                        "job_source": job.get('job_source', job.get('site', 'unknown')),
                        "contacts_found": len(contacts),
                        "top_contacts": contacts[:3],
                        "employee_roles": employee_roles,
                        "company_found": company_found,
                        "recommendation": "TARGET - No internal TA team"
                    })
                    
            except Exception as e:
                logger.warning(f"Error analyzing company {company}: {e}")
                continue
        
        summary = {
            "total_companies_analyzed": len(jobs),
            "target_companies_found": len(target_companies),
            "companies_skipped": len(skipped_companies),
            "skip_reasons": {"has_ta_team": len(skipped_companies)},
            "success_rate": (len(target_companies) / max(len(jobs), 1)) * 100
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

# ===== INSTANTLY.AI CAMPAIGN MANAGEMENT ENDPOINTS =====

from pydantic import BaseModel
from typing import Optional, List

class InstantlyCampaignRequest(BaseModel):
    campaign_name: str
    leads: List[Dict[str, Any]]
    description: Optional[str] = ""

class InstantlyLeadRequest(BaseModel):
    email: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    company_name: Optional[str] = ""
    job_title: Optional[str] = ""

@router.post("/instantly/create-campaign")
async def create_instantly_campaign(request: InstantlyCampaignRequest):
    """Create a new Instantly.ai campaign with leads"""
    try:
        instantly_manager = get_instantly_manager()
        
        # Create the campaign
        campaign_result = instantly_manager.create_recruiting_campaign(
            leads=request.leads,
            campaign_name=request.campaign_name,
            description=request.description
        )
        
        if campaign_result:
            return {
                "success": True,
                "campaign_id": campaign_result,
                "message": f"Campaign '{request.campaign_name}' created successfully",
                "leads_added": len(request.leads)
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create campaign")
            
    except Exception as e:
        logger.error(f"Error creating Instantly campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instantly/campaigns")
async def get_instantly_campaigns():
    """Get all Instantly.ai campaigns"""
    try:
        instantly_manager = get_instantly_manager()
        campaigns = instantly_manager.get_campaigns()
        
        return {
            "success": True,
            "campaigns": campaigns or [],
            "total": len(campaigns) if campaigns else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting Instantly campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instantly/campaigns/{campaign_id}")
async def get_instantly_campaign(campaign_id: str):
    """Get specific Instantly.ai campaign details"""
    try:
        instantly_manager = get_instantly_manager()
        campaign = instantly_manager.get_campaign(campaign_id)
        
        if campaign:
            return {
                "success": True,
                "campaign": campaign
            }
        else:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
    except Exception as e:
        logger.error(f"Error getting Instantly campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/instantly/campaigns/{campaign_id}/activate")
async def activate_instantly_campaign(campaign_id: str):
    """Activate an Instantly.ai campaign"""
    try:
        instantly_manager = get_instantly_manager()
        success = instantly_manager.activate_campaign(campaign_id)
        
        if success:
            return {
                "success": True,
                "message": f"Campaign {campaign_id} activated successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to activate campaign")
            
    except Exception as e:
        logger.error(f"Error activating Instantly campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/instantly/campaigns/{campaign_id}/pause")
async def pause_instantly_campaign(campaign_id: str):
    """Pause an Instantly.ai campaign"""
    try:
        instantly_manager = get_instantly_manager()
        success = instantly_manager.pause_campaign(campaign_id)
        
        if success:
            return {
                "success": True,
                "message": f"Campaign {campaign_id} paused successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to pause campaign")
            
    except Exception as e:
        logger.error(f"Error pausing Instantly campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instantly/campaigns/{campaign_id}/leads")
async def get_campaign_leads(campaign_id: str):
    """Get leads for a specific Instantly.ai campaign"""
    try:
        instantly_manager = get_instantly_manager()
        leads = instantly_manager.get_leads_for_campaign(campaign_id)
        
        return {
            "success": True,
            "leads": leads,
            "total": len(leads)
        }
        
    except Exception as e:
        logger.error(f"Error getting leads for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/instantly/add-leads")
async def add_leads_to_instantly(request: InstantlyLeadRequest):
    """Add individual leads to Instantly.ai"""
    try:
        instantly_manager = get_instantly_manager()
        
        # Convert single lead to list format
        lead_data = {
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "company_name": request.company_name,
            "job_title": request.job_title
        }
        
        # Create a simple campaign or add to default list
        success = instantly_manager.add_lead_to_list(lead_data)
        
        if success:
            return {
                "success": True,
                "message": "Lead added successfully to Instantly.ai"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add lead")
            
    except Exception as e:
        logger.error(f"Error adding lead to Instantly: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instantly/status")
async def get_instantly_status():
    """Check Instantly.ai API connection and status"""
    try:
        instantly_manager = get_instantly_manager()
        
        # Test API connection by trying to get campaigns
        campaigns = instantly_manager.get_campaigns()
        
        return {
            "success": True,
            "api_connected": True,
            "total_campaigns": len(campaigns) if campaigns else 0,
            "message": "Instantly.ai API is working correctly"
        }
        
    except Exception as e:
        logger.error(f"Error checking Instantly status: {e}")
        return {
            "success": False,
            "api_connected": False,
            "error": str(e),
            "message": "Instantly.ai API connection failed"
        }

# ===== CLEAROUT EMAIL VERIFICATION ENDPOINTS =====

@router.post("/verify-email")
async def verify_single_email(request: dict):
    """
    Verify a single email address using ClearOut API
    """
    try:
        email = request.get("email")
        if not email:
            return {"error": "Email address is required"}
        
        result = clearout_manager.verify_email(email)
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"❌ Error in email verification: {str(e)}")
        return {"error": str(e)}

@router.post("/verify-emails-bulk")
async def verify_bulk_emails(request: dict):
    """
    Verify multiple emails in bulk using ClearOut API
    """
    try:
        emails = request.get("emails", [])
        if not emails:
            return {"error": "Email list is required"}
        
        if len(emails) > 1000:
            return {"error": "Maximum 1000 emails allowed per batch"}
        
        result = clearout_manager.bulk_verify_emails(emails)
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"❌ Error in bulk email verification: {str(e)}")
        return {"error": str(e)}

@router.get("/verification-status/{job_id}")
async def get_verification_status(job_id: str):
    """
    Get bulk verification job status and results
    """
    try:
        result = clearout_manager.get_bulk_results(job_id)
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"❌ Error getting verification status: {str(e)}")
        return {"error": str(e)}

@router.get("/clearout-account")
async def get_clearout_account():
    """
    Get ClearOut account information and remaining credits
    """
    try:
        result = clearout_manager.get_account_info()
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"❌ Error getting ClearOut account info: {str(e)}")
        return {"error": str(e)}

@router.post("/find-company-domain")
async def find_company_domain(request: dict):
    """
    Find company website domain using ClearOut API
    """
    try:
        company_name = request.get("company_name")
        if not company_name:
            return {"error": "Company name is required"}
        
        domain = clearout_manager.find_company_domain(company_name)
        return {
            "success": True, 
            "data": {
                "company_name": company_name,
                "domain": domain,
                "found": domain is not None
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error finding company domain: {str(e)}")
        return {"error": str(e)}

# Add a FAST preview endpoint
@router.post("/search-jobs-preview", response_model=JobSearchResponse)
async def search_jobs_preview(request: JobSearchRequest):
    """FAST preview of job opportunities - shows immediate results while processing in background"""
    try:
        job_scraper = get_job_scraper()
        
        # Generate batch ID for logging
        batch_id = f"preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Parse query
        search_params = job_scraper.parse_query(request.query)
        
        # FAST job search - limit to first 20 jobs for speed
        search_params['results_wanted'] = 20  # Limit for speed
        search_params['hours_old'] = request.hours_old
        
        await log_to_supabase(batch_id, f"🚀 Starting FAST preview: {request.query}", "info")
        
        # Get basic job data quickly
        jobs_data = await job_scraper.search_jobs_parallel(search_params)
        
        if not jobs_data or len(jobs_data) == 0:
            await log_to_supabase(batch_id, "❌ No jobs found in preview", "warning")
            return JobSearchResponse(
                agent=Agent(
                    id=f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    query=request.query,
                    status="completed",
                    created_at=datetime.now().isoformat(),
                    total_jobs_found=0,
                    total_emails_found=0
                ),
                results=JobSearchResponse(
                    companies_analyzed=[],
                    jobs_found=0,
                    total_processed=0,
                    search_query=request.query,
                    timestamp=datetime.now().isoformat()
                )
            )
        
        # Process companies quickly - basic info only
        companies_analyzed = []
        
        for job in jobs_data[:10]:  # Process only first 10 for speed
            try:
                company_data = {
                    "company": job.get('company', 'Unknown Company'),
                    "job_title": job.get('title', 'Unknown Title'),
                    "job_url": job.get('job_url', ''),
                    "job_source": job.get('site', 'Unknown'),
                    "location": job.get('location', ''),
                    "has_ta_team": False,  # Default for preview
                    "contacts_found": 0,   # Will be enriched later
                    "top_contacts": [],    # Will be enriched later
                    "emails_generated": [],
                    "campaign_created": False,
                    "processing_stage": "preview",
                    "preview_mode": True
                }
                
                companies_analyzed.append(company_data)
                
            except Exception as e:
                logger.error(f"Error processing company in preview: {e}")
                continue
        
        # Create preview agent
        agent = Agent(
            id=f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            query=request.query,
            status="processing",  # Still processing in background
            created_at=datetime.now().isoformat(),
            total_jobs_found=len(jobs_data),
            total_emails_found=0,  # Will be updated later
            preview_mode=True
        )
        
        results = JobSearchResponse(
            companies_analyzed=companies_analyzed,
            jobs_found=len(jobs_data),
            total_processed=len(companies_analyzed),
            search_query=request.query,
            timestamp=datetime.now().isoformat()
        )
        
        await log_to_supabase(batch_id, f"✅ FAST preview completed: {len(companies_analyzed)} companies", "info")
        
        # TODO: Start background task for full processing
        # background_tasks.add_task(process_full_analysis, agent.id, request)
        
        return JobSearchResponse(agent=agent, results=results)
        
    except Exception as e:
        logger.error(f"Error in preview search: {e}")
        raise HTTPException(status_code=500, detail=f"Preview search failed: {str(e)}")

# Progressive Agent Data Endpoints
@router.get("/leads/jobs")
async def get_all_jobs(limit: int = 100):
    """Get all jobs from progressive agents"""
    try:
        jobs = await progressive_agent_db.get_agent_jobs(limit=limit)
        return {"success": True, "data": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/contacts")
async def get_all_contacts(limit: int = 100):
    """Get all contacts from progressive agents"""
    try:
        contacts = await progressive_agent_db.get_agent_contacts(limit=limit)
        return {"success": True, "data": contacts, "count": len(contacts)}
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/campaigns")
async def get_all_campaigns(limit: int = 100):
    """Get all campaigns from progressive agents"""
    try:
        campaigns = await progressive_agent_db.get_agent_campaigns(limit=limit)
        return {"success": True, "data": campaigns, "count": len(campaigns)}
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/dashboard-stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = await progressive_agent_db.get_dashboard_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/agent/{agent_id}/jobs")
async def get_agent_jobs(agent_id: str, limit: int = 100):
    """Get jobs for a specific agent"""
    try:
        jobs = await progressive_agent_db.get_agent_jobs(agent_id=agent_id, limit=limit)
        return {"success": True, "data": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Error getting agent jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/agent/{agent_id}/contacts")
async def get_agent_contacts(agent_id: str, limit: int = 100):
    """Get contacts for a specific agent"""
    try:
        contacts = await progressive_agent_db.get_agent_contacts(agent_id=agent_id, limit=limit)
        return {"success": True, "data": contacts, "count": len(contacts)}
    except Exception as e:
        logger.error(f"Error getting agent contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/agent/{agent_id}/campaigns")
async def get_agent_campaigns(agent_id: str, limit: int = 100):
    """Get campaigns for a specific agent"""
    try:
        campaigns = await progressive_agent_db.get_agent_campaigns(agent_id=agent_id, limit=limit)
        return {"success": True, "data": campaigns, "count": len(campaigns)}
    except Exception as e:
        logger.error(f"Error getting agent campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Progressive Agent Data Endpoints from Staged Results (Real Data)
@router.get("/leads/linkedin-jobs")
async def get_linkedin_jobs(limit: int = 100):
    """Get LinkedIn jobs from progressive agents' staged results"""
    try:
        # Get LinkedIn jobs directly from database - this is more reliable than in-memory agents
        from utils.progressive_agent_db import progressive_agent_db
        
        all_linkedin_jobs = []
        
        # Get LinkedIn jobs directly from database (most reliable approach)
        if supabase:
            try:
                # Get LinkedIn jobs directly from database
                result = supabase.table("progressive_agent_jobs").select("*").eq("site", "linkedin").order("created_at", desc=True).limit(limit).execute()
                db_jobs = result.data or []
                logger.info(f"🔍 Found {len(db_jobs)} LinkedIn jobs in database")
                
                for job in db_jobs:
                    # Ensure job has proper structure
                    if 'agent_id' not in job:
                        job['agent_id'] = job.get('agent_id', 'unknown')
                    if 'agent_query' not in job:
                        job['agent_query'] = 'unknown'
                    all_linkedin_jobs.append(job)
                    
            except Exception as db_error:
                logger.error(f"Error fetching LinkedIn jobs from database: {db_error}")
        
        # Also check in-memory agents as fallback (for newly created agents)
        try:
            agents = progressive_agent_manager.get_all_agents()
            logger.info(f"🔍 Found {len(agents)} in-memory agents")
            
            for agent in agents:
                try:
                    # Handle both object-style and dict-style agents
                    if hasattr(agent, 'staged_results') and agent.staged_results:
                        linkedin_jobs = getattr(agent.staged_results, 'linkedin_jobs', [])
                    elif isinstance(agent, dict) and 'staged_results' in agent:
                        linkedin_jobs = agent['staged_results'].get('linkedin_jobs', [])
                    else:
                        continue
                    
                    if linkedin_jobs:
                        for job in linkedin_jobs:
                            # Add agent context
                            job_with_context = dict(job)
                            job_with_context['agent_id'] = getattr(agent, 'id', agent.get('id', 'unknown'))
                            job_with_context['agent_query'] = getattr(agent, 'query', agent.get('query', 'unknown'))
                            all_linkedin_jobs.append(job_with_context)
                            
                except Exception as agent_error:
                    logger.warning(f"Error processing agent: {agent_error}")
                    continue
                    
        except Exception as memory_error:
            logger.warning(f"Error accessing in-memory agents: {memory_error}")
        
        # Remove duplicates based on job_id
        seen_jobs = set()
        unique_jobs = []
        for job in all_linkedin_jobs:
            job_id = job.get('job_id') or job.get('id')
            if job_id and job_id not in seen_jobs:
                seen_jobs.add(job_id)
                unique_jobs.append(job)
        
        # Sort by creation date (newest first) and limit
        unique_jobs.sort(key=lambda x: x.get('scraped_at') or x.get('created_at', ''), reverse=True)
        
        logger.info(f"🎯 Returning {len(unique_jobs[:limit])} unique LinkedIn jobs")
        return {"success": True, "data": unique_jobs[:limit], "count": len(unique_jobs[:limit])}
        
        # Sort by creation date (newest first) and limit
        all_linkedin_jobs.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
        
        return {"success": True, "data": all_linkedin_jobs[:limit], "count": len(all_linkedin_jobs[:limit])}
    except Exception as e:
        logger.error(f"Error getting LinkedIn jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/other-jobs")
async def get_other_jobs(limit: int = 100):
    """Get non-LinkedIn jobs from progressive agents' staged results"""
    try:
        # Get other jobs directly from database - this is more reliable than in-memory agents
        all_other_jobs = []
        
        # Get non-LinkedIn jobs directly from database (most reliable approach)
        if supabase:
            try:
                # Get non-LinkedIn jobs directly from database  
                result = supabase.table("progressive_agent_jobs").select("*").neq("site", "linkedin").order("created_at", desc=True).limit(limit).execute()
                db_jobs = result.data or []
                logger.info(f"🔍 Found {len(db_jobs)} non-LinkedIn jobs in database")
                
                for job in db_jobs:
                    # Ensure job has proper structure
                    if 'agent_id' not in job:
                        job['agent_id'] = job.get('agent_id', 'unknown')
                    if 'agent_query' not in job:
                        job['agent_query'] = 'unknown'
                    all_other_jobs.append(job)
                    
            except Exception as db_error:
                logger.error(f"Error fetching non-LinkedIn jobs from database: {db_error}")
        
        # Also check in-memory agents as fallback (for newly created agents)
        try:
            agents = progressive_agent_manager.get_all_agents()
            logger.info(f"🔍 Found {len(agents)} in-memory agents")
            
            for agent in agents:
                try:
                    # Handle both object-style and dict-style agents
                    # Include agents that have completed other_boards stage or are fully completed
                    agent_ready = False
                    if hasattr(agent, 'stages') and hasattr(agent.stages, 'other_boards'):
                        if agent.stages.other_boards.status == "completed":
                            agent_ready = True
                    elif hasattr(agent, 'status') and agent.status == "completed":
                        agent_ready = True
                    elif isinstance(agent, dict):
                        stages = agent.get('stages', {})
                        if isinstance(stages, dict):
                            other_boards = stages.get('other_boards', {})
                            if isinstance(other_boards, dict) and other_boards.get('status') == 'completed':
                                agent_ready = True
                    
                    if agent_ready:
                        if hasattr(agent, 'staged_results') and agent.staged_results:
                            other_jobs = getattr(agent.staged_results, 'other_jobs', [])
                        elif isinstance(agent, dict) and 'staged_results' in agent:
                            other_jobs = agent['staged_results'].get('other_jobs', [])
                        else:
                            continue
                        
                        if other_jobs:
                            for job in other_jobs:
                                # Add agent context
                                job_with_context = dict(job)
                                job_with_context['agent_id'] = getattr(agent, 'id', agent.get('id', 'unknown'))
                                job_with_context['agent_query'] = getattr(agent, 'query', agent.get('query', 'unknown'))
                                all_other_jobs.append(job_with_context)
                                
                except Exception as agent_error:
                    logger.warning(f"Error processing agent: {agent_error}")
                    continue
                    
        except Exception as memory_error:
            logger.warning(f"Error accessing in-memory agents: {memory_error}")
        
        # Remove duplicates based on job_id
        seen_jobs = set()
        unique_jobs = []
        for job in all_other_jobs:
            job_id = job.get('job_id') or job.get('id')
            if job_id and job_id not in seen_jobs:
                seen_jobs.add(job_id)
                unique_jobs.append(job)
        
        # Sort by creation date (newest first) and limit
        unique_jobs.sort(key=lambda x: x.get('scraped_at') or x.get('created_at', ''), reverse=True)
        
        logger.info(f"🎯 Returning {len(unique_jobs[:limit])} unique other jobs")
        return {"success": True, "data": unique_jobs[:limit], "count": len(unique_jobs[:limit])}
    except Exception as e:
        logger.error(f"Error getting other jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/progressive-contacts")
async def get_progressive_contacts(limit: int = 100):
    """Get contacts from progressive agents' staged results"""
    try:
        # Get all completed agents
        agents = progressive_agent_manager.get_all_agents()
        completed_agents = [agent for agent in agents if agent.status == "completed"]
        
        all_contacts = []
        
        for agent in completed_agents:
            if agent.staged_results and agent.staged_results.verified_contacts:
                for contact in agent.staged_results.verified_contacts:
                    # Add agent context
                    contact_with_context = dict(contact)
                    contact_with_context['agent_id'] = agent.id
                    contact_with_context['agent_query'] = agent.query
                    all_contacts.append(contact_with_context)
        
        # Sort by creation date (newest first) and limit
        all_contacts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {"success": True, "data": all_contacts[:limit], "count": len(all_contacts[:limit])}
    except Exception as e:
        logger.error(f"Error getting progressive contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
