-- ==================================================
-- COOGI PLATFORM - COMPATIBILITY-SAFE DATABASE SETUP
-- ==================================================
-- This script safely handles existing tables and mixed ID types
-- Run this in Supabase SQL Editor
-- ==================================================

-- ==================================================
-- STEP 1: CHECK EXISTING TABLES AND THEIR ID TYPES
-- ==================================================

DO $$
DECLARE
    agents_id_type TEXT;
    campaigns_id_type TEXT;
    leads_id_type TEXT;
BEGIN
    -- Check if agents table exists and get its ID type
    SELECT data_type INTO agents_id_type
    FROM information_schema.columns 
    WHERE table_name = 'agents' AND column_name = 'id';
    
    -- Check if campaigns table exists and get its ID type
    SELECT data_type INTO campaigns_id_type
    FROM information_schema.columns 
    WHERE table_name = 'campaigns' AND column_name = 'id';
    
    -- Check if leads table exists and get its ID type
    SELECT data_type INTO leads_id_type
    FROM information_schema.columns 
    WHERE table_name = 'leads' AND column_name = 'id';
    
    RAISE NOTICE 'Existing table ID types:';
    RAISE NOTICE 'Agents ID type: %', COALESCE(agents_id_type, 'TABLE DOES NOT EXIST');
    RAISE NOTICE 'Campaigns ID type: %', COALESCE(campaigns_id_type, 'TABLE DOES NOT EXIST');
    RAISE NOTICE 'Leads ID type: %', COALESCE(leads_id_type, 'TABLE DOES NOT EXIST');
END $$;

-- ==================================================
-- STEP 2: DROP PROBLEMATIC FOREIGN KEY CONSTRAINTS
-- ==================================================

DO $$ 
BEGIN
    -- Drop all existing foreign key constraints that might conflict
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'leads_agent_id_fkey') THEN
        ALTER TABLE leads DROP CONSTRAINT leads_agent_id_fkey;
        RAISE NOTICE 'Dropped leads_agent_id_fkey constraint';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'leads_campaign_id_fkey') THEN
        ALTER TABLE leads DROP CONSTRAINT leads_campaign_id_fkey;
        RAISE NOTICE 'Dropped leads_campaign_id_fkey constraint';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'campaigns_agent_id_fkey') THEN
        ALTER TABLE campaigns DROP CONSTRAINT campaigns_agent_id_fkey;
        RAISE NOTICE 'Dropped campaigns_agent_id_fkey constraint';
    END IF;
    
    -- Drop any other conflicting constraints
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'email_logs_campaign_id_fkey') THEN
        ALTER TABLE email_logs DROP CONSTRAINT email_logs_campaign_id_fkey;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'email_logs_lead_id_fkey') THEN
        ALTER TABLE email_logs DROP CONSTRAINT email_logs_lead_id_fkey;
    END IF;
END $$;

-- ==================================================
-- STEP 3: ENABLE REQUIRED EXTENSIONS
-- ==================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================================================
-- STEP 4: CREATE TABLES CONDITIONALLY BASED ON EXISTING TYPES
-- ==================================================

-- User profiles table (always use UUID for new tables)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    company_name VARCHAR(255),
    company_size VARCHAR(100),
    job_title VARCHAR(255),
    phone VARCHAR(50),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    credits_used INTEGER DEFAULT 0,
    credits_limit INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create agents table with proper ID type handling
DO $$
DECLARE
    existing_agents_id_type TEXT;
BEGIN
    -- Check existing agents table ID type
    SELECT data_type INTO existing_agents_id_type
    FROM information_schema.columns 
    WHERE table_name = 'agents' AND column_name = 'id';
    
    IF existing_agents_id_type IS NULL THEN
        -- Table doesn't exist, create with UUID
        CREATE TABLE agents (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            query TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'created',
            total_jobs_found INTEGER DEFAULT 0,
            total_emails_found INTEGER DEFAULT 0,
            hours_old INTEGER DEFAULT 720,
            custom_tags JSONB DEFAULT '[]'::jsonb,
            search_filters JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        RAISE NOTICE 'Created new agents table with UUID IDs';
    ELSE
        RAISE NOTICE 'Agents table already exists with % IDs - keeping existing structure', existing_agents_id_type;
        
        -- Add missing columns if they don't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'agents' AND column_name = 'user_id') THEN
            ALTER TABLE agents ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'agents' AND column_name = 'custom_tags') THEN
            ALTER TABLE agents ADD COLUMN custom_tags JSONB DEFAULT '[]'::jsonb;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'agents' AND column_name = 'search_filters') THEN
            ALTER TABLE agents ADD COLUMN search_filters JSONB DEFAULT '{}'::jsonb;
        END IF;
    END IF;
END $$;

-- Create campaigns table with proper ID type handling
DO $$
DECLARE
    existing_campaigns_id_type TEXT;
    existing_agents_id_type TEXT;
BEGIN
    -- Check existing table ID types
    SELECT data_type INTO existing_campaigns_id_type
    FROM information_schema.columns 
    WHERE table_name = 'campaigns' AND column_name = 'id';
    
    SELECT data_type INTO existing_agents_id_type
    FROM information_schema.columns 
    WHERE table_name = 'agents' AND column_name = 'id';
    
    IF existing_campaigns_id_type IS NULL THEN
        -- Table doesn't exist, create with matching agent ID type
        IF existing_agents_id_type = 'bigint' THEN
            CREATE TABLE campaigns (
                id BIGSERIAL PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
                agent_id BIGINT REFERENCES agents(id) ON DELETE SET NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'draft',
                email_template TEXT,
                leads_count INTEGER DEFAULT 0,
                emails_sent INTEGER DEFAULT 0,
                open_rate DECIMAL(5,2) DEFAULT 0.0,
                reply_rate DECIMAL(5,2) DEFAULT 0.0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            RAISE NOTICE 'Created campaigns table with BIGINT IDs to match agents';
        ELSE
            CREATE TABLE campaigns (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
                agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'draft',
                email_template TEXT,
                leads_count INTEGER DEFAULT 0,
                emails_sent INTEGER DEFAULT 0,
                open_rate DECIMAL(5,2) DEFAULT 0.0,
                reply_rate DECIMAL(5,2) DEFAULT 0.0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            RAISE NOTICE 'Created campaigns table with UUID IDs to match agents';
        END IF;
    ELSE
        RAISE NOTICE 'Campaigns table already exists with % IDs - keeping existing structure', existing_campaigns_id_type;
        
        -- Add missing columns if they don't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'campaigns' AND column_name = 'user_id') THEN
            ALTER TABLE campaigns ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- Create leads table with proper ID type handling
DO $$
DECLARE
    existing_leads_id_type TEXT;
    existing_agents_id_type TEXT;
    existing_campaigns_id_type TEXT;
BEGIN
    -- Check existing table ID types
    SELECT data_type INTO existing_leads_id_type
    FROM information_schema.columns 
    WHERE table_name = 'leads' AND column_name = 'id';
    
    SELECT data_type INTO existing_agents_id_type
    FROM information_schema.columns 
    WHERE table_name = 'agents' AND column_name = 'id';
    
    SELECT data_type INTO existing_campaigns_id_type
    FROM information_schema.columns 
    WHERE table_name = 'campaigns' AND column_name = 'id';
    
    IF existing_leads_id_type IS NULL THEN
        -- Table doesn't exist, create with matching types
        IF existing_agents_id_type = 'bigint' THEN
            CREATE TABLE leads (
                id BIGSERIAL PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
                agent_id BIGINT REFERENCES agents(id) ON DELETE SET NULL,
                campaign_id BIGINT REFERENCES campaigns(id) ON DELETE SET NULL,
                email VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                full_name VARCHAR(500),
                phone VARCHAR(50),
                linkedin_url TEXT,
                company_name VARCHAR(255),
                company_domain VARCHAR(255),
                company_size VARCHAR(100),
                company_industry VARCHAR(255),
                job_title VARCHAR(255),
                job_department VARCHAR(255),
                status VARCHAR(50) DEFAULT 'new',
                lead_score INTEGER DEFAULT 0,
                last_contacted TIMESTAMPTZ,
                job_url TEXT,
                job_posted_date TIMESTAMPTZ,
                job_description TEXT,
                job_requirements TEXT,
                city VARCHAR(255),
                state VARCHAR(100),
                country VARCHAR(100),
                location_string TEXT,
                tags TEXT[],
                notes TEXT,
                source VARCHAR(100),
                enrichment_status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            RAISE NOTICE 'Created leads table with BIGINT IDs to match existing tables';
        ELSE
            CREATE TABLE leads (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
                agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
                campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
                email VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                full_name VARCHAR(500),
                phone VARCHAR(50),
                linkedin_url TEXT,
                company_name VARCHAR(255),
                company_domain VARCHAR(255),
                company_size VARCHAR(100),
                company_industry VARCHAR(255),
                job_title VARCHAR(255),
                job_department VARCHAR(255),
                status VARCHAR(50) DEFAULT 'new',
                lead_score INTEGER DEFAULT 0,
                last_contacted TIMESTAMPTZ,
                job_url TEXT,
                job_posted_date TIMESTAMPTZ,
                job_description TEXT,
                job_requirements TEXT,
                city VARCHAR(255),
                state VARCHAR(100),
                country VARCHAR(100),
                location_string TEXT,
                tags TEXT[],
                notes TEXT,
                source VARCHAR(100),
                enrichment_status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            RAISE NOTICE 'Created leads table with UUID IDs to match existing tables';
        END IF;
    ELSE
        RAISE NOTICE 'Leads table already exists with % IDs - keeping existing structure', existing_leads_id_type;
        
        -- Add missing columns if they don't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'user_id') THEN
            ALTER TABLE leads ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- ==================================================
-- STEP 5: CREATE REMAINING TABLES (ALWAYS NEW, USE UUID)
-- ==================================================

-- Email logs table
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    campaign_id TEXT, -- Using TEXT to avoid type conflicts, will be converted later
    lead_id TEXT, -- Using TEXT to avoid type conflicts, will be converted later
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    content TEXT,
    email_type VARCHAR(50) DEFAULT 'outreach',
    status VARCHAR(50) DEFAULT 'sent',
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,
    message_id VARCHAR(255),
    delivery_status VARCHAR(50) DEFAULT 'sent',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SES templates table
CREATE TABLE IF NOT EXISTS ses_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    html_content TEXT,
    text_content TEXT,
    template_data JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SES campaigns table
CREATE TABLE IF NOT EXISTS ses_campaigns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES ses_templates(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    total_recipients INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    emails_delivered INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    scheduled_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API usage tracking table
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    api_name VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255),
    request_count INTEGER DEFAULT 1,
    cost DECIMAL(10,4) DEFAULT 0.0000,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscription usage table
CREATE TABLE IF NOT EXISTS subscription_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    usage_type VARCHAR(50) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    quota_limit INTEGER DEFAULT 0,
    reset_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Admin logs table
CREATE TABLE IF NOT EXISTS admin_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    level VARCHAR(20) NOT NULL,
    category VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Prompt templates table
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    template TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inbox messages table
CREATE TABLE IF NOT EXISTS inbox_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    message_id VARCHAR(255) UNIQUE,
    thread_id VARCHAR(255),
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    content TEXT,
    auto_tags TEXT[],
    sentiment VARCHAR(50),
    intent VARCHAR(100),
    priority INTEGER DEFAULT 3,
    confidence_score DECIMAL(3,2),
    status VARCHAR(50) DEFAULT 'unread',
    is_processed BOOLEAN DEFAULT false,
    requires_human_review BOOLEAN DEFAULT false,
    suggested_replies JSONB DEFAULT '[]'::jsonb,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Activity logs table
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    entity_type VARCHAR(50),
    entity_id TEXT, -- Using TEXT to store any ID type
    metadata JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================================================
-- STEP 6: CREATE BASIC INDEXES (SKIP PROBLEMATIC ONES)
-- ==================================================

-- Safe indexes that don't depend on foreign keys
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_company_name ON leads(company_name);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_admin_logs_timestamp ON admin_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_admin_logs_level ON admin_logs(level);

-- ==================================================
-- STEP 7: INSERT DEFAULT DATA
-- ==================================================

INSERT INTO prompt_templates (name, description, category, template, variables) VALUES
('Default Email Outreach', 'Standard email template for job outreach', 'email', 
'Subject: {{job_title}} Opportunity at {{company_name}}

Hi {{first_name}},

I hope this email finds you well. I''m reaching out regarding the {{job_title}} position at {{company_name}}.

{{custom_message}}

I''d love to discuss how my experience could contribute to your team''s success.

Best regards,
{{sender_name}}', 
'["job_title", "company_name", "first_name", "custom_message", "sender_name"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- ==================================================
-- SUCCESS MESSAGE
-- ==================================================

DO $$
BEGIN
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'COOGI DATABASE SETUP COMPLETE!';
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'All tables have been created successfully.';
    RAISE NOTICE 'Existing table structures have been preserved.';
    RAISE NOTICE 'Foreign key conflicts have been avoided.';
    RAISE NOTICE 'Your Coogi platform is ready to use!';
    RAISE NOTICE '===============================================';
END $$;
