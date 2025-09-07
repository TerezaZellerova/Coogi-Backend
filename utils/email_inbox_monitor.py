"""
Email Provider Integration Service
Connects to various email providers (Gmail, Outlook, SES) for inbox monitoring
"""
import imaplib
import email
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import base64
import re
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import smtplib

logger = logging.getLogger(__name__)

class EmailProviderConnection:
    """Base class for email provider connections"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
    
    async def connect(self):
        """Connect to email provider"""
        raise NotImplementedError
    
    async def get_emails(self, folder: str = "INBOX", limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch emails from provider"""
        raise NotImplementedError
    
    async def send_reply(self, original_email: Dict[str, Any], reply_content: str) -> bool:
        """Send reply email"""
        raise NotImplementedError

class GmailConnection(EmailProviderConnection):
    """Gmail IMAP/SMTP connection"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.imap_server = "imap.gmail.com"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    async def connect(self):
        """Connect to Gmail via IMAP"""
        try:
            self.connection = imaplib.IMAP4_SSL(self.imap_server)
            self.connection.login(
                self.config["email"], 
                self.config["app_password"]  # Gmail App Password
            )
            logger.info("✅ Connected to Gmail successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Gmail connection failed: {e}")
            return False
    
    async def get_emails(self, folder: str = "INBOX", limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch emails from Gmail"""
        try:
            if not self.connection:
                await self.connect()
            
            self.connection.select(folder)
            
            # Search for emails from last 24 hours
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            status, messages = self.connection.search(None, f'SINCE "{yesterday}"')
            
            email_ids = messages[0].split()[-limit:]  # Get latest emails
            emails = []
            
            for email_id in email_ids:
                status, msg_data = self.connection.fetch(email_id, "(RFC822)")
                email_message = email.message_from_bytes(msg_data[0][1])
                
                # Parse email content
                parsed_email = self._parse_email_message(email_message, email_id.decode())
                emails.append(parsed_email)
            
            logger.info(f"✅ Fetched {len(emails)} emails from Gmail")
            return emails
            
        except Exception as e:
            logger.error(f"❌ Error fetching Gmail emails: {e}")
            return []
    
    async def send_reply(self, original_email: Dict[str, Any], reply_content: str) -> bool:
        """Send reply via Gmail SMTP"""
        try:
            # Create reply message
            reply = MimeMultipart()
            reply["From"] = self.config["email"]
            reply["To"] = original_email["from_email"]
            reply["Subject"] = f"Re: {original_email['subject']}"
            reply["In-Reply-To"] = original_email.get("message_id", "")
            reply["References"] = original_email.get("message_id", "")
            
            # Add reply content
            reply.attach(MimeText(reply_content, "plain"))
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.config["email"], self.config["app_password"])
                text = reply.as_string()
                server.sendmail(self.config["email"], original_email["from_email"], text)
            
            logger.info(f"✅ Reply sent successfully to {original_email['from_email']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending Gmail reply: {e}")
            return False
    
    def _parse_email_message(self, email_message, email_id: str) -> Dict[str, Any]:
        """Parse email message object into dictionary"""
        try:
            # Extract headers
            subject = email_message.get("Subject", "No Subject")
            from_email = email_message.get("From", "Unknown")
            to_email = email_message.get("To", "Unknown")
            date = email_message.get("Date", "")
            message_id = email_message.get("Message-ID", f"gmail_{email_id}")
            
            # Extract body
            body = self._extract_email_body(email_message)
            
            return {
                "id": email_id,
                "message_id": message_id,
                "subject": subject,
                "from_email": self._clean_email_address(from_email),
                "to_email": self._clean_email_address(to_email),
                "body": body,
                "timestamp": date,
                "provider": "gmail",
                "thread_id": email_message.get("Thread-ID"),
                "is_reply": "Re:" in subject
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing email message: {e}")
            return {}
    
    def _extract_email_body(self, email_message) -> str:
        """Extract text body from email message"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return body.strip()
    
    def _clean_email_address(self, email_str: str) -> str:
        """Extract clean email address from header"""
        email_pattern = r'<([^>]+)>|([^\s<>]+@[^\s<>]+)'
        match = re.search(email_pattern, email_str)
        if match:
            return match.group(1) or match.group(2)
        return email_str

class OutlookConnection(EmailProviderConnection):
    """Outlook/Office365 IMAP/SMTP connection"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.imap_server = "outlook.office365.com"
        self.smtp_server = "smtp-mail.outlook.com"
        self.smtp_port = 587
    
    async def connect(self):
        """Connect to Outlook via IMAP"""
        try:
            self.connection = imaplib.IMAP4_SSL(self.imap_server)
            self.connection.login(
                self.config["email"], 
                self.config["password"]
            )
            logger.info("✅ Connected to Outlook successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Outlook connection failed: {e}")
            return False
    
    async def get_emails(self, folder: str = "INBOX", limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch emails from Outlook (similar to Gmail implementation)"""
        # Implementation similar to Gmail but with Outlook-specific handling
        return await self._fetch_outlook_emails(folder, limit)
    
    async def _fetch_outlook_emails(self, folder: str, limit: int) -> List[Dict[str, Any]]:
        """Outlook-specific email fetching logic"""
        # Similar to Gmail implementation but with Outlook specifics
        return []

class SESInboxConnection(EmailProviderConnection):
    """AWS SES with S3 inbox storage connection"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # SES doesn't have inbox, so we'd use S3 or SNS for incoming emails
    
    async def connect(self):
        """Connect to SES/S3 for inbox monitoring"""
        # Implementation would depend on your SES inbox setup
        return True
    
    async def get_emails(self, folder: str = "INBOX", limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch emails from SES/S3 storage"""
        # Implementation for SES inbox (if configured with S3)
        return []

class EmailInboxMonitor:
    """Email inbox monitoring and processing service"""
    
    def __init__(self):
        self.connections = {}
        self.intelligence_pipeline = None
    
    def add_email_account(self, account_id: str, provider: str, config: Dict[str, Any]):
        """Add email account for monitoring"""
        if provider.lower() == "gmail":
            self.connections[account_id] = GmailConnection(config)
        elif provider.lower() == "outlook":
            self.connections[account_id] = OutlookConnection(config)
        elif provider.lower() == "ses":
            self.connections[account_id] = SESInboxConnection(config)
        else:
            raise ValueError(f"Unsupported email provider: {provider}")
    
    async def monitor_inbox(self, account_id: str, auto_process: bool = True) -> List[Dict[str, Any]]:
        """Monitor inbox and optionally auto-process with GPT"""
        try:
            if account_id not in self.connections:
                raise ValueError(f"Email account {account_id} not configured")
            
            connection = self.connections[account_id]
            
            # Fetch new emails
            emails = await connection.get_emails()
            
            if auto_process and self.intelligence_pipeline:
                # Process emails with GPT intelligence
                processed_results = []
                
                for email_data in emails:
                    try:
                        result = await self.intelligence_pipeline.process_email(email_data)
                        processed_results.append(result)
                        
                        # Auto-reply if conditions are met
                        if result.get("actions", {}).get("auto_reply_eligible", False):
                            reply_content = result["smart_reply"]["suggested_text"]
                            await connection.send_reply(email_data, reply_content)
                            logger.info(f"✅ Auto-reply sent for email {email_data['id']}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing email {email_data.get('id', 'unknown')}: {e}")
                
                return processed_results
            
            return emails
            
        except Exception as e:
            logger.error(f"❌ Inbox monitoring failed for {account_id}: {e}")
            return []
    
    async def process_email_with_intelligence(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process single email with GPT intelligence"""
        if not self.intelligence_pipeline:
            from utils.email_intelligence import EmailIntelligencePipeline, EmailIntelligenceEngine
            import os
            
            engine = EmailIntelligenceEngine(os.getenv("OPENAI_API_KEY"))
            self.intelligence_pipeline = EmailIntelligencePipeline(engine)
        
        return await self.intelligence_pipeline.process_email(email_data)
    
    async def send_smart_reply(self, account_id: str, original_email: Dict[str, Any], reply_content: str) -> bool:
        """Send smart reply through specified account"""
        try:
            if account_id not in self.connections:
                raise ValueError(f"Email account {account_id} not configured")
            
            connection = self.connections[account_id]
            return await connection.send_reply(original_email, reply_content)
            
        except Exception as e:
            logger.error(f"❌ Error sending smart reply: {e}")
            return False

# Example usage and configuration
EMAIL_MONITOR_CONFIG = {
    "gmail_support": {
        "provider": "gmail",
        "email": "support@coogi.ai",
        "app_password": "your_gmail_app_password",
        "auto_process": True,
        "auto_reply": False  # Only for low-priority, high-confidence emails
    },
    "outlook_sales": {
        "provider": "outlook", 
        "email": "sales@coogi.ai",
        "password": "your_outlook_password",
        "auto_process": True,
        "auto_reply": True
    }
}
