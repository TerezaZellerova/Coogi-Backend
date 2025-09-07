-- Create agent_logs table for backend logging
CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    message TEXT NOT NULL,
    level TEXT DEFAULT 'info',
    company TEXT,
    job_title TEXT,
    job_url TEXT,
    processing_stage TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_agent_logs_batch_id ON agent_logs(batch_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created_at ON agent_logs(created_at);

-- Enable RLS
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Create policy (allow all for development)
DROP POLICY IF EXISTS "Allow all operations on agent_logs" ON agent_logs;
CREATE POLICY "Allow all operations on agent_logs" ON agent_logs FOR ALL USING (true);

-- Grant permissions
GRANT ALL ON agent_logs TO anon, authenticated, service_role;
GRANT ALL ON SEQUENCE agent_logs_id_seq TO anon, authenticated, service_role;
