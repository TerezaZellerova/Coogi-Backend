-- Minimal Migration Script for Existing Supabase Databases
-- Run this if you already have some tables and just want to add missing ones

-- Check what tables exist
SELECT 'Checking existing tables...' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%progressive%' OR table_name LIKE '%production%';

-- Add missing columns to existing tables if they don't exist
DO $$
BEGIN
    -- Add missing columns to progressive_agent_jobs if table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'progressive_agent_jobs') THEN
        -- Add company_url if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agent_jobs' AND column_name = 'company_url') THEN
            ALTER TABLE progressive_agent_jobs ADD COLUMN company_url TEXT;
        END IF;
        
        -- Add skills if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agent_jobs' AND column_name = 'skills') THEN
            ALTER TABLE progressive_agent_jobs ADD COLUMN skills TEXT[];
        END IF;
        
        -- Add is_demo if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agent_jobs' AND column_name = 'is_demo') THEN
            ALTER TABLE progressive_agent_jobs ADD COLUMN is_demo BOOLEAN DEFAULT FALSE;
        END IF;
    END IF;

    -- Add missing columns to progressive_agent_contacts if table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'progressive_agent_contacts') THEN
        -- Add confidence_score if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agent_contacts' AND column_name = 'confidence_score') THEN
            ALTER TABLE progressive_agent_contacts ADD COLUMN confidence_score FLOAT;
        END IF;
        
        -- Add phone if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agent_contacts' AND column_name = 'phone') THEN
            ALTER TABLE progressive_agent_contacts ADD COLUMN phone TEXT;
        END IF;
    END IF;

    -- Add missing columns to progressive_agent_campaigns if table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'progressive_agent_campaigns') THEN
        -- Add updated_at if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agent_campaigns' AND column_name = 'updated_at') THEN
            ALTER TABLE progressive_agent_campaigns ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
        END IF;
        
        -- Add platform if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agent_campaigns' AND column_name = 'platform') THEN
            ALTER TABLE progressive_agent_campaigns ADD COLUMN platform TEXT DEFAULT 'Instantly';
        END IF;
    END IF;
END $$;

-- Create production_campaigns table if it doesn't exist (required by backend)
CREATE TABLE IF NOT EXISTS production_campaigns (
    id SERIAL PRIMARY KEY,
    agent_id TEXT NOT NULL,
    campaign_id TEXT UNIQUE,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'Email Campaign',
    status TEXT DEFAULT 'Ready',
    provider TEXT DEFAULT 'Instantly',
    subject TEXT,
    content TEXT,
    target_count INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    bounce_count INTEGER DEFAULT 0,
    unsubscribe_count INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create missing indexes
CREATE INDEX IF NOT EXISTS idx_production_campaigns_agent_id ON production_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_status ON production_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_provider ON production_campaigns(provider);
CREATE INDEX IF NOT EXISTS idx_production_campaigns_created_at ON production_campaigns(created_at);

-- Enable RLS and create policy for production_campaigns
ALTER TABLE production_campaigns ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all operations on production_campaigns" ON production_campaigns;
CREATE POLICY "Allow all operations on production_campaigns" ON production_campaigns FOR ALL USING (true);
GRANT ALL ON production_campaigns TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE production_campaigns_id_seq TO anon, authenticated, service_role;

-- Show final status
SELECT 'Migration completed successfully!' as status;
SELECT 'production_campaigns table created and configured!' as production_ready;
SELECT 'All missing columns added to existing tables!' as schema_updated;

-- Show what we have now
SELECT 
    'progressive_agents' as table_name,
    COUNT(*) as row_count
FROM progressive_agents
UNION ALL
SELECT 
    'progressive_agent_jobs' as table_name,
    COUNT(*) as row_count
FROM progressive_agent_jobs
UNION ALL
SELECT 
    'progressive_agent_contacts' as table_name,
    COUNT(*) as row_count
FROM progressive_agent_contacts
UNION ALL
SELECT 
    'progressive_agent_campaigns' as table_name,
    COUNT(*) as row_count
FROM progressive_agent_campaigns
UNION ALL
SELECT 
    'production_campaigns' as table_name,
    COUNT(*) as row_count
FROM production_campaigns;
