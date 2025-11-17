-- ============================================================================
-- ANVIL COMPLETE DATABASE SCHEMA - IMPLEMENTATION READY
-- ============================================================================
-- Database: anvil_production
-- Engine: MySQL 8.0+
-- Character Set: utf8mb4
-- Collation: utf8mb4_unicode_ci
-- Version: 2.0
-- Last Updated: November 16, 2025
-- Total Tables: 27
-- ============================================================================

-- Drop existing database (CAUTION: Only for fresh installations)
-- DROP DATABASE IF EXISTS anvil_production;

-- Create database
CREATE DATABASE IF NOT EXISTS anvil_production
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE anvil_production;

-- ============================================================================
-- SECTION 1: USER MANAGEMENT (1 table)
-- ============================================================================
-- Purpose: Core user authentication, roles, and KYC management
-- Critical: Every user in the system has exactly one record here
-- ============================================================================

-- Table: users
-- Purpose: Core user accounts with Privy authentication and role management
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(36) NOT NULL UNIQUE COMMENT 'UUID for external systems',
    privy_user_id VARCHAR(255) NOT NULL UNIQUE COMMENT 'Privy DID identifier',
    email VARCHAR(255) NOT NULL UNIQUE,
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    phone VARCHAR(20),
    password_hash VARCHAR(255) COMMENT 'Bcrypt hashed password (optional, Privy handles auth)',
    email_verified BOOLEAN DEFAULT FALSE,
    role TINYINT NOT NULL DEFAULT 2 COMMENT '0=ADMIN, 1=AUDITOR, 2=CLIENT',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '0=INACTIVE, 1=ACTIVE, 2=DELETED',
    last_login_at TIMESTAMP NULL,
    last_active_at TIMESTAMP NULL,
    kyc_status ENUM('none', 'pending', 'approved', 'rejected') DEFAULT 'none',
    kyc_completed_at TIMESTAMP NULL,
    terms_accepted_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL COMMENT 'Soft delete timestamp',
    
    INDEX idx_email (email),
    INDEX idx_uid (uid),
    INDEX idx_privy_user_id (privy_user_id),
    INDEX idx_role_status (role, status),
    INDEX idx_created_at (created_at),
    INDEX idx_kyc_status (kyc_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Core user accounts with authentication and KYC';


-- ============================================================================
-- SECTION 2: WALLET & MULTI-CHAIN (2 tables)
-- ============================================================================
-- Purpose: Wallet management across multiple blockchain networks
-- Integration: Privy embedded wallets with MPC key management
-- ============================================================================

-- Table: wallets
-- Purpose: Primary wallet records linked to Privy embedded wallets
DROP TABLE IF EXISTS wallets;
CREATE TABLE wallets (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    privy_wallet_id VARCHAR(255) NOT NULL UNIQUE COMMENT 'Privy internal wallet identifier',
    address VARCHAR(42) NOT NULL UNIQUE COMMENT 'Primary wallet address (0x...)',
    provider VARCHAR(20) NOT NULL DEFAULT 'privy' COMMENT 'Wallet provider: privy',
    default_chain ENUM('arbitrum', 'base', 'hyperliquid') DEFAULT 'arbitrum',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '0=INACTIVE, 1=ACTIVE, 2=DELETED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_address (address),
    INDEX idx_privy_wallet_id (privy_wallet_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Primary wallet records with Privy integration';

-- Table: chain_addresses
-- Purpose: Multi-chain address mapping for cross-chain support
DROP TABLE IF EXISTS chain_addresses;
CREATE TABLE chain_addresses (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    wallet_id BIGINT UNSIGNED NOT NULL,
    chain ENUM('arbitrum', 'base', 'hyperliquid') NOT NULL,
    address VARCHAR(255) NOT NULL COMMENT 'Chain-specific address format',
    is_active BOOLEAN DEFAULT TRUE,
    balance_usd DECIMAL(20, 2) DEFAULT 0.00 COMMENT 'Cached balance in USD',
    last_balance_update TIMESTAMP NULL COMMENT 'Last RPC balance fetch',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
    UNIQUE KEY unique_wallet_chain (wallet_id, chain),
    INDEX idx_wallet_id (wallet_id),
    INDEX idx_chain (chain),
    INDEX idx_address (address),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Multi-chain address mapping with balance tracking';


-- ============================================================================
-- SECTION 3: TRANSACTIONS (1 table)
-- ============================================================================
-- Purpose: All blockchain transactions (swaps, funding, earning, saving)
-- Critical: Central audit trail for all on-chain activity
-- ============================================================================

-- Table: transactions
-- Purpose: Complete transaction history across all chains and types
DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    wallet_id BIGINT UNSIGNED NOT NULL,
    type TINYINT NOT NULL COMMENT '0=SWAP, 1=FUND, 2=EARN, 3=SAVE, 4=SUBSCRIPTION',
    chain ENUM('arbitrum', 'base', 'hyperliquid') NOT NULL,
    asset_in VARCHAR(20) COMMENT 'Input token symbol',
    amount_in DECIMAL(30, 18) COMMENT 'Input amount',
    asset_out VARCHAR(20) COMMENT 'Output token symbol',
    amount_out DECIMAL(30, 18) COMMENT 'Output amount',
    fee DECIMAL(30, 18) COMMENT 'Gas fee in native token',
    fee_usd DECIMAL(10, 2) COMMENT 'Gas fee in USD',
    tx_hash VARCHAR(66) UNIQUE COMMENT 'Blockchain transaction hash',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '0=PENDING, 1=SUCCESS, 2=FAILED',
    dex_aggregator VARCHAR(50) COMMENT 'DEX used: 1inch, 0x, hyperliquid',
    dex_route JSON COMMENT 'Routing details and pools used',
    slippage DECIMAL(5, 2) COMMENT 'Slippage tolerance percentage',
    error_message TEXT COMMENT 'Error details if failed',
    block_number BIGINT UNSIGNED COMMENT 'Block number where confirmed',
    confirmed_at TIMESTAMP NULL COMMENT 'On-chain confirmation time',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_wallet_id (wallet_id),
    INDEX idx_tx_hash (tx_hash),
    INDEX idx_status (status),
    INDEX idx_type (type),
    INDEX idx_chain (chain),
    INDEX idx_created_at (created_at),
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='All blockchain transactions and activity';


-- ============================================================================
-- SECTION 4: DEFI OPERATIONS (3 tables)
-- ============================================================================
-- Purpose: DeFi position tracking (perpetuals, yield farming, auto-save)
-- Critical: Real-time monitoring for liquidation risk and earnings
-- ============================================================================

-- Table: hyperliquid_positions
-- Purpose: Perpetual trading positions on Hyperliquid L1
DROP TABLE IF EXISTS hyperliquid_positions;
CREATE TABLE hyperliquid_positions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    wallet_id BIGINT UNSIGNED NOT NULL,
    symbol VARCHAR(20) NOT NULL COMMENT 'Trading pair: ETH-USD, BTC-USD',
    side ENUM('long', 'short') NOT NULL,
    leverage DECIMAL(5, 2) NOT NULL COMMENT 'Leverage multiplier: 1.0-20.0',
    size DECIMAL(30, 18) NOT NULL COMMENT 'Position size in base asset',
    entry_price DECIMAL(20, 8) NOT NULL COMMENT 'Average entry price USD',
    mark_price DECIMAL(20, 8) COMMENT 'Current market price',
    liquidation_price DECIMAL(20, 8) COMMENT 'Liquidation price threshold',
    unrealized_pnl DECIMAL(20, 8) COMMENT 'Current profit/loss USD',
    realized_pnl DECIMAL(20, 8) DEFAULT 0 COMMENT 'Locked-in profit/loss',
    margin DECIMAL(20, 8) NOT NULL COMMENT 'Collateral locked',
    funding_rate DECIMAL(10, 6) COMMENT 'Hourly funding rate',
    last_funding_payment DECIMAL(20, 8) COMMENT 'Last funding payment amount',
    status ENUM('open', 'closed', 'liquidated') DEFAULT 'open',
    hyperliquid_order_id VARCHAR(100) COMMENT 'Hyperliquid internal order ID',
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_symbol (symbol),
    INDEX idx_user_status (user_id, status),
    INDEX idx_opened_at (opened_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Hyperliquid perpetual trading positions';

-- Table: earn_positions
-- Purpose: Yield farming and earning positions across DeFi protocols
DROP TABLE IF EXISTS earn_positions;
CREATE TABLE earn_positions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    wallet_id BIGINT UNSIGNED NOT NULL,
    chain ENUM('arbitrum', 'base') NOT NULL,
    protocol VARCHAR(50) NOT NULL COMMENT 'aave, compound, curve, uniswap-v3',
    asset VARCHAR(20) NOT NULL COMMENT 'Deposited asset: USDC, ETH, WBTC',
    amount_deposited DECIMAL(30, 18) NOT NULL,
    current_value DECIMAL(30, 18) COMMENT 'Current position value',
    apy DECIMAL(8, 4) COMMENT 'APY at deposit time',
    current_apy DECIMAL(8, 4) COMMENT 'Current APY (updated hourly)',
    rewards_earned DECIMAL(30, 18) DEFAULT 0 COMMENT 'Rewards in asset units',
    rewards_earned_usd DECIMAL(20, 2) DEFAULT 0 COMMENT 'Rewards in USD',
    status ENUM('active', 'withdrawn', 'emergency_exit') DEFAULT 'active',
    transaction_hash VARCHAR(66) COMMENT 'Related transaction hash',
    deposit_tx_hash VARCHAR(66) COMMENT 'Deposit transaction hash',
    withdraw_tx_hash VARCHAR(66) COMMENT 'Withdrawal transaction hash',
    deposited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    withdrawn_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_protocol (protocol),
    INDEX idx_chain (chain),
    INDEX idx_deposited_at (deposited_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='DeFi yield farming and earning positions';

-- Table: save_schedules
-- Purpose: Automated recurring savings schedules
DROP TABLE IF EXISTS save_schedules;
CREATE TABLE save_schedules (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    wallet_id BIGINT UNSIGNED NOT NULL,
    chain ENUM('arbitrum', 'base') NOT NULL,
    asset VARCHAR(20) NOT NULL COMMENT 'Asset to save: USDC, ETH',
    amount DECIMAL(30, 18) NOT NULL COMMENT 'Amount per execution',
    frequency ENUM('daily', 'weekly', 'biweekly', 'monthly') NOT NULL,
    day_of_week TINYINT COMMENT '0=Sunday, 1=Monday, ..., 6=Saturday',
    day_of_month TINYINT COMMENT '1-31 for monthly frequency',
    destination_protocol VARCHAR(50) COMMENT 'aave, compound, wallet',
    status ENUM('active', 'paused', 'completed', 'failed') DEFAULT 'active',
    next_execution_at TIMESTAMP NOT NULL,
    last_execution_at TIMESTAMP NULL,
    total_saved DECIMAL(30, 18) DEFAULT 0 COMMENT 'Cumulative amount saved',
    execution_count INT DEFAULT 0 COMMENT 'Number of executions',
    max_executions INT COMMENT 'Max executions (null = infinite)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_next_execution (next_execution_at),
    INDEX idx_status_next_execution (status, next_execution_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Automated recurring savings schedules';


-- ============================================================================
-- SECTION 5: PAYMENTS & SUBSCRIPTIONS (3 tables)
-- ============================================================================
-- Purpose: Stripe payment processing and subscription management
-- Integration: Stripe API for credit card and ACH payments
-- ============================================================================

-- Table: funding_transactions
-- Purpose: Fiat-to-crypto funding via Stripe
DROP TABLE IF EXISTS funding_transactions;
CREATE TABLE funding_transactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    wallet_id BIGINT UNSIGNED NOT NULL,
    stripe_payment_intent_id VARCHAR(255) UNIQUE COMMENT 'Stripe PaymentIntent ID',
    amount_fiat DECIMAL(10, 2) NOT NULL COMMENT 'Fiat amount (USD)',
    amount_crypto DECIMAL(30, 18) COMMENT 'Crypto received',
    asset VARCHAR(20) DEFAULT 'USDC' COMMENT 'Crypto asset purchased',
    chain ENUM('arbitrum', 'base') NOT NULL,
    payment_method VARCHAR(50) COMMENT 'card, bank_transfer, ach',
    status ENUM('pending', 'processing', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    stripe_status VARCHAR(50) COMMENT 'Stripe PaymentIntent status',
    transaction_hash VARCHAR(66) COMMENT 'On-chain transaction hash',
    fee_stripe DECIMAL(10, 2) COMMENT 'Stripe processing fee',
    fee_network DECIMAL(10, 2) COMMENT 'Network gas fee',
    error_message TEXT,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_stripe_payment_intent (stripe_payment_intent_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Fiat-to-crypto funding transactions via Stripe';

-- Table: subscriptions
-- Purpose: Pro subscription management
DROP TABLE IF EXISTS subscriptions;
CREATE TABLE subscriptions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    stripe_subscription_id VARCHAR(255) UNIQUE COMMENT 'Stripe Subscription ID',
    stripe_customer_id VARCHAR(255) COMMENT 'Stripe Customer ID',
    plan ENUM('free', 'pro') DEFAULT 'free',
    status ENUM('active', 'past_due', 'canceled', 'trialing', 'paused') DEFAULT 'active',
    price_monthly DECIMAL(10, 2) DEFAULT 9.99,
    billing_cycle_start TIMESTAMP NULL,
    billing_cycle_end TIMESTAMP NULL,
    trial_end TIMESTAMP NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_subscription (user_id),
    INDEX idx_stripe_subscription (stripe_subscription_id),
    INDEX idx_status (status),
    INDEX idx_plan (plan)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User subscription management';

-- Table: subscription_payments
-- Purpose: Subscription payment history
DROP TABLE IF EXISTS subscription_payments;
CREATE TABLE subscription_payments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    subscription_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    stripe_invoice_id VARCHAR(255) UNIQUE COMMENT 'Stripe Invoice ID',
    amount DECIMAL(10, 2) NOT NULL,
    status ENUM('paid', 'pending', 'failed', 'refunded') DEFAULT 'pending',
    billing_reason VARCHAR(50) COMMENT 'subscription_create, subscription_cycle',
    payment_method VARCHAR(50),
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_user_id (user_id),
    INDEX idx_stripe_invoice (stripe_invoice_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Subscription payment history';


-- ============================================================================
-- SECTION 6: AI & AGENTS - TELEMETRY (9 tables)
-- ============================================================================
-- Purpose: AI conversation tracking, agent execution monitoring, and cost analytics
-- Critical: Cost control, debugging, and user experience optimization
-- ============================================================================

-- Table: llm_conversations
-- Purpose: Complete chat conversation history with cost tracking
DROP TABLE IF EXISTS llm_conversations;
CREATE TABLE llm_conversations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    session_id VARCHAR(100) NOT NULL COMMENT 'Frontend session identifier',
    model_id BIGINT UNSIGNED COMMENT 'FK to models table',
    provider VARCHAR(20) NOT NULL COMMENT 'vertex, bedrock',
    model_name VARCHAR(100) NOT NULL,
    prompt_text TEXT NOT NULL,
    response_text TEXT,
    input_tokens INT,
    output_tokens INT,
    total_tokens INT,
    cost_usd DECIMAL(10, 6) COMMENT 'Cost for this request',
    latency_ms INT COMMENT 'Response time in milliseconds',
    status ENUM('success', 'failed', 'rate_limited', 'fallback') DEFAULT 'success',
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_model_id (model_id),
    INDEX idx_provider (provider),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='LLM conversation history and cost tracking';

-- Table: agent_executions
-- Purpose: AI agent workflow execution tracking
DROP TABLE IF EXISTS agent_executions;
CREATE TABLE agent_executions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    conversation_id BIGINT UNSIGNED COMMENT 'FK to llm_conversations',
    agent_type VARCHAR(50) NOT NULL COMMENT 'research, risk, execution, analysis',
    workflow_type VARCHAR(50) NOT NULL COMMENT 'swap, buy, sell, earn, save, analysis',
    status ENUM('pending', 'running', 'completed', 'failed', 'canceled') DEFAULT 'pending',
    input_params JSON COMMENT 'Agent input parameters',
    output_result JSON COMMENT 'Agent execution output',
    total_tasks INT DEFAULT 0 COMMENT 'Number of tasks in workflow',
    completed_tasks INT DEFAULT 0,
    failed_tasks INT DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0,
    execution_time_ms INT COMMENT 'Total execution time',
    error_message TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES llm_conversations(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_agent_type (agent_type),
    INDEX idx_workflow_type (workflow_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='AI agent workflow execution tracking';

-- Table: agent_tasks
-- Purpose: Individual tasks within agent workflows
DROP TABLE IF EXISTS agent_tasks;
CREATE TABLE agent_tasks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    execution_id BIGINT UNSIGNED NOT NULL,
    task_name VARCHAR(100) NOT NULL COMMENT 'Task identifier',
    task_type VARCHAR(50) NOT NULL COMMENT 'research, validation, execution',
    status ENUM('pending', 'running', 'completed', 'failed', 'skipped') DEFAULT 'pending',
    input_data JSON,
    output_data JSON,
    error_message TEXT,
    execution_time_ms INT,
    retry_count INT DEFAULT 0,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES agent_executions(id) ON DELETE CASCADE,
    INDEX idx_execution_id (execution_id),
    INDEX idx_task_type (task_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Individual agent workflow tasks';

-- Table: agent_tools_usage
-- Purpose: Track tool usage by AI agents
DROP TABLE IF EXISTS agent_tools_usage;
CREATE TABLE agent_tools_usage (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    execution_id BIGINT UNSIGNED NOT NULL,
    task_id BIGINT UNSIGNED COMMENT 'FK to agent_tasks',
    tool_name VARCHAR(100) NOT NULL COMMENT 'price_feed, swap_quote, balance_check',
    input_params JSON,
    output_result JSON,
    status ENUM('success', 'failed', 'timeout') DEFAULT 'success',
    execution_time_ms INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES agent_executions(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES agent_tasks(id) ON DELETE SET NULL,
    INDEX idx_execution_id (execution_id),
    INDEX idx_task_id (task_id),
    INDEX idx_tool_name (tool_name),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='AI agent tool usage tracking';

-- Table: llm_rate_limit_events
-- Purpose: Track rate limiting and throttling events
DROP TABLE IF EXISTS llm_rate_limit_events;
CREATE TABLE llm_rate_limit_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    provider VARCHAR(20) NOT NULL COMMENT 'vertex, bedrock',
    model_name VARCHAR(100) NOT NULL,
    event_type ENUM('rate_limit', 'quota_exceeded', 'throttle', 'timeout') NOT NULL,
    user_id BIGINT UNSIGNED COMMENT 'User who triggered the event',
    error_code VARCHAR(50),
    error_message TEXT,
    retry_after_seconds INT COMMENT 'Retry-After header value',
    fallback_used BOOLEAN DEFAULT FALSE COMMENT 'Did we fallback to another provider?',
    fallback_provider VARCHAR(20) COMMENT 'Which provider was used as fallback',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_provider (provider),
    INDEX idx_model_name (model_name),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='LLM rate limiting and throttling events';

-- Table: llm_cost_alerts
-- Purpose: Track cost alerts and thresholds
DROP TABLE IF EXISTS llm_cost_alerts;
CREATE TABLE llm_cost_alerts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    alert_type ENUM('daily_threshold', 'weekly_threshold', 'monthly_threshold', 'user_spike') NOT NULL,
    threshold_usd DECIMAL(10, 2) NOT NULL,
    actual_cost_usd DECIMAL(10, 2) NOT NULL,
    time_period_start TIMESTAMP NOT NULL,
    time_period_end TIMESTAMP NOT NULL,
    user_id BIGINT UNSIGNED COMMENT 'If user-specific alert',
    provider VARCHAR(20) COMMENT 'If provider-specific alert',
    alert_sent BOOLEAN DEFAULT FALSE,
    alert_sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_alert_type (alert_type),
    INDEX idx_time_period (time_period_start, time_period_end),
    INDEX idx_alert_sent (alert_sent),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='LLM cost alerts and threshold monitoring';

-- Table: vertex_api_metrics
-- Purpose: Hourly aggregated Google Cloud Vertex AI metrics
DROP TABLE IF EXISTS vertex_api_metrics;
CREATE TABLE vertex_api_metrics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    model_id BIGINT UNSIGNED COMMENT 'FK to models table',
    region VARCHAR(50) NOT NULL COMMENT 'GCP region: us-central1, us-east1',
    requests_count INT DEFAULT 0,
    tokens_consumed BIGINT DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    quota_exceeded_count INT DEFAULT 0,
    rate_limit_count INT DEFAULT 0,
    avg_latency_ms INT,
    p95_latency_ms INT,
    p99_latency_ms INT,
    error_count INT DEFAULT 0,
    success_rate DECIMAL(5, 2) COMMENT 'Percentage: 0-100',
    failover_to_bedrock_count INT DEFAULT 0,
    time_window_start TIMESTAMP NOT NULL,
    time_window_end TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_model_id (model_id),
    INDEX idx_region (region),
    INDEX idx_time_window (time_window_start),
    UNIQUE KEY unique_model_region_window (model_id, region, time_window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Hourly Vertex AI metrics for monitoring';

-- Table: bedrock_api_metrics
-- Purpose: Hourly aggregated AWS Bedrock metrics
DROP TABLE IF EXISTS bedrock_api_metrics;
CREATE TABLE bedrock_api_metrics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    model_id BIGINT UNSIGNED COMMENT 'FK to models table',
    region VARCHAR(50) NOT NULL COMMENT 'AWS region: us-east-1, us-west-2',
    requests_count INT DEFAULT 0,
    tokens_consumed BIGINT DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    throttle_count INT DEFAULT 0 COMMENT 'Bedrock throttling errors',
    model_not_ready_count INT DEFAULT 0 COMMENT 'Model loading errors',
    avg_latency_ms INT,
    p95_latency_ms INT,
    p99_latency_ms INT,
    error_count INT DEFAULT 0,
    success_rate DECIMAL(5, 2),
    failover_from_vertex_count INT DEFAULT 0,
    time_window_start TIMESTAMP NOT NULL,
    time_window_end TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_model_id (model_id),
    INDEX idx_region (region),
    INDEX idx_time_window (time_window_start),
    UNIQUE KEY unique_model_region_window (model_id, region, time_window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Hourly Bedrock API metrics for failover monitoring';

-- Table: conversation_feedback
-- Purpose: User feedback on AI responses
DROP TABLE IF EXISTS conversation_feedback;
CREATE TABLE conversation_feedback (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    rating TINYINT COMMENT 'Rating: 1-5 stars',
    feedback_type ENUM('helpful', 'not_helpful', 'incorrect', 'offensive', 'other') NOT NULL,
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (conversation_id) REFERENCES llm_conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_user_id (user_id),
    INDEX idx_feedback_type (feedback_type),
    INDEX idx_rating (rating),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User feedback on AI conversations';


-- ============================================================================
-- SECTION 7: SYSTEM CONFIGURATION (3 tables)
-- ============================================================================
-- Purpose: System settings, AI model config, and audit logging
-- Security: Encrypted sensitive settings (API keys, secrets)
-- ============================================================================

-- Table: models
-- Purpose: AI model configuration and availability management
DROP TABLE IF EXISTS models;
CREATE TABLE models (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    provider VARCHAR(20) NOT NULL COMMENT 'vertex, bedrock',
    model_name VARCHAR(100) NOT NULL,
    label VARCHAR(255) NOT NULL COMMENT 'Display name for admin UI',
    is_default BOOLEAN DEFAULT FALSE COMMENT 'Default model for provider',
    is_available BOOLEAN DEFAULT TRUE COMMENT 'Model currently available',
    cost_per_1k_input_tokens DECIMAL(10, 8) NOT NULL,
    cost_per_1k_output_tokens DECIMAL(10, 8) NOT NULL,
    max_tokens INT COMMENT 'Token limit (e.g., 128000)',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '0=INACTIVE, 1=ACTIVE, 2=DEPRECATED',
    request_count BIGINT DEFAULT 0 COMMENT 'Total requests to this model',
    total_cost_usd DECIMAL(12, 2) DEFAULT 0 COMMENT 'Cumulative cost',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_provider_model (provider, model_name),
    INDEX idx_provider (provider),
    INDEX idx_model_name (model_name),
    INDEX idx_is_default (is_default),
    INDEX idx_status (status),
    INDEX idx_is_available (is_available)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='AI model configuration and tracking';

-- Table: settings
-- Purpose: System-wide configuration key-value store
DROP TABLE IF EXISTS settings;
CREATE TABLE settings (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(100) NOT NULL UNIQUE COMMENT 'Setting key identifier',
    `value` TEXT COMMENT 'Setting value (encrypted if sensitive)',
    scope TINYINT NOT NULL DEFAULT 0 COMMENT '0=GLOBAL, 1=SECURITY, 2=PAYMENTS, 3=AI',
    is_sensitive BOOLEAN DEFAULT FALSE COMMENT 'Encrypt value at rest',
    description TEXT COMMENT 'Setting description',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by BIGINT UNSIGNED COMMENT 'Admin user who updated',
    
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_key (`key`),
    INDEX idx_scope (scope),
    INDEX idx_is_sensitive (is_sensitive)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='System-wide configuration settings';

-- Table: audit_logs
-- Purpose: Immutable audit trail for admin actions
DROP TABLE IF EXISTS audit_logs;
CREATE TABLE audit_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor_user_id BIGINT UNSIGNED NOT NULL COMMENT 'Admin who performed action',
    action VARCHAR(100) NOT NULL COMMENT 'Action type: create, update, delete, approve, reject',
    entity VARCHAR(100) NOT NULL COMMENT 'Affected entity: user, wallet, transaction, setting',
    entity_id VARCHAR(100) COMMENT 'ID of affected record',
    payload_json JSON COMMENT 'Full action details: before/after values',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_actor_user_id (actor_user_id),
    INDEX idx_action (action),
    INDEX idx_entity (entity),
    INDEX idx_created_at (created_at),
    INDEX idx_actor_created (actor_user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Immutable audit trail for compliance';


-- ============================================================================
-- SECTION 8: NOTIFICATIONS (1 table)
-- ============================================================================
-- Purpose: Multi-channel notification queue and delivery tracking
-- Integration: FCM (push), SendGrid (email), Twilio (SMS)
-- ============================================================================

-- Table: notifications
-- Purpose: Notification queue and delivery status
DROP TABLE IF EXISTS notifications;
CREATE TABLE notifications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    type VARCHAR(100) NOT NULL COMMENT 'transaction_confirmed, liquidation_warning, deposit_completed',
    channel ENUM('push', 'email', 'in_app', 'sms') NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data_json JSON COMMENT 'Additional data: transaction_id, link, etc.',
    status ENUM('pending', 'sent', 'failed', 'read') DEFAULT 'pending',
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    sent_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL COMMENT 'When user opened (in-app only)',
    error_message TEXT COMMENT 'If status=failed, error details',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_created_at (created_at),
    INDEX idx_user_status (user_id, status),
    INDEX idx_type (type),
    INDEX idx_channel (channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Multi-channel notification queue';


-- ============================================================================
-- INITIAL DATA SEEDING
-- ============================================================================
-- Insert default AI models configuration
-- ============================================================================

INSERT INTO models (provider, model_name, label, is_default, is_available, 
    cost_per_1k_input_tokens, cost_per_1k_output_tokens, max_tokens, status) VALUES
-- Vertex AI Models
('vertex', 'gemini-1.5-flash', 'Gemini 1.5 Flash (Fast & Cheap)', TRUE, TRUE, 0.00002, 0.00006, 1000000, 1),
('vertex', 'gemini-1.5-pro', 'Gemini 1.5 Pro (Balanced)', FALSE, TRUE, 0.00125, 0.00375, 2000000, 1),
('vertex', 'gemini-2.0-flash-exp', 'Gemini 2.0 Flash (Experimental)', FALSE, TRUE, 0.00002, 0.00006, 1000000, 1),

-- AWS Bedrock Models
('bedrock', 'anthropic.claude-3-5-sonnet-20241022-v2:0', 'Claude 3.5 Sonnet v2', TRUE, TRUE, 0.00300, 0.01500, 200000, 1),
('bedrock', 'anthropic.claude-3-5-haiku-20241022-v1:0', 'Claude 3.5 Haiku', FALSE, TRUE, 0.00100, 0.00500, 200000, 1),
('bedrock', 'meta.llama3-1-70b-instruct-v1:0', 'Llama 3.1 70B', FALSE, TRUE, 0.00099, 0.00099, 128000, 1);

-- ============================================================================
-- Insert default system settings
-- ============================================================================

INSERT INTO settings (`key`, `value`, scope, is_sensitive, description) VALUES
-- Global Settings (scope=0)
('maintenance_mode', 'false', 0, FALSE, 'Enable/disable maintenance mode'),
('max_daily_trade_limit', '5000', 0, FALSE, 'Maximum daily trading limit per user (USD)'),
('max_position_size', '10000', 0, FALSE, 'Maximum position size per trade (USD)'),
('min_balance_threshold', '10', 0, FALSE, 'Minimum balance required for transactions (USD)'),

-- Security Settings (scope=1)
('jwt_secret', 'REPLACE_WITH_SECURE_SECRET', 1, TRUE, 'JWT token signing secret'),
('encryption_key', 'REPLACE_WITH_SECURE_KEY', 1, TRUE, 'AES-256 encryption key for sensitive data'),
('privy_app_id', 'REPLACE_WITH_PRIVY_APP_ID', 1, TRUE, 'Privy application ID'),
('privy_app_secret', 'REPLACE_WITH_PRIVY_SECRET', 1, TRUE, 'Privy application secret'),

-- Payment Settings (scope=2)
('stripe_api_key', 'REPLACE_WITH_STRIPE_KEY', 2, TRUE, 'Stripe API secret key'),
('stripe_webhook_secret', 'REPLACE_WITH_WEBHOOK_SECRET', 2, TRUE, 'Stripe webhook signing secret'),
('stripe_publishable_key', 'REPLACE_WITH_PUBLISHABLE_KEY', 2, FALSE, 'Stripe publishable key (client-side)'),
('funding_fee_percentage', '1.5', 2, FALSE, 'Funding transaction fee percentage'),

-- AI Settings (scope=3)
('vertex_project_id', 'REPLACE_WITH_PROJECT_ID', 3, TRUE, 'Google Cloud Project ID'),
('vertex_location', 'us-central1', 3, FALSE, 'Vertex AI location'),
('bedrock_access_key', 'REPLACE_WITH_ACCESS_KEY', 3, TRUE, 'AWS Bedrock access key'),
('bedrock_secret_key', 'REPLACE_WITH_SECRET_KEY', 3, TRUE, 'AWS Bedrock secret key'),
('bedrock_region', 'us-east-1', 3, FALSE, 'AWS Bedrock region'),
('max_tokens_per_request', '4000', 3, FALSE, 'Maximum tokens per LLM request'),
('daily_cost_alert_threshold', '50', 3, FALSE, 'Daily AI cost alert threshold (USD)');


-- ============================================================================
-- DATABASE VIEWS (Optional - for common queries)
-- ============================================================================

-- View: Active users with wallet info
CREATE OR REPLACE VIEW v_active_users AS
SELECT 
    u.id AS user_id,
    u.uid,
    u.email,
    u.firstname,
    u.lastname,
    u.role,
    u.status,
    u.kyc_status,
    u.created_at AS user_created_at,
    w.id AS wallet_id,
    w.address AS wallet_address,
    w.default_chain,
    COUNT(DISTINCT ca.id) AS active_chains
FROM users u
LEFT JOIN wallets w ON u.id = w.user_id
LEFT JOIN chain_addresses ca ON w.id = ca.wallet_id AND ca.is_active = TRUE
WHERE u.status = 1 AND u.deleted_at IS NULL
GROUP BY u.id, w.id;

-- View: User transaction summary
CREATE OR REPLACE VIEW v_user_transaction_summary AS
SELECT 
    t.user_id,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN t.status = 1 THEN 1 ELSE 0 END) AS successful_transactions,
    SUM(CASE WHEN t.type = 0 THEN 1 ELSE 0 END) AS swap_count,
    SUM(CASE WHEN t.type = 1 THEN 1 ELSE 0 END) AS fund_count,
    SUM(t.fee_usd) AS total_fees_paid_usd,
    MAX(t.created_at) AS last_transaction_at
FROM transactions t
GROUP BY t.user_id;

-- View: AI cost summary by user
CREATE OR REPLACE VIEW v_user_ai_costs AS
SELECT 
    c.user_id,
    COUNT(*) AS total_conversations,
    SUM(c.input_tokens) AS total_input_tokens,
    SUM(c.output_tokens) AS total_output_tokens,
    SUM(c.cost_usd) AS total_cost_usd,
    AVG(c.latency_ms) AS avg_latency_ms,
    MAX(c.created_at) AS last_conversation_at
FROM llm_conversations c
WHERE c.status = 'success'
GROUP BY c.user_id;


-- ============================================================================
-- STORED PROCEDURES (Optional - for common operations)
-- ============================================================================

-- Procedure: Get user dashboard summary
DELIMITER //
CREATE PROCEDURE sp_get_user_dashboard(IN p_user_id BIGINT)
BEGIN
    -- User profile
    SELECT * FROM users WHERE id = p_user_id;
    
    -- Wallet balances
    SELECT 
        ca.chain,
        ca.address,
        ca.balance_usd,
        ca.last_balance_update
    FROM chain_addresses ca
    INNER JOIN wallets w ON ca.wallet_id = w.id
    WHERE w.user_id = p_user_id AND ca.is_active = TRUE;
    
    -- Recent transactions
    SELECT * FROM transactions 
    WHERE user_id = p_user_id 
    ORDER BY created_at DESC 
    LIMIT 10;
    
    -- Active positions
    SELECT 
        'hyperliquid' AS position_type,
        symbol,
        side,
        size,
        unrealized_pnl,
        status
    FROM hyperliquid_positions 
    WHERE user_id = p_user_id AND status = 'open'
    UNION ALL
    SELECT 
        'earn' AS position_type,
        CONCAT(protocol, ' - ', asset) AS symbol,
        NULL AS side,
        current_value AS size,
        rewards_earned_usd AS unrealized_pnl,
        status
    FROM earn_positions 
    WHERE user_id = p_user_id AND status = 'active';
END //
DELIMITER ;


-- ============================================================================
-- DATABASE TRIGGERS (Optional - for automated workflows)
-- ============================================================================

-- Trigger: Update wallet balance on chain_addresses update
DELIMITER //
CREATE TRIGGER trg_update_wallet_balance_on_chain_update
AFTER UPDATE ON chain_addresses
FOR EACH ROW
BEGIN
    -- This is a placeholder - actual balance aggregation should be done by application
    -- You can add custom logic here if needed
    NULL;
END //
DELIMITER ;

-- Trigger: Create audit log on user status change
DELIMITER //
CREATE TRIGGER trg_audit_user_status_change
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_logs (
            actor_user_id,
            action,
            entity,
            entity_id,
            payload_json
        ) VALUES (
            NEW.id,
            'update',
            'user',
            NEW.id,
            JSON_OBJECT(
                'field', 'status',
                'old_value', OLD.status,
                'new_value', NEW.status
            )
        );
    END IF;
END //
DELIMITER ;
DELIMITER ;


-- ============================================================================
-- INDEXES SUMMARY
-- ============================================================================
-- Total estimated indexes across all tables: ~120
-- Critical indexes for performance:
-- - Foreign key indexes (automatic for InnoDB)
-- - Composite indexes on frequently joined columns
-- - Time-based indexes for range queries
-- - Status indexes for filtering active records
-- ============================================================================


-- ============================================================================
-- MAINTENANCE COMMANDS
-- ============================================================================
-- Run these periodically for database health

-- Analyze tables (run weekly)
-- ANALYZE TABLE users, wallets, transactions, llm_conversations, agent_executions;

-- Optimize tables (run monthly)
-- OPTIMIZE TABLE users, wallets, transactions, llm_conversations, agent_executions;

-- Check table integrity
-- CHECK TABLE users, wallets, transactions;

-- ============================================================================
-- BACKUP RECOMMENDATIONS
-- ============================================================================
-- 1. Full backup: Daily at 2 AM UTC
-- 2. Incremental backup: Every 6 hours
-- 3. Transaction log backup: Every hour
-- 4. Retention: 30 days for full backups, 7 days for incremental
-- 5. Test restore: Weekly
-- ============================================================================


-- ============================================================================
-- SECURITY NOTES
-- ============================================================================
-- 1. Replace all 'REPLACE_WITH_*' values in settings table with actual secrets
-- 2. Enable SSL/TLS for database connections
-- 3. Use separate read-only database user for reporting/analytics
-- 4. Implement row-level security if needed (MySQL 8.0+ supports this)
-- 5. Encrypt sensitive columns: password_hash, settings.value (when is_sensitive=TRUE)
-- 6. Enable binary logging for point-in-time recovery
-- 7. Set up database firewall rules (allow only application servers)
-- 8. Regular security audits on audit_logs table
-- ============================================================================


-- ============================================================================
-- PERFORMANCE TUNING PARAMETERS (my.cnf / my.ini)
-- ============================================================================
-- innodb_buffer_pool_size = 4G (or 70% of available RAM)
-- innodb_log_file_size = 512M
-- innodb_flush_log_at_trx_commit = 2 (better performance, slight durability trade-off)
-- max_connections = 200
-- query_cache_size = 0 (disabled in MySQL 8.0+)
-- tmp_table_size = 256M
-- max_heap_table_size = 256M
-- ============================================================================


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
-- Database: anvil_production
-- Total Tables: 27
-- Total Views: 3
-- Total Stored Procedures: 1
-- Total Triggers: 2
-- Estimated Size (1,000 users, 1 year): ~500 MB
-- Growth Rate: ~40-50 MB/month
-- ============================================================================

-- Implementation checklist:
-- [ ] Execute this script in MySQL 8.0+ environment
-- [ ] Replace all REPLACE_WITH_* values in settings table
-- [ ] Configure database connection pool (recommended: 20-50 connections)
-- [ ] Set up automated backup system
-- [ ] Configure monitoring and alerting
-- [ ] Create application database users with appropriate privileges
-- [ ] Test all foreign key relationships
-- [ ] Run sample queries to verify indexes
-- [ ] Document any custom business logic in application layer
-- [ ] Set up replication for high availability (if needed)

-- For questions or issues, refer to:
-- - MySQL 8.0 Documentation: https://dev.mysql.com/doc/refman/8.0/en/
-- - Privy Documentation: https://docs.privy.io/
-- - Stripe Documentation: https://stripe.com/docs/api
