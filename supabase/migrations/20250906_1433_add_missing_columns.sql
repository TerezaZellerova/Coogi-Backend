-- Add missing columns to progressive_agents table
ALTER TABLE progressive_agents ADD COLUMN IF NOT EXISTS company_size TEXT DEFAULT 'all';
ALTER TABLE progressive_agents ADD COLUMN IF NOT EXISTS target_type TEXT DEFAULT 'hiring_managers';
ALTER TABLE progressive_agents ADD COLUMN IF NOT EXISTS location_filter TEXT;

-- Add missing columns that the backend expects
ALTER TABLE progressive_agents ADD COLUMN IF NOT EXISTS staged_results JSONB DEFAULT '{}'::jsonb;
ALTER TABLE progressive_agents ADD COLUMN IF NOT EXISTS stages JSONB DEFAULT '{}'::jsonb;
ALTER TABLE progressive_agents ADD COLUMN IF NOT EXISTS final_stats JSONB DEFAULT '{}'::jsonb;
