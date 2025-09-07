-- 🔧 ADMIN PANEL & LOGGING TEMPLATES
-- User management and system logging for Coogi
-- Run this THIRD after main schema and email system
-- Updated: September 6, 2025

-- ============================================================
-- USER MANAGEMENT TABLES
-- ============================================================

-- Admin users table
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, -- Hashed password
    name TEXT NOT NULL,
    role TEXT DEFAULT 'user', -- user, admin, super_admin
    status TEXT DEFAULT 'active', -- active, inactive, suspended
    permissions JSONB DEFAULT '{}', -- JSON object with permissions
    last_login TIMESTAMPTZ,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL REFERENCES admin_users(user_id) ON DELETE CASCADE,
    ip_address TEXT,
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SYSTEM LOGGING TABLES
-- ============================================================

-- Activity logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    log_id TEXT UNIQUE NOT NULL,
    user_id TEXT, -- Can be null for system actions
    action TEXT NOT NULL, -- login, logout, create_agent, run_campaign, etc.
    resource_type TEXT, -- agent, campaign, user, etc.
    resource_id TEXT, -- ID of the resource being acted upon
    details JSONB DEFAULT '{}', -- Additional context
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- System error logs
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    error_id TEXT UNIQUE NOT NULL,
    user_id TEXT, -- Can be null for system errors
    error_type TEXT NOT NULL, -- database, api, authentication, etc.
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    request_data JSONB DEFAULT '{}',
    response_data JSONB DEFAULT '{}',
    severity TEXT DEFAULT 'error', -- info, warning, error, critical
    resolved BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Email templates for notifications
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,
    template_type TEXT NOT NULL, -- welcome, password_reset, campaign_complete, etc.
    variables JSONB DEFAULT '{}', -- Template variables like {{user_name}}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Admin users indexes
CREATE INDEX IF NOT EXISTS idx_admin_users_user_id ON admin_users(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);
CREATE INDEX IF NOT EXISTS idx_admin_users_status ON admin_users(status);

-- User sessions indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Activity logs indexes
CREATE INDEX IF NOT EXISTS idx_activity_logs_log_id ON activity_logs(log_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);

-- Error logs indexes
CREATE INDEX IF NOT EXISTS idx_error_logs_error_id ON error_logs(error_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_user_id ON error_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_error_type ON error_logs(error_type);
CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs(severity);
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp);

-- Email templates indexes
CREATE INDEX IF NOT EXISTS idx_email_templates_template_id ON email_templates(template_id);
CREATE INDEX IF NOT EXISTS idx_email_templates_template_type ON email_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_email_templates_is_active ON email_templates(is_active);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Enable RLS
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow all operations on admin_users" ON admin_users FOR ALL USING (true);
CREATE POLICY "Allow all operations on user_sessions" ON user_sessions FOR ALL USING (true);
CREATE POLICY "Allow all operations on activity_logs" ON activity_logs FOR ALL USING (true);
CREATE POLICY "Allow all operations on error_logs" ON error_logs FOR ALL USING (true);
CREATE POLICY "Allow all operations on email_templates" ON email_templates FOR ALL USING (true);

-- Grant permissions
GRANT ALL ON admin_users TO anon, authenticated, service_role;
GRANT ALL ON user_sessions TO anon, authenticated, service_role;
GRANT ALL ON activity_logs TO anon, authenticated, service_role;
GRANT ALL ON error_logs TO anon, authenticated, service_role;
GRANT ALL ON email_templates TO anon, authenticated, service_role;

GRANT ALL ON SEQUENCE admin_users_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE user_sessions_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE activity_logs_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE error_logs_id_seq TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE email_templates_id_seq TO anon, authenticated, service_role;

-- ============================================================
-- TEST DATA
-- ============================================================

-- Insert default admin user (change password in production!)
INSERT INTO admin_users (user_id, email, password_hash, name, role, permissions) VALUES 
('admin_001', 'admin@coogi.ai', '$2b$12$example_hash_change_in_production', 'Coogi Admin', 'super_admin', 
 '{"unlimited_agents": true, "unlimited_searches": true, "access_all_features": true}'::jsonb);

-- Insert default email templates
INSERT INTO email_templates (template_id, name, subject, body_html, template_type) VALUES 
('welcome_001', 'Welcome Email', 'Welcome to Coogi!', '<h1>Welcome {{user_name}}!</h1><p>Your account is ready.</p>', 'welcome'),
('campaign_complete_001', 'Campaign Complete', 'Your campaign "{{campaign_name}}" is complete', '<h1>Campaign Complete!</h1><p>{{sent_count}} emails sent with {{open_rate}}% open rate.</p>', 'campaign_complete');

-- Success message
SELECT '✅ ADMIN PANEL & LOGGING SYSTEM CREATED!' as status;
SELECT 'User management and logging tables ready!' as message;
