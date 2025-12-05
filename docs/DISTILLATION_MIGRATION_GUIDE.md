# Request Distillation System - Migration Guide

## Overview

Database migration and rollback procedures for the Request Distillation System.

**Last Updated**: 2025-12-01  
**Version**: 1.0

---

## Migration File

**File**: `src/app/infrastructure/persistence_sqla/migrations/versions/20251201_003_add_distillation_telemetry.py`

**Created**: 2025-12-01  
**Revision ID**: `20251201_003`  
**Dependencies**: Previous migration

---

## What's Being Created

### 1. Main Telemetry Table

```sql
CREATE TABLE distillation_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID,
    conversation_id UUID,
    request_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash
    detected_language VARCHAR(10),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    success BOOLEAN NOT NULL,
    reason VARCHAR(50),
    confidence FLOAT,
    latency_ms FLOAT NOT NULL,
    tokens_used INTEGER,
    cost_usd DECIMAL(12, 8),
    fallback_used BOOLEAN DEFAULT FALSE,
    error TEXT
);
```

### 2. Indexes

```sql
-- Query performance
CREATE INDEX idx_distillation_timestamp ON distillation_telemetry(timestamp DESC);
CREATE INDEX idx_distillation_user_id ON distillation_telemetry(user_id);
CREATE INDEX idx_distillation_provider ON distillation_telemetry(provider);
CREATE INDEX idx_distillation_success ON distillation_telemetry(success);
CREATE INDEX idx_distillation_reason ON distillation_telemetry(reason);

-- Composite indexes for common queries
CREATE INDEX idx_distillation_user_timestamp 
    ON distillation_telemetry(user_id, timestamp DESC);
CREATE INDEX idx_distillation_provider_timestamp 
    ON distillation_telemetry(provider, timestamp DESC);
```

### 3. Materialized View

```sql
CREATE MATERIALIZED VIEW distillation_metrics_daily AS
SELECT
    DATE(timestamp) as date,
    provider,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE success = true) as successful_requests,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
    ROUND(AVG(confidence)::numeric, 2) as avg_confidence,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost_usd,
    COUNT(*) FILTER (WHERE fallback_used = true) as fallback_used_count
FROM distillation_telemetry
GROUP BY DATE(timestamp), provider;

CREATE INDEX idx_distillation_metrics_date 
    ON distillation_metrics_daily(date DESC, provider);
```

---

## Running the Migration

### Step 1: Backup Database

```bash
# Full backup
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -Fc $POSTGRES_DB > backup_$(date +%Y%m%d_%H%M%S).dump

# Or table-specific backup (if updating existing system)
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -t existing_table $POSTGRES_DB > existing_table_backup.sql
```

### Step 2: Check Current Version

```bash
# View current migration version
alembic current

# View pending migrations
alembic heads

# View migration history
alembic history
```

### Step 3: Run Migration

```bash
# Dry-run (shows SQL without executing)
alembic upgrade head --sql

# Execute migration
alembic upgrade head

# Verify
alembic current
# Should show: 20251201_003 (head)
```

### Step 4: Verify Tables

```bash
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB
```

```sql
-- Check table exists
\d distillation_telemetry

-- Check indexes
\di distillation_*

-- Check materialized view
\d distillation_metrics_daily

-- Verify empty table
SELECT COUNT(*) FROM distillation_telemetry;
-- Should return: 0
```

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

```bash
# Rollback one migration
alembic downgrade -1

# Verify
alembic current
```

### Complete Rollback

```bash
# Rollback to specific version
alembic downgrade <previous_revision_id>

# Or rollback all distillation changes
alembic downgrade base  # WARNING: Removes ALL migrations
```

### Manual Rollback (if Alembic fails)

```sql
-- Drop materialized view
DROP MATERIALIZED VIEW IF EXISTS distillation_metrics_daily;

-- Drop indexes
DROP INDEX IF EXISTS idx_distillation_timestamp;
DROP INDEX IF EXISTS idx_distillation_user_id;
DROP INDEX IF EXISTS idx_distillation_provider;
DROP INDEX IF EXISTS idx_distillation_success;
DROP INDEX IF EXISTS idx_distillation_reason;
DROP INDEX IF EXISTS idx_distillation_user_timestamp;
DROP INDEX IF EXISTS idx_distillation_provider_timestamp;
DROP INDEX IF EXISTS idx_distillation_metrics_date;

-- Drop table
DROP TABLE IF EXISTS distillation_telemetry;

-- Update alembic version
DELETE FROM alembic_version WHERE version_num = '20251201_003';
```

---

## Data Migration (Existing Systems)

### If You Have Existing Distillation Data

**Scenario**: You have distillation data in a different format or table.

```sql
-- Example: Migrate from old_distillation_logs table
INSERT INTO distillation_telemetry (
    timestamp,
    user_id,
    request_hash,
    provider,
    success,
    latency_ms,
    tokens_used,
    cost_usd
)
SELECT
    created_at as timestamp,
    user_id,
    MD5(message) as request_hash,  -- Generate hash
    'vertex_ai' as provider,  -- Default provider
    is_valid as success,
    response_time_ms as latency_ms,
    token_count as tokens_used,
    cost as cost_usd
FROM old_distillation_logs
WHERE created_at > NOW() - INTERVAL '90 days';  -- Only migrate recent data
```

---

## Post-Migration Tasks

### 1. Refresh Materialized View

```sql
-- Initial refresh (will be empty)
REFRESH MATERIALIZED VIEW distillation_metrics_daily;

-- Set up automatic refresh (optional)
CREATE OR REPLACE FUNCTION refresh_distillation_metrics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY distillation_metrics_daily;
END;
$$ LANGUAGE plpgsql;

-- Schedule with pg_cron (if available)
SELECT cron.schedule('refresh-distillation-metrics', '0 1 * * *', 
    'SELECT refresh_distillation_metrics()');
```

### 2. Grant Permissions

```sql
-- Grant read access to analytics role
GRANT SELECT ON distillation_telemetry TO analytics_role;
GRANT SELECT ON distillation_metrics_daily TO analytics_role;

-- Grant write access to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON distillation_telemetry TO app_role;
```

### 3. Set Up Partitioning (Optional, for high volume)

```sql
-- Convert to partitioned table (if needed)
-- Only necessary for > 100M rows

CREATE TABLE distillation_telemetry_partitioned (
    LIKE distillation_telemetry INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE distillation_telemetry_2025_12 
    PARTITION OF distillation_telemetry_partitioned
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Future: Create partitions automatically with pg_partman
```

---

## Troubleshooting

### Migration Fails: "Relation already exists"

```bash
# Check if table exists
psql -c "\d distillation_telemetry"

# If exists from failed migration, drop and retry
psql -c "DROP TABLE IF EXISTS distillation_telemetry CASCADE;"
alembic upgrade head
```

### Migration Fails: "Permission denied"

```bash
# Grant necessary permissions to migration user
psql -c "GRANT CREATE ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;"
psql -c "GRANT ALL ON SCHEMA public TO $POSTGRES_USER;"
```

### Migration Hangs

```bash
# Check for locks
psql -c "SELECT * FROM pg_locks WHERE NOT granted;"

# Kill blocking queries (if safe)
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
         WHERE datname = '$POSTGRES_DB' AND state = 'idle in transaction';"
```

### Rollback Fails

```bash
# Force rollback with SQL
psql -f rollback_manual.sql

# Fix alembic version table
psql -c "UPDATE alembic_version SET version_num = '<previous_version>';"

# Verify
alembic current
```

---

## Verification Checklist

After migration, verify:

- [ ] `alembic current` shows correct version
- [ ] `distillation_telemetry` table exists
- [ ] All 7 indexes created
- [ ] `distillation_metrics_daily` view exists
- [ ] Table is empty (0 rows)
- [ ] Application starts without errors
- [ ] First distillation request writes to table
- [ ] Admin API endpoints return data
- [ ] Materialized view can be refreshed

---

## Monitoring Post-Migration

### Week 1: Daily Checks

```sql
-- Check row count growth
SELECT COUNT(*), DATE(MIN(timestamp)), DATE(MAX(timestamp))
FROM distillation_telemetry;

-- Check for errors
SELECT error, COUNT(*) FROM distillation_telemetry 
WHERE error IS NOT NULL GROUP BY error;

-- Verify metrics view
REFRESH MATERIALIZED VIEW distillation_metrics_daily;
SELECT * FROM distillation_metrics_daily ORDER BY date DESC LIMIT 7;
```

### Week 2-4: Weekly Checks

```sql
-- Table size
SELECT pg_size_pretty(pg_total_relation_size('distillation_telemetry'));

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'distillation_telemetry';

-- Performance check
EXPLAIN ANALYZE SELECT * FROM distillation_telemetry 
WHERE timestamp > NOW() - INTERVAL '1 hour';
```

---

## Rollback Decision Matrix

| Scenario | Action | Downtime |
|----------|--------|----------|
| Migration fails | Rollback immediately | None |
| Performance degradation | Investigate first, rollback if critical | Possible |
| Data corruption | Rollback + restore backup | Yes |
| Wrong configuration | Fix config, no rollback needed | None |
| User complaints | Investigate first | None |

---

## References

- Migration file: `src/app/infrastructure/persistence_sqla/migrations/versions/20251201_003_add_distillation_telemetry.py`
- Mapping file: `src/app/infrastructure/persistence_sqla/mappings/distillation_telemetry.py`
- Repository: `src/app/infrastructure/persistence_sqla/repositories/distillation_telemetry_repository.py`

---

**Document Status**: ✅ Complete  
**Review Frequency**: After each migration
