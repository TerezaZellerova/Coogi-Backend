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
    target_type: str = "hiring_managers"  # "hiring_managers" or "job_candidates"
    company_size: str = "all"  # "small", "medium", "large", "all"
    location_filter: Optional[str] = None  # Optional location filter

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
    success: bool = True
    batch_id: Optional[str] = None
    message: Optional[str] = None
    estimated_jobs: Optional[int] = None
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

# Agent Models
class Agent(BaseModel):
    id: str
    query: str
    status: str = "processing"
    created_at: str
    total_jobs_found: int = 0
    total_emails_found: int = 0
    hours_old: int = 24
    custom_tags: Optional[List[str]] = None
    batch_id: Optional[str] = None
    processed_cities: Optional[int] = 0
    processed_companies: Optional[int] = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    processing_phase: Optional[str] = None

# Staged Agent Models
class AgentStage(BaseModel):
    name: str
    status: str  # "pending", "running", "completed", "failed"
    progress: int = 0  # 0-100
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    results_count: int = 0

class StagedResults(BaseModel):
    linkedin_jobs: List[Dict[str, Any]] = []
    other_jobs: List[Dict[str, Any]] = []
    verified_contacts: List[Dict[str, Any]] = []
    campaigns: List[Dict[str, Any]] = []
    total_jobs: int = 0
    total_contacts: int = 0
    total_campaigns: int = 0

class ProgressiveAgent(BaseModel):
    id: str
    query: str
    status: str  # "initializing", "linkedin_stage", "enrichment_stage", "completed", "failed"
    created_at: str
    updated_at: str
    total_progress: int = 0  # Overall progress 0-100
    stages: Dict[str, AgentStage] = {}
    staged_results: StagedResults = StagedResults()
    hours_old: int = 24
    custom_tags: Optional[List[str]] = None
    target_type: str = "hiring_managers"  # "hiring_managers" or "job_candidates"
    company_size: str = "all"  # "small", "medium", "large", "all"
    location_filter: Optional[str] = None
    final_stats: Optional[Dict[str, Any]] = None

class ProgressiveAgentResponse(BaseModel):
    agent: ProgressiveAgent
    message: str
    next_update_in_seconds: int = 30  # How often frontend should poll for updates

# SES Email Models
class SESEmailRequest(BaseModel):
    to_emails: List[str]
    subject: str
    body_html: str
    body_text: str
    from_email: str
    reply_to: Optional[str] = None

class SESBulkEmailRequest(BaseModel):
    emails_data: List[Dict[str, Any]]  # Each dict contains email and template_data
    template_name: str
    from_email: str

class SESTemplateRequest(BaseModel):
    template_name: str
    subject: str
    html_part: str
    text_part: str

class SESCampaignRequest(BaseModel):
    query: str
    campaign_name: Optional[str] = None
    max_leads: int = 20
    min_score: float = 0.5
    email_provider: str = "ses"  # "ses", "instantly", "smartlead"
    from_email: str
    subject: str
    email_template: str
    send_immediately: bool = False

class SESCampaignResponse(BaseModel):
    campaign_id: Optional[str]
    campaign_name: str
    leads_added: int
    total_leads_found: int
    emails_sent: int = 0
    email_failures: int = 0
    status: str
    provider: str
    message_ids: List[str] = []
    timestamp: str

class EmailProviderStats(BaseModel):
    provider: str
    send_quota: float  # Changed from daily_quota to match frontend
    sent_last_24_hours: float  # Changed from sent_last_24h to match frontend
    max_send_rate: float  # Changed from send_rate to match frontend
    reputation_score: Optional[float] = None
    bounce_rate: Optional[float] = None
    complaint_rate: Optional[float] = None
    reputation: Optional[Dict[str, Any]] = None  # Added to match frontend expectation
    timestamp: str

# JSearch Models
class JSearchJobRequest(BaseModel):
    query: str
    location: str = "United States"
    employment_types: str = "FULLTIME"
    remote_jobs_only: bool = False
    date_posted: str = "month"
    num_pages: int = 1

class JSearchJobResponse(BaseModel):
    success: bool
    jobs: List[Dict[str, Any]] = []
    total_found: int = 0
    query: str
    location: str
    timestamp: str

class JSearchSalaryRequest(BaseModel):
    job_title: str
    location: str = "United States"

class JSearchSalaryResponse(BaseModel):
    success: bool
    salary_estimates: List[Dict[str, Any]] = []
    job_title: str
    location: str
    timestamp: str

# Smartlead Models
class SmartleadCampaignRequest(BaseModel):
    name: str
    leads: List[Dict[str, Any]]
    email_template: str
    subject: str
    from_email: str
    from_name: str = "Recruiting Team"

class SmartleadAICampaignRequest(BaseModel):
    name: str
    leads: List[Dict[str, Any]]
    template_context: str
    subject_template: str
    from_email: str
    personalization_level: str = "high"

class SmartleadCampaignResponse(BaseModel):
    success: bool
    campaign_id: Optional[str] = None
    campaign_name: str
    leads_added: int = 0
    failed_leads: int = 0
    failed_details: List[Dict[str, Any]] = []
    ai_personalized: bool = False
    personalization_level: Optional[str] = None
    timestamp: str

class SmartleadStatsResponse(BaseModel):
    success: bool
    campaign_id: str
    stats: Dict[str, Any] = {}
    timestamp: str

class SmartleadAccountResponse(BaseModel):
    success: bool
    account: Dict[str, Any] = {}
    timestamp: str

# Email Intelligence Models (GPT Auto-Tagging & Smart Replies)
class EmailMessage(BaseModel):
    id: str
    from_email: str
    to_email: str
    subject: str
    body: str
    timestamp: str
    message_id: str
    thread_id: Optional[str] = None
    is_reply: bool = False
    original_message_id: Optional[str] = None
    email_provider: str = "ses"  # "ses", "gmail", "outlook"

class EmailTag(BaseModel):
    tag_name: str
    confidence: float
    reason: str
    category: str  # "priority", "sentiment", "intent", "department", "topic"
    auto_applied: bool = True
    applied_at: str

class EmailAnalysis(BaseModel):
    message_id: str
    tags: List[EmailTag]
    sentiment: str  # "positive", "negative", "neutral", "frustrated", "happy"
    priority: str   # "urgent", "high", "normal", "low"
    intent: str     # "question", "complaint", "request", "inquiry", "support", "sales"
    department: str # "sales", "support", "hr", "technical", "billing", "general"
    confidence: float
    key_points: List[str]
    suggested_response_tone: str
    needs_human_review: bool
    timestamp: str

class SmartReply(BaseModel):
    original_message_id: str
    suggested_reply: str
    confidence: float
    tone: str  # "professional", "friendly", "empathetic", "technical", "apologetic"
    key_points_addressed: List[str]
    call_to_action: Optional[str] = None
    auto_send_eligible: bool = False
    timestamp: str

class EmailAutoResponse(BaseModel):
    message_id: str
    analysis: EmailAnalysis
    smart_replies: List[SmartReply]
    auto_tag_applied: bool
    auto_reply_sent: bool = False
    human_review_required: bool
    department_routed: Optional[str] = None
    processed_at: str

class EmailIntelligenceRequest(BaseModel):
    email_content: Dict[str, str]  # subject, body, from_email, to_email
    context: Optional[Dict[str, Any]] = None  # customer info, history, etc.
    auto_reply: bool = False
    auto_tag: bool = True

class EmailIntelligenceResponse(BaseModel):
    success: bool
    message_id: str
    analysis: EmailAnalysis
    smart_replies: List[SmartReply]
    actions_taken: Dict[str, bool]  # auto_tagged, auto_replied, routed, etc.
    processing_time_ms: int
    timestamp: str

# Coogi Domain Email Models (SES + S3 Integration)
class CoogiEmailConfig(BaseModel):
    domain: str = "coogi.com"
    supported_emails: List[str]
    s3_bucket: str
    from_email: str
    auto_reply_enabled: bool = True
    gpt_processing: bool = True

class CoogiEmailProcessingRequest(BaseModel):
    hours: int = 24  # How many hours back to process
    auto_reply: bool = True
    specific_email: Optional[str] = None  # Process specific email address only

class CoogiEmailProcessingResponse(BaseModel):
    success: bool
    domain: str
    emails_found: int
    emails_processed: int
    auto_tagged: int
    smart_replies_generated: int
    auto_replies_sent: int
    processing_time_ms: int
    processed_emails: List[Dict[str, Any]]
    timestamp: str

class CoogiEmailStats(BaseModel):
    success: bool
    domain: str
    total_emails_received: int
    emails_last_24h: int
    supported_addresses: List[str]
    s3_bucket: str
    ses_sending_stats: Dict[str, Any]
    timestamp: str

class SESReceiptRule(BaseModel):
    rule_name: str
    enabled: bool
    recipients: List[str]
    s3_bucket: str
    status: str
