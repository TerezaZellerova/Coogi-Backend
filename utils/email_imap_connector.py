#!/usr/bin/env python3
"""
Universal Email IMAP/POP3 Connector
Connect to ANY email provider for inbox monitoring and auto-tagging
"""
import imaplib
import poplib
import email
import ssl
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from .email_intelligence import EmailIntelligenceEngine, EmailIntelligencePipeline

logger = logging.getLogger(__name__)

class UniversalEmailConnector:
    """
    Universal email connector supporting IMAP/POP3 for ANY email provider
    Automatically fetches emails, applies GPT auto-tagging, and generates smart replies
    """
    
    # Popular email provider configurations
    PROVIDER_CONFIGS = {
        "gmail": {
            "imap_server": "imap.gmail.com",
            "imap_port": 993,
            "smtp_server": "smtp.gmail.com", 
            "smtp_port": 587,
            "use_tls": True
        },
        "outlook": {
            "imap_server": "outlook.office365.com",
            "imap_port": 993,
            "smtp_server": "smtp-mail.outlook.com",
            "smtp_port": 587, 
            "use_tls": True
        },
        "yahoo": {
            "imap_server": "imap.mail.yahoo.com",
            "imap_port": 993,
            "smtp_server": "smtp.mail.yahoo.com",
            "smtp_port": 587,
            "use_tls": True
        },
        "protonmail": {
            "imap_server": "127.0.0.1",  # Requires ProtonMail Bridge
            "imap_port": 1143,
            "smtp_server": "127.0.0.1",
            "smtp_port": 1025,
            "use_tls": False
        },
        "custom": {
            # For any custom email server
            "imap_server": "mail.yourdomain.com",
            "imap_port": 993,
            "smtp_server": "mail.yourdomain.com", 
            "smtp_port": 587,
            "use_tls": True
        }
    }
    
    def __init__(self, email_config: Dict[str, Any], intelligence_engine: EmailIntelligenceEngine):
        """
        Initialize email connector
        
        Args:
            email_config: {
                'provider': 'gmail' | 'outlook' | 'yahoo' | 'custom',
                'email': 'user@example.com',
                'password': 'your_password_or_app_password',
                'custom_server': 'mail.domain.com' (if provider=custom),
                'custom_port': 993 (if provider=custom)
            }
            intelligence_engine: GPT intelligence engine for auto-tagging
        """
        self.config = email_config
        self.intelligence_pipeline = EmailIntelligencePipeline(intelligence_engine)
        self.provider_settings = self._get_provider_settings()
        
    def _get_provider_settings(self) -> Dict[str, Any]:
        """Get email server settings based on provider"""
        provider = self.config.get('provider', 'custom')
        
        if provider in self.PROVIDER_CONFIGS:
            settings = self.PROVIDER_CONFIGS[provider].copy()
        else:
            settings = self.PROVIDER_CONFIGS['custom'].copy()
            
        # Override with custom settings if provided
        if 'custom_server' in self.config:
            settings['imap_server'] = self.config['custom_server']
            settings['smtp_server'] = self.config['custom_server']
        if 'custom_port' in self.config:
            settings['imap_port'] = self.config['custom_port']
            
        return settings
    
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server"""
        try:
            if self.provider_settings['use_tls']:
                imap = imaplib.IMAP4_SSL(
                    self.provider_settings['imap_server'],
                    self.provider_settings['imap_port']
                )
            else:
                imap = imaplib.IMAP4(
                    self.provider_settings['imap_server'], 
                    self.provider_settings['imap_port']
                )
            
            # Login
            imap.login(self.config['email'], self.config['password'])
            logger.info(f"✅ Connected to {self.config['provider']} IMAP: {self.config['email']}")
            return imap
            
        except Exception as e:
            logger.error(f"❌ IMAP connection failed: {e}")
            raise
    
    def fetch_recent_emails(self, hours: int = 24, max_emails: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch recent emails from inbox
        
        Args:
            hours: How many hours back to fetch emails
            max_emails: Maximum number of emails to fetch
            
        Returns:
            List of email dictionaries with parsed content
        """
        emails = []
        imap = None
        
        try:
            imap = self.connect_imap()
            imap.select('INBOX')
            
            # Search for emails from last N hours
            since_date = (datetime.now() - timedelta(hours=hours)).strftime('%d-%b-%Y')
            search_criteria = f'(SINCE "{since_date}")'
            
            status, messages = imap.search(None, search_criteria)
            
            if status == 'OK':
                email_ids = messages[0].split()
                
                # Limit to max_emails (get most recent)
                email_ids = email_ids[-max_emails:] if len(email_ids) > max_emails else email_ids
                
                for email_id in email_ids:
                    try:
                        # Fetch email
                        status, msg_data = imap.fetch(email_id, '(RFC822)')
                        
                        if status == 'OK':
                            email_msg = email.message_from_bytes(msg_data[0][1])
                            parsed_email = self._parse_email(email_msg, email_id.decode())
                            emails.append(parsed_email)
                            
                    except Exception as e:
                        logger.error(f"Error parsing email {email_id}: {e}")
                        continue
                        
            logger.info(f"📧 Fetched {len(emails)} emails from {self.config['provider']}")
            return emails
            
        except Exception as e:
            logger.error(f"❌ Error fetching emails: {e}")
            return []
            
        finally:
            if imap:
                try:
                    imap.close()
                    imap.logout()
                except:
                    pass
    
    def _parse_email(self, email_msg: email.message.Message, email_id: str) -> Dict[str, Any]:
        """Parse email message into structured format"""
        
        # Extract headers
        subject = email_msg.get('Subject', 'No Subject')
        from_email = email_msg.get('From', '')
        to_email = email_msg.get('To', '')
        date = email_msg.get('Date', '')
        message_id = email_msg.get('Message-ID', f"imap_{email_id}")
        
        # Extract body
        body = ""
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except:
                        continue
        else:
            try:
                body = email_msg.get_payload(decode=True).decode('utf-8')
            except:
                body = str(email_msg.get_payload())
        
        return {
            "id": email_id,
            "message_id": message_id,
            "subject": subject,
            "from_email": from_email,
            "to_email": to_email,
            "body": body,
            "timestamp": date,
            "email_provider": self.config['provider'],
            "raw_email": email_msg
        }
    
    def process_inbox_with_ai(self, hours: int = 24, auto_reply: bool = False) -> Dict[str, Any]:
        """
        Fetch emails and process them with GPT auto-tagging and smart replies
        
        Args:
            hours: How many hours back to process
            auto_reply: Whether to automatically send smart replies
            
        Returns:
            Processing results with tags, analysis, and actions taken
        """
        try:
            logger.info(f"🚀 Starting AI inbox processing for {self.config['provider']}")
            
            # Step 1: Fetch recent emails
            emails = self.fetch_recent_emails(hours=hours)
            
            if not emails:
                return {
                    "success": True,
                    "message": "No new emails found",
                    "emails_processed": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Process each email with GPT intelligence
            processed_emails = []
            auto_tagged = 0
            smart_replies_generated = 0
            auto_replies_sent = 0
            
            for email_data in emails:
                try:
                    # Process with GPT
                    result = self.intelligence_pipeline.process_email(
                        email_data=email_data,
                        auto_reply=auto_reply
                    )
                    
                    processed_emails.append({
                        "email": email_data,
                        "analysis": result["analysis"],
                        "smart_reply": result["smart_reply"],
                        "actions": result["actions"]
                    })
                    
                    # Count actions
                    if result["actions"]["auto_tagged"]:
                        auto_tagged += 1
                    if result["smart_reply"]["suggested_text"]:
                        smart_replies_generated += 1
                    if auto_reply and result["actions"]["auto_reply_eligible"]:
                        # Send auto-reply if enabled
                        reply_sent = self._send_smart_reply(email_data, result["smart_reply"])
                        if reply_sent:
                            auto_replies_sent += 1
                    
                    logger.info(f"✅ Processed: {email_data['subject'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing email: {e}")
                    continue
            
            # Step 3: Return summary
            return {
                "success": True,
                "provider": self.config['provider'],
                "emails_fetched": len(emails),
                "emails_processed": len(processed_emails),
                "auto_tagged": auto_tagged,
                "smart_replies_generated": smart_replies_generated,
                "auto_replies_sent": auto_replies_sent,
                "processed_emails": processed_emails,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Inbox processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _send_smart_reply(self, original_email: Dict[str, Any], smart_reply: Dict[str, Any]) -> bool:
        """Send smart reply via SMTP"""
        try:
            # Create reply message
            reply_msg = MIMEMultipart()
            reply_msg['From'] = self.config['email']
            reply_msg['To'] = original_email['from_email']
            reply_msg['Subject'] = f"Re: {original_email['subject']}"
            
            # Add reply body
            reply_msg.attach(MIMEText(smart_reply['suggested_text'], 'plain'))
            
            # Connect to SMTP
            if self.provider_settings['use_tls']:
                smtp = smtplib.SMTP(
                    self.provider_settings['smtp_server'],
                    self.provider_settings['smtp_port']
                )
                smtp.starttls()
            else:
                smtp = smtplib.SMTP(
                    self.provider_settings['smtp_server'],
                    self.provider_settings['smtp_port']
                )
            
            smtp.login(self.config['email'], self.config['password'])
            
            # Send reply
            smtp.send_message(reply_msg)
            smtp.quit()
            
            logger.info(f"📤 Auto-reply sent for: {original_email['subject'][:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send auto-reply: {e}")
            return False

# Example usage configurations for different providers
EXAMPLE_CONFIGS = {
    "gmail_example": {
        "provider": "gmail",
        "email": "your_email@gmail.com",
        "password": "your_app_password",  # Use App Password, not regular password
        "notes": "Enable 2FA and create App Password in Google Account settings"
    },
    
    "outlook_example": {
        "provider": "outlook", 
        "email": "your_email@outlook.com",
        "password": "your_password",
        "notes": "Works with personal Outlook accounts"
    },
    
    "office365_example": {
        "provider": "outlook",
        "email": "your_email@company.com", 
        "password": "your_password",
        "notes": "Works with Office 365 business accounts"
    },
    
    "custom_provider_example": {
        "provider": "custom",
        "email": "your_email@yourdomain.com",
        "password": "your_password", 
        "custom_server": "mail.yourdomain.com",
        "custom_port": 993,
        "notes": "Works with ANY email hosting provider"
    }
}

def create_connector_for_provider(provider_name: str, email: str, password: str, intelligence_engine: EmailIntelligenceEngine) -> UniversalEmailConnector:
    """Helper function to create connector for common providers"""
    
    config = {
        "provider": provider_name,
        "email": email,
        "password": password
    }
    
    return UniversalEmailConnector(config, intelligence_engine)
