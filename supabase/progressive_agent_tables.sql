-- Progressive Agent Database Tables
-- Tables to store jobs, contacts, and campaigns from progressive agents

-- Create progressive_agent_jobs table
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

-- Create progressive_agent_contacts table
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

-- Create progressive_agent_campaigns table
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

-- Create progressive_agents table to track agent metadata
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_agent_id ON progressive_agent_jobs(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_company ON progressive_agent_jobs(company);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_site ON progressive_agent_jobs(site);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_jobs_created_at ON progressive_agent_jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_agent_id ON progressive_agent_contacts(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_company ON progressive_agent_contacts(company);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_verified ON progressive_agent_contacts(verified);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_contacts_created_at ON progressive_agent_contacts(created_at);

CREATE INDEX IF NOT EXISTS idx_progressive_agent_campaigns_agent_id ON progressive_agent_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_campaigns_status ON progressive_agent_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_progressive_agent_campaigns_created_at ON progressive_agent_campaigns(created_at);

CREATE INDEX IF NOT EXISTS idx_progressive_agents_agent_id ON progressive_agents(agent_id);
CREATE INDEX IF NOT EXISTS idx_progressive_agents_status ON progressive_agents(status);
CREATE INDEX IF NOT EXISTS idx_progressive_agents_created_at ON progressive_agents(created_at);

-- Enable Row Level Security
ALTER TABLE progressive_agent_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agent_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_agents ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed for production)
CREATE POLICY "Allow all operations on progressive_agent_jobs" ON progressive_agent_jobs FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_contacts" ON progressive_agent_contacts FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agent_campaigns" ON progressive_agent_campaigns FOR ALL USING (true);
CREATE POLICY "Allow all operations on progressive_agents" ON progressive_agents FOR ALL USING (true);
