# Tasks Document: Curve Finance Integration

## Overview
Implementation tasks for completing the Curve Finance integration following hexagonal architecture patterns.

---

## Task 1: Domain Layer - Port and Value Objects

- [x] 1.1 Create CurveGateway port interface
  - File: `src/app/domain/ports/curve_gateway.py`
  - Define Protocol interface with all Curve operations
  - Include type hints for all method signatures
  - Purpose: Establish domain contract for Curve operations
  - _Leverage: `src/app/domain/ports/` existing port patterns_
  - _Requirements: R1, R2, R3, R4, R5_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer specializing in hexagonal architecture and Protocol interfaces | Task: Create CurveGateway Protocol interface in src/app/domain/ports/curve_gateway.py defining methods for get_pools, get_pool_by_address, get_pool_apy, get_swap_quote, get_gauges, get_tvl following the design document. Reference existing port patterns in src/app/domain/ports/. | Restrictions: Do not implement any logic, only define interface. Use typing.Protocol. Follow existing naming conventions. | _Leverage: src/app/domain/ports/ai/llm_gateway.py for Protocol pattern | _Requirements: Requirements 1-5 from requirements.md | Success: Protocol compiles without errors, all methods have proper type hints, follows project port conventions. After completion, mark task as in-progress in tasks.md, log implementation with log-implementation tool, then mark as complete._

- [x] 1.2 Create Pool entity and value objects
  - File: `src/app/domain/entities/curve/pool.py`
  - File: `src/app/domain/value_objects/curve/pool_apy.py`
  - File: `src/app/domain/value_objects/curve/swap_quote.py`
  - Define Pool dataclass with all fields from design
  - Define PoolAPY frozen dataclass for APY breakdown
  - Define SwapQuote frozen dataclass for swap quotes
  - Purpose: Domain models for Curve data
  - _Leverage: `src/app/domain/entities/` existing patterns_
  - _Requirements: R1, R2, R3, R4_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer with DDD expertise | Task: Create Pool entity in src/app/domain/entities/curve/pool.py and PoolAPY, SwapQuote value objects in src/app/domain/value_objects/curve/. Use @dataclass for entity, @dataclass(frozen=True) for value objects. Include to_dict/from_dict methods. | Restrictions: Entities mutable, value objects immutable. Use Decimal for monetary values. | _Leverage: Existing entity patterns in src/app/domain/entities/ | _Requirements: Requirements 1-4 | Success: All models properly typed, serialization works, imports resolve. After completion, log implementation with log-implementation tool, then mark task as complete._

- [x] 1.3 Create Gauge entity
  - File: `src/app/domain/entities/curve/gauge.py`
  - Define Gauge dataclass for gauge reward data
  - Purpose: Domain model for Curve gauge data
  - _Leverage: `src/app/domain/entities/curve/pool.py`_
  - _Requirements: R3_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create Gauge entity in src/app/domain/entities/curve/gauge.py with fields: address, pool_address, crv_emissions_per_day, relative_weight, total_staked, apy. Use @dataclass. | Restrictions: Follow Pool entity pattern. Use Decimal for numeric values. | _Leverage: src/app/domain/entities/curve/pool.py | _Requirements: Requirement 3 | Success: Entity compiles, follows project conventions. Log implementation and mark complete._

---

## Task 2: Domain Layer - Exceptions

- [x] 2.1 Create Curve domain exceptions
  - File: `src/app/domain/exceptions/curve.py`
  - Define CurveError base exception
  - Define PoolNotFoundError, InvalidTokenError, CurveAPIError
  - Purpose: Domain-specific error handling
  - _Leverage: `src/app/domain/exceptions/base.py`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create Curve exceptions in src/app/domain/exceptions/curve.py. Define CurveError(DomainError), PoolNotFoundError(CurveError), InvalidTokenError(CurveError), CurveAPIError(CurveError). Add error_code class attributes. | Restrictions: Extend existing base exceptions. Include docstrings. | _Leverage: src/app/domain/exceptions/base.py | _Requirements: Requirement 9 | Success: Exceptions properly inherit, have codes, importable. Log implementation and mark complete._

---

## Task 3: Infrastructure Layer - Adapter

- [x] 3.1 Create CurveAdapter implementing CurveGateway
  - File: `src/app/infrastructure/adapters/external/curve_adapter.py`
  - Implement CurveGateway Protocol using existing CurveClient
  - Add caching logic with ExternalAPICache
  - Transform client models to domain models
  - Purpose: Bridge between domain port and infrastructure client
  - _Leverage: `src/app/infrastructure/adapters/external/curve_client.py`, `src/app/infrastructure/cache/external_api_cache.py`_
  - _Requirements: R1, R2, R3, R4, R5, R8_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer specializing in adapter patterns | Task: Create CurveAdapter in src/app/infrastructure/adapters/external/curve_adapter.py implementing CurveGateway Protocol. Inject CurveClient and ExternalAPICache. Implement all gateway methods with caching (5min pools, 1min APY, 10min gauges). Transform CurveClient dataclasses to domain entities. | Restrictions: Do not modify CurveClient. Use async/await. Handle API errors with domain exceptions. | _Leverage: src/app/infrastructure/adapters/external/curve_client.py, src/app/infrastructure/cache/external_api_cache.py | _Requirements: Requirements 1-5, 8 | Success: Adapter implements all Protocol methods, caching works, transformations correct. Log implementation and mark complete._

---

## Task 4: Application Layer - Queries

- [x] 4.1 Create GetPools query interactor
  - File: `src/app/application/queries/curve/get_pools.py`
  - Define GetPoolsRequest dataclass
  - Implement GetPools class with execute method
  - Add sorting and filtering logic
  - Purpose: Application use case for pool listing
  - _Leverage: `src/app/application/queries/` existing patterns_
  - _Requirements: R1_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer with Clean Architecture expertise | Task: Create GetPools query in src/app/application/queries/curve/get_pools.py. Define GetPoolsRequest(chain, sort_by, limit). Inject CurveGateway. Implement execute() that gets pools, sorts by tvl/apy/volume, limits results. | Restrictions: Only depend on domain port. No infrastructure imports. | _Leverage: Existing query patterns in src/app/application/queries/ | _Requirements: Requirement 1 | Success: Query works with gateway, sorting correct. Log implementation and mark complete._

- [x] 4.2 Create GetPoolAPY query interactor
  - File: `src/app/application/queries/curve/get_pool_apy.py`
  - Define GetPoolAPYRequest dataclass
  - Implement GetPoolAPY class with execute method
  - Purpose: Get detailed APY breakdown for a pool
  - _Leverage: `src/app/application/queries/curve/get_pools.py`_
  - _Requirements: R4_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetPoolAPY query in src/app/application/queries/curve/get_pool_apy.py. Define GetPoolAPYRequest(pool_address, chain). Inject CurveGateway. Return PoolAPY with base/crv/reward breakdown. | Restrictions: Follow GetPools pattern. Handle PoolNotFoundError. | _Leverage: src/app/application/queries/curve/get_pools.py | _Requirements: Requirement 4 | Success: Returns APY breakdown correctly. Log implementation and mark complete._

- [x] 4.3 Create GetGauges query interactor
  - File: `src/app/application/queries/curve/get_gauges.py`
  - Define GetGaugesRequest dataclass
  - Implement GetGauges class with execute method
  - Purpose: Get gauge reward data
  - _Leverage: `src/app/application/queries/curve/get_pools.py`_
  - _Requirements: R3_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetGauges query in src/app/application/queries/curve/get_gauges.py. Define GetGaugesRequest(chain). Inject CurveGateway. Return list of Gauge entities sorted by APY. | Restrictions: Follow existing query patterns. | _Leverage: src/app/application/queries/curve/get_pools.py | _Requirements: Requirement 3 | Success: Returns gauges correctly. Log implementation and mark complete._

- [x] 4.4 Create GetTVL query interactor
  - File: `src/app/application/queries/curve/get_tvl.py`
  - Define GetTVLRequest dataclass
  - Implement GetTVL class with execute method
  - Purpose: Get TVL analytics
  - _Leverage: `src/app/application/queries/curve/get_pools.py`_
  - _Requirements: R5_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetTVL query in src/app/application/queries/curve/get_tvl.py. Define GetTVLRequest(chain). Inject CurveGateway. Return TVL data with chain breakdown. | Restrictions: Follow existing patterns. | _Leverage: src/app/application/queries/curve/get_pools.py | _Requirements: Requirement 5 | Success: Returns TVL correctly. Log implementation and mark complete._

---

## Task 5: Application Layer - Commands

- [x] 5.1 Create GetSwapQuote command interactor
  - File: `src/app/application/commands/curve/get_swap_quote.py`
  - Define SwapQuoteRequest dataclass
  - Implement GetSwapQuote class with execute method
  - Add price impact warnings
  - Purpose: Get swap quotes with risk warnings
  - _Leverage: `src/app/application/commands/` existing patterns_
  - _Requirements: R2_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetSwapQuote command in src/app/application/commands/curve/get_swap_quote.py. Define SwapQuoteRequest(from_token, to_token, amount, chain). Inject CurveGateway. Add warnings list for high price impact (>0.5%) or depeg risk. | Restrictions: Commands for operations with side effects or complex logic. | _Leverage: Existing command patterns | _Requirements: Requirement 2 | Success: Returns quote with appropriate warnings. Log implementation and mark complete._

---

## Task 6: Presentation Layer - HTTP Router

- [x] 6.1 Create Curve HTTP router
  - File: `src/app/presentation/http/controllers/defi/curve_router.py`
  - Define all endpoints from design document
  - Use Pydantic models for request/response
  - Integrate with Dishka DI
  - Purpose: HTTP API for Curve operations
  - _Leverage: `src/app/presentation/http/controllers/` existing routers_
  - _Requirements: R1, R2, R3, R4, R5_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: FastAPI Developer | Task: Create curve_router.py in src/app/presentation/http/controllers/defi/. Define endpoints: GET /pools, GET /pools/{address}, GET /pools/{address}/apy, POST /quote, GET /gauges, GET /tvl. Use FromDishka for DI. Create Pydantic response models. | Restrictions: Follow existing router patterns. Use error_map for error handling. | _Leverage: src/app/presentation/http/controllers/chat/router.py | _Requirements: Requirements 1-5 | Success: All endpoints work, proper error responses. Log implementation and mark complete._

- [x] 6.2 Create response models
  - File: `src/app/presentation/http/controllers/defi/curve_schemas.py`
  - Define Pydantic models for all responses
  - Include from_domain class methods
  - Purpose: API response serialization
  - _Leverage: `src/app/presentation/http/controllers/` existing schemas_
  - _Requirements: R1, R2, R3, R4, R5_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create curve_schemas.py with Pydantic models: PoolResponse, PoolsResponse, PoolAPYResponse, SwapQuoteResponse, GaugesResponse, TVLResponse. Add from_domain() classmethod to convert domain models. | Restrictions: Use Pydantic v2 syntax. | _Leverage: Existing schema patterns | _Requirements: Requirements 1-5 | Success: All schemas serialize correctly. Log implementation and mark complete._

---

## Task 7: Dependency Injection

- [x] 7.1 Create Curve DI provider
  - File: `src/app/setup/ioc/curve.py`
  - Register CurveClient, CurveAdapter, CurveGateway
  - Configure appropriate scopes
  - Purpose: Enable DI for Curve components
  - _Leverage: `src/app/setup/ioc/` existing providers_
  - _Requirements: All_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer with Dishka DI expertise | Task: Create CurveProvider in src/app/setup/ioc/curve.py. Register: CurveClient (APP scope), CurveAdapter as CurveGateway (APP scope). Inject Settings and ExternalAPICache. | Restrictions: Follow existing provider patterns. | _Leverage: src/app/setup/ioc/ existing providers | _Requirements: All | Success: DI resolves correctly. Log implementation and mark complete._

- [x] 7.2 Register router in app factory
  - File: `src/app/setup/app_factory.py` (modify)
  - Include curve_router in API routes
  - Purpose: Enable Curve endpoints
  - _Leverage: `src/app/setup/app_factory.py`_
  - _Requirements: All_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Modify src/app/setup/app_factory.py to import and include curve_router under /api/v1/defi prefix. Add CurveProvider to provider list. | Restrictions: Minimal changes to existing code. | _Leverage: Existing router registration pattern | _Requirements: All | Success: /api/v1/defi/curve/* endpoints accessible. Log implementation and mark complete._

---

## Task 8: Configuration

- [x] 8.1 Add Curve configuration
  - File: `config/local/config.toml` (modify)
  - Add [curve] section with settings
  - Purpose: Configurable Curve parameters
  - _Leverage: `config/local/config.toml`_
  - _Requirements: R7, R8_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps Engineer | Task: Add [curve] section to config/local/config.toml with: enabled=true, default_chain="ethereum", cache_pool_ttl=300, cache_apy_ttl=60, cache_gauge_ttl=600. Add [curve.chains] mapping. | Restrictions: Follow existing config patterns. | _Leverage: config/local/config.toml | _Requirements: Requirements 7, 8 | Success: Config loads correctly. Log implementation and mark complete._

---

## Task 9: Testing

- [ ] 9.1 Create adapter unit tests
  - File: `tests/unit/infrastructure/adapters/test_curve_adapter.py`
  - Mock CurveClient and cache
  - Test transformation and caching logic
  - Purpose: Ensure adapter reliability
  - _Leverage: `tests/` existing test patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Test Engineer | Task: Create test_curve_adapter.py with pytest. Mock CurveClient responses. Test: get_pools returns transformed data, caching works, errors propagate correctly. Use AsyncMock for async methods. | Restrictions: Unit tests only, no real API calls. | _Leverage: Existing test patterns | _Requirements: All | Success: Tests pass, good coverage. Log implementation and mark complete._

- [ ] 9.2 Create integration tests
  - File: `tests/integration/defi/test_curve_integration.py`
  - Test full flow from router to adapter
  - Purpose: Ensure end-to-end functionality
  - _Leverage: `tests/integration/` existing patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec curve-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Test Engineer | Task: Create test_curve_integration.py. Use TestClient with app. Test: GET /api/v1/defi/curve/pools returns valid response, error handling works. Mock external API at adapter level. | Restrictions: Integration tests, mock external dependencies. | _Leverage: Existing integration test patterns | _Requirements: All | Success: Integration tests pass. Log implementation and mark complete._

---

## Summary

| Phase | Tasks | Files Created |
|-------|-------|---------------|
| Domain | 1.1-1.3, 2.1 | 5 files |
| Infrastructure | 3.1 | 1 file |
| Application | 4.1-4.4, 5.1 | 5 files |
| Presentation | 6.1-6.2 | 2 files |
| DI & Config | 7.1-7.2, 8.1 | 2 files + mods |
| Testing | 9.1-9.2 | 2 files |
| **Total** | **15 tasks** | **~17 files** |
