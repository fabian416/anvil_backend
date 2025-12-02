-- ============================================================================
-- ANVIL MULTI-LLM ORCHESTRATION SYSTEM - DATABASE SCHEMA
-- Version: 1.0.0
-- Last Updated: December 1, 2025
-- ============================================================================
-- Requirements:
--   - PostgreSQL 15+
--   - TimescaleDB extension
--   - pgvector extension (optional, for semantic caching)
--   - uuid-ossp extension
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- ============================================================================
-- MODULE: PROVIDER_MANAGEMENT - LLM Provider Configuration
-- ============================================================================

-- LLM Provider Configuration
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,  -- vertex_ai, deepinfra, bedrock
    display_name VARCHAR(100) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 1,  -- 1=primary, 2=fallback1, 3=fallback2
    is_enabled BOOLEAN DEFAULT true,
    health_status VARCHAR(20) DEFAULT 'healthy',  -- healthy, degraded, down
    last_health_check TIMESTAMPTZ,
    health_check_interval_seconds INTEGER DEFAULT 60,
    
    -- Configuration (encrypted API keys stored separately)
    config JSONB NOT NULL DEFAULT '{}',
    -- Example: {"region": "us-central1", "endpoint": "https://..."}
    
    -- Rate Limits
    rate_limits JSONB DEFAULT '{}',
    -- Example: {"requests_per_minute": 100, "tokens_per_day": 1000000}
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_health CHECK (health_status IN ('healthy', 'degraded', 'down')),
    CONSTRAINT valid_priority CHECK (priority >= 1 AND priority <= 10)
);

-- Index for priority ordering
CREATE INDEX idx_providers_priority ON llm_providers(priority) WHERE is_enabled = true;

-- ============================================================================
-- MODULE: MODEL_CATALOG - Model Definitions and Capabilities
-- ============================================================================

-- Model Catalog per Provider
CREATE TABLE llm_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES llm_providers(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,  -- gemini-1.5-pro, llama-3.1-405b-instruct, etc.
    display_name VARCHAR(100) NOT NULL,
    model_family VARCHAR(50),  -- gemini, llama, claude, mixtral, qwen
    
    -- Capabilities
    capabilities JSONB DEFAULT '[]',
    -- Example: ["chat", "code", "vision", "function_calling", "json_mode"]
    
    -- Technical Specs
    context_window INTEGER,  -- max input + output tokens
    max_output_tokens INTEGER,
    supports_streaming BOOLEAN DEFAULT true,
    supports_tools BOOLEAN DEFAULT true,
    
    -- Pricing (USD per 1K tokens)
    cost_per_1k_input DECIMAL(10,6),
    cost_per_1k_output DECIMAL(10,6),
    
    -- Performance Baseline
    avg_latency_ms INTEGER,  -- baseline latency from provider docs
    
    -- Carousel Configuration
    is_enabled BOOLEAN DEFAULT true,
    carousel_position INTEGER DEFAULT 1,  -- order in retry carousel within provider
    tier VARCHAR(20) DEFAULT 'standard',  -- premium, standard, economy
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_provider_model UNIQUE(provider_id, model_id),
    CONSTRAINT valid_tier CHECK (tier IN ('premium', 'standard', 'economy', 'experimental'))
);

-- Index for model selection queries
CREATE INDEX idx_models_provider_enabled ON llm_models(provider_id, carousel_position) 
    WHERE is_enabled = true;
CREATE INDEX idx_models_capabilities ON llm_models USING GIN (capabilities);

-- ============================================================================
-- MODULE: RANKING_SYSTEM - Adaptive Model Ranking
-- ============================================================================

-- Agent-Model Ranking (Adaptive Performance Tracking)
CREATE TABLE agent_model_rankings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL,  -- swap_agent, trading_agent, portfolio_agent, etc.
    model_id UUID NOT NULL REFERENCES llm_models(id) ON DELETE CASCADE,
    
    -- Calculated Ranking Score (0.0000 to 1.0000)
    ranking_score DECIMAL(5,4) DEFAULT 0.5000,
    
    -- Component Scores
    success_rate DECIMAL(5,4) DEFAULT 0.0000,  -- successful / total
    latency_score DECIMAL(5,4) DEFAULT 0.5000,  -- normalized, lower is better
    cost_score DECIMAL(5,4) DEFAULT 0.5000,  -- normalized, lower is better
    
    -- Raw Metrics
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    timeout_requests INTEGER DEFAULT 0,
    
    -- Aggregated Performance
    avg_latency_ms INTEGER DEFAULT 0,
    p95_latency_ms INTEGER DEFAULT 0,
    avg_cost_per_request DECIMAL(10,6) DEFAULT 0,
    total_tokens_used BIGINT DEFAULT 0,
    
    -- Timestamps
    last_used_at TIMESTAMPTZ,
    last_recalculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_agent_model UNIQUE(agent_type, model_id),
    CONSTRAINT valid_scores CHECK (
        ranking_score >= 0 AND ranking_score <= 1 AND
        success_rate >= 0 AND success_rate <= 1
    )
);

-- Index for ranking queries
CREATE INDEX idx_rankings_agent_score ON agent_model_rankings(agent_type, ranking_score DESC);

-- Ranking Weight Configuration per Agent
CREATE TABLE ranking_weight_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL UNIQUE,
    
    -- Weights (must sum to 1.0)
    success_weight DECIMAL(3,2) DEFAULT 0.50,
    latency_weight DECIMAL(3,2) DEFAULT 0.25,
    cost_weight DECIMAL(3,2) DEFAULT 0.15,
    recency_weight DECIMAL(3,2) DEFAULT 0.10,
    
    -- Configuration
    min_requests_for_ranking INTEGER DEFAULT 10,  -- minimum samples before ranking
    recency_decay_hours INTEGER DEFAULT 24,  -- time window for recency bonus
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT weights_sum_to_one CHECK (
        success_weight + latency_weight + cost_weight + recency_weight = 1.00
    )
);

-- Manual Ranking Overrides
CREATE TABLE ranking_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL,
    model_id UUID NOT NULL REFERENCES llm_models(id) ON DELETE CASCADE,
    
    override_score DECIMAL(5,4) NOT NULL,
    reason TEXT,
    
    created_by UUID,  -- admin user ID
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- NULL = permanent
    
    CONSTRAINT unique_override UNIQUE(agent_type, model_id),
    CONSTRAINT valid_override CHECK (override_score >= 0 AND override_score <= 1)
);

-- ============================================================================
-- MODULE: REQUEST_TRACKING - Full Request Lifecycle
-- ============================================================================

-- LLM Request Tracking
CREATE TABLE llm_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(100) UNIQUE NOT NULL,  -- external tracking ID
    user_id UUID,  -- references users table
    agent_type VARCHAR(50) NOT NULL,
    session_id UUID,  -- chat session if applicable
    
    -- Request Details
    prompt_hash VARCHAR(64),  -- SHA256 for dedup/caching
    input_tokens INTEGER,
    max_output_tokens INTEGER,
    temperature DECIMAL(3,2),
    has_tools BOOLEAN DEFAULT false,
    is_streaming BOOLEAN DEFAULT false,
    
    -- Status Tracking
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    status_history JSONB DEFAULT '[]',
    -- Example: [{"status": "pending", "timestamp": "...", "details": "..."}]
    
    -- Provider/Model Selection
    selected_provider_id UUID REFERENCES llm_providers(id),
    selected_model_id UUID REFERENCES llm_models(id),
    selection_reason VARCHAR(100),  -- ranking, fallback, manual_override, cache_hit
    
    -- Execution Metrics
    attempt_count INTEGER DEFAULT 0,
    total_latency_ms INTEGER,
    time_to_first_token_ms INTEGER,
    output_tokens INTEGER,
    
    -- Cost Tracking
    estimated_cost_usd DECIMAL(10,6),
    actual_cost_usd DECIMAL(10,6),
    
    -- Error Handling
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'queued', 'selecting_model', 'executing', 
        'streaming', 'completed', 'failed', 'timeout', 
        'cancelled', 'retrying'
    ))
);

-- Convert to hypertable for efficient time-series queries
SELECT create_hypertable('llm_requests', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes for common queries
CREATE INDEX idx_requests_status ON llm_requests(status, created_at DESC);
CREATE INDEX idx_requests_user ON llm_requests(user_id, created_at DESC);
CREATE INDEX idx_requests_agent ON llm_requests(agent_type, created_at DESC);
CREATE INDEX idx_requests_model ON llm_requests(selected_model_id, created_at DESC);
CREATE INDEX idx_requests_provider ON llm_requests(selected_provider_id, created_at DESC);

-- Request Attempts (Retry History)
CREATE TABLE llm_request_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES llm_requests(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    
    -- Provider/Model for this attempt
    provider_id UUID REFERENCES llm_providers(id),
    model_id UUID REFERENCES llm_models(id),
    
    -- Attempt Result
    status VARCHAR(30) NOT NULL,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10,6),
    
    -- Error Details (if failed)
    error_type VARCHAR(50),  -- rate_limit, timeout, model_error, provider_down, etc.
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT valid_attempt_status CHECK (status IN (
        'started', 'completed', 'failed', 'timeout', 'rate_limited', 'cancelled'
    ))
);

-- Index for attempt queries
CREATE INDEX idx_attempts_request ON llm_request_attempts(request_id, attempt_number);

-- ============================================================================
-- MODULE: CIRCUIT_BREAKER - Failure Protection
-- ============================================================================

-- Circuit Breaker State
CREATE TABLE circuit_breakers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(20) NOT NULL,  -- provider, model
    entity_id UUID NOT NULL,
    entity_name VARCHAR(100),  -- for display purposes
    
    -- State
    state VARCHAR(20) NOT NULL DEFAULT 'closed',  -- closed, open, half_open
    
    -- Counters
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,  -- for half_open testing
    consecutive_failures INTEGER DEFAULT 0,
    
    -- Timestamps
    last_failure_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    half_open_at TIMESTAMPTZ,
    
    -- Configuration
    config JSONB DEFAULT '{
        "failure_threshold": 5,
        "success_threshold": 3,
        "timeout_seconds": 60,
        "half_open_max_requests": 3
    }',
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_cb_state CHECK (state IN ('closed', 'open', 'half_open')),
    CONSTRAINT unique_circuit_breaker UNIQUE(entity_type, entity_id)
);

-- Index for quick lookups
CREATE INDEX idx_circuit_breakers_entity ON circuit_breakers(entity_type, entity_id);
CREATE INDEX idx_circuit_breakers_state ON circuit_breakers(state) WHERE state != 'closed';

-- ============================================================================
-- MODULE: TELEMETRY - Metrics and Aggregations
-- ============================================================================

-- Hourly Telemetry Aggregations (Pre-computed for Dashboard)
CREATE TABLE llm_telemetry_hourly (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hour_bucket TIMESTAMPTZ NOT NULL,
    
    -- Dimensions
    provider_id UUID REFERENCES llm_providers(id),
    model_id UUID REFERENCES llm_models(id),
    agent_type VARCHAR(50),
    
    -- Request Counts
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    timeout_requests INTEGER DEFAULT 0,
    retried_requests INTEGER DEFAULT 0,
    cached_requests INTEGER DEFAULT 0,
    
    -- Latency Percentiles
    latency_p50_ms INTEGER,
    latency_p95_ms INTEGER,
    latency_p99_ms INTEGER,
    avg_latency_ms INTEGER,
    min_latency_ms INTEGER,
    max_latency_ms INTEGER,
    
    -- Token Usage
    total_input_tokens BIGINT DEFAULT 0,
    total_output_tokens BIGINT DEFAULT 0,
    avg_input_tokens INTEGER,
    avg_output_tokens INTEGER,
    
    -- Cost
    total_cost_usd DECIMAL(12,6) DEFAULT 0,
    avg_cost_per_request DECIMAL(10,6),
    
    -- Quality Metrics
    avg_time_to_first_token_ms INTEGER,
    cache_hit_rate DECIMAL(5,4),
    retry_rate DECIMAL(5,4),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_telemetry_bucket UNIQUE(hour_bucket, provider_id, model_id, agent_type)
);

-- Convert to hypertable
SELECT create_hypertable('llm_telemetry_hourly', 'hour_bucket',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes for dashboard queries
CREATE INDEX idx_telemetry_lookup ON llm_telemetry_hourly(hour_bucket DESC, provider_id, model_id);
CREATE INDEX idx_telemetry_agent ON llm_telemetry_hourly(hour_bucket DESC, agent_type);

-- Daily Cost Summary (for budget tracking)
CREATE TABLE llm_cost_daily (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    provider_id UUID REFERENCES llm_providers(id),
    
    total_cost_usd DECIMAL(12,6) DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    
    -- Breakdown by tier
    premium_cost_usd DECIMAL(12,6) DEFAULT 0,
    standard_cost_usd DECIMAL(12,6) DEFAULT 0,
    economy_cost_usd DECIMAL(12,6) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_daily_cost UNIQUE(date, provider_id)
);

-- ============================================================================
-- MODULE: BUSINESS_CONFIG - Runtime Configuration
-- ============================================================================

-- Business Control Configurations
CREATE TABLE llm_business_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    config_type VARCHAR(50),  -- feature_flag, threshold, limit, etc.
    description TEXT,
    
    -- Audit
    modified_by UUID,  -- admin user ID
    modified_at TIMESTAMPTZ DEFAULT NOW(),
    previous_value JSONB,
    change_reason TEXT,
    
    -- Validation
    validation_schema JSONB,  -- JSON Schema for config_value
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Default configurations
INSERT INTO llm_business_config (config_key, config_value, config_type, description) VALUES
('retry_config', '{
    "max_retries_per_provider": 2,
    "max_total_retries": 6,
    "initial_delay_ms": 100,
    "max_delay_ms": 5000,
    "backoff_multiplier": 2,
    "jitter": true
}', 'threshold', 'Retry behavior configuration'),

('timeout_config', '{
    "per_attempt_ms": 30000,
    "total_request_ms": 120000,
    "streaming_idle_ms": 10000
}', 'threshold', 'Timeout configuration'),

('rate_limits', '{
    "default_requests_per_minute": 60,
    "premium_requests_per_minute": 200,
    "burst_multiplier": 2
}', 'limit', 'Rate limiting configuration'),

('feature_flags', '{
    "enable_caching": true,
    "enable_streaming": true,
    "enable_cost_tracking": true,
    "enable_ranking": true
}', 'feature_flag', 'Feature toggles');

-- Cost Budget Alerts
CREATE TABLE llm_cost_budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    budget_type VARCHAR(20) NOT NULL,  -- daily, weekly, monthly
    
    -- Budget Amounts
    budget_amount_usd DECIMAL(12,2) NOT NULL,
    warning_threshold_percent INTEGER DEFAULT 80,
    critical_threshold_percent INTEGER DEFAULT 95,
    
    -- Current State
    current_spend_usd DECIMAL(12,2) DEFAULT 0,
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    
    -- Enforcement
    is_hard_limit BOOLEAN DEFAULT false,  -- stop requests if exceeded
    
    -- Notification
    notify_emails TEXT[],
    notify_slack_channel VARCHAR(100),
    last_alert_sent_at TIMESTAMPTZ,
    
    -- Metadata
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_budget_type CHECK (budget_type IN ('daily', 'weekly', 'monthly'))
);

-- Budget Alert History
CREATE TABLE llm_budget_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_id UUID NOT NULL REFERENCES llm_cost_budgets(id) ON DELETE CASCADE,
    alert_type VARCHAR(20) NOT NULL,  -- warning, critical, exceeded
    threshold_percent INTEGER,
    current_spend_usd DECIMAL(12,2),
    budget_amount_usd DECIMAL(12,2),
    
    notified_at TIMESTAMPTZ DEFAULT NOW(),
    notification_channels TEXT[]
);

-- ============================================================================
-- MODULE: AUDIT_LOG - Configuration Change Tracking
-- ============================================================================

-- Audit Log for Admin Actions
CREATE TABLE llm_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    
    -- Actor
    actor_id UUID,  -- admin user ID
    actor_ip INET,
    
    -- Change Details
    before_value JSONB,
    after_value JSONB,
    change_reason TEXT,
    
    -- Metadata
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('llm_audit_log', 'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX idx_audit_actor ON llm_audit_log(actor_id, timestamp DESC);
CREATE INDEX idx_audit_entity ON llm_audit_log(entity_type, entity_id, timestamp DESC);

-- ============================================================================
-- MODULE: CACHING - Response Caching (Optional)
-- ============================================================================

-- Response Cache (for identical requests)
CREATE TABLE llm_response_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 of normalized request
    
    -- Request Signature
    agent_type VARCHAR(50),
    prompt_hash VARCHAR(64),
    model_id UUID REFERENCES llm_models(id),
    temperature DECIMAL(3,2),
    
    -- Cached Response
    response_content TEXT,
    output_tokens INTEGER,
    
    -- Cache Metadata
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_hit_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_cache_key ON llm_response_cache(cache_key);
CREATE INDEX idx_cache_expiry ON llm_response_cache(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- VIEWS - Common Query Patterns
-- ============================================================================

-- View: Current Provider Status
CREATE VIEW v_provider_status AS
SELECT 
    p.id,
    p.name,
    p.display_name,
    p.priority,
    p.is_enabled,
    p.health_status,
    p.last_health_check,
    COUNT(m.id) as model_count,
    COUNT(m.id) FILTER (WHERE m.is_enabled) as enabled_model_count,
    cb.state as circuit_breaker_state
FROM llm_providers p
LEFT JOIN llm_models m ON m.provider_id = p.id
LEFT JOIN circuit_breakers cb ON cb.entity_type = 'provider' AND cb.entity_id = p.id
GROUP BY p.id, cb.state
ORDER BY p.priority;

-- View: Model Rankings by Agent
CREATE VIEW v_model_rankings AS
SELECT 
    r.agent_type,
    p.display_name as provider,
    m.display_name as model,
    m.model_id,
    r.ranking_score,
    r.success_rate,
    r.avg_latency_ms,
    r.avg_cost_per_request,
    r.total_requests,
    m.cost_per_1k_input,
    m.cost_per_1k_output,
    COALESCE(o.override_score, r.ranking_score) as effective_score,
    o.expires_at as override_expires
FROM agent_model_rankings r
JOIN llm_models m ON m.id = r.model_id
JOIN llm_providers p ON p.id = m.provider_id
LEFT JOIN ranking_overrides o ON o.agent_type = r.agent_type AND o.model_id = r.model_id
    AND (o.expires_at IS NULL OR o.expires_at > NOW())
WHERE m.is_enabled AND p.is_enabled
ORDER BY r.agent_type, COALESCE(o.override_score, r.ranking_score) DESC;

-- View: Today's Cost Summary
CREATE VIEW v_cost_today AS
SELECT 
    p.display_name as provider,
    SUM(r.actual_cost_usd) as total_cost,
    COUNT(*) as request_count,
    SUM(r.input_tokens + COALESCE(r.output_tokens, 0)) as total_tokens,
    AVG(r.actual_cost_usd) as avg_cost_per_request
FROM llm_requests r
JOIN llm_providers p ON p.id = r.selected_provider_id
WHERE r.created_at >= CURRENT_DATE
    AND r.status = 'completed'
GROUP BY p.id, p.display_name;

-- ============================================================================
-- FUNCTIONS - Helper Functions
-- ============================================================================

-- Function: Update ranking scores
CREATE OR REPLACE FUNCTION update_ranking_scores(p_agent_type VARCHAR DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
    profile RECORD;
    model RECORD;
    new_score DECIMAL(5,4);
    max_latency INTEGER;
    max_cost DECIMAL(10,6);
BEGIN
    -- Get weight profile
    FOR profile IN 
        SELECT * FROM ranking_weight_profiles 
        WHERE p_agent_type IS NULL OR agent_type = p_agent_type
    LOOP
        -- Get max values for normalization
        SELECT 
            COALESCE(MAX(avg_latency_ms), 1),
            COALESCE(MAX(avg_cost_per_request), 0.01)
        INTO max_latency, max_cost
        FROM agent_model_rankings
        WHERE agent_type = profile.agent_type
            AND total_requests >= profile.min_requests_for_ranking;
        
        -- Update each model's ranking
        FOR model IN
            SELECT * FROM agent_model_rankings
            WHERE agent_type = profile.agent_type
        LOOP
            IF model.total_requests < profile.min_requests_for_ranking THEN
                new_score := 0.5000;  -- Default score
            ELSE
                new_score := (
                    profile.success_weight * COALESCE(model.success_rate, 0) +
                    profile.latency_weight * (1 - LEAST(model.avg_latency_ms::decimal / max_latency, 1)) +
                    profile.cost_weight * (1 - LEAST(model.avg_cost_per_request / max_cost, 1)) +
                    profile.recency_weight * CASE 
                        WHEN model.last_used_at IS NULL THEN 0
                        WHEN model.last_used_at > NOW() - (profile.recency_decay_hours || ' hours')::interval THEN 0.5
                        ELSE 0
                    END
                );
            END IF;
            
            UPDATE agent_model_rankings
            SET ranking_score = new_score,
                last_recalculated_at = NOW(),
                updated_at = NOW()
            WHERE id = model.id;
            
            updated_count := updated_count + 1;
        END LOOP;
    END LOOP;
    
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Aggregate hourly telemetry
CREATE OR REPLACE FUNCTION aggregate_hourly_telemetry(p_hour TIMESTAMPTZ DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    target_hour TIMESTAMPTZ;
    inserted_count INTEGER := 0;
BEGIN
    target_hour := COALESCE(p_hour, DATE_TRUNC('hour', NOW() - INTERVAL '1 hour'));
    
    INSERT INTO llm_telemetry_hourly (
        hour_bucket, provider_id, model_id, agent_type,
        total_requests, successful_requests, failed_requests, timeout_requests, retried_requests,
        latency_p50_ms, latency_p95_ms, latency_p99_ms, avg_latency_ms,
        total_input_tokens, total_output_tokens,
        total_cost_usd, avg_cost_per_request, retry_rate
    )
    SELECT 
        target_hour,
        selected_provider_id,
        selected_model_id,
        agent_type,
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'completed'),
        COUNT(*) FILTER (WHERE status = 'failed'),
        COUNT(*) FILTER (WHERE status = 'timeout'),
        COUNT(*) FILTER (WHERE attempt_count > 1),
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_latency_ms),
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_latency_ms),
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_latency_ms),
        AVG(total_latency_ms),
        SUM(input_tokens),
        SUM(output_tokens),
        SUM(actual_cost_usd),
        AVG(actual_cost_usd),
        COUNT(*) FILTER (WHERE attempt_count > 1)::decimal / NULLIF(COUNT(*), 0)
    FROM llm_requests
    WHERE created_at >= target_hour
        AND created_at < target_hour + INTERVAL '1 hour'
    GROUP BY selected_provider_id, selected_model_id, agent_type
    ON CONFLICT (hour_bucket, provider_id, model_id, agent_type) 
    DO UPDATE SET
        total_requests = EXCLUDED.total_requests,
        successful_requests = EXCLUDED.successful_requests,
        failed_requests = EXCLUDED.failed_requests,
        timeout_requests = EXCLUDED.timeout_requests,
        retried_requests = EXCLUDED.retried_requests,
        latency_p50_ms = EXCLUDED.latency_p50_ms,
        latency_p95_ms = EXCLUDED.latency_p95_ms,
        latency_p99_ms = EXCLUDED.latency_p99_ms,
        avg_latency_ms = EXCLUDED.avg_latency_ms,
        total_input_tokens = EXCLUDED.total_input_tokens,
        total_output_tokens = EXCLUDED.total_output_tokens,
        total_cost_usd = EXCLUDED.total_cost_usd,
        avg_cost_per_request = EXCLUDED.avg_cost_per_request,
        retry_rate = EXCLUDED.retry_rate;
    
    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RETURN inserted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SEED DATA - Default Provider and Model Configuration
-- ============================================================================

-- Insert default providers
INSERT INTO llm_providers (name, display_name, priority, config) VALUES
('vertex_ai', 'Google Vertex AI', 1, '{"region": "us-central1"}'),
('deepinfra', 'DeepInfra', 2, '{"base_url": "https://api.deepinfra.com/v1/openai"}'),
('bedrock', 'AWS Bedrock', 3, '{"region": "us-east-1"}');

-- Insert default models (after providers are created)
INSERT INTO llm_models (provider_id, model_id, display_name, model_family, capabilities, context_window, max_output_tokens, cost_per_1k_input, cost_per_1k_output, carousel_position, tier)
SELECT 
    p.id,
    m.model_id,
    m.display_name,
    m.model_family,
    m.capabilities::jsonb,
    m.context_window,
    m.max_output_tokens,
    m.cost_per_1k_input,
    m.cost_per_1k_output,
    m.carousel_position,
    m.tier
FROM llm_providers p
CROSS JOIN (VALUES
    -- Vertex AI Models
    ('vertex_ai', 'gemini-1.5-pro', 'Gemini 1.5 Pro', 'gemini', '["chat", "code", "vision", "function_calling"]', 1000000, 8192, 0.00125, 0.00375, 1, 'premium'),
    ('vertex_ai', 'gemini-1.5-flash', 'Gemini 1.5 Flash', 'gemini', '["chat", "code", "function_calling"]', 1000000, 8192, 0.000075, 0.0003, 2, 'standard'),
    ('vertex_ai', 'gemini-2.0-flash-exp', 'Gemini 2.0 Flash (Exp)', 'gemini', '["chat", "code", "vision", "function_calling"]', 1000000, 8192, 0.0001, 0.0004, 3, 'experimental'),
    
    -- DeepInfra Models
    ('deepinfra', 'meta-llama/Meta-Llama-3.1-405B-Instruct', 'Llama 3.1 405B', 'llama', '["chat", "code", "function_calling"]', 128000, 4096, 0.0027, 0.0027, 1, 'premium'),
    ('deepinfra', 'mistralai/Mixtral-8x22B-Instruct-v0.1', 'Mixtral 8x22B', 'mixtral', '["chat", "code"]', 65536, 4096, 0.00065, 0.00065, 2, 'standard'),
    ('deepinfra', 'Qwen/Qwen2-72B-Instruct', 'Qwen2 72B', 'qwen', '["chat", "code"]', 32768, 4096, 0.00035, 0.00035, 3, 'economy'),
    
    -- Bedrock Models
    ('bedrock', 'anthropic.claude-3-5-sonnet-20241022-v2:0', 'Claude 3.5 Sonnet', 'claude', '["chat", "code", "vision", "function_calling"]', 200000, 8192, 0.003, 0.015, 1, 'premium'),
    ('bedrock', 'anthropic.claude-3-5-haiku-20241022-v1:0', 'Claude 3.5 Haiku', 'claude', '["chat", "code", "function_calling"]', 200000, 8192, 0.0008, 0.004, 2, 'standard'),
    ('bedrock', 'amazon.titan-text-express-v1', 'Titan Text Express', 'titan', '["chat"]', 8192, 4096, 0.0002, 0.0006, 3, 'economy')
) AS m(provider_name, model_id, display_name, model_family, capabilities, context_window, max_output_tokens, cost_per_1k_input, cost_per_1k_output, carousel_position, tier)
WHERE p.name = m.provider_name;

-- Insert default ranking weight profiles
INSERT INTO ranking_weight_profiles (agent_type, success_weight, latency_weight, cost_weight, recency_weight) VALUES
('swap_agent', 0.60, 0.25, 0.10, 0.05),
('trading_agent', 0.55, 0.30, 0.10, 0.05),
('portfolio_agent', 0.45, 0.20, 0.25, 0.10),
('researcher', 0.40, 0.15, 0.30, 0.15),
('risk_analyzer', 0.65, 0.20, 0.10, 0.05),
('default', 0.50, 0.25, 0.15, 0.10);

-- Initialize rankings for each agent-model combination
INSERT INTO agent_model_rankings (agent_type, model_id)
SELECT DISTINCT wp.agent_type, m.id
FROM ranking_weight_profiles wp
CROSS JOIN llm_models m
WHERE m.is_enabled = true;

-- Create default budget
INSERT INTO llm_cost_budgets (name, budget_type, budget_amount_usd, warning_threshold_percent, critical_threshold_percent, is_hard_limit)
VALUES 
('Daily Operations', 'daily', 500.00, 80, 95, false),
('Monthly Total', 'monthly', 10000.00, 80, 95, true);
