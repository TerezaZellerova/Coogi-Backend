"""
Campaign Analytics and Tracking Service
Provides comprehensive analytics for email campaigns including open rates, clicks, responses
"""

import os
import json
import sqlite3
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class CampaignMetrics:
    """Campaign performance metrics"""
    campaign_id: str
    campaign_name: str
    created_at: str
    executed_at: Optional[str] = None
    total_recipients: int = 0
    emails_sent: int = 0
    emails_failed: int = 0
    emails_delivered: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    emails_bounced: int = 0
    emails_unsubscribed: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    conversion_rate: float = 0.0
    platform: str = "unknown"
    campaign_type: str = "outreach"
    target_audience: str = "professionals"

@dataclass
class RecipientActivity:
    """Individual recipient activity tracking"""
    campaign_id: str
    recipient_email: str
    recipient_name: str
    company: str
    title: str
    email_sent_at: Optional[str] = None
    email_delivered_at: Optional[str] = None
    email_opened_at: Optional[str] = None
    email_clicked_at: Optional[str] = None
    email_replied_at: Optional[str] = None
    email_bounced_at: Optional[str] = None
    unsubscribed_at: Optional[str] = None
    status: str = "sent"  # sent, delivered, opened, clicked, replied, bounced, unsubscribed
    open_count: int = 0
    click_count: int = 0
    last_activity_at: Optional[str] = None

class CampaignAnalyticsService:
    """Service for tracking and analyzing email campaign performance"""
    
    def __init__(self):
        """Initialize analytics service with SQLite database"""
        self.db_path = "campaign_analytics.db"
        self._init_database()
        logger.info("📊 Campaign Analytics Service initialized")
    
    def _init_database(self):
        """Initialize SQLite database for analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Campaign metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaign_metrics (
                    campaign_id TEXT PRIMARY KEY,
                    campaign_name TEXT,
                    created_at TEXT,
                    executed_at TEXT,
                    total_recipients INTEGER DEFAULT 0,
                    emails_sent INTEGER DEFAULT 0,
                    emails_failed INTEGER DEFAULT 0,
                    emails_delivered INTEGER DEFAULT 0,
                    emails_opened INTEGER DEFAULT 0,
                    emails_clicked INTEGER DEFAULT 0,
                    emails_replied INTEGER DEFAULT 0,
                    emails_bounced INTEGER DEFAULT 0,
                    emails_unsubscribed INTEGER DEFAULT 0,
                    open_rate REAL DEFAULT 0.0,
                    click_rate REAL DEFAULT 0.0,
                    reply_rate REAL DEFAULT 0.0,
                    bounce_rate REAL DEFAULT 0.0,
                    unsubscribe_rate REAL DEFAULT 0.0,
                    conversion_rate REAL DEFAULT 0.0,
                    platform TEXT DEFAULT 'unknown',
                    campaign_type TEXT DEFAULT 'outreach',
                    target_audience TEXT DEFAULT 'professionals'
                )
            """)
            
            # Recipient activity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recipient_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT,
                    recipient_email TEXT,
                    recipient_name TEXT,
                    company TEXT,
                    title TEXT,
                    email_sent_at TEXT,
                    email_delivered_at TEXT,
                    email_opened_at TEXT,
                    email_clicked_at TEXT,
                    email_replied_at TEXT,
                    email_bounced_at TEXT,
                    unsubscribed_at TEXT,
                    status TEXT DEFAULT 'sent',
                    open_count INTEGER DEFAULT 0,
                    click_count INTEGER DEFAULT 0,
                    last_activity_at TEXT,
                    UNIQUE(campaign_id, recipient_email)
                )
            """)
            
            # Campaign events table for detailed tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaign_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT,
                    recipient_email TEXT,
                    event_type TEXT,
                    event_data TEXT,
                    timestamp TEXT,
                    user_agent TEXT,
                    ip_address TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Analytics database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize analytics database: {e}")
    
    async def track_campaign_creation(self, campaign_data: Dict[str, Any]) -> None:
        """Track campaign creation"""
        try:
            metrics = CampaignMetrics(
                campaign_id=campaign_data.get("id"),
                campaign_name=campaign_data.get("name", ""),
                created_at=datetime.now().isoformat(),
                total_recipients=len(campaign_data.get("candidates", [])),
                platform=campaign_data.get("platform", "unknown"),
                campaign_type=campaign_data.get("type", "outreach"),
                target_audience=campaign_data.get("target_audience", "professionals")
            )
            
            await self._save_campaign_metrics(metrics)
            
            # Track initial recipient data
            for candidate in campaign_data.get("candidates", []):
                activity = RecipientActivity(
                    campaign_id=campaign_data.get("id"),
                    recipient_email=candidate.get("emails", [""])[0] if candidate.get("emails") else "",
                    recipient_name=candidate.get("name", ""),
                    company=candidate.get("company", ""),
                    title=candidate.get("title", ""),
                    status="created"
                )
                await self._save_recipient_activity(activity)
            
            logger.info(f"📊 Campaign creation tracked: {campaign_data.get('id')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to track campaign creation: {e}")
    
    async def track_campaign_execution(self, campaign_id: str, execution_result: Dict[str, Any]) -> None:
        """Track campaign execution results"""
        try:
            # Update campaign metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE campaign_metrics 
                SET executed_at = ?, emails_sent = ?, emails_failed = ?, platform = ?
                WHERE campaign_id = ?
            """, (
                datetime.now().isoformat(),
                execution_result.get("sent_count", 0),
                execution_result.get("failed_count", 0),
                execution_result.get("platform", "unknown"),
                campaign_id
            ))
            
            conn.commit()
            conn.close()
            
            # Update recipient activities
            for result in execution_result.get("results", []):
                if result.get("status") == "sent":
                    await self._update_recipient_status(
                        campaign_id, 
                        result.get("recipient"), 
                        "sent",
                        {"email_sent_at": datetime.now().isoformat()}
                    )
                elif result.get("status") == "failed":
                    await self._update_recipient_status(
                        campaign_id, 
                        result.get("recipient"), 
                        "failed",
                        {"email_sent_at": datetime.now().isoformat()}
                    )
            
            await self._calculate_rates(campaign_id)
            logger.info(f"📊 Campaign execution tracked: {campaign_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to track campaign execution: {e}")
    
    async def track_email_event(self, campaign_id: str, recipient_email: str, event_type: str, 
                               event_data: Dict[str, Any] = None, user_agent: str = None, 
                               ip_address: str = None, metadata: Dict[str, Any] = None) -> None:
        """Track individual email events (opens, clicks, replies, etc.)"""
        try:
            # Merge metadata into event_data if provided
            if metadata:
                if event_data is None:
                    event_data = {}
                event_data.update(metadata)
            
            # Save event
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO campaign_events 
                (campaign_id, recipient_email, event_type, event_data, timestamp, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id,
                recipient_email,
                event_type,
                json.dumps(event_data or {}),
                datetime.now().isoformat(),
                user_agent,
                ip_address
            ))
            
            conn.commit()
            conn.close()
            
            # Update recipient activity based on event type
            update_data = {"last_activity_at": datetime.now().isoformat()}
            
            if event_type == "delivered":
                update_data["email_delivered_at"] = datetime.now().isoformat()
                update_data["status"] = "delivered"
            elif event_type == "opened":
                update_data["email_opened_at"] = datetime.now().isoformat()
                update_data["status"] = "opened"
                update_data["open_count"] = "open_count + 1"
            elif event_type == "clicked":
                update_data["email_clicked_at"] = datetime.now().isoformat()
                update_data["status"] = "clicked"
                update_data["click_count"] = "click_count + 1"
            elif event_type == "replied":
                update_data["email_replied_at"] = datetime.now().isoformat()
                update_data["status"] = "replied"
            elif event_type == "bounced":
                update_data["email_bounced_at"] = datetime.now().isoformat()
                update_data["status"] = "bounced"
            elif event_type == "unsubscribed":
                update_data["unsubscribed_at"] = datetime.now().isoformat()
                update_data["status"] = "unsubscribed"
            
            await self._update_recipient_status(campaign_id, recipient_email, 
                                              update_data.get("status", "sent"), update_data)
            
            # Recalculate campaign metrics
            await self._calculate_rates(campaign_id)
            
            logger.info(f"📊 Email event tracked: {event_type} for {recipient_email} in {campaign_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to track email event: {e}")
    
    async def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a campaign"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get campaign metrics
            cursor.execute("SELECT * FROM campaign_metrics WHERE campaign_id = ?", (campaign_id,))
            metrics_row = cursor.fetchone()
            
            if not metrics_row:
                return {"error": "Campaign not found"}
            
            # Convert to dict
            columns = [desc[0] for desc in cursor.description]
            metrics = dict(zip(columns, metrics_row))
            
            # Get recipient activities
            cursor.execute("""
                SELECT recipient_email, recipient_name, company, title, status, 
                       open_count, click_count, last_activity_at
                FROM recipient_activity 
                WHERE campaign_id = ?
                ORDER BY last_activity_at DESC
            """, (campaign_id,))
            
            recipients = []
            for row in cursor.fetchall():
                recipients.append({
                    "email": row[0],
                    "name": row[1],
                    "company": row[2],
                    "title": row[3],
                    "status": row[4],
                    "open_count": row[5],
                    "click_count": row[6],
                    "last_activity": row[7]
                })
            
            # Get recent events
            cursor.execute("""
                SELECT event_type, recipient_email, timestamp, event_data
                FROM campaign_events 
                WHERE campaign_id = ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (campaign_id,))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "type": row[0],
                    "recipient": row[1],
                    "timestamp": row[2],
                    "data": json.loads(row[3]) if row[3] else {}
                })
            
            conn.close()
            
            return {
                "campaign_metrics": metrics,
                "recipients": recipients,
                "recent_events": events,
                "summary": {
                    "total_recipients": len(recipients),
                    "active_recipients": len([r for r in recipients if r["status"] in ["opened", "clicked", "replied"]]),
                    "conversion_rate": metrics.get("conversion_rate", 0),
                    "engagement_score": self._calculate_engagement_score(metrics)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get campaign analytics: {e}")
            return {"error": str(e)}
    
    async def get_dashboard_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get dashboard analytics for the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Campaign overview
            cursor.execute("""
                SELECT COUNT(*) as total_campaigns,
                       SUM(emails_sent) as total_emails_sent,
                       SUM(emails_opened) as total_opens,
                       SUM(emails_clicked) as total_clicks,
                       SUM(emails_replied) as total_replies,
                       AVG(open_rate) as avg_open_rate,
                       AVG(click_rate) as avg_click_rate,
                       AVG(reply_rate) as avg_reply_rate
                FROM campaign_metrics 
                WHERE created_at >= ?
            """, (cutoff_date,))
            
            overview = cursor.fetchone()
            
            # Campaign performance by type
            cursor.execute("""
                SELECT campaign_type, target_audience, COUNT(*) as count,
                       AVG(open_rate) as avg_open_rate,
                       AVG(click_rate) as avg_click_rate,
                       AVG(reply_rate) as avg_reply_rate
                FROM campaign_metrics 
                WHERE created_at >= ?
                GROUP BY campaign_type, target_audience
            """, (cutoff_date,))
            
            performance_by_type = cursor.fetchall()
            
            # Top performing campaigns
            cursor.execute("""
                SELECT campaign_id, campaign_name, open_rate, click_rate, reply_rate,
                       emails_sent, created_at
                FROM campaign_metrics 
                WHERE created_at >= ?
                ORDER BY reply_rate DESC, open_rate DESC
                LIMIT 10
            """, (cutoff_date,))
            
            top_campaigns = cursor.fetchall()
            
            conn.close()
            
            return {
                "overview": {
                    "total_campaigns": overview[0] or 0,
                    "total_emails_sent": overview[1] or 0,
                    "total_opens": overview[2] or 0,
                    "total_clicks": overview[3] or 0,
                    "total_replies": overview[4] or 0,
                    "avg_open_rate": round(overview[5] or 0, 2),
                    "avg_click_rate": round(overview[6] or 0, 2),
                    "avg_reply_rate": round(overview[7] or 0, 2)
                },
                "performance_by_type": [
                    {
                        "campaign_type": row[0],
                        "target_audience": row[1],
                        "count": row[2],
                        "avg_open_rate": round(row[3] or 0, 2),
                        "avg_click_rate": round(row[4] or 0, 2),
                        "avg_reply_rate": round(row[5] or 0, 2)
                    }
                    for row in performance_by_type
                ],
                "top_campaigns": [
                    {
                        "campaign_id": row[0],
                        "campaign_name": row[1],
                        "open_rate": round(row[2] or 0, 2),
                        "click_rate": round(row[3] or 0, 2),
                        "reply_rate": round(row[4] or 0, 2),
                        "emails_sent": row[5] or 0,
                        "created_at": row[6]
                    }
                    for row in top_campaigns
                ],
                "period_days": days,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get dashboard analytics: {e}")
            return {"error": str(e)}
    
    async def _save_campaign_metrics(self, metrics: CampaignMetrics) -> None:
        """Save campaign metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO campaign_metrics 
            (campaign_id, campaign_name, created_at, executed_at, total_recipients,
             emails_sent, emails_failed, emails_delivered, emails_opened, emails_clicked,
             emails_replied, emails_bounced, emails_unsubscribed, open_rate, click_rate,
             reply_rate, bounce_rate, unsubscribe_rate, conversion_rate, platform,
             campaign_type, target_audience)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.campaign_id, metrics.campaign_name, metrics.created_at, 
            metrics.executed_at, metrics.total_recipients, metrics.emails_sent,
            metrics.emails_failed, metrics.emails_delivered, metrics.emails_opened,
            metrics.emails_clicked, metrics.emails_replied, metrics.emails_bounced,
            metrics.emails_unsubscribed, metrics.open_rate, metrics.click_rate,
            metrics.reply_rate, metrics.bounce_rate, metrics.unsubscribe_rate,
            metrics.conversion_rate, metrics.platform, metrics.campaign_type,
            metrics.target_audience
        ))
        
        conn.commit()
        conn.close()
    
    async def _save_recipient_activity(self, activity: RecipientActivity) -> None:
        """Save recipient activity to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO recipient_activity 
            (campaign_id, recipient_email, recipient_name, company, title,
             email_sent_at, email_delivered_at, email_opened_at, email_clicked_at,
             email_replied_at, email_bounced_at, unsubscribed_at, status,
             open_count, click_count, last_activity_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            activity.campaign_id, activity.recipient_email, activity.recipient_name,
            activity.company, activity.title, activity.email_sent_at,
            activity.email_delivered_at, activity.email_opened_at, activity.email_clicked_at,
            activity.email_replied_at, activity.email_bounced_at, activity.unsubscribed_at,
            activity.status, activity.open_count, activity.click_count,
            activity.last_activity_at
        ))
        
        conn.commit()
        conn.close()
    
    async def _update_recipient_status(self, campaign_id: str, recipient_email: str, 
                                     status: str, update_data: Dict[str, Any]) -> None:
        """Update recipient status and activity data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic update query
        set_clauses = ["status = ?"]
        values = [status]
        
        for key, value in update_data.items():
            if key != "status":
                if isinstance(value, str) and "+" in value:
                    # Handle expressions like "open_count + 1"
                    set_clauses.append(f"{key} = {value}")
                else:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
        
        values.extend([campaign_id, recipient_email])
        
        query = f"""
            UPDATE recipient_activity 
            SET {', '.join(set_clauses)}
            WHERE campaign_id = ? AND recipient_email = ?
        """
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
    
    async def _calculate_rates(self, campaign_id: str) -> None:
        """Calculate and update campaign rates"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current counts
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('delivered', 'opened', 'clicked', 'replied') THEN 1 ELSE 0 END) as delivered,
                    SUM(CASE WHEN status IN ('opened', 'clicked', 'replied') THEN 1 ELSE 0 END) as opened,
                    SUM(CASE WHEN status IN ('clicked', 'replied') THEN 1 ELSE 0 END) as clicked,
                    SUM(CASE WHEN status = 'replied' THEN 1 ELSE 0 END) as replied,
                    SUM(CASE WHEN status = 'bounced' THEN 1 ELSE 0 END) as bounced,
                    SUM(CASE WHEN status = 'unsubscribed' THEN 1 ELSE 0 END) as unsubscribed
                FROM recipient_activity 
                WHERE campaign_id = ?
            """, (campaign_id,))
            
            counts = cursor.fetchone()
            total, delivered, opened, clicked, replied, bounced, unsubscribed = counts
            
            # Calculate rates
            open_rate = (opened / delivered * 100) if delivered > 0 else 0
            click_rate = (clicked / delivered * 100) if delivered > 0 else 0
            reply_rate = (replied / delivered * 100) if delivered > 0 else 0
            bounce_rate = (bounced / total * 100) if total > 0 else 0
            unsubscribe_rate = (unsubscribed / delivered * 100) if delivered > 0 else 0
            conversion_rate = reply_rate  # For now, conversion = reply
            
            # Update campaign metrics
            cursor.execute("""
                UPDATE campaign_metrics 
                SET emails_delivered = ?, emails_opened = ?, emails_clicked = ?,
                    emails_replied = ?, emails_bounced = ?, emails_unsubscribed = ?,
                    open_rate = ?, click_rate = ?, reply_rate = ?, bounce_rate = ?,
                    unsubscribe_rate = ?, conversion_rate = ?
                WHERE campaign_id = ?
            """, (
                delivered, opened, clicked, replied, bounced, unsubscribed,
                round(open_rate, 2), round(click_rate, 2), round(reply_rate, 2),
                round(bounce_rate, 2), round(unsubscribe_rate, 2), round(conversion_rate, 2),
                campaign_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate rates: {e}")
    
    def _calculate_engagement_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall engagement score (0-100)"""
        try:
            open_rate = metrics.get("open_rate", 0)
            click_rate = metrics.get("click_rate", 0)
            reply_rate = metrics.get("reply_rate", 0)
            
            # Weighted engagement score
            engagement = (open_rate * 0.3) + (click_rate * 0.4) + (reply_rate * 1.0)
            return round(min(engagement, 100), 2)
            
        except Exception:
            return 0.0

    async def create_campaign_metrics(
        self, 
        campaign_id: str, 
        campaign_name: str, 
        platform: str = "unknown",
        total_recipients: int = 0,
        campaign_type: str = "outreach",
        target_audience: str = "professionals"
    ) -> None:
        """Create campaign metrics entry"""
        try:
            metrics = CampaignMetrics(
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                created_at=datetime.now().isoformat(),
                total_recipients=total_recipients,
                platform=platform,
                campaign_type=campaign_type,
                target_audience=target_audience
            )
            
            await self._save_campaign_metrics(metrics)
            logger.info(f"📊 Campaign metrics created: {campaign_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create campaign metrics: {e}")
    
    async def add_recipient_activity(
        self,
        campaign_id: str,
        recipient_email: str,
        recipient_name: str,
        company: str,
        title: str,
        status: str = "added"
    ) -> None:
        """Add recipient activity"""
        try:
            activity = RecipientActivity(
                campaign_id=campaign_id,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                company=company,
                title=title,
                status=status
            )
            
            await self._save_recipient_activity(activity)
            logger.info(f"👤 Recipient activity added: {recipient_email}")
            
        except Exception as e:
            logger.error(f"❌ Failed to add recipient activity: {e}")
    
    async def update_campaign_metrics(
        self,
        campaign_id: str,
        emails_sent: Optional[int] = None,
        emails_delivered: Optional[int] = None,
        emails_opened: Optional[int] = None,
        emails_clicked: Optional[int] = None,
        emails_replied: Optional[int] = None,
        executed_at: Optional[str] = None
    ) -> None:
        """Update campaign metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if emails_sent is not None:
                updates.append("emails_sent = ?")
                params.append(emails_sent)
            if emails_delivered is not None:
                updates.append("emails_delivered = ?") 
                params.append(emails_delivered)
            if emails_opened is not None:
                updates.append("emails_opened = ?")
                params.append(emails_opened)
            if emails_clicked is not None:
                updates.append("emails_clicked = ?")
                params.append(emails_clicked)
            if emails_replied is not None:
                updates.append("emails_replied = ?")
                params.append(emails_replied)
            if executed_at is not None:
                updates.append("executed_at = ?")
                params.append(executed_at)
            
            if updates:
                params.append(campaign_id)
                cursor.execute(f"""
                    UPDATE campaign_metrics 
                    SET {', '.join(updates)}
                    WHERE campaign_id = ?
                """, params)
                
                conn.commit()
                await self._calculate_rates(campaign_id)
                
            conn.close()
            logger.info(f"📊 Campaign metrics updated: {campaign_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update campaign metrics: {e}")
    
    async def get_campaign_metrics(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM campaign_metrics WHERE campaign_id = ?
            """, (campaign_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get campaign metrics: {e}")
            return None
    
    async def get_recipient_activities(self, campaign_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recipient activities"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM recipient_activity 
                WHERE campaign_id = ? 
                ORDER BY last_activity_at DESC, id DESC
                LIMIT ?
            """, (campaign_id, limit))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Failed to get recipient activities: {e}")
            return []
    
    async def get_campaign_events(self, campaign_id: str, limit: int = 50, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get campaign events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            cursor.execute("""
                SELECT campaign_id, recipient_email, event_type, event_data, timestamp as created_at
                FROM campaign_events 
                WHERE campaign_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (campaign_id, cutoff_date, limit))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Failed to get campaign events: {e}")
            return []
    
    async def get_performance_overview(self) -> Dict[str, Any]:
        """Get performance overview"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get aggregate metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_campaigns,
                    SUM(total_recipients) as total_recipients,
                    SUM(emails_sent) as total_emails_sent,
                    SUM(emails_opened) as total_emails_opened,
                    SUM(emails_replied) as total_emails_replied,
                    AVG(open_rate) as average_open_rate,
                    AVG(reply_rate) as average_reply_rate
                FROM campaign_metrics
            """)
            
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            if row:
                return dict(zip(columns, row))
            
            return {
                "total_campaigns": 0,
                "total_recipients": 0,
                "total_emails_sent": 0,
                "total_emails_opened": 0,
                "total_emails_replied": 0,
                "average_open_rate": 0,
                "average_reply_rate": 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get performance overview: {e}")
            return {}
    
    async def get_recent_campaigns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent campaigns"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM campaign_metrics 
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent campaigns: {e}")
            return []

# Global instance
campaign_analytics = CampaignAnalyticsService()
