"""
Candidates API Router
Handles candidate search and management using Apollo.io
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from pydantic import BaseModel

from utils.apollo_manager import ApolloManager
from utils.progressive_agent_db import ProgressiveAgentDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/candidates",
    tags=["candidates"],
    responses={404: {"description": "Not found"}},
)

# Request/Response Models
class CandidateSearchRequest(BaseModel):
    job_title: str
    location: Optional[str] = None
    domain: Optional[str] = None
    company_size: Optional[str] = None
    limit: Optional[int] = 10

class CandidateResponse(BaseModel):
    name: str
    first_name: str
    last_name: str
    email: str
    title: str
    company: str
    domain: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    seniority: Optional[str] = None
    departments: List[str] = []
    functions: List[str] = []
    email_status: Optional[str] = None
    apollo_id: str
    source: str = "apollo"

class CandidateSearchResponse(BaseModel):
    success: bool
    candidates: List[CandidateResponse]
    total_found: int
    search_params: Dict[str, Any]
    timestamp: str
    error: Optional[str] = None

class AttachCandidateRequest(BaseModel):
    candidate_id: str
    job_id: str

@router.post("/search", response_model=CandidateSearchResponse)
async def search_candidates(request: CandidateSearchRequest):
    """Search for job candidates using Apollo.io API"""
    try:
        apollo_manager = ApolloManager()
        
        if not apollo_manager.api_key:
            raise HTTPException(
                status_code=400, 
                detail="Apollo.io API key not configured"
            )
        
        logger.info(f"🔍 Searching candidates for: {request.job_title}")
        
        result = apollo_manager.search_candidates(
            job_title=request.job_title,
            location=request.location,
            domain=request.domain,
            company_size=request.company_size,
            limit=request.limit
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=f"Apollo search failed: {result.get('error', 'Unknown error')}"
            )
        
        # Save candidates to database
        db = ProgressiveAgentDB()
        saved_candidates = []
        
        def safe_candidate_data(candidate):
            """Safely extract candidate data with proper null handling"""
            return {
                "name": candidate.get("name", ""),
                "first_name": candidate.get("first_name", ""),
                "last_name": candidate.get("last_name", ""),
                "email": candidate.get("email", ""),
                "title": candidate.get("title", ""),
                "company": candidate.get("company", ""),
                "domain": candidate.get("domain") or "",
                "location": candidate.get("location") or "",
                "linkedin_url": candidate.get("linkedin_url") or "",
                "phone": candidate.get("phone") or "",
                "seniority": candidate.get("seniority") or "",
                "departments": candidate.get("departments", []),
                "functions": candidate.get("functions", []),
                "email_status": candidate.get("email_status") or "",
                "apollo_id": candidate.get("apollo_id", ""),
                "source": candidate.get("source", "apollo")
            }
        
        for candidate in result["candidates"]:
            try:
                # Check if candidate already exists
                existing_query = db.supabase.table('candidates').select('*').eq('email', candidate['email']).execute()
                
                if existing_query.data:
                    # Update existing candidate
                    candidate_data = safe_candidate_data(candidate)
                    candidate_data["updated_at"] = datetime.now().isoformat()
                    
                    update_result = db.supabase.table('candidates').update(candidate_data).eq('email', candidate['email']).execute()
                    saved_candidates.append(safe_candidate_data(candidate))
                else:
                    # Insert new candidate
                    candidate_data = safe_candidate_data(candidate)
                    candidate_data.update({
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })
                    
                    insert_result = db.supabase.table('candidates').insert(candidate_data).execute()
                    saved_candidates.append(safe_candidate_data(candidate))
                    
            except Exception as db_error:
                logger.error(f"Failed to save candidate {candidate['email']}: {db_error}")
                # Continue with next candidate
                saved_candidates.append(candidate)
        
        logger.info(f"✅ Found and saved {len(saved_candidates)} candidates")
        
        return CandidateSearchResponse(
            success=True,
            candidates=saved_candidates,
            total_found=len(saved_candidates),
            search_params=result["search_params"],
            timestamp=result["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Candidate search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-apollo")
async def test_apollo_connection():
    """Test Apollo.io API connection"""
    try:
        apollo_manager = ApolloManager()
        result = apollo_manager.test_api_connection()
        
        if result.get("status") == "operational":
            return {
                "status": "success",
                "message": "Apollo.io API connection successful",
                "details": result
            }
        else:
            return {
                "status": "error",
                "message": "Apollo.io API connection failed",
                "details": result
            }
            
    except Exception as e:
        logger.error(f"Apollo test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/attach-to-job")
async def attach_candidate_to_job(request: AttachCandidateRequest):
    """Attach a candidate to a specific job"""
    try:
        db = ProgressiveAgentDB()
        # Check if candidate exists
        candidate_query = db.supabase.table('candidates').select('*').eq('id', request.candidate_id).execute()
        if not candidate_query.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Check if job exists (assuming you have a jobs table)
        job_query = db.supabase.table('jobs').select('*').eq('id', request.job_id).execute()
        if not job_query.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Create job-candidate relationship
        relationship_data = {
            "job_id": request.job_id,
            "candidate_id": request.candidate_id,
            "status": "potential",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Check if relationship already exists
        existing_rel = db.supabase.table('job_candidates').select('*').eq('job_id', request.job_id).eq('candidate_id', request.candidate_id).execute()
        
        if existing_rel.data:
            # Update existing relationship
            result = db.supabase.table('job_candidates').update(relationship_data).eq('job_id', request.job_id).eq('candidate_id', request.candidate_id).execute()
        else:
            # Create new relationship
            result = db.supabase.table('job_candidates').insert(relationship_data).execute()
        
        logger.info(f"✅ Attached candidate {request.candidate_id} to job {request.job_id}")
        
        return {
            "success": True,
            "message": "Candidate successfully attached to job",
            "relationship": result.data[0] if result.data else relationship_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attach candidate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-job/{job_id}")
async def get_candidates_by_job(job_id: str):
    """Get all candidates attached to a specific job"""
    try:
        db = ProgressiveAgentDB()
        # Get job-candidate relationships
        relationships_query = db.supabase.table('job_candidates').select('*, candidates(*)').eq('job_id', job_id).execute()
        
        candidates = []
        for rel in relationships_query.data:
            if rel.get('candidates'):
                candidate = rel['candidates']
                candidate['relationship_status'] = rel.get('status', 'potential')
                candidate['attached_at'] = rel.get('created_at')
                candidates.append(candidate)
        
        return {
            "success": True,
            "job_id": job_id,
            "candidates": candidates,
            "total_count": len(candidates),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get candidates by job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: str):
    """Delete a candidate"""
    try:
        db = ProgressiveAgentDB()
        # Delete candidate (this will cascade to job_candidates if properly set up)
        result = db.supabase.table('candidates').delete().eq('id', candidate_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        logger.info(f"✅ Deleted candidate {candidate_id}")
        
        return {
            "success": True,
            "message": "Candidate deleted successfully",
            "candidate_id": candidate_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete candidate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
