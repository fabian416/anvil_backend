# DeFi Operations Metadata & Architecture

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Anvil DeFi Operations module provides comprehensive integration with major DeFi protocols for lending, perpetual trading, liquidity pools, and cross-chain operations.

**Supported Protocols**: 6 (Aave, Morpho, Hyperliquid, Curve, LayerZero, Axelar)  
**Total Endpoints**: 40+  
**Multi-Chain Support**: Ethereum, Polygon, Arbitrum, Optimism, Avalanche, Base

---

## 1. Module Status

| Protocol | Status | Health | Endpoints | Notes |
|----------|--------|--------|-----------|-------|
| Aave V3 | ✅ Production | Healthy | 8 | Full lending support |
| Morpho | ✅ Production | Healthy | 6 | MetaMorpho vaults |
| Hyperliquid | ✅ Production | Healthy | 6 | Perpetual futures |
| Curve | ✅ Production | Healthy | 6 | Liquidity pools |
| LayerZero | ✅ Production | Healthy | 5 | Cross-chain messaging |
| Axelar | ✅ Production | Healthy | 5 | Cross-chain bridging |
| Data Providers | ✅ Production | Healthy | - | CoinGecko, DeFiLlama, 1inch |
| Celery Tasks | ⚠️ Partial | Limited | 1 | Only graph stats refresh |

---

## 2. File Reference Index

### 2.1 Presentation Layer (Routers)

```
src/app/presentation/http/controllers/defi/
├── __init__.py                    # Module exports
├── aave_router.py                 # Aave V3 endpoints
├── aave_schemas.py                # Aave Pydantic models
├── morpho_router.py               # Morpho endpoints
├── morpho_schemas.py              # Morpho Pydantic models
├── hyperliquid_router.py          # Hyperliquid endpoints
├── hyperliquid_schemas.py         # Hyperliquid Pydantic models
├── curve_router.py                # Curve Finance endpoints
├── curve_schemas.py               # Curve Pydantic models
├── layerzero_router.py            # LayerZero endpoints
├── layerzero_schemas.py           # LayerZero Pydantic models
├── axelar_router.py               # Axelar endpoints
└── axelar_schemas.py              # Axelar Pydantic models
```

### 2.2 Domain Layer (Ports & Entities)

```
src/app/domain/
├── ports/
│   ├── aave_gateway.py            # AaveGateway protocol
│   ├── morpho_gateway.py          # MorphoGateway protocol
│   ├── perpetual_gateway.py       # PerpetualGateway protocol
│   ├── curve_gateway.py           # CurveGateway protocol
│   ├── layerzero_gateway.py       # LayerZeroGateway protocol
│   └── axelar_gateway.py          # AxelarGateway protocol
├── entities/
│   ├── lending/
│   │   ├── aave_market.py         # AaveMarket entity
│   │   ├── aave_position.py       # AavePosition, AaveSupplyPosition, AaveBorrowPosition
│   │   ├── morpho_vault.py        # MorphoVault entity
│   │   ├── morpho_market.py       # MorphoMarket entity
│   │   └── morpho_position.py     # MorphoPosition entity
│   ├── perpetual/
│   │   ├── market.py              # PerpMarket entity
│   │   ├── position.py            # Position entity
│   │   └── liquidation.py         # Liquidation entity
│   ├── curve/
│   │   ├── pool.py                # Pool entity
│   │   └── gauge.py               # Gauge entity
│   ├── cross_chain/
│   │   ├── lz_message.py          # LZMessage entity
│   │   └── oft_transfer.py        # OFTTransfer entity
│   └── bridge/
│       └── axelar_transfer.py     # AxelarTransfer entity
├── value_objects/
│   ├── lending/
│   │   ├── health_factor.py       # HealthFactor, RiskLevel
│   │   ├── vault_apy.py           # VaultAPY
│   │   ├── risk_tier.py           # RiskTier
│   │   └── market_allocation.py   # MarketAllocation
│   ├── perpetual/
│   │   ├── funding_rate.py        # FundingRate
│   │   ├── order_book.py          # OrderBook
│   │   └── risk_metrics.py        # RiskMetrics
│   ├── curve/
│   │   ├── pool_apy.py            # PoolAPY
│   │   ├── swap_quote.py          # SwapQuote
│   │   └── tvl_data.py            # TVLData
│   ├── cross_chain/
│   │   ├── message_status.py      # MessageStatus
│   │   ├── lz_chain.py            # LZChain
│   │   └── message_fee.py         # MessageFee
│   └── bridge/
│       ├── transfer_status.py     # TransferStatus
│       ├── bridge_route.py        # BridgeRoute
│       └── transfer_estimate.py   # TransferEstimate
└── exceptions/
    ├── aave.py                    # Aave exceptions
    ├── morpho.py                  # Morpho exceptions
    ├── perpetual.py               # Perpetual exceptions
    ├── curve.py                   # Curve exceptions
    ├── layerzero.py               # LayerZero exceptions
    └── axelar.py                  # Axelar exceptions
```

### 2.3 Application Layer (Queries & Commands)

```
src/app/application/
├── queries/
│   ├── morpho/
│   │   ├── get_vaults.py          # GetVaults query
│   │   ├── get_vault_details.py   # GetVaultDetails query
│   │   ├── get_vault_apy.py       # GetVaultAPY query
│   │   ├── get_markets.py         # GetMarkets query
│   │   ├── get_user_positions.py  # GetUserPositions query
│   │   └── compare_yields.py      # CompareYields query
│   ├── perpetual/
│   │   ├── get_markets.py         # GetMarkets query
│   │   ├── get_order_book.py      # GetOrderBook query
│   │   ├── get_funding_rates.py   # GetFundingRates query
│   │   ├── get_liquidations.py    # GetLiquidations query
│   │   └── get_positions.py       # GetPositions query
│   ├── curve/
│   │   ├── get_pools.py           # GetPools query
│   │   ├── get_pool_apy.py        # GetPoolAPY query
│   │   ├── get_gauges.py          # GetGauges query
│   │   └── get_tvl.py             # GetTVL query
│   ├── layerzero/
│   │   ├── track_message.py       # TrackMessage query
│   │   ├── get_message_history.py # GetMessageHistory query
│   │   ├── get_chains.py          # GetChains query
│   │   ├── estimate_fees.py       # EstimateFees query
│   │   └── get_oft_transfers.py   # GetOFTTransfers query
│   └── axelar/
│       ├── get_routes.py          # GetRoutes query
│       ├── estimate_transfer.py   # EstimateTransfer query
│       ├── track_transfer.py      # TrackTransfer query
│       ├── get_chains.py          # GetChains query
│       └── get_tokens.py          # GetTokens query
├── commands/
│   ├── perpetual/
│   │   └── calculate_risk.py      # CalculateRisk command
│   └── curve/
│       └── get_swap_quote.py      # GetSwapQuote command
└── templates/library/defi/
    ├── __init__.py
    ├── apr_apy_calculator.py      # APR/APY templates
    ├── liquidity_analysis.py      # Liquidity templates
    ├── risk_vs_reward_comparison.py
    ├── protocol_deep_dive.py
    └── smart_contract_security_analysis.py
```

### 2.4 Infrastructure Layer (Adapters & Providers)

```
src/app/infrastructure/
├── adapters/external/
│   ├── aave_adapter.py            # AaveGateway implementation
│   ├── morpho_adapter.py          # MorphoGateway implementation
│   ├── hyperliquid_adapter.py     # PerpetualGateway implementation
│   ├── curve_adapter.py           # CurveGateway implementation
│   ├── layerzero_adapter.py       # LayerZeroGateway implementation
│   └── axelar_adapter.py          # AxelarGateway implementation
├── defi/
│   ├── providers/
│   │   ├── coingecko.py           # CoinGecko API client
│   │   ├── defillama.py           # DeFiLlama API client
│   │   ├── oneinch.py             # 1inch API client
│   │   ├── hyperliquid.py         # Hyperliquid API client
│   │   └── wallet_provider.py     # Wallet data provider
│   └── tools/
│       ├── swap_tools.py          # Swap agent tools
│       ├── trading_tools.py       # Trading agent tools
│       ├── portfolio_tools.py     # Portfolio agent tools
│       ├── position_management_tools.py
│       └── advanced_swap_tools.py
└── persistence_sqla/mappings/
    └── defi_operations.py         # DeFi tables mapping
```

### 2.5 IoC Providers

```
src/app/setup/ioc/
├── aave.py                        # AaveProvider
├── morpho.py                      # MorphoProvider (if exists)
├── hyperliquid.py                 # HyperliquidProvider (if exists)
├── curve.py                       # CurveProvider (if exists)
├── layerzero.py                   # LayerZeroProvider (if exists)
└── axelar.py                      # AxelarProvider (if exists)
```

### 2.6 Test Files

```
tests/
├── integration/defi/
│   ├── __init__.py
│   ├── test_aave_integration.py   # Aave integration tests
│   └── test_defi_integration.py   # Multi-protocol tests
└── unit/infrastructure/adapters/
    ├── test_aave_adapter.py
    ├── test_morpho_adapter.py
    ├── test_hyperliquid_adapter.py
    ├── test_curve_adapter.py
    ├── test_layerzero_adapter.py
    └── test_axelar_adapter.py
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                                                                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                  │
│  │  Web App  │ │Mobile App │ │  AI Chat  │ │ Agent Bot │                  │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                  │
└────────┼─────────────┼─────────────┼─────────────┼──────────────────────────┘
         │             │             │             │
         ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │AaveRouter  │ │MorphoRouter│ │HyperliquidR│ │CurveRouter │              │
│  │/api/v1/aave│ │/api/v1/    │ │/api/v1/    │ │/api/v1/    │              │
│  │            │ │morpho      │ │hyperliquid │ │curve       │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│                                                                              │
│  ┌────────────┐ ┌────────────┐                                            │
│  │LayerZero   │ │Axelar      │                                            │
│  │/api/v1/    │ │/api/v1/    │                                            │
│  │layerzero   │ │axelar      │                                            │
│  └────────────┘ └────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                     │
│                                                                              │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐    │
│  │           Queries              │  │          Commands              │    │
│  │                                │  │                                │    │
│  │  GetVaults • GetMarkets        │  │  CalculateRisk • GetSwapQuote  │    │
│  │  GetPositions • TrackMessage   │  │                                │    │
│  │  CompareYields • GetFunding    │  │                                │    │
│  └────────────────────────────────┘  └────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Gateway Ports                                   │   │
│  │  AaveGateway • MorphoGateway • PerpetualGateway • CurveGateway     │   │
│  │  LayerZeroGateway • AxelarGateway                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       Entities                                       │   │
│  │  AaveMarket • AavePosition • MorphoVault • PerpMarket • Position    │   │
│  │  Pool • Gauge • LZMessage • OFTTransfer • AxelarTransfer           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Value Objects                                    │   │
│  │  HealthFactor • RiskLevel • VaultAPY • RiskTier • FundingRate      │   │
│  │  OrderBook • RiskMetrics • SwapQuote • MessageStatus • BridgeRoute │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          Adapters                                    │   │
│  │  AaveAdapter • MorphoAdapter • HyperliquidAdapter • CurveAdapter   │   │
│  │  LayerZeroAdapter • AxelarAdapter                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       Data Providers                                 │   │
│  │  CoinGeckoClient • DefiLlamaClient • OneInchClient • HyperliquidCl │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Agent Tools                                   │   │
│  │  SwapTools • TradingTools • PortfolioTools • PositionMgmtTools     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SERVICES                                     │
│                                                                              │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐            │
│  │Aave V3│ │Morpho │ │Hyper- │ │Curve  │ │Layer- │ │Axelar │            │
│  │API    │ │Blue   │ │liquid │ │API    │ │Zero   │ │API    │            │
│  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘            │
│                                                                              │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐                                  │
│  │Coin-  │ │DeFi-  │ │1inch  │ │TheGraph│                                 │
│  │Gecko  │ │Llama  │ │API    │ │        │                                 │
│  └───────┘ └───────┘ └───────┘ └───────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### 4.1 Hyperliquid Positions Table

```sql
CREATE TABLE hyperliquid_positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Position details
    symbol VARCHAR(20) NOT NULL,
    side side_enum NOT NULL,  -- 'LONG' or 'SHORT'
    leverage NUMERIC(5, 2) NOT NULL,
    size NUMERIC(30, 18) NOT NULL,
    entry_price NUMERIC(20, 8) NOT NULL,
    mark_price NUMERIC(20, 8),
    liquidation_price NUMERIC(20, 8),
    
    -- P&L
    unrealized_pnl NUMERIC(20, 8),
    realized_pnl NUMERIC(20, 8) DEFAULT 0,
    margin NUMERIC(20, 8) NOT NULL,
    funding_rate NUMERIC(10, 6),
    last_funding_payment NUMERIC(20, 8),
    
    -- Status
    status position_status_enum DEFAULT 'OPEN',
    hyperliquid_order_id VARCHAR(100),
    
    -- Timestamps
    opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_hl_positions_user_id (user_id),
    INDEX idx_hl_positions_symbol (symbol),
    INDEX idx_hl_positions_status (status),
    INDEX idx_hl_positions_opened_at (opened_at)
);
```

### 4.2 Earn Positions Table

```sql
CREATE TABLE earn_positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Position details
    chain chain_type_enum NOT NULL,
    protocol VARCHAR(50) NOT NULL,
    asset VARCHAR(20) NOT NULL,
    amount_deposited NUMERIC(30, 18) NOT NULL,
    current_value NUMERIC(30, 18),
    
    -- Yield
    apy NUMERIC(8, 4),
    current_apy NUMERIC(8, 4),
    rewards_earned NUMERIC(30, 18) DEFAULT 0,
    rewards_earned_usd NUMERIC(20, 2) DEFAULT 0,
    
    -- Status
    status earn_status_enum DEFAULT 'ACTIVE',
    
    -- Transaction hashes
    transaction_hash VARCHAR(66),
    deposit_tx_hash VARCHAR(66),
    withdraw_tx_hash VARCHAR(66),
    
    -- Timestamps
    deposited_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    withdrawn_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_earn_positions_user_id (user_id),
    INDEX idx_earn_positions_chain (chain),
    INDEX idx_earn_positions_protocol (protocol),
    INDEX idx_earn_positions_status (status)
);
```

### 4.3 Save Schedules Table

```sql
CREATE TABLE save_schedules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Schedule details
    chain chain_type_enum NOT NULL,
    asset VARCHAR(20) NOT NULL,
    amount NUMERIC(30, 18) NOT NULL,
    
    -- Frequency
    frequency frequency_enum NOT NULL,
    day_of_week INTEGER,
    day_of_month INTEGER,
    destination_protocol VARCHAR(50),
    
    -- Status
    status schedule_status_enum DEFAULT 'ACTIVE',
    
    -- Execution
    next_execution_at TIMESTAMPTZ NOT NULL,
    last_execution_at TIMESTAMPTZ,
    total_saved NUMERIC(30, 18) DEFAULT 0,
    execution_count INTEGER DEFAULT 0,
    max_executions INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_save_schedules_user_id (user_id),
    INDEX idx_save_schedules_status (status),
    INDEX idx_save_schedules_next_execution (next_execution_at)
);
```

---

## 5. Improvements Roadmap

### 5.1 High Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Celery Tasks** | Implement data refresh tasks | Medium | Performance |
| **HTTP Tests** | Add endpoint integration tests | Medium | Quality |
| **Liquidation Alerts** | Real-time position monitoring | High | User safety |
| **Price Caching** | Redis-based price cache | Low | Performance |

### 5.2 Medium Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **E2E Tests** | Full workflow testing | Medium | Quality |
| **Analytics Dashboard** | DeFi activity metrics | High | Business insights |
| **Position Tracking** | Persistent position storage | Medium | User experience |
| **Webhook Support** | Real-time protocol events | High | Feature completeness |

### 5.3 Low Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Historical Data** | Historical rates/prices | High | Analytics |
| **Multi-wallet** | Multiple wallet support | Medium | Feature |
| **Tax Reporting** | DeFi transaction reports | High | Compliance |
| **Strategy Builder** | Automated DeFi strategies | Very High | Feature |

---

## 6. Performance Metrics

### 6.1 Current Performance

| Metric | Value | Target |
|--------|-------|--------|
| Market data latency | ~500ms | <1000ms |
| Position lookup | ~300ms | <500ms |
| Health factor calc | ~50ms | <100ms |
| Cross-chain tracking | ~800ms | <1500ms |

### 6.2 Caching Strategy

- **Redis**: Price data (TTL: 2 min), market data (TTL: 5 min)
- **In-memory**: Static protocol data
- **PostgreSQL**: Historical analytics

---

## 7. Security Considerations

### 7.1 Implemented

- ✅ Read-only protocol interactions (no write operations)
- ✅ Address validation for all queries
- ✅ Rate limiting on external API calls
- ✅ Error sanitization (no internal details exposed)

### 7.2 Recommendations

- ⚠️ Add request signing for authenticated endpoints
- ⚠️ Implement IP-based rate limiting
- ⚠️ Add audit logging for position queries
- ⚠️ Review cross-chain transaction verification

---

## 8. Multi-Chain Support

| Protocol | Ethereum | Polygon | Arbitrum | Optimism | Avalanche | Base |
|----------|----------|---------|----------|----------|-----------|------|
| Aave V3 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Morpho | ✅ | - | - | - | - | ✅ |
| Hyperliquid | ✅ (L1) | - | - | - | - | - |
| Curve | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| LayerZero | All EVM chains supported |
| Axelar | All supported chains |

---

## References

- **Endpoints Spec**: `docs/ceo/defi/endpoints.md`
- **Services Spec**: `docs/ceo/defi/services.md`
- **Celery Spec**: `docs/ceo/defi/celery.md`
- **Test Spec**: `docs/ceo/defi/test.md`
- **Aave Docs**: https://docs.aave.com/
- **Morpho Docs**: https://docs.morpho.org/
- **Hyperliquid Docs**: https://hyperliquid.gitbook.io/
- **Curve Docs**: https://resources.curve.fi/
- **LayerZero Docs**: https://layerzero.network/
- **Axelar Docs**: https://docs.axelar.dev/
