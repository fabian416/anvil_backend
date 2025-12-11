# Tasks Document: Axelar Network Integration

## Overview
Implementation tasks for completing the Axelar cross-chain bridging integration following hexagonal architecture patterns.

---

## Task 1: Domain Layer - Port and Models

- [x] 1.1 Create AxelarGateway port interface
  - File: `src/app/domain/ports/axelar_gateway.py`
  - Define Protocol interface for Axelar operations
  - Purpose: Domain contract for bridge operations
  - _Leverage: `src/app/domain/ports/` patterns_
  - _Requirements: R1, R2, R3, R4, R5_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer | Task: Create AxelarGateway Protocol in src/app/domain/ports/axelar_gateway.py with methods: get_routes, estimate_transfer, track_transfer, get_chains, get_tokens. Use typing.Protocol with full type hints. | Restrictions: Interface only. | _Leverage: src/app/domain/ports/ patterns | _Requirements: Requirements 1-5 | Success: Protocol compiles. Log implementation and mark complete._

- [x] 1.2 Create AxelarTransfer entity
  - File: `src/app/domain/entities/bridge/axelar_transfer.py`
  - Define AxelarTransfer dataclass
  - Purpose: Domain model for bridge transfers
  - _Leverage: `src/app/domain/entities/` patterns_
  - _Requirements: R3_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create AxelarTransfer entity in src/app/domain/entities/bridge/axelar_transfer.py with fields: tx_hash, source_chain, destination_chain, token, amount, status (TransferStatus), source_tx_hash, destination_tx_hash, created_at, completed_at, error_message, is_express. Use @dataclass. | Restrictions: Follow entity patterns. | _Leverage: src/app/domain/entities/ patterns | _Requirements: Requirement 3 | Success: Entity typed. Log implementation and mark complete._

- [x] 1.3 Create value objects (TransferStatus, BridgeRoute, TransferEstimate)
  - File: `src/app/domain/value_objects/bridge/transfer_status.py`
  - File: `src/app/domain/value_objects/bridge/bridge_route.py`
  - File: `src/app/domain/value_objects/bridge/transfer_estimate.py`
  - Define enums and frozen dataclasses
  - Purpose: Domain value objects
  - _Leverage: `src/app/domain/value_objects/` patterns_
  - _Requirements: R1, R2, R3_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create VOs: TransferStatus Enum (PENDING, CONFIRMED, EXECUTING, EXECUTED, FAILED), BridgeRoute frozen (source_chain, destination_chain, token, estimated_time_seconds, fee_usd, fee_native, security_score, is_express), TransferEstimate frozen (source_chain, destination_chain, token, amount, fee_usd, gas_estimate_usd, total_cost_usd, estimated_time_seconds, is_express). | Restrictions: Use @dataclass(frozen=True). | _Leverage: src/app/domain/value_objects/ patterns | _Requirements: Requirements 1-3 | Success: VOs immutable. Log implementation and mark complete._

---

## Task 2: Domain Layer - Exceptions

- [x] 2.1 Create Axelar domain exceptions
  - File: `src/app/domain/exceptions/axelar.py`
  - Define AxelarError, TransferNotFoundError, UnsupportedChainError, UnsupportedTokenError
  - Purpose: Domain-specific error handling
  - _Leverage: `src/app/domain/exceptions/base.py`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create exceptions in src/app/domain/exceptions/axelar.py: AxelarError(DomainError), TransferNotFoundError, UnsupportedChainError, UnsupportedTokenError. Add error_code attributes. | Restrictions: Extend base exceptions. | _Leverage: src/app/domain/exceptions/base.py | _Requirements: Requirement 9 | Success: Exceptions inherit correctly. Log implementation and mark complete._

---

## Task 3: Infrastructure Layer - Adapter

- [x] 3.1 Create AxelarAdapter implementing AxelarGateway
  - File: `src/app/infrastructure/adapters/external/axelar_adapter.py`
  - Implement AxelarGateway using existing AxelarClient
  - Add express transfer support
  - Implement variable TTL caching
  - Purpose: Bridge domain port to infrastructure client
  - _Leverage: `src/app/infrastructure/adapters/external/axelar_client.py`, `src/app/infrastructure/cache/external_api_cache.py`_
  - _Requirements: R1, R2, R3, R4, R5, R6, R9_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer | Task: Create AxelarAdapter in src/app/infrastructure/adapters/external/axelar_adapter.py implementing AxelarGateway. Inject AxelarClient and cache. Implement express premium logic (2x fee, 3x faster). Cache: 1h chains, 5min routes, 15s active transfers, 24h completed. Transform client models to domain. | Restrictions: Do not modify client. | _Leverage: src/app/infrastructure/adapters/external/axelar_client.py | _Requirements: Requirements 1-6, 9 | Success: Adapter implements Protocol, express works. Log implementation and mark complete._

---

## Task 4: Application Layer - Queries

- [x] 4.1 Create GetRoutes query
  - File: `src/app/application/queries/axelar/get_routes.py`
  - Define GetRoutesRequest dataclass
  - Implement GetRoutes
  - Purpose: Get available bridge routes
  - _Leverage: `src/app/application/queries/` patterns_
  - _Requirements: R1_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetRoutes query in src/app/application/queries/axelar/get_routes.py. Define GetRoutesRequest(source_chain, destination_chain, token). Inject AxelarGateway. Return list of BridgeRoute including standard and express options. | Restrictions: Depend only on domain port. | _Leverage: src/app/application/queries/ patterns | _Requirements: Requirement 1 | Success: Returns routes. Log implementation and mark complete._

- [x] 4.2 Create EstimateTransfer query
  - File: `src/app/application/queries/axelar/estimate_transfer.py`
  - Define EstimateTransferRequest dataclass
  - Implement EstimateTransfer with express comparison
  - Purpose: Estimate transfer costs
  - _Leverage: `src/app/application/queries/axelar/get_routes.py`_
  - _Requirements: R2, R6_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create EstimateTransfer query in src/app/application/queries/axelar/estimate_transfer.py. Define EstimateTransferRequest(source_chain, destination_chain, token, amount, include_express). Return TransferEstimateResponse with standard, express estimates, and recommendation (EXPRESS if savings > 10min and cost < $5). | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/axelar/get_routes.py | _Requirements: Requirements 2, 6 | Success: Returns estimates with recommendation. Log implementation and mark complete._

- [x] 4.3 Create TrackTransfer query
  - File: `src/app/application/queries/axelar/track_transfer.py`
  - Define TrackTransferRequest dataclass
  - Implement TrackTransfer with progress calculation
  - Purpose: Track transfer status
  - _Leverage: `src/app/application/queries/axelar/get_routes.py`_
  - _Requirements: R3_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create TrackTransfer query in src/app/application/queries/axelar/track_transfer.py. Define TrackTransferRequest(tx_hash). Return TransferTrackingResponse with transfer, progress_pct (PENDING=10, CONFIRMED=30, EXECUTING=70, EXECUTED=100), next_step (human-readable), estimated_completion. | Restrictions: Raise TransferNotFoundError if not found. | _Leverage: src/app/application/queries/axelar/get_routes.py | _Requirements: Requirement 3 | Success: Returns tracking with progress. Log implementation and mark complete._

- [x] 4.4 Create GetChains query
  - File: `src/app/application/queries/axelar/get_chains.py`
  - Define GetChainsRequest dataclass
  - Implement GetChains
  - Purpose: Get supported chains
  - _Leverage: `src/app/application/queries/axelar/get_routes.py`_
  - _Requirements: R5_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetChains query in src/app/application/queries/axelar/get_chains.py. Define GetChainsRequest(). Return list of supported chains with chain_id and name. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/axelar/get_routes.py | _Requirements: Requirement 5 | Success: Returns chains. Log implementation and mark complete._

- [x] 4.5 Create GetTokens query
  - File: `src/app/application/queries/axelar/get_tokens.py`
  - Define GetTokensRequest dataclass
  - Implement GetTokens for chain
  - Purpose: Get supported tokens
  - _Leverage: `src/app/application/queries/axelar/get_routes.py`_
  - _Requirements: R5_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetTokens query in src/app/application/queries/axelar/get_tokens.py. Define GetTokensRequest(chain). Return list of tokens with symbol, decimals, address. Indicate axl-wrapped tokens. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/axelar/get_routes.py | _Requirements: Requirement 5 | Success: Returns tokens. Log implementation and mark complete._

---

## Task 5: Presentation Layer - HTTP Router

- [x] 5.1 Create Axelar HTTP router
  - File: `src/app/presentation/http/controllers/defi/axelar_router.py`
  - Define all endpoints from design
  - Purpose: HTTP API for bridge operations
  - _Leverage: `src/app/presentation/http/controllers/` patterns_
  - _Requirements: R1-R6_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: FastAPI Developer | Task: Create axelar_router.py in src/app/presentation/http/controllers/defi/. Endpoints: GET /routes, GET /estimate, GET /transfer/{tx_hash}, GET /chains, GET /tokens/{chain}. Use FromDishka for DI. | Restrictions: Follow router patterns. | _Leverage: src/app/presentation/http/controllers/ patterns | _Requirements: Requirements 1-6 | Success: All endpoints work. Log implementation and mark complete._

- [x] 5.2 Create response schemas
  - File: `src/app/presentation/http/controllers/defi/axelar_schemas.py`
  - Define Pydantic models
  - Purpose: API response serialization
  - _Leverage: Existing schema patterns_
  - _Requirements: R1-R6_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create axelar_schemas.py with: RoutesResponse, TransferEstimateResponse (with standard, express, recommendation), TransferTrackingResponse (with progress_pct, next_step), ChainsResponse, TokensResponse. Add from_domain() methods. | Restrictions: Use Pydantic v2. | _Leverage: Existing schema patterns | _Requirements: Requirements 1-6 | Success: Schemas serialize. Log implementation and mark complete._

---

## Task 6: Dependency Injection

- [x] 6.1 Create Axelar DI provider
  - File: `src/app/setup/ioc/axelar.py`
  - Register AxelarClient, AxelarAdapter, AxelarGateway
  - Purpose: Enable DI
  - _Leverage: `src/app/setup/ioc/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create AxelarProvider in src/app/setup/ioc/axelar.py. Register AxelarClient and AxelarAdapter as AxelarGateway (APP scope). Inject cache and settings. | Restrictions: Follow provider patterns. | _Leverage: src/app/setup/ioc/ patterns | _Requirements: All | Success: DI resolves. Log implementation and mark complete._

- [x] 6.2 Register router in app factory
  - File: `src/app/setup/app_factory.py` (modify)
  - Include axelar_router
  - Purpose: Enable endpoints
  - _Leverage: `src/app/setup/app_factory.py`_
  - _Requirements: All_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Modify app_factory.py to import and include axelar_router under /api/v1/defi prefix. Add AxelarProvider. | Restrictions: Minimal changes. | _Leverage: Existing pattern | _Requirements: All | Success: Endpoints accessible. Log implementation and mark complete._

---

## Task 7: Configuration

- [x] 7.1 Add Axelar configuration
  - File: `config/local/config.toml` (modify)
  - Add [axelar] section
  - Purpose: Configurable parameters
  - _Leverage: `config/local/config.toml`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps | Task: Add [axelar] section to config.toml with: enabled=true, testnet=false, cache_route_ttl=300, cache_chain_ttl=3600, cache_transfer_ttl=15. Add [axelar.express] with fee_multiplier=2.0, time_divisor=3. Add [axelar.endpoints]. | Restrictions: Follow config patterns. | _Leverage: config/local/config.toml | _Requirements: Requirement 9 | Success: Config loads. Log implementation and mark complete._

---

## Task 8: Testing

- [x] 8.1 Create adapter unit tests
  - File: `tests/unit/infrastructure/adapters/test_axelar_adapter.py`
  - Test transformation and express logic
  - Purpose: Ensure adapter reliability
  - _Leverage: `tests/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_axelar_adapter.py. Mock AxelarClient. Test: get_routes returns standard and express, estimate_transfer applies express premium correctly (2x fee, 3x faster), caching varies by status. | Restrictions: Unit tests only. | _Leverage: Existing test patterns | _Requirements: All | Success: Tests pass. Log implementation and mark complete._

- [x] 8.2 Create integration tests
  - File: `tests/integration/defi/test_axelar_integration.py`
  - Test full flow
  - Purpose: End-to-end functionality
  - _Leverage: `tests/integration/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec axelar-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_axelar_integration.py. Test: GET /routes returns options, GET /estimate returns recommendation, GET /transfer/{hash} returns tracking. Mock external API. | Restrictions: Mock external deps. | _Leverage: Existing integration patterns | _Requirements: All | Success: Integration tests pass. Log implementation and mark complete._

---

## Summary

| Phase | Tasks | Files Created |
|-------|-------|---------------|
| Domain | 1.1-1.3, 2.1 | 6 files |
| Infrastructure | 3.1 | 1 file |
| Application | 4.1-4.5 | 5 files |
| Presentation | 5.1-5.2 | 2 files |
| DI & Config | 6.1-6.2, 7.1 | 2 files + mods |
| Testing | 8.1-8.2 | 2 files |
| **Total** | **14 tasks** | **~18 files** |
