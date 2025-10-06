-- Database Optimization Script for Quiz Website
-- Run this script to add indexes and optimize database performance

-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_admin ON users(is_admin);

-- Quiz sessions indexes
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_completed ON quiz_sessions(completed_at) WHERE completed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_started ON quiz_sessions(started_at);

-- AWS questions indexes
CREATE INDEX IF NOT EXISTS idx_aws_questions_random ON aws_questions(random()) WHERE id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_aws_questions_multiselect ON aws_questions(is_multiselect);

-- User performance summary indexes
CREATE INDEX IF NOT EXISTS idx_user_perf_user_id ON user_performance_summary(user_id);
CREATE INDEX IF NOT EXISTS idx_user_perf_updated ON user_performance_summary(updated_at);

-- User activity indexes (if table exists)
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_activity_action ON user_activity(action_type);

-- Password reset tokens indexes (if table exists)
CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_expires ON password_reset_tokens(expires_at);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_completed ON quiz_sessions(user_id, completed_at) WHERE completed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active);

-- Analyze tables for better query planning
ANALYZE users;
ANALYZE quiz_sessions;
ANALYZE aws_questions;
ANALYZE user_performance_summary;

-- Optional: Update table statistics
-- VACUUM ANALYZE users;
-- VACUUM ANALYZE quiz_sessions;
-- VACUUM ANALYZE aws_questions;