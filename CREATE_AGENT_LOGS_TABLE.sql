-- ========================================
-- SUPABASE AGENT_LOGS TABLE CREATION
-- Run this SQL in your Supabase Dashboard
-- ========================================

-- Create the agent_logs table for real-time logging
CREATE TABLE IF NOT EXISTS public.agent_logs (
    id SERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    message TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'info', -- 'info', 'warning', 'error', 'success'
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agent_logs_batch_id ON public.agent_logs(batch_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON public.agent_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_logs_level ON public.agent_logs(level);

-- Enable Row Level Security (RLS) if needed
ALTER TABLE public.agent_logs ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow authenticated users to insert/select
CREATE POLICY IF NOT EXISTS "Allow authenticated users to manage agent_logs" 
ON public.agent_logs 
FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

-- Grant permissions to the service role
GRANT ALL ON public.agent_logs TO service_role;
GRANT ALL ON public.agent_logs TO anon;

-- Grant usage on the sequence
GRANT USAGE, SELECT ON SEQUENCE public.agent_logs_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.agent_logs_id_seq TO anon;
