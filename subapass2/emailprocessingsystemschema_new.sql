-- 🔧 EMAIL PROCESSING SYSTEM
-- Inbox processing and email reply management for Coogi
-- Run this FOURTH (optional - for advanced email processing)
-- Updated: September 6, 2025

-- ============================================================
-- EMAIL PROCESSING TABLES
-- ============================================================

-- Inbox processing for received emails
CREATE TABLE IF NOT EXISTS email_inbox (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL, -- Email message ID
    campaign_id TEXT, -- Link to originating campaign if applicable
    from_email TEXT NOT NULL,
    to_email TEXT NOT NULL,
    subject TEXT,
    body_text TEXT,
    body_html TEXT,
    attachments JSONB DEFAULT '[]', -- Array of attachment metadata
    headers JSONB DEFAULT '{}', -- Email headers
    is_reply BOOLEAN DEFAULT FALSE,
    is_auto_reply BOOLEAN DEFAULT FALSE,
    sentiment_score FLOAT, -- AI sentiment analysis score
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    received_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email reply threads
CREATE TABLE IF NOT EXISTS email_threads (
    id SERIAL PRIMARY KEY,
    thread_id TEXT UNIQUE NOT NULL,
    campaign_id TEXT,
    contact_email TEXT NOT NULL,
    subject TEXT,
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    status TEXT DEFAULT 'active', -- active, closed, escalated
    assigned_to TEXT, -- User ID who is handling this thread
    tags TEXT[] DEFAULT '{}',
    priority TEXT DEFAULT 'normal', -- low, normal, high, urgent
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual messages within threads
CREATE TABLE IF NOT EXISTS thread_messages (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    thread_id TEXT NOT NULL REFERENCES email_threads(thread_id) ON DELETE CASCADE,
    inbox_message_id TEXT REFERENCES email_inbox(message_id),
    direction TEXT NOT NULL, -- inbound, outbound
    from_email TEXT NOT NULL,
    to_email TEXT NOT NULL,
    body_text TEXT,
    body_html TEXT,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    ai_confidence FLOAT, -- Confidence score if AI generated
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-reply configurations
CREATE TABLE IF NOT EXISTS auto_reply_configs (
    id SERIAL PRIMARY KEY,
    config_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    trigger_keywords TEXT[] DEFAULT '{}', -- Keywords that trigger this auto-reply
    reply_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    delay_minutes INTEGER DEFAULT 0, -- Minutes to wait before sending
    max_replies_per_thread INTEGER DEFAULT 1, -- Prevent spam
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email processing rules
CREATE TABLE IF NOT EXISTS processing_rules (
    id SERIAL PRIMARY KEY,
    rule_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    conditions JSONB NOT NULL, -- JSON conditions for matching emails
    actions JSONB NOT NULL, -- JSON actions to perform
    priority INTEGER DEFAULT 100, -- Lower number = higher priority
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Email inbox indexes
CREATE INDEX IF NOT EXISTS idx_email_inbox_message_id ON email_inbox(message_id);
CREATE INDEX IF NOT EXISTS idx_email_inbox_campaign_id ON email_inbox(campaign_id);
CREATE INDEX IF NOT EXISTS idx_email_inbox_from_email ON email_inbox(from_email);
CREATE INDEX IF NOT EXISTS idx_email_inbox_to_email ON email_inbox(to_email);
CREATE INDEX IF NOT EXISTS idx_email_inbox_is_reply ON email_inbox(is_reply);
CREATE INDEX IF NOT EXISTS idx_email_inbox_processed ON email_inbox(processed);
CREATE INDEX IF NOT EXISTS idx_email_inbox_received_at ON email_inbox(received_at);

-- Email threads indexes
CREATE INDEX IF NOT EXISTS idx_email_threads_thread_id ON email_threads(thread_id);
CREATE INDEX IF NOT EXISTS idx_email_threads_campaign_id ON email_threads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_email_threads_contact_email ON email_threads(contact_email);
CREATE INDEX IF NOT EXISTS idx_email_threads_status ON email_threads(status);
CREATE INDEX IF NOT EXISTS idx_email_threads_assigned_to ON email_threads(assigned_to);
CREATE INDEX IF NOT EXISTS idx_email_threads_priority ON email_threads(priority);

-- Thread messages indexes
CREATE INDEX IF NOT EXISTS idx_thread_messages_message_id ON thread_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_thread_messages_thread_id ON thread_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_thread_messages_direction ON thread_messages(direction);
CREATE INDEX IF NOT EXISTS idx_thread_messages_sent_at ON thread_messages(sent_at);

-- Auto-reply configs indexes
CREATE INDEX IF NOT EXISTS idx_auto_reply_configs_config_id ON auto_reply_configs(config_id);
CREATE INDEX IF NOT EXISTS idx_auto_reply_configs_is_active ON auto_reply_configs(is_active);

-- Processing rules indexes
CREATE INDEX IF NOT EXISTS idx_processing_rules_rule_id ON processing_rules(rule_id);
CREATE INDEX IF NOT EXISTS idx_processing_rules_priority ON processing_rules(priority);
CREATE INDEX IF NOT EXISTS idx_processing_rules_is_active ON processing_rules(is_active);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Enable RLS
ALTER TABLE email_inbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE thread_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE auto_reply_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_rules ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow all operations on email_inbox" ON email_inbox FOR ALL USING (true);
CREATE POLICY "Allow all operations on email_threads" ON email_threads FOR ALL USING (true);
CREATE POLICY "Allow all operations on thread_messages" ON thread_messages FOR ALL USING (true);
CREATE POLICY "Allow all operations on auto_reply_configs" ON auto_reply_configs FOR ALL USING (true);
CREATE POLICY "Allow all operations on processing_rules" ON processing_rules FOR ALL USING (true);

-- Grant permissions
GRANT ALL ON email_inbox TO anon, authenticated, service_role;
GRANT ALL ON email_threads TO anon, authenticated, service_role;
GRANT ALL ON thread_messages TO anon, authenticated, service_role;
GRANT ALL ON auto_reply_configs TO anon, authenticated, service_role;
GRANT ALL ON processing_rules TO anon, authenticated, service_role;

GRANT ALL ON SEQUENCE email_inbox_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE email_threads_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE thread_messages_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE auto_reply_configs_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE processing_rules_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- TEST DATA
-- ============================================================

-- Insert default auto-reply config
INSERT INTO auto_reply_configs (config_id, name, trigger_keywords, reply_template) VALUES 
('auto_reply_001', 'Out of Office', ARRAY['out of office', 'vacation', 'unavailable'], 
 'Thank you for your email. I am currently out of office and will respond when I return.');

-- Insert default processing rule
INSERT INTO processing_rules (rule_id, name, conditions, actions) VALUES 
('rule_001', 'Auto-categorize replies', 
 '{"contains_keywords": ["interested", "tell me more"]}'::jsonb,
 '{"add_tags": ["hot_lead"], "set_priority": "high"}'::jsonb);

-- Success message
SELECT '✅ EMAIL PROCESSING SYSTEM CREATED!' as status;
SELECT 'Inbox processing and auto-reply system ready!' as message;
