-- 🚀 EMAIL CAMPAIGN SYSTEM SCHEMA
-- AWS SES Email Campaign Management for Coogi
-- Run this SECOND after the main schema
-- Updated: September 6, 2025

-- ============================================================
-- SES EMAIL CAMPAIGNS TABLES
-- ============================================================

-- Email list management
CREATE TABLE IF NOT EXISTS ses_email_lists (
    id SERIAL PRIMARY KEY,
    list_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    total_contacts INTEGER DEFAULT 0,
    verified_contacts INTEGER DEFAULT 0,
    bounced_contacts INTEGER DEFAULT 0,
    suppressed_contacts INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active', -- active, inactive, processing
    tags TEXT[] DEFAULT '{}',
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email contacts within lists
CREATE TABLE IF NOT EXISTS ses_email_contacts (
    id SERIAL PRIMARY KEY,
    contact_id TEXT UNIQUE NOT NULL,
    list_id TEXT NOT NULL REFERENCES ses_email_lists(list_id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    company TEXT,
    job_title TEXT,
    phone TEXT,
    linkedin_url TEXT,
    verification_status TEXT DEFAULT 'pending', -- pending, verified, invalid, bounced
    suppression_reason TEXT, -- bounce, complaint, manual
    metadata JSONB DEFAULT '{}',
    last_engagement TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email campaigns using SES
CREATE TABLE IF NOT EXISTS ses_email_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    from_email TEXT NOT NULL,
    from_name TEXT NOT NULL,
    reply_to_email TEXT,
    subject_line TEXT NOT NULL,
    email_content TEXT NOT NULL,
    list_id TEXT NOT NULL REFERENCES ses_email_lists(list_id),
    status TEXT DEFAULT 'draft', -- draft, scheduled, sending, sent, paused, completed, failed
    send_at TIMESTAMPTZ,
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    bounce_count INTEGER DEFAULT 0,
    complaint_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    delivery_rate FLOAT DEFAULT 0.0,
    open_rate FLOAT DEFAULT 0.0,
    click_rate FLOAT DEFAULT 0.0,
    error_message TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Email sending logs
CREATE TABLE IF NOT EXISTS ses_email_logs (
    id SERIAL PRIMARY KEY,
    log_id TEXT UNIQUE NOT NULL,
    campaign_id TEXT REFERENCES ses_email_campaigns(campaign_id),
    contact_id TEXT REFERENCES ses_email_contacts(contact_id),
    message_id TEXT, -- AWS SES message ID
    email TEXT NOT NULL,
    event_type TEXT NOT NULL, -- send, bounce, complaint, delivery, open, click, reject
    event_data JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Email lists indexes
CREATE INDEX IF NOT EXISTS idx_ses_email_lists_list_id ON ses_email_lists(list_id);
CREATE INDEX IF NOT EXISTS idx_ses_email_lists_status ON ses_email_lists(status);
CREATE INDEX IF NOT EXISTS idx_ses_email_lists_created_at ON ses_email_lists(created_at);

-- Email contacts indexes
CREATE INDEX IF NOT EXISTS idx_ses_email_contacts_contact_id ON ses_email_contacts(contact_id);
CREATE INDEX IF NOT EXISTS idx_ses_email_contacts_list_id ON ses_email_contacts(list_id);
CREATE INDEX IF NOT EXISTS idx_ses_email_contacts_email ON ses_email_contacts(email);
CREATE INDEX IF NOT EXISTS idx_ses_email_contacts_verification_status ON ses_email_contacts(verification_status);
CREATE INDEX IF NOT EXISTS idx_ses_email_contacts_company ON ses_email_contacts(company);

-- Email campaigns indexes
CREATE INDEX IF NOT EXISTS idx_ses_email_campaigns_campaign_id ON ses_email_campaigns(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ses_email_campaigns_list_id ON ses_email_campaigns(list_id);
CREATE INDEX IF NOT EXISTS idx_ses_email_campaigns_status ON ses_email_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_ses_email_campaigns_created_at ON ses_email_campaigns(created_at);
CREATE INDEX IF NOT EXISTS idx_ses_email_campaigns_send_at ON ses_email_campaigns(send_at);

-- Email logs indexes
CREATE INDEX IF NOT EXISTS idx_ses_email_logs_log_id ON ses_email_logs(log_id);
CREATE INDEX IF NOT EXISTS idx_ses_email_logs_campaign_id ON ses_email_logs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ses_email_logs_contact_id ON ses_email_logs(contact_id);
CREATE INDEX IF NOT EXISTS idx_ses_email_logs_event_type ON ses_email_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_ses_email_logs_timestamp ON ses_email_logs(timestamp);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Enable RLS
ALTER TABLE ses_email_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE ses_email_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ses_email_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE ses_email_logs ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow all operations on ses_email_lists" ON ses_email_lists FOR ALL USING (true);
CREATE POLICY "Allow all operations on ses_email_contacts" ON ses_email_contacts FOR ALL USING (true);
CREATE POLICY "Allow all operations on ses_email_campaigns" ON ses_email_campaigns FOR ALL USING (true);
CREATE POLICY "Allow all operations on ses_email_logs" ON ses_email_logs FOR ALL USING (true);

-- Grant permissions
GRANT ALL ON ses_email_lists TO anon, authenticated, service_role;
GRANT ALL ON ses_email_contacts TO anon, authenticated, service_role;
GRANT ALL ON ses_email_campaigns TO anon, authenticated, service_role;
GRANT ALL ON ses_email_logs TO anon, authenticated, service_role;

GRANT ALL ON SEQUENCE ses_email_lists_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE ses_email_contacts_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE ses_email_campaigns_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE ses_email_logs_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- TEST DATA
-- ============================================================

-- Insert test email list
INSERT INTO ses_email_lists (list_id, name, description, total_contacts) VALUES 
('test_list_001', 'Test Email List', 'Sample email list for testing', 0);

-- Success message
SELECT '✅ SES EMAIL CAMPAIGN SYSTEM CREATED!' as status;
SELECT 'All SES tables created with proper indexes and security!' as message;
