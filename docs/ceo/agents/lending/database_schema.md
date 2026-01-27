# Lending Database Schema

**Version**: 1.0
**Date**: 2026-01-27
**Status**: Schema Specification
**Database**: PostgreSQL 16+

---

## Overview

This document defines the database schema for lending positions, transactions, and user preferences across Aave V3 and Morpho Protocol.

### Schema Requirements

- **UUID primary keys** for all tables
- **Timestamp tracking** (created_at, updated_at)
- **Soft deletes** where applicable
- **Indexing** for performance
- **Foreign key constraints** for referential integrity
- **Check constraints** for data validation

---

## Table: `lending_positions`

**Purpose**: Track user lending positions across protocols

```sql
CREATE TABLE lending_positions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User Reference
    user_id UUID NOT NULL,
    wallet_address VARCHAR(42) NOT NULL,

    -- Protocol Information
    protocol VARCHAR(20) NOT NULL CHECK (protocol IN ('aave', 'morpho')),
    chain VARCHAR(20) NOT NULL CHECK (chain IN ('ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 'avalanche')),

    -- Position Summary
    total_collateral_usd NUMERIC(20, 6) NOT NULL DEFAULT 0 CHECK (total_collateral_usd >= 0),
    total_debt_usd NUMERIC(20, 6) NOT NULL DEFAULT 0 CHECK (total_debt_usd >= 0),
    available_borrow_usd NUMERIC(20, 6) NOT NULL DEFAULT 0 CHECK (available_borrow_usd >= 0),

    -- Health Metrics
    health_factor NUMERIC(20, 18) NULL,  -- NULL if no debt
    current_ltv NUMERIC(5, 4) NULL CHECK (current_ltv >= 0 AND current_ltv <= 1),
    liquidation_threshold NUMERIC(5, 4) NULL CHECK (liquidation_threshold >= 0 AND liquidation_threshold <= 1),

    -- Risk Classification
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low' CHECK (risk_level IN ('low', 'moderate', 'high', 'critical', 'liquidatable')),
    requires_action BOOLEAN NOT NULL DEFAULT FALSE,
    last_health_check_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_healthy BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Soft Delete
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Indexes
CREATE INDEX idx_lending_positions_user_id ON lending_positions(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lending_positions_wallet_address ON lending_positions(wallet_address) WHERE deleted_at IS NULL;
CREATE INDEX idx_lending_positions_protocol_chain ON lending_positions(protocol, chain) WHERE deleted_at IS NULL;
CREATE INDEX idx_lending_positions_risk_level ON lending_positions(risk_level) WHERE deleted_at IS NULL AND risk_level IN ('high', 'critical', 'liquidatable');
CREATE INDEX idx_lending_positions_health_check ON lending_positions(last_health_check_at) WHERE deleted_at IS NULL AND health_factor < 1.5;

-- Comments
COMMENT ON TABLE lending_positions IS 'User lending positions across Aave and Morpho protocols';
COMMENT ON COLUMN lending_positions.health_factor IS 'Health factor: (Collateral × Liquidation Threshold) / Total Debt. NULL if no debt.';
COMMENT ON COLUMN lending_positions.risk_level IS 'Risk classification based on health factor';
COMMENT ON COLUMN lending_positions.requires_action IS 'TRUE if position needs immediate attention (HF < 1.2)';
```

---

## Table: `lending_supplies`

**Purpose**: Individual supply positions per asset

```sql
CREATE TABLE lending_supplies (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Position Reference
    position_id UUID NOT NULL REFERENCES lending_positions(id) ON DELETE CASCADE,

    -- Asset Information
    asset_symbol VARCHAR(20) NOT NULL,
    asset_address VARCHAR(42) NOT NULL,
    asset_decimals INTEGER NOT NULL CHECK (asset_decimals >= 0 AND asset_decimals <= 18),

    -- Supply Details
    amount NUMERIC(30, 18) NOT NULL CHECK (amount >= 0),
    amount_usd NUMERIC(20, 6) NOT NULL CHECK (amount_usd >= 0),

    -- Yield Information
    supply_apy NUMERIC(8, 6) NOT NULL CHECK (supply_apy >= 0),
    reward_apy NUMERIC(8, 6) DEFAULT 0 CHECK (reward_apy >= 0),
    total_apy NUMERIC(8, 6) GENERATED ALWAYS AS (supply_apy + reward_apy) STORED,

    -- Collateral Status
    is_collateral BOOLEAN NOT NULL DEFAULT TRUE,
    ltv NUMERIC(5, 4) NULL CHECK (ltv >= 0 AND ltv <= 1),

    -- Protocol-Specific
    atoken_address VARCHAR(42) NULL,  -- Aave aToken
    vault_address VARCHAR(42) NULL,   -- Morpho vault
    vault_name VARCHAR(255) NULL,     -- Morpho vault name

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_protocol_specific CHECK (
        (atoken_address IS NOT NULL AND vault_address IS NULL) OR
        (atoken_address IS NULL AND vault_address IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_lending_supplies_position_id ON lending_supplies(position_id);
CREATE INDEX idx_lending_supplies_asset ON lending_supplies(asset_symbol);
CREATE INDEX idx_lending_supplies_apy ON lending_supplies(total_apy DESC);

-- Comments
COMMENT ON TABLE lending_supplies IS 'Individual supply positions per asset';
COMMENT ON COLUMN lending_supplies.total_apy IS 'Computed column: supply_apy + reward_apy';
```

---

## Table: `lending_borrows`

**Purpose**: Individual borrow positions per asset (Aave only)

```sql
CREATE TABLE lending_borrows (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Position Reference
    position_id UUID NOT NULL REFERENCES lending_positions(id) ON DELETE CASCADE,

    -- Asset Information
    asset_symbol VARCHAR(20) NOT NULL,
    asset_address VARCHAR(42) NOT NULL,
    asset_decimals INTEGER NOT NULL CHECK (asset_decimals >= 0 AND asset_decimals <= 18),

    -- Borrow Details
    amount NUMERIC(30, 18) NOT NULL CHECK (amount >= 0),
    amount_usd NUMERIC(20, 6) NOT NULL CHECK (amount_usd >= 0),

    -- Interest Rate
    borrow_apy NUMERIC(8, 6) NOT NULL CHECK (borrow_apy >= 0),
    rate_mode VARCHAR(10) NOT NULL CHECK (rate_mode IN ('variable', 'stable')),

    -- Protocol-Specific
    debt_token_address VARCHAR(42) NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_lending_borrows_position_id ON lending_borrows(position_id);
CREATE INDEX idx_lending_borrows_asset ON lending_borrows(asset_symbol);
CREATE INDEX idx_lending_borrows_rate_mode ON lending_borrows(rate_mode);

-- Comments
COMMENT ON TABLE lending_borrows IS 'Individual borrow positions per asset (Aave only)';
COMMENT ON COLUMN lending_borrows.rate_mode IS 'Interest rate type: variable or stable';
```

---

## Table: `lending_transactions`

**Purpose**: Track all lending transactions

```sql
CREATE TABLE lending_transactions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User Reference
    user_id UUID NOT NULL,
    wallet_address VARCHAR(42) NOT NULL,

    -- Position Reference (nullable for failed transactions)
    position_id UUID NULL REFERENCES lending_positions(id) ON DELETE SET NULL,

    -- Transaction Details
    tx_hash VARCHAR(66) NOT NULL UNIQUE,
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('supply', 'withdraw', 'borrow', 'repay', 'leverage_loop', 'health_check')),

    -- Protocol Information
    protocol VARCHAR(20) NOT NULL CHECK (protocol IN ('aave', 'morpho')),
    chain VARCHAR(20) NOT NULL CHECK (chain IN ('ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 'avalanche')),

    -- Asset Information
    asset_symbol VARCHAR(20) NOT NULL,
    asset_address VARCHAR(42) NOT NULL,
    amount NUMERIC(30, 18) NOT NULL CHECK (amount >= 0),
    amount_usd NUMERIC(20, 6) NULL CHECK (amount_usd >= 0),

    -- Transaction Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'failed', 'reverted')),
    block_number BIGINT NULL,
    gas_used BIGINT NULL,
    gas_price_gwei NUMERIC(20, 9) NULL,
    total_gas_cost_usd NUMERIC(20, 6) NULL,

    -- Health Factor Impact (for borrow/withdraw)
    health_factor_before NUMERIC(20, 18) NULL,
    health_factor_after NUMERIC(20, 18) NULL,

    -- Error Information (for failed transactions)
    error_message TEXT NULL,
    error_code VARCHAR(50) NULL,

    -- Metadata
    metadata JSONB NULL,  -- Additional context (e.g., leverage loop iteration number)

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMP WITH TIME ZONE NULL
);

-- Indexes
CREATE INDEX idx_lending_transactions_user_id ON lending_transactions(user_id);
CREATE INDEX idx_lending_transactions_wallet_address ON lending_transactions(wallet_address);
CREATE INDEX idx_lending_transactions_position_id ON lending_transactions(position_id);
CREATE INDEX idx_lending_transactions_tx_hash ON lending_transactions(tx_hash);
CREATE INDEX idx_lending_transactions_status ON lending_transactions(status);
CREATE INDEX idx_lending_transactions_action_type ON lending_transactions(action_type);
CREATE INDEX idx_lending_transactions_created_at ON lending_transactions(created_at DESC);

-- Comments
COMMENT ON TABLE lending_transactions IS 'All lending transactions with status tracking';
COMMENT ON COLUMN lending_transactions.metadata IS 'Additional transaction context (JSON)';
```

---

## Table: `user_lending_preferences`

**Purpose**: User-specific lending preferences and risk settings

```sql
CREATE TABLE user_lending_preferences (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User Reference
    user_id UUID NOT NULL UNIQUE,

    -- Risk Preferences
    risk_tolerance VARCHAR(20) NOT NULL DEFAULT 'moderate' CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
    min_health_factor NUMERIC(5, 2) NOT NULL DEFAULT 1.5 CHECK (min_health_factor >= 1.0 AND min_health_factor <= 10.0),

    -- Auto-Management Settings
    auto_repay_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    auto_repay_threshold NUMERIC(5, 2) NOT NULL DEFAULT 1.2 CHECK (auto_repay_threshold >= 1.0 AND auto_repay_threshold <= 2.0),
    auto_add_collateral_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    auto_add_collateral_threshold NUMERIC(5, 2) NOT NULL DEFAULT 1.3 CHECK (auto_add_collateral_threshold >= 1.0 AND auto_add_collateral_threshold <= 2.0),

    -- Notification Settings
    notify_health_factor_warning BOOLEAN NOT NULL DEFAULT TRUE,
    notify_health_factor_critical BOOLEAN NOT NULL DEFAULT TRUE,
    notify_high_apy_opportunities BOOLEAN NOT NULL DEFAULT TRUE,

    -- Protocol Preferences
    preferred_protocol VARCHAR(20) NULL CHECK (preferred_protocol IN ('aave', 'morpho', NULL)),
    preferred_chains VARCHAR(255)[] NOT NULL DEFAULT ARRAY['ethereum', 'base'],  -- Array of preferred chains

    -- Leverage Settings
    max_leverage NUMERIC(5, 2) NOT NULL DEFAULT 2.0 CHECK (max_leverage >= 1.0 AND max_leverage <= 10.0),
    allow_leverage_loops BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_lending_preferences_user_id ON user_lending_preferences(user_id);
CREATE INDEX idx_user_lending_preferences_auto_management ON user_lending_preferences(auto_repay_enabled, auto_add_collateral_enabled) WHERE auto_repay_enabled OR auto_add_collateral_enabled;

-- Comments
COMMENT ON TABLE user_lending_preferences IS 'User-specific lending preferences and risk settings';
COMMENT ON COLUMN user_lending_preferences.min_health_factor IS 'Minimum health factor user is comfortable with (default: 1.5)';
COMMENT ON COLUMN user_lending_preferences.auto_repay_threshold IS 'Health factor threshold to trigger auto-repay';
```

---

## Table: `lending_health_checks`

**Purpose**: Health check monitoring history

```sql
CREATE TABLE lending_health_checks (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Position Reference
    position_id UUID NOT NULL REFERENCES lending_positions(id) ON DELETE CASCADE,

    -- Health Metrics
    health_factor NUMERIC(20, 18) NOT NULL,
    total_collateral_usd NUMERIC(20, 6) NOT NULL,
    total_debt_usd NUMERIC(20, 6) NOT NULL,
    liquidation_threshold NUMERIC(5, 4) NOT NULL,

    -- Risk Assessment
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'critical', 'liquidatable')),
    liquidation_price_usd NUMERIC(20, 6) NULL,
    buffer_percentage NUMERIC(8, 4) NULL,  -- Price drop % before liquidation

    -- Action Recommendations
    recommended_action VARCHAR(50) NULL CHECK (recommended_action IN ('none', 'monitor', 'add_collateral', 'repay_debt', 'urgent_action')),
    recommended_repay_amount_usd NUMERIC(20, 6) NULL,
    recommended_collateral_amount_usd NUMERIC(20, 6) NULL,

    -- Alert Status
    alert_sent BOOLEAN NOT NULL DEFAULT FALSE,
    alert_sent_at TIMESTAMP WITH TIME ZONE NULL,

    -- Timestamps
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_lending_health_checks_position_id ON lending_health_checks(position_id);
CREATE INDEX idx_lending_health_checks_risk_level ON lending_health_checks(risk_level);
CREATE INDEX idx_lending_health_checks_checked_at ON lending_health_checks(checked_at DESC);
CREATE INDEX idx_lending_health_checks_alert_pending ON lending_health_checks(alert_sent) WHERE alert_sent = FALSE AND risk_level IN ('high', 'critical', 'liquidatable');

-- Comments
COMMENT ON TABLE lending_health_checks IS 'Health check monitoring history for positions';
COMMENT ON COLUMN lending_health_checks.buffer_percentage IS 'Percentage price can drop before liquidation';
```

---

## Table: `leverage_loop_executions`

**Purpose**: Track leverage loop execution progress

```sql
CREATE TABLE leverage_loop_executions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User Reference
    user_id UUID NOT NULL,
    wallet_address VARCHAR(42) NOT NULL,

    -- Position Reference
    position_id UUID NOT NULL REFERENCES lending_positions(id) ON DELETE CASCADE,

    -- Loop Configuration
    initial_collateral_amount NUMERIC(30, 18) NOT NULL,
    initial_collateral_asset VARCHAR(20) NOT NULL,
    target_leverage NUMERIC(5, 2) NOT NULL CHECK (target_leverage >= 1.0 AND target_leverage <= 10.0),
    max_iterations INTEGER NOT NULL CHECK (max_iterations >= 1 AND max_iterations <= 10),

    -- Execution Progress
    current_iteration INTEGER NOT NULL DEFAULT 0,
    total_iterations INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')),

    -- Results
    final_collateral_usd NUMERIC(20, 6) NULL,
    final_debt_usd NUMERIC(20, 6) NULL,
    final_leverage NUMERIC(5, 2) NULL,
    final_health_factor NUMERIC(20, 18) NULL,

    -- Transaction References
    transaction_hashes VARCHAR(66)[] NULL,  -- Array of tx hashes for each iteration

    -- Cost Tracking
    total_gas_cost_usd NUMERIC(20, 6) NULL,

    -- Error Information
    error_message TEXT NULL,
    failed_at_iteration INTEGER NULL,

    -- Protocol Information
    protocol VARCHAR(20) NOT NULL CHECK (protocol IN ('aave', 'morpho')),
    chain VARCHAR(20) NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE NULL
);

-- Indexes
CREATE INDEX idx_leverage_loop_executions_user_id ON leverage_loop_executions(user_id);
CREATE INDEX idx_leverage_loop_executions_position_id ON leverage_loop_executions(position_id);
CREATE INDEX idx_leverage_loop_executions_status ON leverage_loop_executions(status);
CREATE INDEX idx_leverage_loop_executions_created_at ON leverage_loop_executions(created_at DESC);

-- Comments
COMMENT ON TABLE leverage_loop_executions IS 'Track leverage loop execution progress with multiple iterations';
COMMENT ON COLUMN leverage_loop_executions.transaction_hashes IS 'Array of transaction hashes for each loop iteration';
```

---

## Views

### `v_user_lending_summary`

**Purpose**: Summary view of user lending positions

```sql
CREATE OR REPLACE VIEW v_user_lending_summary AS
SELECT
    lp.user_id,
    lp.wallet_address,
    COUNT(DISTINCT lp.id) AS total_positions,
    COUNT(DISTINCT CASE WHEN lp.protocol = 'aave' THEN lp.id END) AS aave_positions,
    COUNT(DISTINCT CASE WHEN lp.protocol = 'morpho' THEN lp.id END) AS morpho_positions,
    SUM(lp.total_collateral_usd) AS total_collateral_usd,
    SUM(lp.total_debt_usd) AS total_debt_usd,
    SUM(lp.available_borrow_usd) AS available_borrow_usd,
    MIN(lp.health_factor) AS min_health_factor,  -- Lowest HF across positions
    COUNT(CASE WHEN lp.risk_level IN ('high', 'critical', 'liquidatable') THEN 1 END) AS at_risk_positions,
    MAX(lp.updated_at) AS last_updated_at
FROM lending_positions lp
WHERE lp.deleted_at IS NULL
  AND lp.is_active = TRUE
GROUP BY lp.user_id, lp.wallet_address;

COMMENT ON VIEW v_user_lending_summary IS 'Summary view of user lending positions across all protocols';
```

### `v_lending_position_details`

**Purpose**: Detailed view combining positions with supplies and borrows

```sql
CREATE OR REPLACE VIEW v_lending_position_details AS
SELECT
    lp.id AS position_id,
    lp.user_id,
    lp.wallet_address,
    lp.protocol,
    lp.chain,
    lp.health_factor,
    lp.risk_level,

    -- Supply summary
    COUNT(DISTINCT ls.id) AS supply_count,
    COALESCE(SUM(ls.amount_usd), 0) AS total_supplied_usd,
    COALESCE(AVG(ls.total_apy), 0) AS avg_supply_apy,

    -- Borrow summary (Aave only)
    COUNT(DISTINCT lb.id) AS borrow_count,
    COALESCE(SUM(lb.amount_usd), 0) AS total_borrowed_usd,
    COALESCE(AVG(lb.borrow_apy), 0) AS avg_borrow_apy,

    lp.created_at,
    lp.updated_at
FROM lending_positions lp
LEFT JOIN lending_supplies ls ON ls.position_id = lp.id
LEFT JOIN lending_borrows lb ON lb.position_id = lp.id
WHERE lp.deleted_at IS NULL
GROUP BY lp.id;

COMMENT ON VIEW v_lending_position_details IS 'Detailed view of positions with supply and borrow aggregates';
```

---

## Alembic Migration Template

### Migration Script

```python
"""Add lending tables

Revision ID: lending_v1
Revises: <previous_revision>
Create Date: 2026-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'lending_v1'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lending_positions table
    op.create_table(
        'lending_positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wallet_address', sa.String(42), nullable=False),
        sa.Column('protocol', sa.String(20), nullable=False),
        sa.Column('chain', sa.String(20), nullable=False),
        sa.Column('total_collateral_usd', sa.Numeric(20, 6), nullable=False, server_default='0'),
        sa.Column('total_debt_usd', sa.Numeric(20, 6), nullable=False, server_default='0'),
        sa.Column('available_borrow_usd', sa.Numeric(20, 6), nullable=False, server_default='0'),
        sa.Column('health_factor', sa.Numeric(20, 18), nullable=True),
        sa.Column('current_ltv', sa.Numeric(5, 4), nullable=True),
        sa.Column('liquidation_threshold', sa.Numeric(5, 4), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=False, server_default='low'),
        sa.Column('requires_action', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_health_check_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_healthy', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("protocol IN ('aave', 'morpho')", name='chk_protocol'),
        sa.CheckConstraint("chain IN ('ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 'avalanche')", name='chk_chain'),
        sa.CheckConstraint('total_collateral_usd >= 0', name='chk_collateral_positive'),
        sa.CheckConstraint('total_debt_usd >= 0', name='chk_debt_positive'),
    )

    # Create indexes
    op.create_index('idx_lending_positions_user_id', 'lending_positions', ['user_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_lending_positions_wallet_address', 'lending_positions', ['wallet_address'], postgresql_where=sa.text('deleted_at IS NULL'))
    # ... (add remaining indexes)

    # Create remaining tables (lending_supplies, lending_borrows, etc.)
    # ... (similar pattern)


def downgrade() -> None:
    op.drop_table('leverage_loop_executions')
    op.drop_table('lending_health_checks')
    op.drop_table('user_lending_preferences')
    op.drop_table('lending_transactions')
    op.drop_table('lending_borrows')
    op.drop_table('lending_supplies')
    op.drop_table('lending_positions')
```

---

## Data Retention Policy

### Archive Strategy

- **Active positions**: Keep indefinitely
- **Inactive positions**: Archive after 12 months
- **Transactions**: Keep for 7 years (compliance)
- **Health checks**: Keep last 30 days, archive older
- **Leverage executions**: Keep for 24 months

### Soft Delete Implementation

All tables with `deleted_at` column support soft deletes:

```sql
-- Soft delete a position
UPDATE lending_positions
SET deleted_at = NOW()
WHERE id = '<position_id>';

-- Query only active positions
SELECT * FROM lending_positions
WHERE deleted_at IS NULL;
```

---

## Performance Optimization

### Query Optimization

1. **Composite indexes** for common query patterns
2. **Partial indexes** for frequently filtered subsets
3. **Generated columns** for computed values (e.g., total_apy)
4. **JSONB indexes** for metadata queries

### Partitioning Strategy

Consider partitioning `lending_transactions` by date for high-volume scenarios:

```sql
CREATE TABLE lending_transactions (
    ...
) PARTITION BY RANGE (created_at);

CREATE TABLE lending_transactions_2026_01 PARTITION OF lending_transactions
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## Security Considerations

### Row-Level Security (RLS)

```sql
-- Enable RLS
ALTER TABLE lending_positions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own positions
CREATE POLICY user_positions_policy ON lending_positions
FOR SELECT
USING (user_id = current_setting('app.current_user_id')::uuid);
```

### Encryption

- **wallet_address**: Consider encryption at rest
- **transaction metadata**: Encrypt sensitive data in JSONB
- **preferences**: Encrypt auto-management settings

---

## Monitoring and Alerting

### Critical Queries

```sql
-- Positions at high risk
SELECT * FROM lending_positions
WHERE health_factor < 1.2
  AND is_active = TRUE
  AND deleted_at IS NULL;

-- Positions requiring immediate action
SELECT * FROM lending_positions
WHERE requires_action = TRUE
  AND is_active = TRUE
  AND deleted_at IS NULL;

-- Failed transactions in last hour
SELECT * FROM lending_transactions
WHERE status = 'failed'
  AND created_at > NOW() - INTERVAL '1 hour';
```

---

## Summary

This database schema provides:

1. **Comprehensive tracking** of lending positions across protocols
2. **Health factor monitoring** with historical data
3. **Transaction tracking** with status and error handling
4. **User preferences** for risk management
5. **Leverage loop execution** tracking
6. **Performance optimizations** via indexes and views
7. **Data integrity** via constraints and foreign keys
8. **Security** via RLS policies

The schema follows PostgreSQL best practices and integrates seamlessly with the hexagonal architecture defined in `architecture.md`.
