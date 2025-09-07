-- Enhanced Email Processing Database Schema
-- Complete tables for production email system

-- Email accounts configuration
CREATE TABLE IF NOT EXISTS email_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL DEFAULT 'gmail',
    display_name VARCHAR(255),
    credentials_encrypted TEXT, -- Encrypted OAuth credentials
    is_active BOOLEAN DEFAULT true,
    auto_reply_enabled BOOLEAN DEFAULT true,
    last_fetch_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enhanced inbox messages table
DROP TABLE IF EXISTS inbox_messages CASCADE;
CREATE TABLE inbox_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id VARCHAR(255) NOT NULL UNIQUE, -- Gmail message ID
    user_email VARCHAR(255) NOT NULL REFERENCES email_accounts(email),
    thread_id VARCHAR(255), -- Gmail thread ID
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject TEXT,
    body TEXT,
    received_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,
    
    -- GPT Analysis Results
    category VARCHAR(50), -- job_inquiry, interview_request, etc.
    confidence DECIMAL(3,2), -- 0.00 to 1.00
    tags TEXT[], -- Array of tags
    sentiment VARCHAR(20), -- positive, negative, neutral
    priority VARCHAR(20), -- low, medium, high, urgent
    key_points TEXT[], -- Key points extracted by GPT
    
    -- Processing Status
    is_processed BOOLEAN DEFAULT false,
    requires_review BOOLEAN DEFAULT false,
    is_read BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    
    -- Metadata
    provider VARCHAR(50) DEFAULT 'gmail',
    raw_data JSONB, -- Original email data from provider
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-replies log
CREATE TABLE IF NOT EXISTS inbox_auto_replies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id VARCHAR(255) NOT NULL REFERENCES inbox_messages(email_id),
    recipient VARCHAR(255) NOT NULL,
    reply_content TEXT NOT NULL,
    category VARCHAR(50),
    response_tone VARCHAR(20), -- professional, friendly, formal
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivery_status VARCHAR(20) DEFAULT 'sent', -- sent, failed, bounced
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email processing jobs queue
CREATE TABLE IF NOT EXISTS email_processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL, -- fetch, process, reply
    email_account VARCHAR(255) REFERENCES email_accounts(email),
    email_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    priority INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email templates for auto-replies
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    variables TEXT[], -- Available template variables
    tone VARCHAR(20) DEFAULT 'professional',
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_inbox_messages_user_email ON inbox_messages(user_email);
CREATE INDEX IF NOT EXISTS idx_inbox_messages_received_at ON inbox_messages(received_at);
CREATE INDEX IF NOT EXISTS idx_inbox_messages_category ON inbox_messages(category);
CREATE INDEX IF NOT EXISTS idx_inbox_messages_is_processed ON inbox_messages(is_processed);
CREATE INDEX IF NOT EXISTS idx_inbox_messages_requires_review ON inbox_messages(requires_review);
CREATE INDEX IF NOT EXISTS idx_inbox_messages_thread_id ON inbox_messages(thread_id);

CREATE INDEX IF NOT EXISTS idx_auto_replies_email_id ON inbox_auto_replies(email_id);
CREATE INDEX IF NOT EXISTS idx_auto_replies_sent_at ON inbox_auto_replies(sent_at);

CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON email_processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_scheduled_at ON email_processing_jobs(scheduled_at);

CREATE INDEX IF NOT EXISTS idx_email_accounts_user_id ON email_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_email_accounts_is_active ON email_accounts(is_active);

-- Insert default email templates
INSERT INTO email_templates (name, category, subject_template, body_template, variables, tone) VALUES
('Job Inquiry Response', 'job_inquiry', 'Re: {subject}', 
'Hi {sender_name},

Thank you for your interest in our job opportunities. We have received your inquiry and will review your background.

Our team will get back to you within 2-3 business days if your profile matches our current openings.

Best regards,
{company_name} Recruiting Team', 
ARRAY['sender_name', 'subject', 'company_name'], 'professional'),

('Interview Scheduling', 'interview_request', 'Re: {subject}', 
'Hi {sender_name},

Thank you for your interview request. We would be happy to schedule a conversation with you.

Please reply with your availability for the following time slots:
- Option 1: [Date/Time]
- Option 2: [Date/Time]
- Option 3: [Date/Time]

Looking forward to speaking with you.

Best regards,
{recruiter_name}', 
ARRAY['sender_name', 'subject', 'recruiter_name'], 'friendly'),

('Follow-up Acknowledgment', 'follow_up', 'Re: {subject}', 
'Hi {sender_name},

Thank you for following up on your application. We appreciate your continued interest.

We are still reviewing candidates and will update you on the next steps by {estimated_date}.

Best regards,
{company_name} Team', 
ARRAY['sender_name', 'subject', 'company_name', 'estimated_date'], 'professional'),

('Candidate Outreach', 'candidate_outreach', 'Exciting Career Opportunities - {company_name}', 
'Dear {candidate_first_name},

I hope this note finds you well. My name is Cole Chuck, and I represent Liac Group LLC, a recruitment agency dedicated to connecting talented professionals with rewarding opportunities across IT, administrative, and specialized fields.

We work closely with hiring managers at leading organizations, giving our candidates direct access to roles that may not be widely advertised. Whether you''re actively looking or just open to hearing about the right opportunity, we''d love to support your next career move.

What we offer candidates:
- Access to exclusive openings across top companies.
- A streamlined process—we advocate on your behalf to hiring managers.
- Guidance to ensure your skills and goals align with the right role.

If you''re interested in learning more, simply reply with your resume or availability for a quick call. Our goal is to make your job search easier, faster, and more rewarding.

Best regards,
Cole Chuck
Liac Group LLC', 
ARRAY['candidate_first_name', 'company_name'], 'professional'),

('Hiring Manager Outreach', 'hiring_manager_outreach', 'Partnership Opportunity - Liac Group LLC Recruitment Services', 
'Dear {hiring_manager_name},

I hope this message finds you well. I''m reaching out on behalf of Liac Group LLC, a recruitment agency dedicated to helping companies like yours meet staffing goals with speed, precision, and care.

We specialize in sourcing and placing qualified professionals across IT, administrative, and specialized roles, including niche areas such as veterinary staffing. Our process focuses on reducing time-to-hire while ensuring every candidate we present is thoroughly vetted and aligned with your team''s needs.

Whether you''re looking for contract, contract-to-hire, or permanent placements, we tailor our approach to fit your requirements. Our goal is to act as an extension of your HR team—delivering top candidates while allowing you to focus on what matters most: running your business.

I would love the opportunity to learn more about your current and upcoming hiring needs. If you''d like, we can schedule a quick call to discuss how Liac Group can support your recruitment efforts.

Best regards,
Cole Chuck
Liac Group LLC', 
ARRAY['hiring_manager_name'], 'professional')

ON CONFLICT DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_email_accounts_updated_at ON email_accounts;
DROP TRIGGER IF EXISTS update_inbox_messages_updated_at ON inbox_messages;
DROP TRIGGER IF EXISTS update_email_templates_updated_at ON email_templates;

CREATE TRIGGER update_email_accounts_updated_at BEFORE UPDATE ON email_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_inbox_messages_updated_at BEFORE UPDATE ON inbox_messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
