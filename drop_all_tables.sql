-- Drop all tables manually to clean the database
-- Run with: PGPASSWORD=changethis psql -h localhost -U anvil -d anvil_db -f drop_all_tables.sql

-- Disable all foreign key checks temporarily
SET session_replication_role = replica;

-- Drop all legacy LLM tables
DROP TABLE IF EXISTS llm_providers CASCADE;
DROP TABLE IF EXISTS llm_cost_daily CASCADE;
DROP TABLE IF EXISTS circuit_breakers CASCADE;
DROP TABLE IF EXISTS user_chat_preferences CASCADE;
DROP TABLE IF EXISTS conversation_exports CASCADE;
DROP TABLE IF EXISTS llm_cost_budgets CASCADE;
DROP TABLE IF EXISTS conversation_templates CASCADE;
DROP TABLE IF EXISTS agent_performance_metrics CASCADE;
DROP TABLE IF EXISTS analytics_snapshots CASCADE;
DROP TABLE IF EXISTS llm_business_config CASCADE;
DROP TABLE IF EXISTS agent_debates CASCADE;
DROP TABLE IF EXISTS llm_request_attempts CASCADE;
DROP TABLE IF EXISTS agent_model_rankings CASCADE;
DROP TABLE IF EXISTS llm_requests CASCADE;
DROP TABLE IF EXISTS llm_response_cache CASCADE;
DROP TABLE IF EXISTS llm_audit_log CASCADE;
DROP TABLE IF EXISTS custom_agent_configs CASCADE;
DROP TABLE IF EXISTS ranking_weight_profiles CASCADE;
DROP TABLE IF EXISTS llm_models CASCADE;
DROP TABLE IF EXISTS ranking_overrides CASCADE;
DROP TABLE IF EXISTS template_executions CASCADE;
DROP TABLE IF EXISTS distillation_telemetry CASCADE;
DROP TABLE IF EXISTS llm_budget_alerts CASCADE;
DROP TABLE IF EXISTS voting_rounds CASCADE;
DROP TABLE IF EXISTS llm_telemetry_hourly CASCADE;

-- Drop alembic_version
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Drop all ENUM types (must be done AFTER tables are dropped)
DROP TYPE IF EXISTS llmprovider CASCADE;
DROP TYPE IF EXISTS userrole CASCADE;
DROP TYPE IF EXISTS subscriptionstatus CASCADE;
DROP TYPE IF EXISTS subscriptionplan CASCADE;
DROP TYPE IF EXISTS messagetype CASCADE;
DROP TYPE IF EXISTS messagevisibility CASCADE;
DROP TYPE IF EXISTS languagecode CASCADE;
DROP TYPE IF EXISTS widgettype CASCADE;
DROP TYPE IF EXISTS intenttype CASCADE;
DROP TYPE IF EXISTS blockchainnetwork CASCADE;
DROP TYPE IF EXISTS transactiontype CASCADE;
DROP TYPE IF EXISTS transactionstatus CASCADE;
DROP TYPE IF EXISTS defiprotocol CASCADE;

-- Re-enable foreign key checks
SET session_replication_role = DEFAULT;

-- Verify all tables are gone
\dt
