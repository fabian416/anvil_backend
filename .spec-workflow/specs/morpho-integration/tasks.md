# Tasks Document: Morpho Protocol Integration

## Overview
Implementation tasks for completing the Morpho Protocol lending vaults integration following hexagonal architecture patterns. This is a **new integration** requiring a MorphoClient infrastructure client.

---

## Task 1: Domain Layer - Port and Models

- [x] 1.1 Create MorphoGateway port interface
  - File: `src/app/domain/ports/morpho_gateway.py`
  - Define Protocol interface for Morpho operations
  - Purpose: Domain contract for lending vault operations
  - _Leverage: `src/app/domain/ports/` patterns_
  - _Requirements: R1, R2, R3, R4, R5, R6_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer | Task: Create MorphoGateway Protocol in src/app/domain/ports/morpho_gateway.py with methods: get_vaults, get_vault_details, get_vault_apy, get_markets, get_user_positions, get_user_deposits, compare_yields. Use typing.Protocol with full type hints. | Restrictions: Interface only. | _Leverage: src/app/domain/ports/ patterns | _Requirements: Requirements 1-6 | Success: Protocol compiles. Log implementation and mark complete._

- [x] 1.2 Create MorphoVault entity
  - File: `src/app/domain/entities/lending/morpho_vault.py`
  - Define MorphoVault dataclass
  - Purpose: Domain model for MetaMorpho vaults
  - _Leverage: `src/app/domain/entities/` patterns_
  - _Requirements: R1_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create MorphoVault entity in src/app/domain/entities/lending/morpho_vault.py with fields: address, name, symbol, asset, total_assets, total_shares, apy, fee_percentage, curator_address, guardian_address, risk_tier (RiskTier), market_allocations (list[MarketAllocation]), created_at. Use @dataclass. | Restrictions: Follow entity patterns. Use Decimal for values. | _Leverage: src/app/domain/entities/ patterns | _Requirements: Requirement 1 | Success: Entity typed. Log implementation and mark complete._

- [x] 1.3 Create MorphoMarket entity
  - File: `src/app/domain/entities/lending/morpho_market.py`
  - Define MorphoMarket dataclass
  - Purpose: Domain model for Morpho Blue markets
  - _Leverage: `src/app/domain/entities/lending/morpho_vault.py`_
  - _Requirements: R2_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create MorphoMarket entity in src/app/domain/entities/lending/morpho_market.py with fields: market_id, collateral_asset, loan_asset, lltv (loan-to-value), oracle, irm_address, total_supply, total_borrow, utilization, supply_apy, borrow_apy. Use Decimal for rates. | Restrictions: Follow entity patterns. | _Leverage: src/app/domain/entities/lending/morpho_vault.py | _Requirements: Requirement 2 | Success: Entity typed. Log implementation and mark complete._

- [x] 1.4 Create MorphoPosition entity
  - File: `src/app/domain/entities/lending/morpho_position.py`
  - Define MorphoPosition dataclass
  - Purpose: Domain model for user positions
  - _Leverage: `src/app/domain/entities/lending/morpho_vault.py`_
  - _Requirements: R4_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create MorphoPosition entity in src/app/domain/entities/lending/morpho_position.py with fields: user_address, vault_address, vault_name, shares, assets, apy, deposited_at, earnings (calculated property). Use Decimal. | Restrictions: Follow entity patterns. | _Leverage: src/app/domain/entities/lending/morpho_vault.py | _Requirements: Requirement 4 | Success: Entity typed. Log implementation and mark complete._

- [x] 1.5 Create value objects (VaultAPY, RiskTier, MarketAllocation)
  - File: `src/app/domain/value_objects/lending/vault_apy.py`
  - File: `src/app/domain/value_objects/lending/risk_tier.py`
  - File: `src/app/domain/value_objects/lending/market_allocation.py`
  - Define enums and frozen dataclasses
  - Purpose: Domain value objects
  - _Leverage: `src/app/domain/value_objects/` patterns_
  - _Requirements: R1, R3, R5_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create VOs: VaultAPY frozen (base_apy, supply_apy, reward_apy, total_apy, apy_7d_avg, apy_30d_avg), RiskTier Enum (LOW, MEDIUM, HIGH, VERY_HIGH), MarketAllocation frozen (market_id, collateral_asset, loan_asset, allocation_percentage, lltv, supply_apy). Use Decimal for rates. | Restrictions: Use @dataclass(frozen=True). | _Leverage: src/app/domain/value_objects/ patterns | _Requirements: Requirements 1, 3, 5 | Success: VOs immutable. Log implementation and mark complete._

---

## Task 2: Domain Layer - Exceptions

- [x] 2.1 Create Morpho domain exceptions
  - File: `src/app/domain/exceptions/morpho.py`
  - Define MorphoError, VaultNotFoundError, InvalidVaultAddressError, MorphoAPIError
  - Purpose: Domain-specific error handling
  - _Leverage: `src/app/domain/exceptions/base.py`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create exceptions in src/app/domain/exceptions/morpho.py: MorphoError(DomainError), VaultNotFoundError, InvalidVaultAddressError, MorphoAPIError. Add error_code attributes. | Restrictions: Extend base exceptions. | _Leverage: src/app/domain/exceptions/base.py | _Requirements: Requirement 9 | Success: Exceptions inherit correctly. Log implementation and mark complete._

---

## Task 3: Infrastructure Layer - Client (NEW)

- [x] 3.1 Create MorphoClient infrastructure client
  - File: `src/app/infrastructure/adapters/external/morpho_client.py`
  - Implement GraphQL/Subgraph queries for Morpho data
  - Purpose: HTTP client for Morpho API
  - _Leverage: `src/app/infrastructure/adapters/external/` patterns_
  - _Requirements: R1, R2, R3, R4_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer | Task: Create MorphoClient in src/app/infrastructure/adapters/external/morpho_client.py. Use httpx.AsyncClient. Implement GraphQL queries to Morpho subgraph (https://api.thegraph.com/subgraphs/name/morpho-association/morpho-blue-mainnet or similar). Methods: get_vaults, get_vault, get_markets, get_user_positions. Return typed dataclasses (MorphoVaultData, MorphoMarketData, etc.). | Restrictions: Use async/await. Follow existing client patterns. Handle GraphQL errors. | _Leverage: src/app/infrastructure/adapters/external/ patterns | _Requirements: Requirements 1-4 | Success: Client queries subgraph correctly. Log implementation and mark complete._

---

## Task 4: Infrastructure Layer - Adapter

- [x] 4.1 Create MorphoAdapter implementing MorphoGateway
  - File: `src/app/infrastructure/adapters/external/morpho_adapter.py`
  - Implement MorphoGateway using MorphoClient
  - Add caching (10min vaults, 5min APY, 10min positions)
  - Transform client models to domain models
  - Implement risk tier calculation
  - Purpose: Bridge domain port to infrastructure client
  - _Leverage: `src/app/infrastructure/adapters/external/morpho_client.py`, `src/app/infrastructure/cache/external_api_cache.py`_
  - _Requirements: R1, R2, R3, R4, R5, R6, R9_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer | Task: Create MorphoAdapter in src/app/infrastructure/adapters/external/morpho_adapter.py implementing MorphoGateway. Inject MorphoClient and cache. Implement risk_tier calculation based on lltv and utilization (HIGH lltv + HIGH util = VERY_HIGH risk). Cache: 10min vaults, 5min APY, 10min positions. Transform client dataclasses to domain entities. | Restrictions: Do not modify MorphoClient. | _Leverage: src/app/infrastructure/adapters/external/morpho_client.py | _Requirements: Requirements 1-6, 9 | Success: Adapter implements Protocol. Log implementation and mark complete._

---

## Task 5: Application Layer - Queries

- [x] 5.1 Create GetVaults query
  - File: `src/app/application/queries/morpho/get_vaults.py`
  - Define GetVaultsRequest dataclass
  - Implement GetVaults with filtering and APY enrichment
  - Purpose: Get available vaults with yields
  - _Leverage: `src/app/application/queries/` patterns_
  - _Requirements: R1, R5_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetVaults query in src/app/application/queries/morpho/get_vaults.py. Define GetVaultsRequest(asset, risk_tier, min_apy, sort_by). Inject MorphoGateway. Filter by asset/risk_tier, enrich with APY data, sort by apy/tvl/risk. Return VaultsResponse with vaults and top_opportunities (highest APY per risk tier). | Restrictions: Depend only on domain port. | _Leverage: src/app/application/queries/ patterns | _Requirements: Requirements 1, 5 | Success: Returns vaults with opportunities. Log implementation and mark complete._

- [x] 5.2 Create GetVaultDetails query
  - File: `src/app/application/queries/morpho/get_vault_details.py`
  - Define GetVaultDetailsRequest dataclass
  - Implement GetVaultDetails with full market allocation
  - Purpose: Get vault details with market breakdown
  - _Leverage: `src/app/application/queries/morpho/get_vaults.py`_
  - _Requirements: R1_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetVaultDetails query in src/app/application/queries/morpho/get_vault_details.py. Define GetVaultDetailsRequest(vault_address). Return vault with full market_allocations showing where funds are deployed. Raise VaultNotFoundError if not found. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/morpho/get_vaults.py | _Requirements: Requirement 1 | Success: Returns vault details. Log implementation and mark complete._

- [x] 5.3 Create GetVaultAPY query
  - File: `src/app/application/queries/morpho/get_vault_apy.py`
  - Define GetVaultAPYRequest dataclass
  - Implement GetVaultAPY with historical APY
  - Purpose: Get detailed APY breakdown
  - _Leverage: `src/app/application/queries/morpho/get_vaults.py`_
  - _Requirements: R3_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetVaultAPY query in src/app/application/queries/morpho/get_vault_apy.py. Define GetVaultAPYRequest(vault_address). Return VaultAPY with base/supply/reward breakdown and 7d/30d averages. Calculate effective_apy = total_apy - fee. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/morpho/get_vaults.py | _Requirements: Requirement 3 | Success: Returns APY breakdown. Log implementation and mark complete._

- [x] 5.4 Create GetMarkets query
  - File: `src/app/application/queries/morpho/get_markets.py`
  - Define GetMarketsRequest dataclass
  - Implement GetMarkets
  - Purpose: Get Morpho Blue markets
  - _Leverage: `src/app/application/queries/morpho/get_vaults.py`_
  - _Requirements: R2_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetMarkets query in src/app/application/queries/morpho/get_markets.py. Define GetMarketsRequest(collateral_asset, loan_asset). Return list of MorphoMarket sorted by supply_apy. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/morpho/get_vaults.py | _Requirements: Requirement 2 | Success: Returns markets. Log implementation and mark complete._

- [x] 5.5 Create GetUserPositions query
  - File: `src/app/application/queries/morpho/get_user_positions.py`
  - Define GetUserPositionsRequest dataclass
  - Implement GetUserPositions with earnings calculation
  - Purpose: Get user vault positions
  - _Leverage: `src/app/application/queries/morpho/get_vaults.py`_
  - _Requirements: R4_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetUserPositions query in src/app/application/queries/morpho/get_user_positions.py. Define GetUserPositionsRequest(user_address). Return UserPositionsResponse with positions, total_deposited, total_earnings, average_apy (weighted by deposit). | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/morpho/get_vaults.py | _Requirements: Requirement 4 | Success: Returns positions with earnings. Log implementation and mark complete._

- [x] 5.6 Create CompareYields query
  - File: `src/app/application/queries/morpho/compare_yields.py`
  - Define CompareYieldsRequest dataclass
  - Implement CompareYields across protocols
  - Purpose: Compare Morpho yields with other protocols
  - _Leverage: `src/app/application/queries/morpho/get_vaults.py`_
  - _Requirements: R6_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create CompareYields query in src/app/application/queries/morpho/compare_yields.py. Define CompareYieldsRequest(asset, protocols). Inject MorphoGateway and optionally other gateways (Curve, Aave). Return YieldComparisonResponse with yields by protocol, best_option, apy_advantage (vs next best). | Restrictions: Handle missing protocol data gracefully. | _Leverage: src/app/application/queries/morpho/get_vaults.py | _Requirements: Requirement 6 | Success: Compares yields across protocols. Log implementation and mark complete._

---

## Task 6: Presentation Layer - HTTP Router

- [x] 6.1 Create Morpho HTTP router
  - File: `src/app/presentation/http/controllers/defi/morpho_router.py`
  - Define all endpoints from design
  - Purpose: HTTP API for lending operations
  - _Leverage: `src/app/presentation/http/controllers/` patterns_
  - _Requirements: R1-R6_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: FastAPI Developer | Task: Create morpho_router.py in src/app/presentation/http/controllers/defi/. Endpoints: GET /vaults, GET /vaults/{address}, GET /vaults/{address}/apy, GET /markets, GET /positions/{user}, GET /compare. Use FromDishka for DI. | Restrictions: Follow router patterns. | _Leverage: src/app/presentation/http/controllers/ patterns | _Requirements: Requirements 1-6 | Success: All endpoints work. Log implementation and mark complete._

- [x] 6.2 Create response schemas
  - File: `src/app/presentation/http/controllers/defi/morpho_schemas.py`
  - Define Pydantic models
  - Purpose: API response serialization
  - _Leverage: Existing schema patterns_
  - _Requirements: R1-R6_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create morpho_schemas.py with: VaultsResponse (with top_opportunities), VaultDetailsResponse, VaultAPYResponse (with effective_apy), MarketsResponse, UserPositionsResponse (with total_earnings), YieldComparisonResponse (with best_option). Add from_domain() methods. | Restrictions: Use Pydantic v2. | _Leverage: Existing schema patterns | _Requirements: Requirements 1-6 | Success: Schemas serialize. Log implementation and mark complete._

---

## Task 7: Dependency Injection

- [x] 7.1 Create Morpho DI provider
  - File: `src/app/setup/ioc/morpho.py`
  - Register MorphoClient, MorphoAdapter, MorphoGateway
  - Purpose: Enable DI
  - _Leverage: `src/app/setup/ioc/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create MorphoProvider in src/app/setup/ioc/morpho.py. Register MorphoClient (APP scope), MorphoAdapter as MorphoGateway (APP scope). Inject cache and settings (for subgraph URL). | Restrictions: Follow provider patterns. | _Leverage: src/app/setup/ioc/ patterns | _Requirements: All | Success: DI resolves. Log implementation and mark complete._

- [x] 7.2 Register router in app factory
  - File: `src/app/setup/app_factory.py` (modify)
  - Include morpho_router
  - Purpose: Enable endpoints
  - _Leverage: `src/app/setup/app_factory.py`_
  - _Requirements: All_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Modify app_factory.py to import and include morpho_router under /api/v1/defi prefix. Add MorphoProvider. | Restrictions: Minimal changes. | _Leverage: Existing pattern | _Requirements: All | Success: Endpoints accessible. Log implementation and mark complete._

---

## Task 8: Configuration

- [x] 8.1 Add Morpho configuration
  - File: `config/local/config.toml` (modify)
  - Add [morpho] section
  - Purpose: Configurable parameters
  - _Leverage: `config/local/config.toml`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps | Task: Add [morpho] section to config.toml with: enabled=true, subgraph_url="https://api.thegraph.com/subgraphs/name/morpho-association/morpho-blue-mainnet", cache_vault_ttl=600, cache_apy_ttl=300, cache_position_ttl=600. Add [morpho.risk] with lltv_high_threshold=0.85, utilization_high_threshold=0.9. | Restrictions: Follow config patterns. | _Leverage: config/local/config.toml | _Requirements: Requirement 9 | Success: Config loads. Log implementation and mark complete._

---

## Task 9: Testing

- [ ] 9.1 Create client unit tests
  - File: `tests/unit/infrastructure/adapters/test_morpho_client.py`
  - Test GraphQL queries
  - Purpose: Ensure client works correctly
  - _Leverage: `tests/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_morpho_client.py. Mock httpx responses for GraphQL queries. Test: get_vaults parses response correctly, get_markets handles empty results, error handling for GraphQL errors. | Restrictions: Unit tests only. | _Leverage: Existing test patterns | _Requirements: All | Success: Tests pass. Log implementation and mark complete._

- [ ] 9.2 Create adapter unit tests
  - File: `tests/unit/infrastructure/adapters/test_morpho_adapter.py`
  - Test transformation and risk calculation
  - Purpose: Ensure adapter reliability
  - _Leverage: `tests/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_morpho_adapter.py. Mock MorphoClient. Test: risk_tier calculation (high lltv + high util = VERY_HIGH), caching varies correctly, transformations preserve data. | Restrictions: Unit tests only. | _Leverage: Existing test patterns | _Requirements: All | Success: Tests pass. Log implementation and mark complete._

- [ ] 9.3 Create integration tests
  - File: `tests/integration/defi/test_morpho_integration.py`
  - Test full flow
  - Purpose: End-to-end functionality
  - _Leverage: `tests/integration/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec morpho-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_morpho_integration.py. Test: GET /vaults returns opportunities, GET /vaults/{address}/apy returns breakdown, GET /compare shows best option. Mock subgraph. | Restrictions: Mock external deps. | _Leverage: Existing integration patterns | _Requirements: All | Success: Integration tests pass. Log implementation and mark complete._

---

## Summary

| Phase | Tasks | Files Created |
|-------|-------|---------------|
| Domain | 1.1-1.5, 2.1 | 8 files |
| Infrastructure (Client) | 3.1 | 1 file |
| Infrastructure (Adapter) | 4.1 | 1 file |
| Application | 5.1-5.6 | 6 files |
| Presentation | 6.1-6.2 | 2 files |
| DI & Config | 7.1-7.2, 8.1 | 2 files + mods |
| Testing | 9.1-9.3 | 3 files |
| **Total** | **18 tasks** | **~23 files** |
