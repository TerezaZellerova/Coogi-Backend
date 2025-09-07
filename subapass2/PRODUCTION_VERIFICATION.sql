-- 🔍 COMPREHENSIVE PRODUCTION VERIFICATION QUERIES
-- Run these in Supabase SQL Editor to verify 100% production readiness

-- ============================================================
-- 1. CHECK ALL REQUIRED TABLES EXIST
-- ============================================================
SELECT 'STEP 1: Table Existence Check' as verification_step;

SELECT 
    table_name,
    CASE WHEN table_name IN (
        'progressive_agents', 'progressive_agent_jobs', 'progressive_agent_contacts', 
        'progressive_agent_campaigns', 'production_campaigns', 'contacts',
        'ses_email_lists', 'ses_email_contacts', 'admin_users', 'email_templates'
    ) THEN '✅ EXISTS' ELSE '❌ MISSING' END as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN (
        'progressive_agents', 'progressive_agent_jobs', 'progressive_agent_contacts',
        'progressive_agent_campaigns', 'production_campaigns', 'contacts',
        'ses_email_lists', 'ses_email_contacts', 'admin_users', 'email_templates'
    )
ORDER BY table_name;

-- ============================================================
-- 2. VERIFY PRODUCTION_CAMPAIGNS TABLE STRUCTURE
-- ============================================================
SELECT 'STEP 2: Production Campaigns Table Structure' as verification_step;

SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'production_campaigns' 
    AND table_schema = 'public'
ORDER BY ordinal_position;

-- ============================================================
-- 3. CHECK CRITICAL FIELDS FOR FRONTEND/BACKEND COMPATIBILITY
-- ============================================================
SELECT 'STEP 3: Critical Field Verification' as verification_step;

-- Check if production_campaigns has all required fields
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'campaign_id') THEN '✅' ELSE '❌' END as campaign_id,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'agent_id') THEN '✅' ELSE '❌' END as agent_id,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'name') THEN '✅' ELSE '❌' END as name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'status') THEN '✅' ELSE '❌' END as status,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'platform') THEN '✅' ELSE '❌' END as platform,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'subject_line') THEN '✅' ELSE '❌' END as subject_line,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'from_email') THEN '✅' ELSE '❌' END as from_email,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'email_sequence') THEN '✅' ELSE '❌' END as email_sequence,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'verified_contacts') THEN '✅' ELSE '❌' END as verified_contacts,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'sent_count') THEN '✅' ELSE '❌' END as sent_count,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'open_count') THEN '✅' ELSE '❌' END as open_count,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'production_campaigns' AND column_name = 'reply_count') THEN '✅' ELSE '❌' END as reply_count;

-- ============================================================
-- 4. CHECK PROGRESSIVE AGENTS TABLE COMPATIBILITY
-- ============================================================
SELECT 'STEP 4: Progressive Agents Compatibility' as verification_step;

SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agents' AND column_name = 'agent_id') THEN '✅' ELSE '❌' END as agent_id,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agents' AND column_name = 'query') THEN '✅' ELSE '❌' END as query,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agents' AND column_name = 'status') THEN '✅' ELSE '❌' END as status,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agents' AND column_name = 'total_jobs') THEN '✅' ELSE '❌' END as total_jobs,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agents' AND column_name = 'total_contacts') THEN '✅' ELSE '❌' END as total_contacts,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'progressive_agents' AND column_name = 'total_campaigns') THEN '✅' ELSE '❌' END as total_campaigns;

-- ============================================================
-- 5. VERIFY INDEXES EXIST
-- ============================================================
SELECT 'STEP 5: Index Verification' as verification_step;

SELECT 
    indexname,
    tablename,
    CASE WHEN indexname LIKE 'idx_%' THEN '✅ CUSTOM INDEX' ELSE '🔍 DEFAULT INDEX' END as index_status
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND tablename IN ('progressive_agents', 'production_campaigns', 'contacts', 'progressive_agent_jobs')
ORDER BY tablename, indexname;

-- ============================================================
-- 6. CHECK ROW LEVEL SECURITY
-- ============================================================
SELECT 'STEP 6: Security Policy Verification' as verification_step;

SELECT 
    tablename,
    policyname,
    CASE WHEN policyname IS NOT NULL THEN '✅ SECURED' ELSE '❌ NO POLICIES' END as security_status
FROM pg_policies 
WHERE schemaname = 'public' 
    AND tablename IN ('progressive_agents', 'production_campaigns', 'contacts')
ORDER BY tablename;

-- ============================================================
-- 7. TEST DATA VALIDATION
-- ============================================================
SELECT 'STEP 7: Test Data Validation' as verification_step;

-- Check test data structure
SELECT 
    'Test Agent' as data_type,
    agent_id,
    query,
    status,
    total_jobs,
    total_contacts,
    total_campaigns
FROM progressive_agents 
WHERE agent_id = 'production-test-agent';

SELECT 
    'Test Campaign' as data_type,
    campaign_id,
    name,
    status,
    platform,
    subject_line,
    target_count,
    LENGTH(email_sequence::text) as email_sequence_length
FROM production_campaigns 
WHERE agent_id = 'production-test-agent';

-- ============================================================
-- 8. FRONTEND API COMPATIBILITY CHECK
-- ============================================================
SELECT 'STEP 8: Frontend API Compatibility' as verification_step;

-- Test query that frontend will use
SELECT 
    pa.agent_id as id,
    pa.query,
    pa.status,
    pa.created_at,
    pa.updated_at,
    pa.total_jobs as total_jobs_found,
    pa.total_contacts as total_emails_found,
    pa.hours_old,
    pa.total_progress
FROM progressive_agents pa
WHERE pa.agent_id = 'production-test-agent';

-- Test campaign query that frontend will use
SELECT 
    pc.campaign_id as id,
    pc.name,
    pc.status,
    pc.platform,
    pc.subject_line,
    pc.from_email,
    pc.from_name,
    pc.email_sequence,
    pc.target_count,
    pc.verified_contacts,
    pc.sent_count,
    pc.open_count,
    pc.reply_count,
    pc.open_rate,
    pc.reply_rate,
    pc.created_at,
    pc.updated_at,
    pc.agent_id
FROM production_campaigns pc
WHERE pc.agent_id = 'production-test-agent';

-- ============================================================
-- 9. FINAL PRODUCTION READINESS SCORE
-- ============================================================
SELECT 'STEP 9: Production Readiness Summary' as verification_step;

WITH readiness_check AS (
    SELECT 
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('progressive_agents', 'production_campaigns', 'contacts')) as core_tables,
        (SELECT COUNT(*) FROM progressive_agents WHERE agent_id = 'production-test-agent') as test_data,
        (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%') as custom_indexes,
        (SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public') as security_policies
)
SELECT 
    CASE WHEN core_tables >= 3 THEN '✅' ELSE '❌' END as core_tables_status,
    CASE WHEN test_data >= 1 THEN '✅' ELSE '❌' END as test_data_status,
    CASE WHEN custom_indexes >= 5 THEN '✅' ELSE '❌' END as indexes_status,
    CASE WHEN security_policies >= 5 THEN '✅' ELSE '❌' END as security_status,
    CASE 
        WHEN core_tables >= 3 AND test_data >= 1 AND custom_indexes >= 5 AND security_policies >= 5 
        THEN '🎉 100% PRODUCTION READY! 🎉' 
        ELSE '⚠️ NEEDS ATTENTION ⚠️' 
    END as overall_status
FROM readiness_check;

-- SUCCESS MESSAGE
SELECT '✅ VERIFICATION COMPLETE - CHECK RESULTS ABOVE ✅' as final_message;
