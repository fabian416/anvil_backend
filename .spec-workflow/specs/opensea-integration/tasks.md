# Tasks Document: OpenSea Integration

## Overview
Implementation tasks for completing the OpenSea NFT marketplace integration following hexagonal architecture patterns.

---

## Task 1: Domain Layer - Port and Models

- [x] 1.1 Create NFTMarketplaceGateway port interface
  - File: `src/app/domain/ports/nft_marketplace_gateway.py`
  - Define Protocol interface for NFT operations
  - Purpose: Domain contract for NFT marketplace operations
  - _Leverage: `src/app/domain/ports/` patterns_
  - _Requirements: R1, R2, R3, R4, R5_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer | Task: Create NFTMarketplaceGateway Protocol in src/app/domain/ports/nft_marketplace_gateway.py with methods: get_nfts_by_owner, get_collection, get_collection_stats, get_nft, get_listings, get_floor_price. Use typing.Protocol with full type hints. | Restrictions: Interface only. | _Leverage: src/app/domain/ports/ patterns | _Requirements: Requirements 1-5 | Success: Protocol compiles. Log implementation and mark complete._

- [x] 1.2 Create NFTAsset entity
  - File: `src/app/domain/entities/nft/nft_asset.py`
  - Define NFTAsset dataclass
  - Purpose: Domain model for NFT assets
  - _Leverage: `src/app/domain/entities/` patterns_
  - _Requirements: R1, R4_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create NFTAsset entity in src/app/domain/entities/nft/nft_asset.py with fields: identifier, collection_slug, contract_address, name, description, image_url, animation_url, traits (list[NFTTrait]), rarity_rank, last_sale_price, last_sale_currency. Use @dataclass. | Restrictions: Follow entity patterns. | _Leverage: src/app/domain/entities/ patterns | _Requirements: Requirements 1, 4 | Success: Entity typed. Log implementation and mark complete._

- [x] 1.3 Create NFTCollection entity
  - File: `src/app/domain/entities/nft/nft_collection.py`
  - Define NFTCollection dataclass
  - Purpose: Domain model for NFT collections
  - _Leverage: `src/app/domain/entities/nft/nft_asset.py`_
  - _Requirements: R2_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create NFTCollection entity in src/app/domain/entities/nft/nft_collection.py with fields: slug, name, description, image_url, banner_image_url, total_supply, created_date, contracts (list of chain/address dicts). | Restrictions: Follow entity patterns. | _Leverage: src/app/domain/entities/nft/nft_asset.py | _Requirements: Requirement 2 | Success: Entity typed. Log implementation and mark complete._

- [x] 1.4 Create value objects (CollectionStats, NFTTrait, NFTListing)
  - File: `src/app/domain/value_objects/nft/collection_stats.py`
  - File: `src/app/domain/value_objects/nft/nft_traits.py`
  - File: `src/app/domain/value_objects/nft/nft_listing.py`
  - Define frozen dataclasses
  - Purpose: Domain value objects
  - _Leverage: `src/app/domain/value_objects/` patterns_
  - _Requirements: R3, R4, R5_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create VOs: CollectionStats frozen (slug, floor_price, floor_price_usd, total_volume, total_sales, num_owners, average_price, market_cap, one_day_volume, one_day_change, seven_day_volume, seven_day_change), NFTTrait frozen (trait_type, value, rarity_pct), NFTListing frozen (order_hash, token_id, collection_slug, price, price_usd, currency, seller, created_date, expiration_date). Use Decimal for prices. | Restrictions: Use @dataclass(frozen=True). | _Leverage: src/app/domain/value_objects/ patterns | _Requirements: Requirements 3-5 | Success: VOs immutable. Log implementation and mark complete._

---

## Task 2: Domain Layer - Exceptions

- [x] 2.1 Create NFT domain exceptions
  - File: `src/app/domain/exceptions/nft.py`
  - Define NFTError, CollectionNotFoundError, NFTNotFoundError, InvalidAddressError, OpenSeaAPIError
  - Purpose: Domain-specific error handling
  - _Leverage: `src/app/domain/exceptions/base.py`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create exceptions in src/app/domain/exceptions/nft.py: NFTError(DomainError), CollectionNotFoundError, NFTNotFoundError, InvalidAddressError, OpenSeaAPIError. Add error_code attributes. | Restrictions: Extend base exceptions. | _Leverage: src/app/domain/exceptions/base.py | _Requirements: Requirement 9 | Success: Exceptions inherit correctly. Log implementation and mark complete._

---

## Task 3: Infrastructure Layer - Adapter

- [x] 3.1 Create OpenSeaAdapter implementing NFTMarketplaceGateway
  - File: `src/app/infrastructure/adapters/external/opensea_adapter.py`
  - Implement NFTMarketplaceGateway using existing OpenSeaClient
  - Add caching (15min collection, 5min stats, 10min portfolio)
  - Transform client models to domain models
  - Purpose: Bridge domain port to infrastructure client
  - _Leverage: `src/app/infrastructure/adapters/external/opensea_client.py`, `src/app/infrastructure/cache/external_api_cache.py`_
  - _Requirements: R1, R2, R3, R4, R5, R9_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Backend Developer | Task: Create OpenSeaAdapter in src/app/infrastructure/adapters/external/opensea_adapter.py implementing NFTMarketplaceGateway. Inject OpenSeaClient and cache. Cache: 15min collection, 5min stats, 10min portfolio, 1min listings. Transform client NFTAsset/CollectionStats to domain models. | Restrictions: Do not modify client. | _Leverage: src/app/infrastructure/adapters/external/opensea_client.py | _Requirements: Requirements 1-5, 9 | Success: Adapter implements Protocol, caching works. Log implementation and mark complete._

---

## Task 4: Application Layer - Queries

- [x] 4.1 Create GetNFTPortfolio query
  - File: `src/app/application/queries/nft/get_nft_portfolio.py`
  - Define GetNFTPortfolioRequest dataclass
  - Implement GetNFTPortfolio with valuation
  - Purpose: Get NFT portfolio with floor price valuation
  - _Leverage: `src/app/application/queries/` patterns_
  - _Requirements: R1, R6_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetNFTPortfolio query in src/app/application/queries/nft/get_nft_portfolio.py. Define GetNFTPortfolioRequest(address, chain, include_valuation). Inject NFTMarketplaceGateway. Group NFTs by collection, calculate total_value_eth/usd using floor prices if include_valuation=True. Return NFTPortfolioResponse with nfts, by_collection breakdown, total counts and values. | Restrictions: Depend only on domain port. | _Leverage: src/app/application/queries/ patterns | _Requirements: Requirements 1, 6 | Success: Returns portfolio with valuation. Log implementation and mark complete._

- [x] 4.2 Create GetCollection query
  - File: `src/app/application/queries/nft/get_collection.py`
  - Define GetCollectionRequest dataclass
  - Implement GetCollection
  - Purpose: Get collection information
  - _Leverage: `src/app/application/queries/nft/get_nft_portfolio.py`_
  - _Requirements: R2_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetCollection query in src/app/application/queries/nft/get_collection.py. Define GetCollectionRequest(collection_slug). Inject NFTMarketplaceGateway. Return NFTCollection entity. Raise CollectionNotFoundError if not found. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/nft/get_nft_portfolio.py | _Requirements: Requirement 2 | Success: Returns collection. Log implementation and mark complete._

- [x] 4.3 Create GetCollectionStats query
  - File: `src/app/application/queries/nft/get_collection_stats.py`
  - Define GetCollectionStatsRequest dataclass
  - Implement GetCollectionStats with sentiment analysis
  - Purpose: Get collection market statistics
  - _Leverage: `src/app/application/queries/nft/get_collection.py`_
  - _Requirements: R3_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetCollectionStats query in src/app/application/queries/nft/get_collection_stats.py. Define GetCollectionStatsRequest(collection_slug). Return CollectionStatsResponse with stats, market_sentiment (BULLISH if 1d_change > 10, BEARISH if < -10, else NEUTRAL), floor_change_alert (SIGNIFICANT_DROP if < -20%, SIGNIFICANT_RISE if > 30%). | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/nft/get_collection.py | _Requirements: Requirement 3 | Success: Returns stats with analysis. Log implementation and mark complete._

- [x] 4.4 Create GetNFTDetails query
  - File: `src/app/application/queries/nft/get_nft_details.py`
  - Define GetNFTDetailsRequest dataclass
  - Implement GetNFTDetails
  - Purpose: Get single NFT details
  - _Leverage: `src/app/application/queries/nft/get_collection.py`_
  - _Requirements: R4_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetNFTDetails query in src/app/application/queries/nft/get_nft_details.py. Define GetNFTDetailsRequest(contract_address, token_id, chain). Inject NFTMarketplaceGateway. Return NFTAsset with traits. Raise NFTNotFoundError if not found. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/nft/get_collection.py | _Requirements: Requirement 4 | Success: Returns NFT details. Log implementation and mark complete._

- [x] 4.5 Create GetListings query
  - File: `src/app/application/queries/nft/get_listings.py`
  - Define GetListingsRequest dataclass
  - Implement GetListings
  - Purpose: Get active listings for collection
  - _Leverage: `src/app/application/queries/nft/get_collection.py`_
  - _Requirements: R5_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create GetListings query in src/app/application/queries/nft/get_listings.py. Define GetListingsRequest(collection_slug, limit). Return list of NFTListing sorted by price ascending. | Restrictions: Follow query patterns. | _Leverage: src/app/application/queries/nft/get_collection.py | _Requirements: Requirement 5 | Success: Returns listings. Log implementation and mark complete._

---

## Task 5: Presentation Layer - HTTP Router

- [x] 5.1 Create OpenSea HTTP router
  - File: `src/app/presentation/http/controllers/nft/opensea_router.py`
  - Define all endpoints from design
  - Purpose: HTTP API for NFT operations
  - _Leverage: `src/app/presentation/http/controllers/` patterns_
  - _Requirements: R1-R6_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: FastAPI Developer | Task: Create opensea_router.py in src/app/presentation/http/controllers/nft/. Endpoints: GET /portfolio/{address}, GET /collections/{slug}, GET /collections/{slug}/stats, GET /assets/{contract}/{token_id}, GET /collections/{slug}/listings, GET /collections/{slug}/floor. Use FromDishka for DI. | Restrictions: Follow router patterns. | _Leverage: src/app/presentation/http/controllers/ patterns | _Requirements: Requirements 1-6 | Success: All endpoints work. Log implementation and mark complete._

- [x] 5.2 Create response schemas
  - File: `src/app/presentation/http/controllers/nft/opensea_schemas.py`
  - Define Pydantic models
  - Purpose: API response serialization
  - _Leverage: Existing schema patterns_
  - _Requirements: R1-R6_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create opensea_schemas.py with: NFTPortfolioResponse (with total_value, by_collection breakdown), CollectionResponse, CollectionStatsResponse (with market_sentiment, floor_change_alert), NFTDetailsResponse, ListingsResponse, FloorPriceResponse. Add from_domain() methods. | Restrictions: Use Pydantic v2. | _Leverage: Existing schema patterns | _Requirements: Requirements 1-6 | Success: Schemas serialize. Log implementation and mark complete._

---

## Task 6: Dependency Injection

- [x] 6.1 Create OpenSea DI provider
  - File: `src/app/setup/ioc/opensea.py`
  - Register OpenSeaClient, OpenSeaAdapter, NFTMarketplaceGateway
  - Purpose: Enable DI
  - _Leverage: `src/app/setup/ioc/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Create OpenSeaProvider in src/app/setup/ioc/opensea.py. Register OpenSeaClient and OpenSeaAdapter as NFTMarketplaceGateway (APP scope). Inject cache and settings (for API key). | Restrictions: Follow provider patterns. | _Leverage: src/app/setup/ioc/ patterns | _Requirements: All | Success: DI resolves. Log implementation and mark complete._

- [x] 6.2 Register router in app factory
  - File: `src/app/setup/app_factory.py` (modify)
  - Include opensea_router under /api/v1/nft
  - Purpose: Enable endpoints
  - _Leverage: `src/app/setup/app_factory.py`_
  - _Requirements: All_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer | Task: Modify app_factory.py to import and include opensea_router under /api/v1/nft prefix (new prefix for NFT endpoints). Add OpenSeaProvider. | Restrictions: Minimal changes. | _Leverage: Existing pattern | _Requirements: All | Success: Endpoints accessible. Log implementation and mark complete._

---

## Task 7: Configuration

- [x] 7.1 Add OpenSea configuration
  - File: `config/local/config.toml` (modify)
  - Add [opensea] section
  - Purpose: Configurable parameters
  - _Leverage: `config/local/config.toml`_
  - _Requirements: R9_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps | Task: Add [opensea] section to config.toml with: enabled=true, api_key="", cache_collection_ttl=900, cache_stats_ttl=300, cache_portfolio_ttl=600, cache_listings_ttl=60. Add [opensea.chains] mapping. | Restrictions: Follow config patterns. | _Leverage: config/local/config.toml | _Requirements: Requirement 9 | Success: Config loads. Log implementation and mark complete._

---

## Task 8: Testing

- [x] 8.1 Create adapter unit tests
  - File: `tests/unit/infrastructure/adapters/test_opensea_adapter.py`
  - Test transformation and caching
  - Purpose: Ensure adapter reliability
  - _Leverage: `tests/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_opensea_adapter.py. Mock OpenSeaClient. Test: get_nfts_by_owner transforms correctly, caching varies (15min collection, 5min stats), mock responses work when no API key. | Restrictions: Unit tests only. | _Leverage: Existing test patterns | _Requirements: All | Success: Tests pass. Log implementation and mark complete._

- [x] 8.2 Create integration tests
  - File: `tests/integration/nft/test_opensea_integration.py`
  - Test full flow
  - Purpose: End-to-end functionality
  - _Leverage: `tests/integration/` patterns_
  - _Requirements: All_
  - _Prompt: Implement the task for spec opensea-integration, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Test Engineer | Task: Create test_opensea_integration.py. Test: GET /portfolio/{address} returns NFTs, GET /collections/{slug}/stats returns analysis, 404 for unknown collection. Mock external API. | Restrictions: Mock external deps. | _Leverage: Existing integration patterns | _Requirements: All | Success: Integration tests pass. Log implementation and mark complete._

---

## Summary

| Phase | Tasks | Files Created |
|-------|-------|---------------|
| Domain | 1.1-1.4, 2.1 | 7 files |
| Infrastructure | 3.1 | 1 file |
| Application | 4.1-4.5 | 5 files |
| Presentation | 5.1-5.2 | 2 files |
| DI & Config | 6.1-6.2, 7.1 | 2 files + mods |
| Testing | 8.1-8.2 | 2 files |
| **Total** | **14 tasks** | **~19 files** |
