# Tasks Document: Hyperliquid Integration

## Overview
Implementation tasks for completing the Hyperliquid perpetual futures integration following hexagonal architecture patterns.

---

## Task 1: Domain Layer - Port and Value Objects

- [x] 1.1 Create PerpetualGateway port interface
  - File: `src/app/domain/ports/perpetual_gateway.py`
  - Define Protocol interface with all perpetual operations
  - Include type hints for all method signatures
  - Purpose: Establish domain contract for perpetual operations
  - _Leverage: `src/app/domain/ports/` existing port patterns_
  - _Requirements: R1, R2, R3, R4, R5, R7_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer specializing in hexagonal architecture | Task: Create PerpetualGateway Protocol in src/app/domain/ports/perpetual_gateway.py defining methods for get_markets, get_order_book, get_funding_rate, get_funding_rates, get_liquidations, get_positions, calculate_liquidation_price. Use typing.Protocol. | Restrictions: Only define interface, no implementation. | _Leverage: src/app/domain/ports/ existing patterns | _Requirements: Requirements 1-5, 7 | Success: Protocol compiles, proper type hints. Log implementation and mark complete._

- [x] 1.2 Create PerpMarket entity
  - File: `src/app/domain/entities/perpetual/market.py`
  - Define PerpMarket dataclass with all trading fields
  - Purpose: Domain model for perpetual markets
  - _Leverage: `src/app/domain/entities/` existing patterns_
  - _Requirements: R1_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer with DDD expertise | Task: Create PerpMarket entity in src/app/domain/entities/perpetual/market.py with fields: symbol, mark_price, index_price, funding_rate, open_interest, volume_24h, price_change_24h, max_leverage. Use @dataclass, Decimal for prices. | Restrictions: Follow existing entity patterns. | _Leverage: src/app/domain/entities/ patterns | _Requirements: Requirement 1 | Success: Entity properly typed. Log implementation and mark complete._

- [x] 1.3 Create Position entity
  - File: `src/app/domain/entities/perpetual/position.py`
  - Define Position dataclass for user positions
  - Purpose: Domain model for trading positions
  - _Leverage: `src/app/domain/entities/perpetual/market.py`_
  - _Requirements: R5_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create Position entity in src/app/domain/entities/perpetual/position.py with fields: symbol, side, size, entry_price, mark_price, unrealized_pnl, leverage, liquidation_price, margin_ratio. Add pnl_pct property. | Restrictions: Follow entity patterns. Use Decimal. | _Leverage: src/app/domain/entities/perpetual/market.py | _Requirements: Requirement 5 | Success: Entity with calculated properties. Log implementation and mark complete._

- [x] 1.4 Create Liquidation entity
  - File: `src/app/domain/entities/perpetual/liquidation.py`
  - Define Liquidation dataclass for liquidation events
  - Purpose: Domain model for liquidation data
  - _Leverage: `src/app/domain/entities/perpetual/position.py`_
  - _Requirements: R4_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create Liquidation entity in src/app/domain/entities/perpetual/liquidation.py with fields: symbol, side, size, price, timestamp. Use @dataclass. | Restrictions: Follow existing patterns. | _Leverage: src/app/domain/entities/perpetual/position.py | _Requirements: Requirement 4 | Success: Entity properly typed. Log implementation and mark complete._

- [x] 1.5 Create value objects (FundingRate, OrderBook, RiskMetrics)
  - File: `src/app/domain/value_objects/perpetual/funding_rate.py`
  - File: `src/app/domain/value_objects/perpetual/order_book.py`
  - File: `src/app/domain/value_objects/perpetual/risk_metrics.py`
  - Define frozen dataclasses for immutable data
  - Purpose: Domain value objects for trading data
  - _Leverage: `src/app/domain/value_objects/` patterns_
  - _Requirements: R2, R3, R7_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create value objects: FundingRate(symbol, rate, annualized_rate, next_funding_time, direction_bias property), OrderBook(symbol, bids, asks, spread/spread_pct properties), RiskMetrics(liquidation_price, margin_required, max_loss, distance_to_liquidation_pct, risk_level). Use @dataclass(frozen=True). | Restrictions: Immutable value objects. | _Leverage: src/app/domain/value_objects/ patterns | _Requirements: Requirements 2, 3, 7 | Success: All VOs frozen, properties work. Log implementation and mark complete._

---

## Task 2: Domain Layer - Exceptions

- [x] 2.1 Create Perpetual domain exceptions
  - File: `src/app/domain/exceptions/perpetual.py`
  - Define PerpetualError, SymbolNotFoundError, InvalidAddressError, HyperliquidAPIError
  - Purpose: Domain-specific error handling
  - _Leverage: `src/app/domain/exceptions/base.py`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create perpetual exceptions in src/app/domain/exceptions/perpetual.py. Define PerpetualError(DomainError), SymbolNotFoundError, InvalidAddressError, HyperliquidAPIError. Add error_code attributes. | Restrictions: Extend base exceptions. | _Leverage: src/app/domain/exceptions/base.py | _Requirements: Requirement 9 | Success: Exceptions inherit correctly. Log implementation and mark complete._

---

## Task 3: Infrastructure Layer - Adapter

- [x] 3.1 Create HyperliquidAdapter implementing PerpetualGateway
  - File: `src/app/infrastructure/adapters/external/hyperliquid_adapter.py`
  - Implement PerpetualGateway using existing HyperliquidClient
  - Add minimal caching (5s markets, 30s funding)
  - Transform client models to domain models
  - Purpose: Bridge domain port to infrastructure client
  - _Leverage: `src/app/infrastructure/adapters/external/hyperliquid_client.py`, `src/app/infrastructure/cache/external_api_cache.py`_
  - _Requirements: R1, R2, R3, R4, R5, R9_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer | Task: Create HyperliquidAdapter in src/app/infrastructure/adapters/external/hyperliquid_adapter.py implementing PerpetualGateway. Inject HyperliquidClient and cache. Implement all methods with short TTL caching (5s markets, 30s funding, no cache orderbook). Transform client dataclasses to domain entities. | Restrictions: Do not modify existing client. Handle errors with domain exceptions. | _Leverage: src/app/infrastructure/adapters/external/hyperliquid_client.py | _Requirements: Requirements 1-5, 9 | Success: Adapter implements Protocol, caching works. Log implementation and mark complete._

---

## Task 4: Application Layer - Queries

- [x] 4.1 Create GetMarkets query
  - File: `src/app/application/queries/perpetual/get_markets.py`
  - Define GetMarketsRequest dataclass
  - Implement GetMarkets class
  - Purpose: Get all perpetual markets
  - _Leverage: `src/app/application/queries/` patterns_
  - _Requirements: R1_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetMarkets query in src/app/application/queries/perpetual/get_markets.py. Define GetMarketsRequest(). Inject PerpetualGateway. Return sorted list of PerpMarket by volume. | Restrictions: Depend only on domain port. | _Leverage: src/app/application/queries/ patterns | _Requirements: Requirement 1 | Success: Returns markets correctly. Log implementation and mark complete._

- [x] 4.2 Create GetOrderBook query
  - File: `src/app/application/queries/perpetual/get_order_book.py`
  - Define GetOrderBookRequest dataclass
  - Implement GetOrderBook class with spread analysis
  - Purpose: Get order book with liquidity analysis
  - _Leverage: `src/app/application/queries/perpetual/get_markets.py`_
  - _Requirements: R2_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetOrderBook query in src/app/application/queries/perpetual/get_order_book.py. Define GetOrderBookRequest(symbol, depth). Return OrderBook with spread analysis. Add warning if spread > 0.1%. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/perpetual/get_markets.py | _Requirements: Requirement 2 | Success: Returns orderbook with warnings. Log implementation and mark complete._

- [x] 4.3 Create GetFundingRates query
  - File: `src/app/application/queries/perpetual/get_funding_rates.py`
  - Define GetFundingRatesRequest dataclass
  - Implement GetFundingRates with opportunity identification
  - Purpose: Get funding rates with arbitrage opportunities
  - _Leverage: `src/app/application/queries/perpetual/get_markets.py`_
  - _Requirements: R3_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetFundingRates query in src/app/application/queries/perpetual/get_funding_rates.py. Define GetFundingRatesRequest(sort_by, min_rate). Return FundingRatesResponse with rates and opportunities list (>50% annualized = opportunity). | Restrictions: Include opportunity identification logic. | _Leverage: src/app/application/queries/perpetual/get_markets.py | _Requirements: Requirement 3 | Success: Identifies funding opportunities. Log implementation and mark complete._

- [x] 4.4 Create GetLiquidations query
  - File: `src/app/application/queries/perpetual/get_liquidations.py`
  - Define GetLiquidationsRequest dataclass
  - Implement GetLiquidations with aggregation
  - Purpose: Get liquidation events with market stress analysis
  - _Leverage: `src/app/application/queries/perpetual/get_markets.py`_
  - _Requirements: R4_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetLiquidations query in src/app/application/queries/perpetual/get_liquidations.py. Define GetLiquidationsRequest(symbol, hours). Return liquidations with long/short breakdown and total volume. Flag cascade if >$1M in 1 hour. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/perpetual/get_markets.py | _Requirements: Requirement 4 | Success: Returns liquidations with analysis. Log implementation and mark complete._

- [x] 4.5 Create GetPositions query
  - File: `src/app/application/queries/perpetual/get_positions.py`
  - Define GetPositionsRequest dataclass
  - Implement GetPositions with PnL calculation
  - Purpose: Get user positions with risk indicators
  - _Leverage: `src/app/application/queries/perpetual/get_markets.py`_
  - _Requirements: R5_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetPositions query in src/app/application/queries/perpetual/get_positions.py. Define GetPositionsRequest(address). Return positions with aggregate PnL and risk warnings for high leverage (>10x) or low margin (<20%). | Restrictions: Validate address format. | _Leverage: src/app/application/queries/perpetual/get_markets.py | _Requirements: Requirement 5 | Success: Returns positions with warnings. Log implementation and mark complete._

---

## Task 5: Application Layer - Commands

- [x] 5.1 Create CalculateRisk command
  - File: `src/app/application/commands/perpetual/calculate_risk.py`
  - Define CalculateRiskRequest dataclass
  - Implement CalculateRisk with liquidation price calculation
  - Purpose: Calculate position risk metrics
  - _Leverage: `src/app/application/commands/` patterns_
  - _Requirements: R7_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create CalculateRisk command in src/app/application/commands/perpetual/calculate_risk.py. Define CalculateRiskRequest(entry_price, size, leverage, side, account_balance). Calculate liquidation_price, margin_required, max_loss, distance_to_liquidation_pct. Return RiskMetrics with risk_level (EXTREME/HIGH/MEDIUM/LOW). | Restrictions: Pure calculation, no external calls. | _Leverage: src/app/application/commands/ patterns | _Requirements: Requirement 7 | Success: Risk calculations accurate. Log implementation and mark complete._

---

## Task 6: Presentation Layer - HTTP Router

- [x] 6.1 Create Hyperliquid HTTP router
  - File: `src/app/presentation/http/controllers/defi/hyperliquid_router.py`
  - Define all endpoints from design document
  - Use Pydantic models for request/response
  - Purpose: HTTP API for perpetual operations
  - _Leverage: `src/app/presentation/http/controllers/` existing routers_
  - _Requirements: R1-R7_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: FastAPI Developer | Task: Create hyperliquid_router.py in src/app/presentation/http/controllers/defi/. Endpoints: GET /markets, GET /markets/{symbol}/orderbook, GET /funding, GET /liquidations, GET /positions/{address}, POST /risk/calculate. Use FromDishka for DI. | Restrictions: Follow existing router patterns. | _Leverage: src/app/presentation/http/controllers/ patterns | _Requirements: Requirements 1-7 | Success: All endpoints work. Log implementation and mark complete._

- [x] 6.2 Create response schemas
  - File: `src/app/presentation/http/controllers/defi/hyperliquid_schemas.py`
  - Define Pydantic models for all responses
  - Purpose: API response serialization
  - _Leverage: Existing schema patterns_
  - _Requirements: R1-R7_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create hyperliquid_schemas.py with Pydantic models: MarketsResponse, OrderBookResponse, FundingRatesResponse (with opportunities), LiquidationsResponse, PositionsResponse, RiskMetricsResponse. Add from_domain() methods. | Restrictions: Use Pydantic v2. | _Leverage: Existing schema patterns | _Requirements: Requirements 1-7 | Success: All schemas serialize correctly. Log implementation and mark complete._

---

## Task 7: Dependency Injection

- [x] 7.1 Create Hyperliquid DI provider
  - File: `src/app/setup/ioc/hyperliquid.py`
  - Register HyperliquidClient, HyperliquidAdapter, PerpetualGateway
  - Purpose: Enable DI for Hyperliquid components
  - _Leverage: `src/app/setup/ioc/` existing providers_
  - _Requirements: All_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create HyperliquidProvider in src/app/setup/ioc/hyperliquid.py. Register HyperliquidClient and HyperliquidAdapter as PerpetualGateway (APP scope). | Restrictions: Follow provider patterns. | _Leverage: src/app/setup/ioc/ patterns | _Requirements: All | Success: DI resolves correctly. Log implementation and mark complete._

- [x] 7.2 Register router in app factory
  - File: `src/app/setup/app_factory.py` (modify)
  - Include hyperliquid_router in API routes
  - Purpose: Enable Hyperliquid endpoints
  - _Leverage: `src/app/setup/app_factory.py`_
  - _Requirements: All_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Modify app_factory.py to import and include hyperliquid_router under /api/v1/defi prefix. Add HyperliquidProvider to providers. | Restrictions: Minimal changes. | _Leverage: Existing registration pattern | _Requirements: All | Success: Endpoints accessible. Log implementation and mark complete._

---

## Task 8: Configuration

- [x] 8.1 Add Hyperliquid configuration
  - File: `config/local/config.toml` (modify)
  - Add [hyperliquid] section with settings
  - Purpose: Configurable parameters
  - _Leverage: `config/local/config.toml`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps | Task: Add [hyperliquid] section to config.toml with: enabled=true, testnet=false, cache_market_ttl=5, cache_funding_ttl=30, cache_position_ttl=10. Add [hyperliquid.risk] with default_maintenance_margin=0.005. | Restrictions: Follow config patterns. | _Leverage: config/local/config.toml | _Requirements: Requirement 9 | Success: Config loads correctly. Log implementation and mark complete._

---

## Task 9: Testing

- [ ] 9.1 Create adapter unit tests
  - File: `tests/unit/infrastructure/adapters/test_hyperliquid_adapter.py`
  - Test transformation and caching logic
  - Purpose: Ensure adapter reliability
  - _Leverage: `tests/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_hyperliquid_adapter.py. Mock HyperliquidClient. Test: get_markets transforms correctly, get_order_book not cached, funding rates cached 30s. Use AsyncMock. | Restrictions: Unit tests only. | _Leverage: Existing test patterns | _Requirements: All | Success: Tests pass. Log implementation and mark complete._

- [ ] 9.2 Create integration tests
  - File: `tests/integration/defi/test_hyperliquid_integration.py`
  - Test full flow from router to adapter
  - Purpose: End-to-end functionality
  - _Leverage: `tests/integration/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec hyperliquid-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_hyperliquid_integration.py. Use TestClient. Test: GET /markets returns data, GET /funding returns opportunities, error handling works. | Restrictions: Mock external APIs. | _Leverage: Existing integration patterns | _Requirements: All | Success: Integration tests pass. Log implementation and mark complete._

---

## Summary

| Phase | Tasks | Files Created |
|-------|-------|---------------|
| Domain | 1.1-1.5, 2.1 | 8 files |
| Infrastructure | 3.1 | 1 file |
| Application | 4.1-4.5, 5.1 | 6 files |
| Presentation | 6.1-6.2 | 2 files |
| DI & Config | 7.1-7.2, 8.1 | 2 files + mods |
| Testing | 9.1-9.2 | 2 files |
| **Total** | **17 tasks** | **~21 files** |
