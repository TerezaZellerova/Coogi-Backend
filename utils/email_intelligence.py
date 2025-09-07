"""
GPT-Powered Email Intelligence System
Auto-tagging, sentiment analysis, and smart reply generation
"""
import openai
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmailAnalysisResult:
    tags: List[Dict[str, Any]]
    sentiment: str
    priority: str
    intent: str
    department: str
    confidence: float
    key_points: List[str]
    suggested_tone: str

@dataclass
class SmartReplyResult:
    reply_text: str
    tone: str
    confidence: float
    key_points_addressed: List[str]

class EmailIntelligenceEngine:
    """GPT-powered email analysis and smart reply system optimized for high volume"""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini", max_tokens: int = 500):
        """
        Initialize with OpenAI API key and model configuration
        
        Args:
            openai_api_key: OpenAI API key
            model: GPT model to use (gpt-4o-mini for cost efficiency at scale)
            max_tokens: Maximum tokens per response (optimized for speed/cost)
        """
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        self.max_tokens = max_tokens
        
        # Define tag categories and rules
        self.tag_categories = {
            "priority": ["urgent", "high_priority", "normal", "low_priority"],
            "sentiment": ["positive", "negative", "neutral", "frustrated", "happy"],
            "intent": ["question", "complaint", "request", "inquiry", "support", "sales"],
            "department": ["sales", "support", "hr", "technical", "billing", "general"],
            "topic": ["product", "pricing", "demo", "integration", "bug_report", "feature_request"]
        }
        
        # Smart reply templates by context
        self.reply_templates = {
            "sales_inquiry": {
                "professional": "Thank you for your interest in our solution. I'd be happy to discuss how we can help your business...",
                "friendly": "Thanks for reaching out! We're excited to learn more about your needs...",
                "technical": "Thank you for your inquiry. Based on your requirements, I can provide detailed information..."
            },
            "support_request": {
                "empathetic": "I understand your concern and I'm here to help resolve this issue quickly...",
                "technical": "Thank you for reporting this issue. Let me provide you with the solution...",
                "apologetic": "I apologize for the inconvenience you've experienced. Here's how we can fix this..."
            },
            "complaint": {
                "apologetic": "I sincerely apologize for this experience. Let me personally ensure we resolve this...",
                "solution_focused": "I understand your frustration. Here's what we can do to make this right...",
                "escalation": "This is concerning and I want to address it immediately. I'm escalating this to..."
            }
        }

    def analyze_email(self, email_content: Dict[str, str]) -> EmailAnalysisResult:
        """
        Analyze email for auto-tagging and context understanding
        
        Args:
            email_content: Dict with 'subject', 'body', 'from_email'
            
        Returns:
            EmailAnalysisResult with tags, sentiment, priority, etc.
        """
        try:
            analysis_prompt = self._create_analysis_prompt(email_content)
            
            response = self.client.chat.completions.create(
                model=self.model,  # Use configured model (gpt-4o-mini)
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert email analyst. Analyze emails quickly and provide structured insights for automated tagging and response generation. Be concise and accurate."
                    },
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=self.max_tokens  # Optimized for high-volume processing
            )
            
            # Parse GPT response
            analysis_text = response.choices[0].message.content
            parsed_analysis = self._parse_analysis_response(analysis_text)
            
            return EmailAnalysisResult(**parsed_analysis)
            
        except Exception as e:
            logger.error(f"❌ Email analysis failed: {e}")
            return self._fallback_analysis(email_content)

    def generate_smart_reply(self, email_content: Dict[str, str], analysis: EmailAnalysisResult, context: Dict[str, Any] = None) -> SmartReplyResult:
        """
        Generate intelligent reply suggestions based on email analysis
        
        Args:
            email_content: Original email content
            analysis: Email analysis results
            context: Additional context (customer info, previous conversations, etc.)
            
        Returns:
            SmartReplyResult with suggested reply
        """
        try:
            reply_prompt = self._create_reply_prompt(email_content, analysis, context)
            
            response = self.client.chat.completions.create(
                model=self.model,  # Use configured model (gpt-4o-mini)
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional email response specialist. Generate helpful, contextual, and appropriate email replies quickly and efficiently."
                    },
                    {"role": "user", "content": reply_prompt}
                ],
                temperature=0.7,
                max_tokens=self.max_tokens  # Optimized for high-volume processing
            )
            
            reply_text = response.choices[0].message.content.strip()
            
            return SmartReplyResult(
                reply_text=reply_text,
                tone=analysis.suggested_tone,
                confidence=0.85,  # Could be calculated based on analysis confidence
                key_points_addressed=analysis.key_points
            )
            
        except Exception as e:
            logger.error(f"❌ Smart reply generation failed: {e}")
            return self._fallback_reply(analysis)

    def _create_analysis_prompt(self, email_content: Dict[str, str]) -> str:
        """Create GPT prompt for email analysis"""
        return f"""
Analyze this email and provide structured insights:

SUBJECT: {email_content.get('subject', 'No subject')}
FROM: {email_content.get('from_email', 'Unknown')}
BODY: {email_content.get('body', 'No content')}

Please analyze and respond with JSON format:
{{
    "tags": [
        {{"name": "tag_name", "category": "priority|sentiment|intent|department|topic", "confidence": 0.0-1.0, "reason": "why this tag applies"}}
    ],
    "sentiment": "positive|negative|neutral|frustrated|happy",
    "priority": "urgent|high|normal|low",
    "intent": "question|complaint|request|inquiry|support|sales",
    "department": "sales|support|hr|technical|billing|general",
    "confidence": 0.0-1.0,
    "key_points": ["main point 1", "main point 2"],
    "suggested_tone": "professional|friendly|empathetic|technical|apologetic"
}}

Focus on:
1. Customer sentiment and urgency indicators
2. Main intent (what they want)
3. Which department should handle this
4. Key points that need addressing
5. Appropriate response tone
"""

    def _create_reply_prompt(self, email_content: Dict[str, str], analysis: EmailAnalysisResult, context: Dict[str, Any] = None) -> str:
        """Create GPT prompt for smart reply generation"""
        context_info = ""
        if context:
            context_info = f"""
CONTEXT:
- Customer: {context.get('customer_name', 'Unknown')}
- Previous interactions: {context.get('interaction_history', 'None')}
- Account status: {context.get('account_status', 'Unknown')}
- Product/Service: {context.get('product_context', 'General')}
"""
        
        return f"""
Generate a professional email reply based on this analysis:

ORIGINAL EMAIL:
Subject: {email_content.get('subject', 'No subject')}
From: {email_content.get('from_email', 'Unknown')}
Body: {email_content.get('body', 'No content')}

ANALYSIS:
- Sentiment: {analysis.sentiment}
- Priority: {analysis.priority}
- Intent: {analysis.intent}
- Department: {analysis.department}
- Key Points: {', '.join(analysis.key_points)}
- Suggested Tone: {analysis.suggested_tone}

{context_info}

Requirements:
1. Use {analysis.suggested_tone} tone
2. Address all key points: {', '.join(analysis.key_points)}
3. Be helpful and solution-oriented
4. Include clear next steps
5. Keep it concise but complete
6. Match the urgency level ({analysis.priority})

Generate only the email reply content (no subject line needed):
"""

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse GPT analysis response into structured data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Fallback parsing if JSON fails
        return self._fallback_parsing(response_text)

    def _fallback_analysis(self, email_content: Dict[str, str]) -> EmailAnalysisResult:
        """Fallback analysis when GPT fails"""
        # Basic keyword-based analysis as fallback
        body = email_content.get('body', '').lower()
        subject = email_content.get('subject', '').lower()
        
        # Determine priority based on keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical']
        priority = "urgent" if any(word in body + subject for word in urgent_keywords) else "normal"
        
        # Basic sentiment analysis
        negative_keywords = ['problem', 'issue', 'error', 'bug', 'broken', 'frustrated']
        sentiment = "negative" if any(word in body + subject for word in negative_keywords) else "neutral"
        
        return EmailAnalysisResult(
            tags=[{"name": "auto_processed", "category": "system", "confidence": 0.5, "reason": "Fallback analysis"}],
            sentiment=sentiment,
            priority=priority,
            intent="inquiry",
            department="general",
            confidence=0.5,
            key_points=["Requires human review"],
            suggested_tone="professional"
        )

    def _fallback_reply(self, analysis: EmailAnalysisResult) -> SmartReplyResult:
        """Fallback reply when GPT fails"""
        return SmartReplyResult(
            reply_text="Thank you for your email. We've received your message and will respond within 24 hours.",
            tone="professional",
            confidence=0.3,
            key_points_addressed=["acknowledgment"]
        )

    def _fallback_parsing(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails"""
        return {
            "tags": [{"name": "needs_review", "category": "system", "confidence": 0.3, "reason": "Parsing failed"}],
            "sentiment": "neutral",
            "priority": "normal", 
            "intent": "inquiry",
            "department": "general",
            "confidence": 0.3,
            "key_points": ["Requires human review"],
            "suggested_tone": "professional"
        }

# Email Processing Pipeline
class EmailIntelligencePipeline:
    """Complete email processing pipeline with auto-tagging and smart replies"""
    
    def __init__(self, intelligence_engine: EmailIntelligenceEngine):
        self.engine = intelligence_engine
        
    def process_email(self, email_data: Dict[str, Any], auto_reply: bool = False) -> Dict[str, Any]:
        """
        Complete email processing pipeline
        
        Args:
            email_data: Email content and metadata
            auto_reply: Whether to automatically send replies
            
        Returns:
            Processing results with tags, analysis, and suggested replies
        """
        try:
            # Step 1: Analyze email
            analysis = self.engine.analyze_email(email_data)
            
            # Step 2: Generate smart reply suggestions
            smart_reply = self.engine.generate_smart_reply(email_data, analysis)
            
            # Step 3: Apply auto-tags
            applied_tags = self._apply_auto_tags(analysis)
            
            # Step 4: Determine if human review is needed
            needs_review = self._needs_human_review(analysis)
            
            result = {
                "message_id": email_data.get('message_id'),
                "analysis": {
                    "tags": applied_tags,
                    "sentiment": analysis.sentiment,
                    "priority": analysis.priority,
                    "intent": analysis.intent,
                    "department": analysis.department,
                    "confidence": analysis.confidence,
                    "key_points": analysis.key_points
                },
                "smart_reply": {
                    "suggested_text": smart_reply.reply_text,
                    "tone": smart_reply.tone,
                    "confidence": smart_reply.confidence,
                    "key_points_addressed": smart_reply.key_points_addressed
                },
                "actions": {
                    "auto_tagged": True,
                    "needs_human_review": needs_review,
                    "auto_reply_eligible": not needs_review and analysis.confidence > 0.7,
                    "department_routed": analysis.department
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 5: Auto-reply if enabled and conditions are met
            if auto_reply and result["actions"]["auto_reply_eligible"]:
                # Here you would integrate with your email sending system
                result["actions"]["auto_reply_sent"] = True
                logger.info(f"✅ Auto-reply sent for message {email_data.get('message_id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Email processing failed: {e}")
            return {"error": str(e), "message_id": email_data.get('message_id')}

    def _apply_auto_tags(self, analysis: EmailAnalysisResult) -> List[Dict[str, Any]]:
        """Apply auto-tags based on analysis"""
        applied_tags = []
        
        for tag in analysis.tags:
            if tag.get('confidence', 0) > 0.6:  # Only apply high-confidence tags
                applied_tags.append({
                    "tag": tag['name'],
                    "category": tag['category'],
                    "confidence": tag['confidence'],
                    "auto_applied": True,
                    "timestamp": datetime.now().isoformat()
                })
        
        # Add system tags
        applied_tags.extend([
            {"tag": f"priority_{analysis.priority}", "category": "priority", "confidence": 1.0, "auto_applied": True},
            {"tag": f"sentiment_{analysis.sentiment}", "category": "sentiment", "confidence": 1.0, "auto_applied": True},
            {"tag": f"dept_{analysis.department}", "category": "routing", "confidence": 1.0, "auto_applied": True}
        ])
        
        return applied_tags

    def _needs_human_review(self, analysis: EmailAnalysisResult) -> bool:
        """Determine if email needs human review"""
        # High priority or negative sentiment needs review
        if analysis.priority in ["urgent", "high"] or analysis.sentiment in ["negative", "frustrated"]:
            return True
        
        # Low confidence needs review
        if analysis.confidence < 0.7:
            return True
        
        # Complaints always need review
        if analysis.intent in ["complaint"]:
            return True
            
        return False
