-- ============================================================================
-- ANVIL NEW FEATURES - DATABASE SCHEMA
-- Feature 1: Distillation Pass System
-- Feature 2: Admin-Configured Projects
-- Version: 1.0.0
-- Last Updated: December 1, 2025
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- For semantic caching

-- ============================================================================
-- MODULE: DISTILLATION_PASS - Intent Classification & Routing
-- ============================================================================

-- Distillation Configuration
CREATE TABLE distillation_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    modified_by UUID,
    modified_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default configuration
INSERT INTO distillation_config (config_key, config_value, description) VALUES
('feature_flags', '{
    "enabled": true,
    "cache_enabled": true,
    "static_responses_enabled": true,
    "semantic_cache_enabled": true
}', 'Feature toggles for distillation'),

('thresholds', '{
    "min_confidence": 0.7,
    "semantic_similarity": 0.95,
    "max_latency_ms": 100
}', 'Classification thresholds'),

('routing_rules', '{
    "force_full_llm_intents": ["swap_request", "borrow_request", "risk_assessment"],
    "cache_ttl_by_intent": {
        "price_check": 60,
        "explain_concept": 3600,
        "how_to": 3600
    }
}', 'Routing configuration');

-- Static Response Library
CREATE TABLE distillation_static_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intent VARCHAR(50) NOT NULL,
    variant VARCHAR(50) DEFAULT 'default',
    
    -- Response template
    response_template TEXT NOT NULL,
    template_variables JSONB DEFAULT '[]',  -- Variables to inject
    data_source VARCHAR(100),               -- API to fetch dynamic data
    
    -- Conditions
    conditions JSONB DEFAULT '{}',          -- When to use this variant
    priority INTEGER DEFAULT 1,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(intent, variant)
);

-- Insert default static responses
INSERT INTO distillation_static_responses (intent, variant, response_template, data_source) VALUES
('greeting', 'default', 'Hello! I''m Anvil, your DeFi assistant. How can I help you today?', NULL),
('greeting', 'morning', 'Good morning! Ready to help with your DeFi needs.', NULL),
('greeting', 'evening', 'Good evening! What can I help you with?', NULL),
('price_check', 'default', 'The current price of {token} is ${price} ({change_24h}% 24h).', 'coingecko_api'),
('gas_check', 'default', 'Current gas prices on {chain}:\n• Low: {low} gwei\n• Average: {avg} gwei\n• High: {high} gwei', 'gas_api'),
('balance_check', 'default', 'Your portfolio value: ${total_value}\n\nTop holdings:\n{holdings_list}', 'portfolio_service'),
('off_topic', 'default', 'I''m specialized in DeFi and crypto assistance. I can help you with swaps, staking, lending, and other DeFi operations. What would you like to do?', NULL);

-- Exact Match Cache
CREATE TABLE distillation_cache_exact (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 hash
    
    -- Request signature
    normalized_query TEXT NOT NULL,
    intent VARCHAR(50),
    entities JSONB DEFAULT '{}',
    
    -- Cached response
    response_content TEXT NOT NULL,
    response_metadata JSONB DEFAULT '{}',
    
    -- Statistics
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_hit_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Source
    source_model VARCHAR(100),
    source_request_id UUID
);

CREATE INDEX idx_cache_exact_key ON distillation_cache_exact(cache_key);
CREATE INDEX idx_cache_exact_expiry ON distillation_cache_exact(expires_at);

-- Semantic Cache (Vector similarity)
CREATE TABLE distillation_cache_semantic (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Embedding
    query_embedding vector(1536),  -- OpenAI embedding dimension
    original_query TEXT NOT NULL,
    
    -- Classification
    intent VARCHAR(50),
    entities JSONB DEFAULT '{}',
    
    -- Cached response
    response_content TEXT NOT NULL,
    response_metadata JSONB DEFAULT '{}',
    
    -- Statistics
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_hit_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Source
    source_model VARCHAR(100),
    source_request_id UUID
);

-- Vector index for similarity search
CREATE INDEX idx_cache_semantic_embedding ON distillation_cache_semantic 
    USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 100);

-- Distillation Request Log
CREATE TABLE distillation_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(100) NOT NULL,
    user_id UUID,
    
    -- Input
    original_query TEXT NOT NULL,
    normalized_query TEXT,
    
    -- Classification Results
    intent VARCHAR(50),
    intent_confidence DECIMAL(4,3),
    complexity VARCHAR(20),
    entities JSONB DEFAULT '{}',
    
    -- Routing Decision
    route_type VARCHAR(20) NOT NULL,  -- REJECT, CACHE, STATIC, LIGHT_LLM, FULL_LLM
    routing_reason TEXT,
    suggested_model_tier VARCHAR(20),
    suggested_agent VARCHAR(50),
    
    -- Cache info
    cache_key VARCHAR(64),
    cache_hit BOOLEAN DEFAULT false,
    cache_level VARCHAR(20),  -- exact, semantic, none
    
    -- Performance
    classification_latency_ms INTEGER,
    total_latency_ms INTEGER,
    
    -- Outcome
    was_processed BOOLEAN,
    llm_request_id UUID,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('distillation_requests', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX idx_distill_requests_user ON distillation_requests(user_id, created_at DESC);
CREATE INDEX idx_distill_requests_route ON distillation_requests(route_type, created_at DESC);
CREATE INDEX idx_distill_requests_intent ON distillation_requests(intent, created_at DESC);

-- Distillation Telemetry (Hourly aggregation)
CREATE TABLE distillation_telemetry_hourly (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hour_bucket TIMESTAMPTZ NOT NULL,
    
    -- Counts by route type
    total_requests INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    cache_hit_count INTEGER DEFAULT 0,
    static_response_count INTEGER DEFAULT 0,
    light_llm_count INTEGER DEFAULT 0,
    full_llm_count INTEGER DEFAULT 0,
    
    -- Cache metrics
    exact_cache_hits INTEGER DEFAULT 0,
    semantic_cache_hits INTEGER DEFAULT 0,
    cache_hit_rate DECIMAL(5,4),
    
    -- Classification metrics
    avg_classification_latency_ms INTEGER,
    avg_confidence DECIMAL(4,3),
    
    -- Intent distribution
    intent_distribution JSONB DEFAULT '{}',
    
    -- Cost savings
    estimated_cost_saved_usd DECIMAL(10,4) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(hour_bucket)
);

SELECT create_hypertable('distillation_telemetry_hourly', 'hour_bucket',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================================
-- MODULE: ADMIN_PROJECTS - Project Configuration System
-- ============================================================================

-- Projects Table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Branding
    icon VARCHAR(50),              -- Emoji or icon name
    color VARCHAR(7),              -- Hex color
    banner_url TEXT,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    visibility VARCHAR(20) NOT NULL DEFAULT 'public',
    
    -- System Prompt
    system_prompt TEXT NOT NULL,
    welcome_message TEXT,
    
    -- DeFi Configuration
    enabled_protocols TEXT[] DEFAULT '{}',
    enabled_chains TEXT[] DEFAULT '{}',
    enabled_tools TEXT[] DEFAULT '{}',
    
    -- Risk Configuration
    risk_config JSONB DEFAULT '{}',
    
    -- User limits
    max_users INTEGER,
    
    -- Display order
    display_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT false,
    
    -- Audit
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'archived')),
    CONSTRAINT valid_visibility CHECK (visibility IN ('public', 'private', 'invite_only'))
);

CREATE INDEX idx_projects_status ON projects(status) WHERE status = 'active';
CREATE INDEX idx_projects_slug ON projects(slug);

-- Project Knowledge Bases
CREATE TABLE project_knowledge_bases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Configuration
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Embedding settings
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    chunk_size INTEGER DEFAULT 500,
    chunk_overlap INTEGER DEFAULT 50,
    
    -- Statistics
    total_documents INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',
    last_indexed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(project_id)
);

-- Knowledge Documents
CREATE TABLE project_knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_base_id UUID NOT NULL REFERENCES project_knowledge_bases(id) ON DELETE CASCADE,
    
    -- Content
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    doc_type VARCHAR(50) NOT NULL,  -- guide, faq, reference, data, announcement
    
    -- Source
    source_url TEXT,
    source_type VARCHAR(50) DEFAULT 'manual',  -- manual, crawled, api
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',
    priority INTEGER DEFAULT 1,
    
    -- Processing status
    is_processed BOOLEAN DEFAULT false,
    chunk_count INTEGER DEFAULT 0,
    processing_error TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_doc_type CHECK (doc_type IN ('guide', 'faq', 'reference', 'data', 'announcement'))
);

CREATE INDEX idx_knowledge_docs_kb ON project_knowledge_documents(knowledge_base_id);

-- Knowledge Chunks (for RAG)
CREATE TABLE project_knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES project_knowledge_documents(id) ON DELETE CASCADE,
    knowledge_base_id UUID NOT NULL REFERENCES project_knowledge_bases(id) ON DELETE CASCADE,
    
    -- Content
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    
    -- Embedding
    embedding vector(1536),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector index for similarity search
CREATE INDEX idx_knowledge_chunks_embedding ON project_knowledge_chunks 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_knowledge_chunks_kb ON project_knowledge_chunks(knowledge_base_id);

-- Project Tool Configuration
CREATE TABLE project_tool_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tool_id VARCHAR(50) NOT NULL,
    
    -- Enablement
    is_enabled BOOLEAN DEFAULT true,
    
    -- Restrictions
    max_calls_per_session INTEGER,
    max_amount_per_call DECIMAL(20,8),
    requires_confirmation BOOLEAN DEFAULT true,
    
    -- Custom parameters
    default_params JSONB DEFAULT '{}',
    locked_params JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(project_id, tool_id)
);

-- User-Project Assignments
CREATE TABLE user_project_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Assignment type
    assignment_type VARCHAR(20) NOT NULL,  -- auto, manual, self
    assigned_by UUID,                       -- Admin ID for manual assignments
    assignment_reason TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    removed_at TIMESTAMPTZ,
    
    UNIQUE(user_id, project_id),
    CONSTRAINT valid_assignment_type CHECK (assignment_type IN ('auto', 'manual', 'self'))
);

CREATE INDEX idx_assignments_user ON user_project_assignments(user_id) WHERE is_active = true;
CREATE INDEX idx_assignments_project ON user_project_assignments(project_id) WHERE is_active = true;

-- User Active Project (current context)
CREATE TABLE user_active_projects (
    user_id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    session_count INTEGER DEFAULT 0,
    
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-Assignment Rules
CREATE TABLE project_auto_assign_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Rule definition
    rule_name VARCHAR(100) NOT NULL,
    condition_type VARCHAR(50) NOT NULL,  -- PORTFOLIO, ACTIVITY, PREFERENCE, ONBOARDING
    condition_params JSONB NOT NULL,
    
    -- Behavior
    priority INTEGER DEFAULT 1,
    auto_switch BOOLEAN DEFAULT false,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Project Invitations (for invite_only projects)
CREATE TABLE project_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Invitation details
    email VARCHAR(255),
    invitation_code VARCHAR(50) UNIQUE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, expired, revoked
    
    -- Timestamps
    invited_by UUID NOT NULL,
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    accepted_by UUID,
    
    CONSTRAINT valid_invitation_status CHECK (status IN ('pending', 'accepted', 'expired', 'revoked'))
);

-- Project Chat Sessions (extends existing chat_sessions)
CREATE TABLE project_chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,  -- References chat_sessions
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    
    -- Context used
    system_prompt_version INTEGER DEFAULT 1,
    knowledge_chunks_used INTEGER DEFAULT 0,
    tools_used TEXT[] DEFAULT '{}',
    
    -- Metrics
    messages_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    
    UNIQUE(session_id)
);

CREATE INDEX idx_project_sessions_project ON project_chat_sessions(project_id, created_at DESC);
CREATE INDEX idx_project_sessions_user ON project_chat_sessions(user_id, created_at DESC);

-- Project Analytics (Daily aggregation)
CREATE TABLE project_analytics_daily (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- User metrics
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    returning_users INTEGER DEFAULT 0,
    
    -- Session metrics
    total_sessions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    avg_session_duration_seconds INTEGER,
    avg_messages_per_session DECIMAL(6,2),
    
    -- Engagement
    satisfaction_score_avg DECIMAL(3,2),
    helpful_rate DECIMAL(5,4),
    
    -- Knowledge usage
    knowledge_queries INTEGER DEFAULT 0,
    knowledge_hit_rate DECIMAL(5,4),
    top_queries JSONB DEFAULT '[]',
    
    -- Transactions (if applicable)
    total_transactions INTEGER DEFAULT 0,
    total_volume_usd DECIMAL(20,2) DEFAULT 0,
    transaction_success_rate DECIMAL(5,4),
    
    -- Tools
    tool_usage JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(project_id, date)
);

CREATE INDEX idx_project_analytics_date ON project_analytics_daily(project_id, date DESC);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Active Projects with Stats
CREATE VIEW v_projects_with_stats AS
SELECT 
    p.*,
    COALESCE(ua.user_count, 0) as total_users,
    COALESCE(ua.active_count, 0) as active_users,
    kb.total_documents,
    kb.total_chunks
FROM projects p
LEFT JOIN (
    SELECT 
        project_id,
        COUNT(*) as user_count,
        COUNT(*) FILTER (WHERE last_active_at > NOW() - INTERVAL '7 days') as active_count
    FROM user_project_assignments
    WHERE is_active = true
    GROUP BY project_id
) ua ON ua.project_id = p.id
LEFT JOIN project_knowledge_bases kb ON kb.project_id = p.id
WHERE p.status = 'active';

-- View: Distillation Summary
CREATE VIEW v_distillation_summary AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE route_type = 'CACHE') as cache_hits,
    COUNT(*) FILTER (WHERE route_type = 'STATIC') as static_responses,
    COUNT(*) FILTER (WHERE route_type = 'LIGHT_LLM') as light_llm,
    COUNT(*) FILTER (WHERE route_type = 'FULL_LLM') as full_llm,
    COUNT(*) FILTER (WHERE route_type = 'REJECT') as rejected,
    AVG(classification_latency_ms) as avg_classification_ms,
    AVG(intent_confidence) as avg_confidence
FROM distillation_requests
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Get best project for user based on auto-assign rules
CREATE OR REPLACE FUNCTION get_recommended_project(p_user_id UUID)
RETURNS UUID AS $$
DECLARE
    v_project_id UUID;
    v_rule RECORD;
BEGIN
    -- Check each rule by priority
    FOR v_rule IN 
        SELECT r.*, p.id as project_id
        FROM project_auto_assign_rules r
        JOIN projects p ON p.id = r.project_id
        WHERE r.is_active = true
            AND p.status = 'active'
        ORDER BY r.priority DESC
    LOOP
        -- Evaluate rule (simplified - actual implementation would check conditions)
        IF v_rule.condition_type = 'PORTFOLIO' THEN
            -- Check user portfolio against condition_params
            -- This is a placeholder - actual implementation needed
            NULL;
        ELSIF v_rule.condition_type = 'ONBOARDING' THEN
            -- Check user onboarding preferences
            NULL;
        END IF;
    END LOOP;
    
    -- Return default project if no match
    SELECT id INTO v_project_id
    FROM projects
    WHERE status = 'active' AND is_featured = true
    ORDER BY display_order
    LIMIT 1;
    
    RETURN v_project_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Search knowledge base
CREATE OR REPLACE FUNCTION search_project_knowledge(
    p_project_id UUID,
    p_query_embedding vector(1536),
    p_limit INTEGER DEFAULT 5,
    p_similarity_threshold DECIMAL DEFAULT 0.7
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    chunk_text TEXT,
    similarity DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.document_id,
        c.chunk_text,
        1 - (c.embedding <=> p_query_embedding) as similarity
    FROM project_knowledge_chunks c
    WHERE c.knowledge_base_id = (
        SELECT id FROM project_knowledge_bases WHERE project_id = p_project_id
    )
    AND 1 - (c.embedding <=> p_query_embedding) >= p_similarity_threshold
    ORDER BY c.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SEED DATA - Default Projects
-- ============================================================================

-- Insert 10 default projects
INSERT INTO projects (slug, name, description, icon, color, status, visibility, system_prompt, welcome_message, enabled_protocols, enabled_chains, enabled_tools, risk_config, created_by) VALUES

-- 1. Savings Project
('savings', 'Smart Savings', 'Low-risk yield optimization for stablecoin holdings', '💰', '#10B981', 'active', 'public',
'You are Anvil''s Savings Specialist, focused on helping users maximize returns on their stablecoin holdings with minimal risk.

Your expertise includes:
- Stablecoin yield opportunities across protocols
- Risk assessment for different yield strategies
- USDC, USDT, DAI optimization
- Understanding of depeg risks and mitigation

Guidelines:
- Always prioritize capital preservation over yield
- Recommend only audited, battle-tested protocols
- Explain risks clearly before any action
- Focus on APY consistency over maximum returns',
'Welcome to Smart Savings! 💰

I help you find the best low-risk yields for your stablecoins.

What would you like to optimize today?',
ARRAY['aave', 'compound', 'morpho', 'yearn'],
ARRAY['ethereum', 'arbitrum', 'base'],
ARRAY['lend', 'analyze_portfolio', 'check_health'],
'{"max_slippage_bps": 50, "max_position_usd": 100000, "allowed_tokens": ["USDC", "USDT", "DAI", "FRAX"]}',
'00000000-0000-0000-0000-000000000001'),

-- 2. Earning Project
('earning', 'Yield Farming', 'Active yield farming and liquidity provision strategies', '🌾', '#F59E0B', 'active', 'public',
'You are Anvil''s Yield Farming Expert, helping users maximize returns through active DeFi strategies.

Your expertise includes:
- Liquidity provision on Uniswap, Curve, Balancer
- Yield farming opportunities across chains
- Impermanent loss calculations and mitigation

Guidelines:
- Explain impermanent loss risk for every LP position
- Calculate realistic APY after fees
- Consider reward token sustainability',
'Welcome to Yield Farming! 🌾

I''m here to help you find and manage high-yield DeFi opportunities.

What yields are you looking to capture?',
ARRAY['uniswap', 'curve', 'balancer', 'convex', 'yearn', 'beefy'],
ARRAY['ethereum', 'arbitrum', 'polygon', 'optimism'],
ARRAY['swap', 'stake', 'lend', 'analyze_portfolio'],
'{"max_slippage_bps": 100, "max_position_usd": 50000}',
'00000000-0000-0000-0000-000000000001'),

-- 3. Aave Project
('aave', 'Aave Lending', 'Complete Aave lending and borrowing assistance', '🏦', '#B6509E', 'active', 'public',
'You are Anvil''s Aave Specialist, an expert in the Aave lending protocol.

Your expertise includes:
- Supply and borrow optimization on Aave V3
- Health factor management and liquidation prevention
- E-mode strategies for correlated assets

Guidelines:
- Always check health factor before borrowing
- Warn about liquidation risks clearly
- Explain interest rate models',
'Welcome to Aave Lending! 🏦

I''m your dedicated Aave assistant.

What would you like to do with Aave today?',
ARRAY['aave'],
ARRAY['ethereum', 'arbitrum', 'polygon', 'optimism', 'base'],
ARRAY['lend', 'borrow', 'check_health', 'swap'],
'{"max_slippage_bps": 50, "max_position_usd": 100000, "min_health_factor": 1.5}',
'00000000-0000-0000-0000-000000000001'),

-- 4. Trading Project
('trading', 'DeFi Trading', 'Spot and perpetual futures trading assistance', '📈', '#3B82F6', 'active', 'public',
'You are Anvil''s Trading Assistant, helping users execute trades in DeFi markets.

Your expertise includes:
- DEX aggregation for best execution
- Perpetual futures on Hyperliquid, GMX
- Leverage management and risk

Guidelines:
- Always quote slippage and price impact
- Warn about leverage risks
- Never provide financial advice on direction',
'Welcome to DeFi Trading! 📈

I help you execute trades efficiently.

What trade are you looking to execute?',
ARRAY['uniswap', '1inch', 'hyperliquid', 'gmx', 'dydx'],
ARRAY['ethereum', 'arbitrum', 'optimism'],
ARRAY['swap', 'trade_perps', 'analyze_portfolio'],
'{"max_slippage_bps": 100, "max_leverage": 10, "max_position_usd": 25000}',
'00000000-0000-0000-0000-000000000001'),

-- 5. Staking Project
('staking', 'Staking Hub', 'ETH staking and liquid staking token management', '🥩', '#8B5CF6', 'active', 'public',
'You are Anvil''s Staking Expert, specializing in Ethereum staking and LSDs.

Your expertise includes:
- Native ETH staking requirements
- Liquid staking with Lido, Rocket Pool
- LST yield optimization

Guidelines:
- Explain staking vs liquid staking tradeoffs
- Discuss slashing risks honestly
- Compare LST options fairly',
'Welcome to Staking Hub! 🥩

I''m here to help you stake your ETH.

How would you like to put your ETH to work?',
ARRAY['lido', 'rocket_pool', 'coinbase', 'eigenlayer'],
ARRAY['ethereum'],
ARRAY['stake', 'swap', 'analyze_portfolio'],
'{"max_slippage_bps": 50, "max_position_usd": 500000, "allowed_tokens": ["ETH", "stETH", "rETH", "cbETH"]}',
'00000000-0000-0000-0000-000000000001'),

-- 6. Bridge Project
('bridge', 'Cross-Chain Bridge', 'Safe cross-chain asset transfers', '🌉', '#EC4899', 'active', 'public',
'You are Anvil''s Bridge Expert, helping users move assets across chains safely.

Your expertise includes:
- Native bridges vs third-party bridges
- Bridge security and risk assessment
- Gas optimization for bridging

Guidelines:
- Always verify bridge contract addresses
- Warn about bridge security history
- Explain expected wait times',
'Welcome to Cross-Chain Bridge! 🌉

I help you move assets safely between blockchains.

Where would you like to move your assets?',
ARRAY['arbitrum_bridge', 'optimism_bridge', 'polygon_bridge', 'stargate', 'across'],
ARRAY['ethereum', 'arbitrum', 'optimism', 'polygon', 'base'],
ARRAY['bridge', 'swap', 'analyze_portfolio'],
'{"max_slippage_bps": 100, "max_position_usd": 100000}',
'00000000-0000-0000-0000-000000000001'),

-- 7. Portfolio Project
('portfolio', 'Portfolio Manager', 'Portfolio tracking and optimization', '📊', '#06B6D4', 'active', 'public',
'You are Anvil''s Portfolio Manager, helping users track and optimize holdings.

Your expertise includes:
- Multi-chain portfolio aggregation
- Performance attribution analysis
- Risk assessment and diversification

Guidelines:
- Provide comprehensive portfolio views
- Calculate true cost basis
- Identify concentration risks',
'Welcome to Portfolio Manager! 📊

I help you understand and optimize your DeFi portfolio.

Want me to analyze your current portfolio?',
ARRAY['all'],
ARRAY['ethereum', 'arbitrum', 'polygon', 'optimism', 'base'],
ARRAY['analyze_portfolio', 'swap', 'rebalance'],
'{"max_slippage_bps": 100, "max_position_usd": 500000}',
'00000000-0000-0000-0000-000000000001'),

-- 8. Governance Project
('governance', 'DAO Governance', 'DAO participation and voting', '🗳️', '#F97316', 'active', 'public',
'You are Anvil''s Governance Expert, helping users participate in DeFi governance.

Your expertise includes:
- Understanding DAO proposals
- Voting strategies and delegation
- Governance token economics

Guidelines:
- Summarize proposals objectively
- Never recommend how to vote
- Highlight contentious issues',
'Welcome to DAO Governance! 🗳️

I help you participate in DeFi governance.

Which DAO would you like to engage with?',
ARRAY['aave_governance', 'uniswap_governance', 'compound_governance', 'curve_governance'],
ARRAY['ethereum'],
ARRAY['governance', 'delegate', 'analyze_proposal'],
'{}',
'00000000-0000-0000-0000-000000000001'),

-- 9. Risk Project
('risk', 'Risk Management', 'Position protection and risk mitigation', '🛡️', '#EF4444', 'active', 'public',
'You are Anvil''s Risk Manager, helping users protect positions and manage risks.

Your expertise includes:
- Position risk assessment
- Hedging strategies
- Liquidation prevention
- Insurance protocols

Guidelines:
- Prioritize capital preservation
- Quantify risks clearly
- Suggest appropriate hedges',
'Welcome to Risk Management! 🛡️

I help you protect your DeFi positions.

Would you like me to analyze your risk profile?',
ARRAY['aave', 'compound', 'nexus_mutual', 'insurace', 'gmx'],
ARRAY['ethereum', 'arbitrum'],
ARRAY['check_health', 'analyze_portfolio', 'hedge', 'insure'],
'{"max_slippage_bps": 50, "conservative_mode": true}',
'00000000-0000-0000-0000-000000000001'),

-- 10. NFT Finance Project
('nft-finance', 'NFT Finance', 'NFT collateral and financial strategies', '🎨', '#A855F7', 'active', 'public',
'You are Anvil''s NFT Finance Expert, helping users leverage NFTs.

Your expertise includes:
- NFT-backed lending
- Floor price tracking
- NFT fractionalization

Guidelines:
- Verify collection authenticity
- Explain liquidation risks for NFT loans
- Warn about illiquidity risks',
'Welcome to NFT Finance! 🎨

I help you unlock the financial potential of your NFTs.

What would you like to do with your NFTs?',
ARRAY['blur_lending', 'nftfi', 'bendao', 'sudoswap'],
ARRAY['ethereum'],
ARRAY['nft_lend', 'nft_borrow', 'check_floor', 'analyze_portfolio'],
'{"max_slippage_bps": 200, "max_position_usd": 50000}',
'00000000-0000-0000-0000-000000000001');

-- Create knowledge bases for each project
INSERT INTO project_knowledge_bases (project_id, name, description)
SELECT id, name || ' Knowledge Base', 'Knowledge base for ' || name
FROM projects;
