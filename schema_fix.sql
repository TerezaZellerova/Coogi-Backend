-- Essential Coogi Database Tables
-- Core tables needed for the backend to function

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
    company_size TEXT DEFAULT 'all',
    target_type TEXT DEFAULT 'hiring_managers',
    location_filter TEXT,
    staged_results JSONB DEFAULT '{}'::jsonb,
    stages JSONB DEFAULT '{}'::jsonb,
    final_stats JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

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

-- Simple contacts table
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

-- Production campaigns table (FIXED VERSION)
CREATE TABLE IF NOT EXISTS production_campaigns (
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_agent_id ON progressive_agent_jobs(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_agent_id ON progressive_agent_contacts(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_campaigns_agent_id ON progressive_agent_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agents_agent_id ON progressive_agents(agent_id);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_campaign_id ON production_campaigns(campaign_id);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_agent_id ON production_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);

-- Enable RLS
ALTER TABLE progressive_agent_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE production_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for now)
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_jobs" ON progressive_agent_jobs;
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_contacts" ON progressive_agent_contacts;
DROP POLICY IF EXISTS "Allow all operations on progressive_agent_campaigns" ON progressive_agent_campaigns;
DROP POLICY IF EXISTS "Allow all operations on progressive_agents" ON progressive_agents;
DROP POLICY IF EXISTS "Allow all operations on production_campaigns" ON production_campaigns;
DROP POLICY IF EXISTS "Allow all operations on contacts" ON contacts;

CREATE POLICY "Allow all operations on progressive_agent_jobs" ON progressive_agent_jobs FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_contacts" ON progressive_agent_contacts FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_campaigns" ON progressive_agent_campaigns FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agents" ON progressive_agents FOR ALL USING (true);
CREATE POLICY "Allow all operations on production_campaigns" ON production_campaigns FOR ALL USING (true);
CREATE POLICY "Allow all operations on contacts" ON contacts FOR ALL USING (true);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
