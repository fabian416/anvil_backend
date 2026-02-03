-- ============================================================================
-- ANVIL BACKEND - DATABASE INITIALIZATION
-- ============================================================================
-- This script runs automatically when PostgreSQL container starts for the first time.
-- It creates the necessary schema and extensions.
-- ============================================================================

-- Create the anvil schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS anvil;

-- Set default search path
ALTER DATABASE anvil_db SET search_path TO anvil, public;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";        -- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- Trigram text similarity
CREATE EXTENSION IF NOT EXISTS "btree_gin";       -- GIN index support

-- Optional: Enable AGE extension for graph database (if available)
-- CREATE EXTENSION IF NOT EXISTS age;

-- Create read-only role for analytics/reporting (optional)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anvil_readonly') THEN
        CREATE ROLE anvil_readonly;
    END IF;
END
$$;

-- Grant usage on schema
GRANT USAGE ON SCHEMA anvil TO anvil_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA anvil TO anvil_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA anvil GRANT SELECT ON TABLES TO anvil_readonly;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE '✅ Anvil database initialized successfully!';
    RAISE NOTICE '   Schema: anvil';
    RAISE NOTICE '   Extensions: uuid-ossp, pgcrypto, pg_trgm, btree_gin';
END
$$;
