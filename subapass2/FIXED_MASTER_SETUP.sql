-- 🚀 FIXED MASTER COOGI DATABASE SETUP
-- This version fixes the production_campaigns table issue
-- Copy and paste this ENTIRE script into Supabase SQL Editor

-- First, let's drop the problematic table if it exists
DROP TABLE IF EXISTS production_campaigns CASCADE;

-- ============================================================
-- STEP 1: CORE PROGRESSIVE AGENT SYSTEM
-- ============================================================

-- Progressive agent jobs table
CREATE TABLE IF NOT EXISTS progressive_agent_jobs (
    id SERIAL PRIMARY KEY,
    agent_id TEXT NOT NULL,
    job_id TEXT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    url TEXT,
    description TEXT,
    posted_date TEXT,
    employment_type TEXT,
    experience_level TEXT,
    salary TEXT,
    site TEXT DEFAULT 'LinkedIn',
    company_url TEXT,
    is_remote BOOLEAN DEFAULT FALSE,
    skills TEXT[],
    is_demo BOOLEAN DEFAULT FALSE,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Progressive agent contacts table
CREATE TABLE IF NOT EXISTS progressive_agent_contacts (
    id SERIAL PRIMARY KEY,
    agent_id TEXT NOT NULL,
    contact_id TEXT,
    name TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    company TEXT,
    role TEXT,
    title TEXT,
    linkedin_url TEXT,
    phone TEXT,
    verified BOOLEAN DEFAULT FALSE,
    source TEXT DEFAULT 'Hunter',
    confidence_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Progressive agent campaigns table
CREATE TABLE IF NOT EXISTS progressive_agent_campaigns (
    id SERIAL PRIMARY KEY,
    agent_id TEXT NOT NULL,
    campaign_id TEXT,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'Email Campaign',
    status TEXT DEFAULT 'Ready',
    subject TEXT,
    content TEXT,
    target_count INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    platform TEXT DEFAULT 'Instantly',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Progressive agents metadata table
CREATE TABLE IF NOT EXISTS progressive_agents (
    id SERIAL PRIMARY KEY,
    agent_id TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    status TEXT NOT NULL,
    total_progress INTEGER DEFAULT 0,
    hours_old INTEGER DEFAULT 24,
    custom_tags TEXT[],
    total_jobs INTEGER DEFAULT 0,
    total_contacts INTEGER DEFAULT 0,
    total_campaigns INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Production campaigns table (FIXED VERSION)
CREATE TABLE production_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id TEXT UNIQUE NOT NULL,
    agent_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    platform TEXT NOT NULL DEFAULT 'instantly',
    subject_line TEXT NOT NULL,
    from_email TEXT NOT NULL,
    from_name TEXT NOT NULL,
    email_sequence JSONB NOT NULL DEFAULT '[]'::jsonb,
    target_count INTEGER DEFAULT 0,
    verified_contacts JSONB DEFAULT '[]'::jsonb,
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    bounce_count INTEGER DEFAULT 0,
    unsubscribe_count INTEGER DEFAULT 0,
    open_rate FLOAT DEFAULT 0.0,
    reply_rate FLOAT DEFAULT 0.0,
    click_rate FLOAT DEFAULT 0.0,
    provider_campaign_id TEXT,
    error_message TEXT,
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Simple contacts table (for the missing contacts table error)
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    company TEXT,
    title TEXT,
    phone TEXT,
    linkedin_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- STEP 2: EMAIL CAMPAIGN SYSTEM
-- ============================================================

-- SES Email lists
CREATE TABLE IF NOT EXISTS ses_email_lists (
    id SERIAL PRIMARY KEY,
    list_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    total_contacts INTEGER DEFAULT 0,
    verified_contacts INTEGER DEFAULT 0,
    bounced_contacts INTEGER DEFAULT 0,
    suppressed_contacts INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    tags TEXT[] DEFAULT '{}',
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SES Email contacts
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
    verification_status TEXT DEFAULT 'pending',
    suppression_reason TEXT,
    metadata JSONB DEFAULT '{}',
    last_engagement TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Admin users
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    status TEXT DEFAULT 'active',
    permissions JSONB DEFAULT '{}',
    last_login TIMESTAMPTZ,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email templates
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,
    template_type TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- STEP 3: CREATE INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_agent_id ON progressive_agent_jobs(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_agent_id ON progressive_agent_contacts(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_campaigns_agent_id ON progressive_agent_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agents_agent_id ON progressive_agents(agent_id);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_campaign_id ON production_campaigns(campaign_id);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_agent_id ON production_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);

-- ============================================================
-- STEP 4: ENABLE SECURITY
-- ============================================================

ALTER TABLE progressive_agent_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE production_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ses_email_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE ses_email_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;

-- Drop existing policies first
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_jobs" ON progressive_agent_jobs;
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_contacts" ON progressive_agent_contacts;
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_campaigns" ON progressive_agent_campaigns;
DROP POLICY IF EXISTS "Allow all operations on progressive_agents" ON progressive_agents;
DROP POLICY IF EXISTS "Allow all operations on production_campaigns" ON production_campaigns;
DROP POLICY IF EXISTS "Allow all operations on contacts" ON contacts;
DROP POLICY IF EXISTS "Allow all operations on ses_email_lists" ON ses_email_lists;
DROP POLICY IF EXISTS "Allow all operations on ses_email_contacts" ON ses_email_contacts;
DROP POLICY IF EXISTS "Allow all operations on admin_users" ON admin_users;
DROP POLICY IF EXISTS "Allow all operations on email_templates" ON email_templates;

-- Create new policies
CREATE POLICY "Allow all operations on progressive_agent_jobs" ON progressive_agent_jobs FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_contacts" ON progressive_agent_contacts FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_campaigns" ON progressive_agent_campaigns FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agents" ON progressive_agents FOR ALL USING (true);
CREATE POLICY "Allow all operations on production_campaigns" ON production_campaigns FOR ALL USING (true);
CREATE POLICY "Allow all operations on contacts" ON contacts FOR ALL USING (true);
CREATE POLICY "Allow all operations on ses_email_lists" ON ses_email_lists FOR ALL USING (true);
CREATE POLICY "Allow all operations on ses_email_contacts" ON ses_email_contacts FOR ALL USING (true);
CREATE POLICY "Allow all operations on admin_users" ON admin_users FOR ALL USING (true);
CREATE POLICY "Allow all operations on email_templates" ON email_templates FOR ALL USING (true);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

-- ============================================================
-- STEP 5: INSERT TEST DATA
-- ============================================================

-- Insert test data only if it doesn't exist
DO $$
BEGIN
    -- Insert test progressive agent
    IF NOT EXISTS (SELECT 1 FROM progressive_agents WHERE agent_id = 'production-test-agent') THEN
        INSERT INTO progressive_agents (agent_id, query, status, total_progress, hours_old, total_jobs, total_contacts, total_campaigns) 
        VALUES ('production-test-agent', 'software engineer', 'completed', 100, 24, 3, 2, 1);

        -- Insert test jobs
        INSERT INTO progressive_agent_jobs (agent_id, title, company, location, salary, site, is_remote) VALUES
        ('production-test-agent', 'Senior Software Engineer', 'Google', 'Mountain View, CA', '$180k - $250k', 'LinkedIn', false),
        ('production-test-agent', 'Frontend Developer', 'Meta', 'Menlo Park, CA', '$170k - $240k', 'LinkedIn', true),
        ('production-test-agent', 'Full Stack Engineer', 'Netflix', 'Los Gatos, CA', '$200k - $280k', 'LinkedIn', false);

        -- Insert test contacts
        INSERT INTO progressive_agent_contacts (agent_id, first_name, last_name, email, company, title, verified) VALUES
        ('production-test-agent', 'Sarah', 'Johnson', 'sarah.johnson@google.com', 'Google', 'Engineering Manager', true),
        ('production-test-agent', 'Mike', 'Chen', 'mike.chen@meta.com', 'Meta', 'Senior Recruiter', true);

        -- Insert test contacts in the simple contacts table too
        INSERT INTO contacts (email, first_name, last_name, company, title) VALUES
        ('sarah.johnson@google.com', 'Sarah', 'Johnson', 'Google', 'Engineering Manager'),
        ('mike.chen@meta.com', 'Mike', 'Chen', 'Meta', 'Senior Recruiter'),
        ('test@example.com', 'Test', 'User', 'Test Company', 'Test Title');

        -- Insert test campaigns
        INSERT INTO progressive_agent_campaigns (agent_id, name, type, status, target_count) VALUES
        ('production-test-agent', 'Google Outreach Campaign', 'Email Campaign', 'Active', 10);

        -- Insert test production campaign
        INSERT INTO production_campaigns (campaign_id, agent_id, name, status, platform, subject_line, from_email, from_name, email_sequence, target_count) VALUES
        ('campaign_20250906_test_001', 'production-test-agent', 'Production Test Campaign', 'active', 'instantly', 'Test Subject Line', 'outreach@coogi.ai', 'Coogi Team', '[{"step_number": 1, "subject": "Test", "body": "Test email content", "delay_days": 0}]'::jsonb, 5);
    END IF;

    -- Insert test email list
    IF NOT EXISTS (SELECT 1 FROM ses_email_lists WHERE list_id = 'test_list_001') THEN
        INSERT INTO ses_email_lists (list_id, name, description, total_contacts) VALUES 
        ('test_list_001', 'Test Email List', 'Sample email list for testing', 0);
    END IF;

    -- Insert test admin user
    IF NOT EXISTS (SELECT 1 FROM admin_users WHERE user_id = 'admin_001') THEN
        INSERT INTO admin_users (user_id, email, password_hash, name, role, permissions) VALUES 
        ('admin_001', 'admin@coogi.ai', '$2b$12$example_hash_change_in_production', 'Coogi Admin', 'super_admin', 
         '{"unlimited_agents": true, "unlimited_searches": true, "access_all_features": true}'::jsonb);
    END IF;
END $$;

-- ============================================================
-- STEP 6: VERIFICATION
-- ============================================================

-- Verify all tables exist
SELECT 'Table Verification' as test_type, COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN (
        'progressive_agents', 'production_campaigns', 'contacts',
        'progressive_agent_jobs', 'progressive_agent_contacts',
        'progressive_agent_campaigns', 'ses_email_lists', 'admin_users'
    );

-- Count test data
SELECT 
    (SELECT COUNT(*) FROM progressive_agents) as total_agents,
    (SELECT COUNT(*) FROM progressive_agent_jobs) as total_jobs,
    (SELECT COUNT(*) FROM progressive_agent_contacts) as total_contacts,
    (SELECT COUNT(*) FROM progressive_agent_campaigns) as total_campaigns,
    (SELECT COUNT(*) FROM production_campaigns) as total_production_campaigns,
    (SELECT COUNT(*) FROM contacts) as total_simple_contacts,
    (SELECT COUNT(*) FROM admin_users) as total_admin_users;

-- SUCCESS MESSAGE
SELECT '🎉 FIXED COOGI DATABASE SETUP COMPLETE! 🎉' as status;
SELECT 'All core tables created successfully!' as message;
SELECT 'Test data inserted - ready for backend testing!' as backend_ready;
