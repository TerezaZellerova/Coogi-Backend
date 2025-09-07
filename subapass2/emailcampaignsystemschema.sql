-- Fix Campaign Tables - Handle Existing Schema Conflicts
-- This script fixes the foreign key type mismatch and ensures clean schema

-- First, drop existing tables in correct order (foreign keys first)
DROP TABLE IF EXISTS campaign_sequences CASCADE;
DROP TABLE IF EXISTS email_events CASCADE;
DROP TABLE IF EXISTS campaign_messages CASCADE;
DROP TABLE IF EXISTS campaign_targets CASCADE;
DROP TABLE IF EXISTS suppression_list CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;

-- Now create clean schema with UUID primary keys
-- Main campaigns table
CREATE TABLE campaigns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    from_email TEXT NOT NULL, -- e.g., noreply@liacgroupllc.com (SES verified)
    from_name TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft|scheduled|sending|paused|completed|failed
    send_strategy VARCHAR(20) NOT NULL DEFAULT 'immediate', -- immediate|scheduled|sequenced
    scheduled_at TIMESTAMPTZ NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaign targets (leads/emails to send to)
CREATE TABLE campaign_targets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    lead_id UUID NULL, -- FK to leads table if exists
    email TEXT NOT NULL,
    name TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending|queued|sent|bounced|complained|unsubscribed|replied|failed
    last_sent_at TIMESTAMPTZ NULL,
    message_id TEXT NULL, -- SES MessageId
    thread_token UUID DEFAULT gen_random_uuid(), -- used to correlate replies
    opens_count INTEGER DEFAULT 0,
    replies_count INTEGER DEFAULT 0,
    fail_reason TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, email)
);

-- Individual campaign messages (tracks each email sent)
CREATE TABLE campaign_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES campaign_targets(id) ON DELETE CASCADE,
    stage INTEGER DEFAULT 1, -- 1=initial, 2=follow-up1, etc.
    subject TEXT NOT NULL,
    html TEXT NOT NULL,
    text TEXT NOT NULL,
    message_id TEXT NOT NULL, -- SES MessageId
    sent_at TIMESTAMPTZ NOT NULL,
    delivery_status VARCHAR(20) DEFAULT 'accepted', -- accepted|rejected|bounced|complained|delivered|unknown
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email events (immutable append-only log)
CREATE TABLE email_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID NULL REFERENCES campaigns(id),
    target_id UUID NULL REFERENCES campaign_targets(id),
    message_id TEXT NOT NULL,
    type VARCHAR(20) NOT NULL, -- sent|open|reply|bounce|complaint|delivery|unsubscribe
    payload JSONB DEFAULT '{}'::jsonb, -- raw SNS/SES/inbound payload
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Global suppression list
CREATE TABLE suppression_list (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    reason VARCHAR(20) NOT NULL, -- unsubscribe|bounce|complaint|manual
    note TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaign sequences for follow-ups (optional but recommended)
CREATE TABLE campaign_sequences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    stage INTEGER NOT NULL, -- 1, 2, 3, etc.
    delay_hours INTEGER NOT NULL, -- hours to wait after previous stage
    subject TEXT NOT NULL,
    html TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, stage)
);

-- Indexes for performance
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_by ON campaigns(created_by);
CREATE INDEX idx_campaigns_scheduled_at ON campaigns(scheduled_at);

CREATE INDEX idx_campaign_targets_campaign_id ON campaign_targets(campaign_id);
CREATE INDEX idx_campaign_targets_status ON campaign_targets(status);
CREATE INDEX idx_campaign_targets_email ON campaign_targets(email);
CREATE INDEX idx_campaign_targets_last_sent_at ON campaign_targets(last_sent_at);
CREATE INDEX idx_campaign_targets_thread_token ON campaign_targets(thread_token);

CREATE INDEX idx_campaign_messages_campaign_id ON campaign_messages(campaign_id);
CREATE INDEX idx_campaign_messages_target_id ON campaign_messages(target_id);
CREATE INDEX idx_campaign_messages_message_id ON campaign_messages(message_id);
CREATE INDEX idx_campaign_messages_sent_at ON campaign_messages(sent_at);

CREATE INDEX idx_email_events_campaign_id ON email_events(campaign_id);
CREATE INDEX idx_email_events_target_id ON email_events(target_id);
CREATE INDEX idx_email_events_message_id ON email_events(message_id);
CREATE INDEX idx_email_events_type ON email_events(type);
CREATE INDEX idx_email_events_created_at ON email_events(created_at);

CREATE INDEX idx_suppression_list_email ON suppression_list(email);
CREATE INDEX idx_suppression_list_reason ON suppression_list(reason);

CREATE INDEX idx_campaign_sequences_campaign_id ON campaign_sequences(campaign_id);
CREATE INDEX idx_campaign_sequences_stage ON campaign_sequences(stage);

-- Add some initial test data to verify the schema works
INSERT INTO campaigns (name, subject, from_email, from_name, created_by) VALUES 
(
    'Test Campaign', 
    'Test Email Subject', 
    'noreply@liacgroupllc.com', 
    'COOGI Team', 
    gen_random_uuid()
);

-- Comments for documentation
COMMENT ON TABLE campaigns IS 'Email campaigns with SES integration';
COMMENT ON TABLE campaign_targets IS 'Individual email targets for campaigns';
COMMENT ON TABLE campaign_messages IS 'Actual messages sent via SES';
COMMENT ON TABLE email_events IS 'Immutable log of all email events (opens, clicks, bounces, etc.)';
COMMENT ON TABLE suppression_list IS 'Global email suppression list (unsubscribes, bounces, complaints)';
COMMENT ON TABLE campaign_sequences IS 'Multi-stage follow-up sequences';

-- Verify tables created successfully
SELECT 'campaigns' as table_name, COUNT(*) as row_count FROM campaigns
UNION ALL
SELECT 'campaign_targets', COUNT(*) FROM campaign_targets
UNION ALL
SELECT 'campaign_messages', COUNT(*) FROM campaign_messages
UNION ALL
SELECT 'email_events', COUNT(*) FROM email_events
UNION ALL
SELECT 'suppression_list', COUNT(*) FROM suppression_list
UNION ALL
SELECT 'campaign_sequences', COUNT(*) FROM campaign_sequences;
