# Tasks Document: LI.FI SDK Integration

## Phase 1: Domain Layer

- [ ] 1. Create CrossChainGateway port interface
  - File: `src/app/domain/ports/cross_chain_gateway.py`
  - Define protocol interface for cross-chain operations
  - Include type hints for all methods
  - Purpose: Establish domain contract for cross-chain functionality
  - _Leverage: `src/app/domain/ports/` existing port patterns_
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Domain Architect specializing in hexagonal architecture and protocol interfaces
      
      Task: Create CrossChainGateway port interface following requirements 1.1, 2.1, 3.1, 4.1, 5.1, 6.1:
      1. Create `src/app/domain/ports/cross_chain_gateway.py`
      2. Define `CrossChainGateway(Protocol)` with methods:
         - `get_quote(from_chain, to_chain, from_token, to_token, from_amount, from_address, slippage) -> Quote`
         - `get_routes(from_chain, to_chain, from_token, to_token, from_amount, from_address, options) -> list[Route]`
         - `get_chains() -> list[Chain]`
         - `get_tokens(chain_id) -> list[Token]`
         - `get_token_balance(address, chain_id, token_address) -> TokenBalance`
         - `get_status(tx_hash, from_chain, to_chain) -> TransactionStatus`
      3. All methods must be async
      4. Use proper type hints with domain models
      
      Restrictions:
      - Must be a Protocol class (structural typing)
      - No implementation details in the port
      - No dependencies on infrastructure
      - Follow existing port patterns in the codebase
      
      _Leverage: `src/app/domain/ports/` for existing patterns
      
      Success:
      - Port defines clean interface for all cross-chain operations
      - All methods have proper type hints
      - No infrastructure dependencies
      - Follows hexagonal architecture principles
      
      After completing, mark this task as in-progress in tasks.md by changing [ ] to [-], implement, then log implementation with log-implementation tool, then mark as complete [x]._

- [ ] 2. Create cross-chain domain models
  - File: `src/app/domain/entities/cross_chain.py`
  - Define Quote, Route, Chain, Token, TransactionStatus entities
  - Purpose: Establish domain models for cross-chain data
  - _Leverage: `src/app/domain/entities/` existing entity patterns_
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 4.1, 6.1_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Domain Developer specializing in DDD and value objects
      
      Task: Create cross-chain domain models following requirements:
      1. Create `src/app/domain/entities/cross_chain.py` with dataclasses:
         - `Chain(id, name, key, logo_uri, native_token, rpc_urls, explorer_url, is_testnet)`
         - `Token(address, symbol, name, decimals, chain_id, logo_uri, price_usd)`
         - `TokenBalance(token, amount, amount_usd)`
         - `GasEstimate(gas_limit, gas_price, total_cost_usd)`
         - `FeeCost(name, amount, amount_usd, token)`
         - `Step(tool, type, from_token, to_token, from_amount, to_amount, estimate)`
         - `Quote(id, from_chain_id, to_chain_id, from_token, to_token, from_amount, to_amount, to_amount_min, slippage, gas_estimate, fee_costs, execution_duration, tool, steps)`
         - `Route(id, from_chain_id, to_chain_id, from_token, to_token, from_amount, to_amount, gas_estimate, steps, tags)`
         - `TransactionStatus(status, from_chain_id, to_chain_id, from_tx_hash, to_tx_hash, from_amount, to_amount, bridge, substatus, error_message)`
      2. Use `Decimal` for amounts (not float)
      3. Create `TransactionState` enum: PENDING, IN_PROGRESS, COMPLETED, FAILED
      
      Restrictions:
      - All models must be immutable dataclasses (frozen=True)
      - Use Decimal for financial amounts
      - No infrastructure dependencies
      - Follow existing entity patterns
      
      _Leverage: `src/app/domain/entities/` patterns
      
      Success:
      - All domain models defined with proper types
      - Models are immutable
      - Decimal used for financial values
      - Enums defined for status values
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 3. Create cross-chain domain exceptions
  - File: `src/app/domain/exceptions/cross_chain.py`
  - Define exceptions for cross-chain error scenarios
  - Purpose: Establish domain exception hierarchy for cross-chain errors
  - _Leverage: `src/app/domain/exceptions/` existing exception patterns_
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in error handling and exception design
      
      Task: Create cross-chain domain exceptions following requirements 9.1-9.5:
      1. Create `src/app/domain/exceptions/cross_chain.py`
      2. Define exception classes:
         - `CrossChainError(DomainError)` - Base exception
         - `InvalidTokenError(CrossChainError)` - Invalid token address
         - `UnsupportedChainError(CrossChainError)` - Chain not supported
         - `NoRoutesFoundError(CrossChainError)` - No routes available
         - `InsufficientLiquidityError(CrossChainError)` - Not enough liquidity
         - `RateLimitExceededError(CrossChainError)` - API rate limit hit
         - `LiFiAPIError(CrossChainError)` - Generic API error
         - `TransactionFailedError(CrossChainError)` - Transaction failed
      3. Add error codes to each exception
      4. Include helpful error messages
      
      Restrictions:
      - Must inherit from domain base exception
      - Include error codes for translation
      - Follow existing exception patterns
      - No infrastructure dependencies
      
      _Leverage: `src/app/domain/exceptions/` for patterns
      
      Success:
      - All exceptions inherit from CrossChainError
      - Each exception has unique error code
      - Error messages are user-friendly
      - Exceptions can be caught hierarchically
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 2: Infrastructure Layer - LI.FI Client

- [ ] 4. Create LiFiClient HTTP wrapper
  - File: `src/app/infrastructure/adapters/external/lifi/client.py`
  - Implement async HTTP client for LI.FI REST API
  - Include retry logic and timeout handling
  - Purpose: Provide low-level HTTP access to LI.FI API
  - _Leverage: `src/app/infrastructure/adapters/external/` existing HTTP patterns_
  - _Requirements: 1.1, 1.2, 9.2, 9.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in async HTTP clients and API integrations
      
      Task: Create LiFiClient HTTP wrapper following requirements 1.1, 1.2, 9.2, 9.5:
      1. Create `src/app/infrastructure/adapters/external/lifi/client.py`
      2. Implement `LiFiClient` class with:
         - `__init__(base_url, integrator, timeout, retry_config)`
         - `request(method, endpoint, params, json) -> dict` - Base request method
         - `get_quote(params) -> dict` - GET /quote
         - `get_routes(params) -> dict` - POST /advanced/routes
         - `get_chains() -> dict` - GET /chains
         - `get_tokens(chains) -> dict` - GET /tokens
         - `get_status(params) -> dict` - GET /status
         - `close() -> None` - Cleanup
      3. Use httpx AsyncClient with connection pooling
      4. Implement retry with tenacity (exponential backoff)
      5. Add proper timeout handling
      6. Include `x-lifi-integrator` header in all requests
      
      Restrictions:
      - Must be fully async
      - Use httpx, not requests
      - Implement proper resource cleanup (async context manager)
      - Rate limit handling with backoff
      
      _Leverage: HTTP patterns from `src/app/infrastructure/adapters/external/`
      
      Success:
      - Client makes proper HTTP requests to LI.FI API
      - Retry logic handles transient failures
      - Timeouts prevent hanging requests
      - Resources properly cleaned up
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 5. Create LI.FI response models
  - File: `src/app/infrastructure/adapters/external/lifi/models.py`
  - Define Pydantic models for API response parsing
  - Purpose: Type-safe parsing of LI.FI API responses
  - _Leverage: Existing Pydantic model patterns_
  - _Requirements: 2.1, 2.2, 3.1, 4.1, 6.1_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in Pydantic and API response modeling
      
      Task: Create LI.FI response models following requirements:
      1. Create `src/app/infrastructure/adapters/external/lifi/models.py`
      2. Define Pydantic models for LI.FI API responses:
         - `LiFiChainResponse` - Chain data from /chains
         - `LiFiTokenResponse` - Token data from /tokens
         - `LiFiQuoteResponse` - Quote data from /quote
         - `LiFiRoutesResponse` - Routes data from /advanced/routes
         - `LiFiStatusResponse` - Status data from /status
         - `LiFiErrorResponse` - Error response structure
      3. Include nested models for complex structures:
         - `LiFiStep`, `LiFiEstimate`, `LiFiGasCost`, `LiFiFeeCost`
      4. Add validators for amounts (convert to Decimal)
      
      Restrictions:
      - Use Pydantic v2 syntax
      - Handle optional fields gracefully
      - Convert string amounts to Decimal
      - Follow LI.FI API response structure exactly
      
      _Leverage: LI.FI API documentation structure
      
      Success:
      - All API responses can be parsed without errors
      - Amounts converted to Decimal correctly
      - Optional fields handled properly
      - Models validate real API responses
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 6. Create LI.FI exception handling
  - File: `src/app/infrastructure/adapters/external/lifi/exceptions.py`
  - Map LI.FI API errors to domain exceptions
  - Purpose: Translate API errors to domain language
  - _Leverage: `src/app/domain/exceptions/cross_chain.py`_
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in error handling and exception translation
      
      Task: Create LI.FI exception handling following requirements 9.1-9.5:
      1. Create `src/app/infrastructure/adapters/external/lifi/exceptions.py`
      2. Implement `parse_lifi_error(response: dict, status_code: int) -> CrossChainError`:
         - Map LI.FI error codes to domain exceptions
         - Extract error message from response
         - Handle unknown errors gracefully
      3. Create error code mapping:
         - `INVALID_TOKEN` -> InvalidTokenError
         - `CHAIN_NOT_SUPPORTED` -> UnsupportedChainError
         - `NO_ROUTES_FOUND` -> NoRoutesFoundError
         - `INSUFFICIENT_LIQUIDITY` -> InsufficientLiquidityError
         - Rate limit (429) -> RateLimitExceededError
         - Server error (5xx) -> LiFiAPIError
      4. Include original error details in exception
      
      Restrictions:
      - Must return domain exceptions, not infrastructure exceptions
      - Handle all known LI.FI error codes
      - Unknown errors wrapped as LiFiAPIError
      - Include debugging information
      
      _Leverage: `src/app/domain/exceptions/cross_chain.py`
      
      Success:
      - All LI.FI errors mapped to domain exceptions
      - Error messages preserved for debugging
      - Unknown errors handled gracefully
      - Exception hierarchy maintained
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 3: Infrastructure Layer - Adapter

- [ ] 7. Create LiFiAdapter implementing CrossChainGateway
  - File: `src/app/infrastructure/adapters/external/lifi/adapter.py`
  - Implement gateway interface using LiFiClient
  - Transform API responses to domain models
  - Purpose: Bridge between domain and LI.FI API
  - _Leverage: `src/app/domain/ports/cross_chain_gateway.py`, `src/app/infrastructure/adapters/external/lifi/client.py`_
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in adapter patterns and data transformation
      
      Task: Create LiFiAdapter implementing CrossChainGateway:
      1. Create `src/app/infrastructure/adapters/external/lifi/adapter.py`
      2. Implement `LiFiAdapter(CrossChainGateway)` with:
         - `__init__(client: LiFiClient, cache: ExternalAPICache, chain_cache_ttl, token_cache_ttl)`
         - All methods from CrossChainGateway port
      3. Implement transformation methods:
         - `_transform_chain(data: dict) -> Chain`
         - `_transform_token(data: dict) -> Token`
         - `_transform_quote(data: dict) -> Quote`
         - `_transform_route(data: dict) -> Route`
         - `_transform_status(data: dict) -> TransactionStatus`
      4. Use cache for chains and tokens
      5. Handle errors using exception module
      
      Restrictions:
      - Must implement all gateway methods
      - Transform ALL fields from API to domain models
      - Use caching appropriately (chains: 1hr, tokens: 15min)
      - Handle errors with proper exception translation
      
      _Leverage: Domain models, LiFiClient, exception handling
      
      Success:
      - Adapter implements all gateway methods
      - API responses correctly transformed to domain models
      - Caching reduces API calls for static data
      - Errors properly translated to domain exceptions
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 8. Create LI.FI caching layer
  - File: `src/app/infrastructure/adapters/external/lifi/cache.py`
  - Implement cache wrapper for chains and tokens
  - Purpose: Reduce API calls for slowly-changing data
  - _Leverage: `src/app/infrastructure/cache/external_api_cache.py`_
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in caching strategies
      
      Task: Create LI.FI caching layer following requirements 8.1-8.5:
      1. Create `src/app/infrastructure/adapters/external/lifi/cache.py`
      2. Implement `LiFiCache` class with:
         - `__init__(cache: ExternalAPICache)`
         - `get_chains() -> list[Chain] | None`
         - `set_chains(chains, ttl=3600) -> None`
         - `get_tokens(chain_id) -> list[Token] | None`
         - `set_tokens(chain_id, tokens, ttl=900) -> None`
         - `invalidate_chains() -> None`
         - `invalidate_tokens(chain_id) -> None`
      3. Use cache key patterns:
         - `lifi:chains` for chain list
         - `lifi:tokens:{chain_id}` for token lists
      4. Serialize domain models to JSON for storage
      
      Restrictions:
      - Use existing ExternalAPICache infrastructure
      - Proper serialization/deserialization
      - TTL must be configurable
      - Handle cache misses gracefully
      
      _Leverage: `src/app/infrastructure/cache/external_api_cache.py`
      
      Success:
      - Chains cached for 1 hour
      - Tokens cached for 15 minutes per chain
      - Cache hits return domain models
      - Cache misses return None (not error)
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 9. Create LI.FI module exports
  - File: `src/app/infrastructure/adapters/external/lifi/__init__.py`
  - Export public classes and functions
  - Purpose: Clean module interface
  - _Leverage: Existing module patterns_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer
      
      Task: Create LI.FI module exports:
      1. Create `src/app/infrastructure/adapters/external/lifi/__init__.py`
      2. Export public classes:
         - `LiFiClient` from client.py
         - `LiFiAdapter` from adapter.py
         - `LiFiCache` from cache.py
         - Response models from models.py
         - `parse_lifi_error` from exceptions.py
      3. Add module docstring explaining purpose
      
      Restrictions:
      - Only export public API
      - Use `__all__` for explicit exports
      - Follow existing module patterns
      
      Success:
      - `from app.infrastructure.adapters.external.lifi import LiFiAdapter` works
      - All public classes accessible
      - Internal implementation hidden
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 4: Application Layer

- [ ] 10. Create GetQuote interactor
  - File: `src/app/application/commands/cross_chain/get_quote.py`
  - Implement quote retrieval use case
  - Purpose: Application layer for quote requests
  - _Leverage: `src/app/application/commands/` existing patterns_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in application layer design
      
      Task: Create GetQuote interactor following requirements 2.1-2.6:
      1. Create `src/app/application/commands/cross_chain/get_quote.py`
      2. Define `GetQuoteRequest` dataclass with:
         - from_chain_id, to_chain_id, from_token, to_token
         - from_amount, from_address, slippage (default 0.5)
      3. Implement `GetQuote` class:
         - `__init__(gateway: CrossChainGateway)`
         - `execute(request: GetQuoteRequest) -> Quote`
      4. Add input validation (addresses, amounts)
      5. Handle gateway errors appropriately
      
      Restrictions:
      - Must use gateway port (not adapter directly)
      - Validate inputs before calling gateway
      - Return domain Quote model
      - Follow existing interactor patterns
      
      _Leverage: `src/app/application/commands/` patterns
      
      Success:
      - Interactor accepts request and returns Quote
      - Input validation prevents invalid requests
      - Errors from gateway propagate correctly
      - Follows CQRS command pattern
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 11. Create GetRoutes interactor
  - File: `src/app/application/commands/cross_chain/get_routes.py`
  - Implement routes discovery use case
  - Purpose: Application layer for route discovery
  - _Leverage: `src/app/application/commands/` existing patterns_
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in application layer design
      
      Task: Create GetRoutes interactor following requirements 3.1-3.5:
      1. Create `src/app/application/commands/cross_chain/get_routes.py`
      2. Define `RouteOptions` dataclass:
         - sort_by: "CHEAPEST" | "FASTEST" | "SAFEST"
         - max_routes: int (default 5)
         - bridges: list[str] | None (filter)
         - exchanges: list[str] | None (filter)
      3. Define `GetRoutesRequest` dataclass
      4. Implement `GetRoutes` class:
         - `__init__(gateway: CrossChainGateway)`
         - `execute(request: GetRoutesRequest) -> list[Route]`
      5. Sort routes based on options
      
      Restrictions:
      - Must use gateway port
      - Support filtering and sorting
      - Return list of domain Route models
      - Handle empty results gracefully
      
      _Leverage: `src/app/application/commands/` patterns
      
      Success:
      - Returns list of available routes
      - Sorting works correctly
      - Filtering reduces results appropriately
      - Empty results return empty list (not error)
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 12. Create GetStatus interactor
  - File: `src/app/application/commands/cross_chain/get_status.py`
  - Implement transaction status tracking use case
  - Purpose: Application layer for status tracking
  - _Leverage: `src/app/application/commands/` existing patterns_
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in application layer design
      
      Task: Create GetStatus interactor following requirements 6.1-6.5:
      1. Create `src/app/application/commands/cross_chain/get_status.py`
      2. Define `GetStatusRequest` dataclass:
         - tx_hash, from_chain_id, to_chain_id
      3. Implement `GetStatus` class:
         - `__init__(gateway: CrossChainGateway)`
         - `execute(request: GetStatusRequest) -> TransactionStatus`
      4. Validate transaction hash format
      5. Handle not-found scenarios
      
      Restrictions:
      - Must use gateway port
      - Validate tx_hash format (0x...)
      - Return domain TransactionStatus model
      - Handle unknown transactions gracefully
      
      _Leverage: `src/app/application/commands/` patterns
      
      Success:
      - Returns transaction status
      - Invalid tx_hash rejected with clear error
      - Unknown transactions handled appropriately
      - All status states can be returned
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 13. Create chain/token query interactors
  - Files: `src/app/application/queries/cross_chain/get_chains.py`, `get_tokens.py`, `get_token_balance.py`
  - Implement read-only queries for chain/token data
  - Purpose: Application layer for data queries
  - _Leverage: `src/app/application/queries/` existing patterns_
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in CQRS query patterns
      
      Task: Create chain/token query interactors following requirements 4.1-4.5:
      1. Create `src/app/application/queries/cross_chain/get_chains.py`:
         - `QueryChains` class returning `list[Chain]`
      2. Create `src/app/application/queries/cross_chain/get_tokens.py`:
         - `QueryTokensRequest(chain_id: int)`
         - `QueryTokens` class returning `list[Token]`
      3. Create `src/app/application/queries/cross_chain/get_token_balance.py`:
         - `QueryTokenBalanceRequest(address, chain_id, token_address)`
         - `QueryTokenBalance` class returning `TokenBalance`
      4. All queries use CrossChainGateway
      
      Restrictions:
      - Use query pattern (read-only)
      - Must use gateway port
      - Return domain models
      - Follow CQRS conventions
      
      _Leverage: `src/app/application/queries/` patterns
      
      Success:
      - All queries return appropriate domain models
      - Queries are read-only
      - Gateway abstraction maintained
      - Follows CQRS query pattern
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 5: Presentation Layer

- [ ] 14. Create cross-chain API router
  - File: `src/app/presentation/http/controllers/cross_chain/router.py`
  - Set up API router with prefix and tags
  - Purpose: Organize cross-chain endpoints
  - _Leverage: `src/app/presentation/http/controllers/` existing patterns_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in FastAPI
      
      Task: Create cross-chain API router:
      1. Create `src/app/presentation/http/controllers/cross_chain/router.py`
      2. Create `APIRouter(prefix="/cross-chain", tags=["Cross-Chain"])`
      3. Import and include sub-routers:
         - quotes router
         - routes router
         - chains router
         - status router
      4. Add error mapping for cross-chain exceptions
      
      Restrictions:
      - Follow existing router patterns
      - Use error-aware router
      - Proper prefix and tags
      - Clean module organization
      
      Success:
      - Router properly configured
      - All sub-routers included
      - Error mapping set up
      - Tags visible in OpenAPI
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 15. Create quote endpoint
  - File: `src/app/presentation/http/controllers/cross_chain/quotes.py`
  - Implement GET /quote endpoint
  - Purpose: Expose quote functionality via HTTP
  - _Leverage: `src/app/presentation/http/controllers/` existing patterns_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in FastAPI endpoints
      
      Task: Create quote endpoint following requirements 2.1-2.6:
      1. Create `src/app/presentation/http/controllers/cross_chain/quotes.py`
      2. Define `QuoteResponse` Pydantic model
      3. Implement `GET /quote` endpoint:
         - Query params: from_chain, to_chain, from_token, to_token, from_amount, from_address, slippage
         - Returns QuoteResponse
         - Uses GetQuote interactor via Dishka
      4. Add proper error responses (400, 404, 429, 502)
      5. Add OpenAPI documentation
      
      Restrictions:
      - Use Dishka for DI
      - Validate all inputs
      - Return proper HTTP status codes
      - Document all parameters
      
      _Leverage: Existing controller patterns
      
      Success:
      - Endpoint accepts query parameters
      - Returns properly formatted quote
      - Errors return appropriate status codes
      - OpenAPI docs complete
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 16. Create routes endpoint
  - File: `src/app/presentation/http/controllers/cross_chain/routes.py`
  - Implement POST /routes endpoint
  - Purpose: Expose route discovery via HTTP
  - _Leverage: `src/app/presentation/http/controllers/` existing patterns_
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in FastAPI endpoints
      
      Task: Create routes endpoint following requirements 3.1-3.5:
      1. Create `src/app/presentation/http/controllers/cross_chain/routes.py`
      2. Define `RoutesRequest` Pydantic model (body)
      3. Define `RoutesResponse` Pydantic model
      4. Implement `POST /routes` endpoint:
         - Body: RoutesRequest with options
         - Returns RoutesResponse with list of routes
         - Uses GetRoutes interactor
      5. Add sorting and filtering support
      
      Restrictions:
      - Use POST for complex request
      - Include route options in request
      - Return sorted routes
      - Document response structure
      
      Success:
      - Endpoint accepts complex request body
      - Returns multiple routes
      - Sorting/filtering works
      - OpenAPI docs complete
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 17. Create chains and tokens endpoints
  - File: `src/app/presentation/http/controllers/cross_chain/chains.py`
  - Implement chain and token listing endpoints
  - Purpose: Expose chain/token data via HTTP
  - _Leverage: `src/app/presentation/http/controllers/` existing patterns_
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in FastAPI endpoints
      
      Task: Create chains and tokens endpoints following requirements 4.1-4.5:
      1. Create `src/app/presentation/http/controllers/cross_chain/chains.py`
      2. Define response models: `ChainsResponse`, `TokensResponse`, `TokenBalanceResponse`
      3. Implement endpoints:
         - `GET /chains` - List all supported chains
         - `GET /tokens/{chain_id}` - List tokens for chain
         - `GET /balance` - Get token balance (query params: address, chain_id, token_address)
      4. Use query interactors via Dishka
      
      Restrictions:
      - Cache-friendly endpoints (can be cached by CDN)
      - Proper path parameters
      - Include chain metadata in response
      - Handle unknown chains gracefully
      
      Success:
      - All endpoints return proper data
      - Responses include full metadata
      - Unknown chains return 404
      - Performance suitable for caching
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 18. Create status endpoint
  - File: `src/app/presentation/http/controllers/cross_chain/status.py`
  - Implement transaction status endpoint
  - Purpose: Expose status tracking via HTTP
  - _Leverage: `src/app/presentation/http/controllers/` existing patterns_
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in FastAPI endpoints
      
      Task: Create status endpoint following requirements 6.1-6.5:
      1. Create `src/app/presentation/http/controllers/cross_chain/status.py`
      2. Define `StatusResponse` Pydantic model
      3. Implement `GET /status` endpoint:
         - Query params: tx_hash, from_chain, to_chain
         - Returns StatusResponse
         - Uses GetStatus interactor
      4. Include all status fields (substatus, error, etc.)
      5. Support polling (no caching headers)
      
      Restrictions:
      - No caching (status changes)
      - Include all status details
      - Handle unknown transactions
      - Support frequent polling
      
      Success:
      - Endpoint returns current status
      - All status fields included
      - Polling-friendly (no cache)
      - Unknown transactions handled
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 6: Dependency Injection & Configuration

- [ ] 19. Create LI.FI DI provider
  - File: `src/app/setup/ioc/lifi.py`
  - Register LI.FI components in Dishka
  - Purpose: Enable dependency injection for LI.FI components
  - _Leverage: `src/app/setup/ioc/` existing patterns_
  - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in dependency injection
      
      Task: Create LI.FI DI provider following requirements 1.1-1.4:
      1. Create `src/app/setup/ioc/lifi.py`
      2. Implement `LiFiProvider(Provider)` with:
         - `get_lifi_client(settings) -> LiFiClient` (APP scope)
         - `get_lifi_cache(cache) -> LiFiCache` (APP scope)
         - `get_cross_chain_gateway(client, cache, settings) -> CrossChainGateway` (APP scope)
      3. Read configuration from settings
      4. Handle disabled state (settings.lifi.enabled = false)
      
      Restrictions:
      - Use proper Dishka scopes
      - Read config from settings object
      - Handle disabled feature gracefully
      - Follow existing provider patterns
      
      _Leverage: `src/app/setup/ioc/` patterns
      
      Success:
      - Provider registers all LI.FI components
      - Gateway injectable throughout app
      - Configuration read from settings
      - Disabled state returns None or raises
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 20. Add LI.FI configuration settings
  - Files: `src/app/setup/config/lifi.py`, `config/local/config.toml`
  - Define configuration schema and defaults
  - Purpose: Configure LI.FI integration
  - _Leverage: `src/app/setup/config/` existing patterns_
  - _Requirements: 1.1, 8.1, 8.2_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in configuration management
      
      Task: Add LI.FI configuration settings:
      1. Create `src/app/setup/config/lifi.py`:
         - `LiFiSettings` Pydantic settings class
         - Fields: enabled, base_url, integrator, timeout, cache_chains_ttl, cache_tokens_ttl
         - Retry settings: max_attempts, backoff_base, backoff_max
      2. Update `config/local/config.toml` with [lifi] section
      3. Add to main settings aggregation
      
      Restrictions:
      - Use Pydantic settings
      - Provide sensible defaults
      - Follow existing config patterns
      - Include all tunable parameters
      
      _Leverage: `src/app/setup/config/` patterns
      
      Success:
      - Settings class defined
      - TOML config section added
      - Settings injectable via DI
      - All parameters configurable
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 21. Register router and finalize integration
  - Files: `src/app/presentation/http/controllers/api_v1_router.py`, `src/app/setup/ioc/provider_registry.py`
  - Register cross-chain router and provider
  - Purpose: Complete integration into application
  - _Leverage: Existing router and provider registration_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer
      
      Task: Register router and finalize integration:
      1. Update `src/app/presentation/http/controllers/api_v1_router.py`:
         - Import cross_chain router
         - Include with prefix `/api/v1/cross-chain`
      2. Update `src/app/setup/ioc/provider_registry.py`:
         - Import LiFiProvider
         - Add to provider list
      3. Verify all components connected
      4. Test endpoint accessibility
      
      Restrictions:
      - Follow existing registration patterns
      - Ensure proper import order
      - Verify no circular imports
      - Test with real request
      
      Success:
      - `/api/v1/cross-chain/chains` returns data
      - All endpoints accessible
      - DI working correctly
      - No import errors
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 7: Testing & Documentation

- [ ] 22. Create unit tests for LI.FI components
  - Files: `tests/unit/infrastructure/lifi/test_client.py`, `test_adapter.py`, `test_cache.py`
  - Test client, adapter, and cache in isolation
  - Purpose: Ensure component reliability
  - _Leverage: `tests/unit/` existing patterns, mock fixtures_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: QA Engineer specializing in Python unit testing
      
      Task: Create unit tests for LI.FI components:
      1. Create `tests/unit/infrastructure/lifi/test_client.py`:
         - Test request formatting
         - Test retry logic
         - Test timeout handling
         - Mock HTTP responses
      2. Create `tests/unit/infrastructure/lifi/test_adapter.py`:
         - Test transformation methods
         - Test caching integration
         - Test error handling
         - Mock client responses
      3. Create `tests/unit/infrastructure/lifi/test_cache.py`:
         - Test cache get/set
         - Test TTL behavior
         - Test invalidation
      
      Restrictions:
      - No real API calls
      - Mock all external dependencies
      - Test edge cases
      - Follow existing test patterns
      
      Success:
      - 90%+ code coverage for LI.FI components
      - All transformation logic tested
      - Error scenarios covered
      - Tests run quickly
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 23. Create integration tests for cross-chain endpoints
  - File: `tests/integration/cross_chain/test_endpoints.py`
  - Test full request flow with mocked LI.FI API
  - Purpose: Verify end-to-end functionality
  - _Leverage: `tests/integration/` existing patterns_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: QA Engineer specializing in integration testing
      
      Task: Create integration tests for cross-chain endpoints:
      1. Create `tests/integration/cross_chain/test_endpoints.py`
      2. Test all endpoints:
         - GET /api/v1/cross-chain/quote
         - POST /api/v1/cross-chain/routes
         - GET /api/v1/cross-chain/chains
         - GET /api/v1/cross-chain/tokens/{chain_id}
         - GET /api/v1/cross-chain/status
      3. Mock LI.FI API responses
      4. Test error scenarios (400, 404, 429, 502)
      5. Verify response structure
      
      Restrictions:
      - Use TestClient
      - Mock external API only
      - Test full request flow
      - Verify response schemas
      
      Success:
      - All endpoints tested
      - Error responses verified
      - Response schemas validated
      - Tests use realistic mock data
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 24. Create API documentation
  - File: `docs/api/CROSS_CHAIN_API.md`
  - Document all cross-chain endpoints
  - Purpose: Enable frontend integration
  - _Leverage: `docs/` existing documentation_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec lifi-sdk-integration, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Technical Writer
      
      Task: Create API documentation:
      1. Create `docs/api/CROSS_CHAIN_API.md`
      2. Document all endpoints:
         - GET /quote - Request/response examples
         - POST /routes - Request/response examples
         - GET /chains - Response structure
         - GET /tokens/{chain_id} - Response structure
         - GET /status - Polling guidance
      3. Include error codes and meanings
      4. Add usage examples with curl/JavaScript
      5. Document rate limits and caching behavior
      
      Restrictions:
      - Use real response examples
      - Include all parameters
      - Document error scenarios
      - Follow existing doc style
      
      Success:
      - All endpoints documented
      - Examples are runnable
      - Error codes explained
      - Frontend team can integrate
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._
