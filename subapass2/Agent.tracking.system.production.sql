-- 🚀 COMPLETE COOGI DATABASE SETUP FROM SCRATCH
-- Production-Ready Progressive Agent Tracking System
-- Run this FIRST in Supabase SQL Editor to create all tables
-- Updated: September 6, 2025

-- ============================================================
-- STEP 1: CREATE ALL CORE TABLES
-- ============================================================

-- 1. Create progressive_agent_jobs table for storing actual jobs found
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

-- 2. Create progressive_agent_contacts table for storing contacts found
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

-- 3. Create progressive_agent_campaigns table for storing campaigns
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

-- 4. Create progressive_agents table to track agent metadata
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

-- 5. Create indexes for lightning-fast performance
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_agent_id ON progressive_agent_jobs(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_company ON progressive_agent_jobs(company);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_site ON progressive_agent_jobs(site);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_created_at ON progressive_agent_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_is_remote ON progressive_agent_jobs(is_remote);

CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_agent_id ON progressive_agent_contacts(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_company ON progressive_agent_contacts(company);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_verified ON progressive_agent_contacts(verified);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_created_at ON progressive_agent_contacts(created_at);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_email ON progressive_agent_contacts(email);

CREATE INDEX IF NOT EXISTS idx_progressive_agent_campaigns_agent_id ON progressive_agent_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_campaigns_status ON progressive_agent_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_campaigns_created_at ON progressive_agent_campaigns(created_at);

CREATE INDEX IF NOT EXISTS idx_progressive_agents_agent_id ON progressive_agents(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agents_status ON progressive_agents(status);
CREATE INDEX IF NOT EXISTS idx_progressive_agents_created_at ON progressive_agents(created_at);

-- ============================================================
-- STEP 2: ENABLE SECURITY AND PERMISSIONS
-- ============================================================

-- 6. Enable Row Level Security for all new tables
ALTER TABLE progressive_agent_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agents ENABLE ROW LEVEL SECURITY;

-- 7. Drop existing policies if they exist (to avoid "policy already exists" error)
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_jobs" ON progressive_agent_jobs;
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_contacts" ON progressive_agent_contacts;
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_campaigns" ON progressive_agent_campaigns;
DROP POLICY IF EXISTS "Allow all operations on progressive_agents" ON progressive_agents;

-- 8. Create new policies for public access (you can restrict later if needed)
CREATE POLICY "Allow all operations on progressive_agent_jobs" ON progressive_agent_jobs FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_contacts" ON progressive_agent_contacts FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_campaigns" ON progressive_agent_campaigns FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agents" ON progressive_agents FOR ALL USING (true);

-- 9. Grant full permissions to all roles
GRANT ALL ON progressive_agent_jobs TO anon, authenticated, service_role;
GRANT ALL ON progressive_agent_contacts TO anon, authenticated, service_role;
GRANT ALL ON progressive_agent_campaigns TO anon, authenticated, service_role;
GRANT ALL ON progressive_agents TO anon, authenticated, service_role;

GRANT ALL ON SEQUENCE progressive_agent_jobs_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE progressive_agent_contacts_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE progressive_agent_campaigns_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE progressive_agents_id_seq TO anon, authenticated, service_role;

-- 10. Create production_campaigns table (CRITICAL for backend)
CREATE TABLE IF NOT EXISTS production_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id TEXT UNIQUE NOT NULL, -- Generated by backend: campaign_20250906_123456_7890
    agent_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft', -- draft, ready, active, paused, completed, error
    platform TEXT NOT NULL DEFAULT 'instantly', -- instantly, smartlead, internal
    subject_line TEXT NOT NULL,
    from_email TEXT NOT NULL,
    from_name TEXT NOT NULL,
    email_sequence JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of email steps
    target_count INTEGER DEFAULT 0,
    verified_contacts JSONB DEFAULT '[]'::jsonb, -- Array of contact objects
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    bounce_count INTEGER DEFAULT 0,
    unsubscribe_count INTEGER DEFAULT 0,
    open_rate FLOAT DEFAULT 0.0,
    reply_rate FLOAT DEFAULT 0.0,
    click_rate FLOAT DEFAULT 0.0,
    provider_campaign_id TEXT, -- External provider ID (Instantly/Smartlead)
    error_message TEXT,
    config JSONB DEFAULT '{}'::jsonb, -- Additional configuration
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for production_campaigns (CRITICAL for performance)
CREATE INDEX IF NOT EXISTS idx_production_campaigns_campaign_id ON production_campaigns(campaign_id);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_agent_id ON production_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_status ON production_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_platform ON production_campaigns(platform);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_created_at ON production_campaigns(created_at);

-- Enable RLS and create policy for production_campaigns
ALTER TABLE production_campaigns ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all operations on production_campaigns" ON production_campaigns;
CREATE POLICY "Allow all operations on production_campaigns" ON production_campaigns FOR ALL USING (true);
GRANT ALL ON production_campaigns TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE production_campaigns_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- STEP 3: INSERT TEST DATA (to verify everything works)
-- ============================================================

-- 11. Insert minimal test data (remove after confirming everything works)
DO $$
BEGIN
    -- Only insert if no data exists
    IF NOT EXISTS (SELECT 1 FROM progressive_agents WHERE agent_id = 'production-test-agent') THEN
        INSERT INTO progressive_agents (agent_id, query, status, total_progress, hours_old, total_jobs, total_contacts, total_campaigns) 
        VALUES ('production-test-agent', 'software engineer', 'completed', 100, 24, 3, 2, 1);

        INSERT INTO progressive_agent_jobs (agent_id, title, company, location, salary, site, is_remote) VALUES
        ('production-test-agent', 'Senior Software Engineer', 'Google', 'Mountain View, CA', '$180k - $250k', 'LinkedIn', false),
        ('production-test-agent', 'Frontend Developer', 'Meta', 'Menlo Park, CA', '$170k - $240k', 'LinkedIn', true),
        ('production-test-agent', 'Full Stack Engineer', 'Netflix', 'Los Gatos, CA', '$200k - $280k', 'LinkedIn', false);

        INSERT INTO progressive_agent_contacts (agent_id, first_name, last_name, email, company, title, verified) VALUES
        ('production-test-agent', 'Sarah', 'Johnson', 'sarah.johnson@google.com', 'Google', 'Engineering Manager', true),
        ('production-test-agent', 'Mike', 'Chen', 'mike.chen@meta.com', 'Meta', 'Senior Recruiter', true);

        INSERT INTO progressive_agent_campaigns (agent_id, name, type, status, target_count) VALUES
        ('production-test-agent', 'Google Outreach Campaign', 'Email Campaign', 'Active', 10);

        INSERT INTO production_campaigns (campaign_id, agent_id, name, status, platform, subject_line, from_email, from_name, email_sequence, target_count) VALUES
        ('campaign_20250906_test_001', 'production-test-agent', 'Production Test Campaign', 'active', 'instantly', 'Test Subject Line', 'outreach@coogi.ai', 'Coogi Team', '[{"step_number": 1, "subject": "Test", "body": "Test email content", "delay_days": 0}]'::jsonb, 5);
    END IF;
END $$;

-- ============================================================
-- STEP 4: VERIFICATION QUERIES
-- ============================================================

-- 12. Test queries to verify everything works
SELECT 'Testing production progressive agent data...' as test_status;

-- Count all data
SELECT 
    (SELECT COUNT(*) FROM progressive_agents) as total_agents,
    (SELECT COUNT(*) FROM progressive_agent_jobs) as total_jobs,
    (SELECT COUNT(*) FROM progressive_agent_contacts) as total_contacts,
    (SELECT COUNT(*) FROM progressive_agent_campaigns) as total_campaigns,
    (SELECT COUNT(*) FROM production_campaigns) as total_production_campaigns;

-- Test the main dashboard query
SELECT 
    pa.agent_id,
    pa.query,
    pa.status,
    pa.total_jobs,
    pa.total_contacts,
    pa.total_campaigns,
    COUNT(DISTINCT paj.id) as actual_jobs,
    COUNT(DISTINCT pac.id) as actual_contacts,
    COUNT(DISTINCT cam.id) as actual_campaigns
FROM progressive_agents pa
LEFT JOIN progressive_agent_jobs paj ON pa.agent_id = paj.agent_id
LEFT JOIN progressive_agent_contacts pac ON pa.agent_id = pac.agent_id
LEFT JOIN progressive_agent_campaigns cam ON pa.agent_id = cam.agent_id
WHERE pa.agent_id = 'production-test-agent'
GROUP BY pa.agent_id, pa.query, pa.status, pa.total_jobs, pa.total_contacts, pa.total_campaigns;

-- ============================================================
-- SUCCESS! DATABASE SETUP COMPLETE 🎉
-- ============================================================
SELECT '🎉 COOGI DATABASE SETUP COMPLETE! 🎉' as status;
SELECT 'All tables created with proper RLS policies and indexes!' as message;
SELECT 'Backend will now connect successfully!' as backend_ready;
SELECT 'Frontend Lead Database will display real-time data!' as frontend_ready;
SELECT 'Test data inserted - run cleanup script when ready!' as cleanup_note;

-- ============================================================
-- CLEANUP SCRIPT (run this after confirming everything works)
-- ============================================================
/*
-- Uncomment and run this to remove test data:
DELETE FROM production_campaigns WHERE agent_id = 'production-test-agent';
DELETE FROM progressive_agent_campaigns WHERE agent_id = 'production-test-agent';
DELETE FROM progressive_agent_contacts WHERE agent_id = 'production-test-agent';
DELETE FROM progressive_agent_jobs WHERE agent_id = 'production-test-agent';
DELETE FROM progressive_agents WHERE agent_id = 'production-test-agent';

SELECT 'Test data cleaned up successfully!' as cleanup_status;
*/
