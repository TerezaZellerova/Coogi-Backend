"""
Shared Pydantic models for the API
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Request/Response Models
class JobSearchRequest(BaseModel):
    query: str
    hours_old: int = 720  # Default to 1 month for broader results
    enforce_salary: bool = True
    auto_generate_messages: bool = False
    create_campaigns: bool = True  # Default to True - automatically create Instantly campaigns
    campaign_name: Optional[str] = None  # Optional: custom campaign name
    min_score: float = 0.5  # Minimum lead score for campaign inclusion
    custom_tags: Optional[List[str]] = None  # Optional: custom tags to add to leads

class Lead(BaseModel):
    name: str
    title: str
    company: str
    email: str
    job_title: str
    job_url: str
    message: str = ""
    score: float
    timestamp: str

class JobSearchResponse(BaseModel):
    companies_analyzed: List[Dict[str, Any]]
    jobs_found: int
    total_processed: int
    search_query: str
    timestamp: str
    campaigns_created: Optional[List[str]] = None  # List of campaign IDs created
    leads_added: int = 0  # Total leads added to campaigns

class RawJobSpyResponse(BaseModel):
    jobs: List[Dict[str, Any]]
    total_jobs: int
    search_query: str
    location: str
    timestamp: str

class MessageGenerationRequest(BaseModel):
    job_title: str
    company: str
    contact_title: str
    job_url: str
    tone: str = "professional"
    additional_context: str = ""

class MessageGenerationResponse(BaseModel):
    message: str
    subject_line: str
    timestamp: str

class CompanyAnalysisRequest(BaseModel):
    query: str
    include_job_data: bool = True
    max_companies: int = 10

class CompanySkipReason(BaseModel):
    company: str
    reason: str
    ta_roles: List[str]
    timestamp: str

class CompanyReport(BaseModel):
    company: str
    has_ta_team: bool
    ta_roles: List[str]
    job_count: int
    active_jobs: List[Dict[str, Any]]
    decision_makers: List[Dict[str, Any]]
    recommendation: str
    skip_reason: Optional[str]

class CompanyAnalysisResponse(BaseModel):
    target_companies: List[CompanyReport]
    skipped_companies: List[CompanySkipReason]
    summary: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    api_status: Dict[str, bool]
    demo_mode: bool

class ContractOpportunityRequest(BaseModel):
    query: str
    max_companies: int = 20

class ContractOpportunity(BaseModel):
    company: str
    total_positions: int
    total_candidate_salaries: int
    estimated_recruiting_fees: int
    contract_value_score: float
    urgency_indicators: int
    growth_indicators: int
    seniority_score: float
    departments: List[str]
    locations: List[str]
    role_types: List[str]
    recruiting_pitch: str
    jobs: List[Dict[str, Any]]

class ContractAnalysisResponse(BaseModel):
    opportunities: List[ContractOpportunity]
    summary: Dict[str, Any]
    timestamp: str

class InstantlyCampaignRequest(BaseModel):
    query: str
    campaign_name: Optional[str] = None
    max_leads: int = 20
    min_score: float = 0.5

class InstantlyCampaignResponse(BaseModel):
    campaign_id: Optional[str]
    campaign_name: str
    leads_added: int
    total_leads_found: int
    status: str
    timestamp: str

class CompanyJobsRequest(BaseModel):
    company_name: str
    max_pages: int = 3

class CompanyJobsResponse(BaseModel):
    company: str
    total_jobs: int
    jobs: List[Dict[str, Any]]
    timestamp: str

# Add webhook models for production architecture
class WebhookResult(BaseModel):
    company: str
    job_title: str
    job_url: str
    has_ta_team: bool
    contacts_found: int
    top_contacts: List[Dict[str, Any]]
    recommendation: str
    hunter_emails: List[str] = []
    instantly_campaign_id: Optional[str] = None
    timestamp: str

class WebhookRequest(BaseModel):
    batch_id: str
    results: List[WebhookResult]
    summary: Dict[str, Any]
    timestamp: str

# Authentication Models
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
