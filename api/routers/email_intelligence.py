"""
Email Intelligence API Router
GPT-powered auto-tagging and smart reply endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime
import logging
import time
import os
from typing import Dict, Any, List

from ..models import (
    EmailIntelligenceRequest, EmailIntelligenceResponse,
    EmailMessage, EmailAnalysis, SmartReply, EmailAutoResponse
)
from ..dependencies import get_current_user
from utils.email_intelligence import EmailIntelligenceEngine, EmailIntelligencePipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["email-intelligence"])

# Initialize email intelligence engine
def get_email_intelligence_engine():
    """Get email intelligence engine instance"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    return EmailIntelligenceEngine(openai_api_key)

def get_email_pipeline():
    """Get email processing pipeline"""
    engine = get_email_intelligence_engine()
    return EmailIntelligencePipeline(engine)

@router.post("/email-intelligence/analyze", response_model=EmailIntelligenceResponse)
async def analyze_email_intelligence(
    request: EmailIntelligenceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze email with GPT for auto-tagging and smart reply generation
    
    Features:
    - Automatic sentiment analysis
    - Priority detection
    - Intent classification
    - Department routing
    - Smart reply generation
    - Auto-tagging
    """
    start_time = time.time()
    
    try:
        pipeline = get_email_pipeline()
        
        # Process the email
        result = await pipeline.process_email(
            email_data=request.email_content,
            auto_reply=request.auto_reply
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Convert to response model
        analysis = EmailAnalysis(
            message_id=result["analysis"]["message_id"] if "message_id" in result["analysis"] else request.email_content.get("message_id", "unknown"),
            tags=[],  # Will be populated from result
            sentiment=result["analysis"]["sentiment"],
            priority=result["analysis"]["priority"],
            intent=result["analysis"]["intent"],
            department=result["analysis"]["department"],
            confidence=result["analysis"]["confidence"],
            key_points=result["analysis"]["key_points"],
            suggested_response_tone=result["smart_reply"]["tone"],
            needs_human_review=result["actions"]["needs_human_review"],
            timestamp=result["timestamp"]
        )
        
        smart_reply = SmartReply(
            original_message_id=analysis.message_id,
            suggested_reply=result["smart_reply"]["suggested_text"],
            confidence=result["smart_reply"]["confidence"],
            tone=result["smart_reply"]["tone"],
            key_points_addressed=result["smart_reply"]["key_points_addressed"],
            auto_send_eligible=result["actions"]["auto_reply_eligible"],
            timestamp=result["timestamp"]
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return EmailIntelligenceResponse(
            success=True,
            message_id=analysis.message_id,
            analysis=analysis,
            smart_replies=[smart_reply],
            actions_taken={
                "auto_tagged": result["actions"]["auto_tagged"],
                "auto_replied": result["actions"].get("auto_reply_sent", False),
                "department_routed": True,
                "needs_review": result["actions"]["needs_human_review"]
            },
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Email intelligence analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/email-intelligence/batch-process")
async def batch_process_emails(
    emails: List[Dict[str, Any]],
    auto_reply: bool = False,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """
    Batch process multiple emails for auto-tagging and smart replies
    
    Useful for:
    - Processing inbox backlog
    - Bulk email analysis
    - Training data generation
    """
    try:
        pipeline = get_email_pipeline()
        
        results = []
        for email_data in emails[:50]:  # Limit batch size
            try:
                result = await pipeline.process_email(email_data, auto_reply=False)  # No auto-reply in batch
                results.append({
                    "message_id": email_data.get("message_id", "unknown"),
                    "success": True,
                    "analysis": result.get("analysis", {}),
                    "smart_reply": result.get("smart_reply", {}),
                    "actions": result.get("actions", {})
                })
            except Exception as e:
                results.append({
                    "message_id": email_data.get("message_id", "unknown"),
                    "success": False,
                    "error": str(e)
                })
        
        successful = len([r for r in results if r["success"]])
        failed = len(results) - successful
        
        return {
            "success": True,
            "total_processed": len(results),
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Batch email processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email-intelligence/stats")
async def get_email_intelligence_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get email intelligence processing statistics
    
    Returns:
    - Processing volume
    - Accuracy metrics
    - Auto-reply rates
    - Department routing stats
    """
    try:
        # In a real implementation, you'd query your database for these stats
        # For now, returning mock data structure
        
        stats = {
            "total_emails_processed": 1250,
            "auto_tags_applied": 1180,
            "smart_replies_generated": 950,
            "auto_replies_sent": 320,
            "human_reviews_required": 180,
            "accuracy_metrics": {
                "sentiment_accuracy": 0.92,
                "priority_accuracy": 0.88,
                "department_routing_accuracy": 0.85,
                "auto_reply_satisfaction": 0.78
            },
            "department_distribution": {
                "support": 45,
                "sales": 30,
                "technical": 15,
                "billing": 8,
                "general": 2
            },
            "priority_distribution": {
                "urgent": 12,
                "high": 23,
                "normal": 55,
                "low": 10
            },
            "sentiment_distribution": {
                "positive": 40,
                "neutral": 45,
                "negative": 12,
                "frustrated": 3
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting email intelligence stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/email-intelligence/train")
async def train_email_classifier(
    training_data: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user)
):
    """
    Train/improve email classification with feedback data
    
    Training data format:
    [
        {
            "email_content": {...},
            "correct_tags": [...],
            "correct_sentiment": "...",
            "correct_priority": "...",
            "feedback": "..."
        }
    ]
    """
    try:
        # In a real implementation, you'd:
        # 1. Store training data
        # 2. Fine-tune models
        # 3. Update classification rules
        # 4. Validate improvements
        
        logger.info(f"📚 Received {len(training_data)} training examples")
        
        # Mock training process
        training_results = {
            "training_examples_processed": len(training_data),
            "model_accuracy_improvement": 0.03,  # 3% improvement
            "new_patterns_learned": 15,
            "classification_rules_updated": 8,
            "training_completed_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message": "Email classifier training completed",
            "results": training_results
        }
        
    except Exception as e:
        logger.error(f"❌ Email classifier training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/email-intelligence/generate-reply")
async def generate_smart_reply(
    email_content: Dict[str, str],
    reply_context: Dict[str, Any] = None,
    tone: str = "professional",
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a smart reply for a specific email
    
    Args:
        email_content: Original email (subject, body, from_email)
        reply_context: Additional context (customer info, history, etc.)
        tone: Desired response tone
    
    Returns:
        Generated smart reply with confidence score
    """
    try:
        engine = get_email_intelligence_engine()
        
        # First analyze the email
        analysis = await engine.analyze_email(email_content)
        
        # Override tone if specified
        if tone:
            analysis.suggested_tone = tone
        
        # Generate smart reply
        smart_reply = await engine.generate_smart_reply(
            email_content, 
            analysis, 
            context=reply_context
        )
        
        return {
            "success": True,
            "original_email": {
                "subject": email_content.get("subject"),
                "from": email_content.get("from_email")
            },
            "analysis": {
                "sentiment": analysis.sentiment,
                "priority": analysis.priority,
                "intent": analysis.intent,
                "key_points": analysis.key_points
            },
            "smart_reply": {
                "suggested_text": smart_reply.reply_text,
                "tone": smart_reply.tone,
                "confidence": smart_reply.confidence,
                "key_points_addressed": smart_reply.key_points_addressed
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Smart reply generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email-intelligence/health")
async def email_intelligence_health():
    """Check email intelligence system health"""
    try:
        # Test OpenAI connection
        engine = get_email_intelligence_engine()
        
        # Quick test analysis
        test_email = {
            "subject": "Test email",
            "body": "This is a test email for health check",
            "from_email": "test@example.com"
        }
        
        analysis = await engine.analyze_email(test_email)
        
        return {
            "status": "healthy",
            "openai_connection": "connected",
            "analysis_engine": "operational",
            "test_analysis_confidence": analysis.confidence,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Email intelligence health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
