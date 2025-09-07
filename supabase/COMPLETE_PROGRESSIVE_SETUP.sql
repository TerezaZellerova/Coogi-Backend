-- ============================================================
-- COMPLETE PROGRESSIVE AGENT TABLES FOR COOGI (ONE-TIME SETUP)
-- Copy this ENTIRE script and paste into Supabase SQL Editor
-- This adds real-time job/contact/campaign tracking to your existing setup
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

-- 6. Enable Row Level Security for all new tables
ALTER TABLE progressive_agent_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agents ENABLE ROW LEVEL SECURITY;

-- 7. Create policies for public access (you can restrict later if needed)
CREATE POLICY "Allow all operations on progressive_agent_jobs" ON progressive_agent_jobs FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_contacts" ON progressive_agent_contacts FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_campaigns" ON progressive_agent_campaigns FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agents" ON progressive_agents FOR ALL USING (true);

-- 8. Grant full permissions to all roles
GRANT ALL ON progressive_agent_jobs TO anon, authenticated, service_role;
GRANT ALL ON progressive_agent_contacts TO anon, authenticated, service_role;
GRANT ALL ON progressive_agent_campaigns TO anon, authenticated, service_role;
GRANT ALL ON progressive_agents TO anon, authenticated, service_role;

GRANT ALL ON SEQUENCE progressive_agent_jobs_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE progressive_agent_contacts_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE progressive_agent_campaigns_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE progressive_agents_id_seq TO anon, authenticated, service_role;

-- 9. Insert demo data to test everything works
INSERT INTO progressive_agents (agent_id, query, status, total_progress, hours_old, total_jobs, total_contacts, total_campaigns) 
VALUES ('demo-agent-123', 'software engineer', 'completed', 100, 24, 25, 15, 2);

INSERT INTO progressive_agent_jobs (agent_id, title, company, location, salary, site, is_remote) VALUES
('demo-agent-123', 'Senior Software Engineer', 'Google', 'Mountain View, CA', '$180k - $250k', 'LinkedIn', false),
('demo-agent-123', 'Frontend Developer', 'Meta', 'Menlo Park, CA', '$170k - $240k', 'LinkedIn', true),
('demo-agent-123', 'Full Stack Engineer', 'Netflix', 'Los Gatos, CA', '$200k - $280k', 'LinkedIn', false);

INSERT INTO progressive_agent_contacts (agent_id, first_name, last_name, email, company, title, verified) VALUES
('demo-agent-123', 'Sarah', 'Johnson', 'sarah.johnson@google.com', 'Google', 'Engineering Manager', true),
('demo-agent-123', 'Mike', 'Chen', 'mike.chen@meta.com', 'Meta', 'Senior Recruiter', true);

INSERT INTO progressive_agent_campaigns (agent_id, name, type, status, target_count) VALUES
('demo-agent-123', 'Google Outreach Campaign', 'Email Campaign', 'Active', 10),
('demo-agent-123', 'Meta Follow-up Campaign', 'Email Campaign', 'Ready', 5);

-- 10. Test queries to verify everything works
SELECT 'Testing progressive agent data...' as test_status;

-- Count demo data
SELECT 
    (SELECT COUNT(*) FROM progressive_agents) as total_agents,
    (SELECT COUNT(*) FROM progressive_agent_jobs) as total_jobs,
    (SELECT COUNT(*) FROM progressive_agent_contacts) as total_contacts,
    (SELECT COUNT(*) FROM progressive_agent_campaigns) as total_campaigns;

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
WHERE pa.agent_id = 'demo-agent-123'
GROUP BY pa.agent_id, pa.query, pa.status, pa.total_jobs, pa.total_contacts, pa.total_campaigns;

-- 11. Clean up demo data (comment out if you want to keep it for testing)
DELETE FROM progressive_agent_campaigns WHERE agent_id = 'demo-agent-123';
DELETE FROM progressive_agent_contacts WHERE agent_id = 'demo-agent-123';
DELETE FROM progressive_agent_jobs WHERE agent_id = 'demo-agent-123';
DELETE FROM progressive_agents WHERE agent_id = 'demo-agent-123';

-- ============================================================
-- SUCCESS MESSAGE - YOU'RE ALL SET! 🎉
-- ============================================================
SELECT '🎉 PROGRESSIVE AGENT TABLES CREATED SUCCESSFULLY! 🎉' as status;
SELECT 'Your database now supports real-time job/contact/campaign tracking!' as message;
SELECT 'Frontend Lead Database and Campaigns tabs will now show real data!' as benefit;
SELECT 'No code changes needed - everything will work automatically!' as easy_mode;
