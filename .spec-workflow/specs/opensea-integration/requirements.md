# Requirements Document: OpenSea Integration

## Introduction

This specification defines the requirements for completing the **OpenSea integration** into the Anvil Backend DeFi Multi-Agents Chat platform. OpenSea is the largest NFT marketplace, providing comprehensive NFT data, pricing, and market analytics across multiple blockchains.

The existing `OpenSeaClient` infrastructure adapter provides basic API connectivity. This spec focuses on:
- **Full domain layer integration** (ports, entities, value objects)
- **Application layer interactors** for NFT portfolio tracking
- **HTTP API endpoints** for frontend consumption
- **Portfolio Agent integration** for NFT holdings visibility

### Why OpenSea Matters

OpenSea provides essential NFT infrastructure:
- **85%+ Market Share**: Dominant NFT marketplace
- **Multi-Chain Support**: Ethereum, Polygon, Arbitrum, Optimism, Base
- **Comprehensive Data**: Collections, floor prices, traits, rarity
- **API Access**: Programmatic access to NFT metadata

### Expanding to NFT Vertical

This integration expands the platform's scope beyond fungible DeFi tokens to include:
- NFT portfolio valuation
- Floor price tracking
- Collection analytics
- NFT-as-collateral awareness

## Alignment with Product Vision

### Key Features Alignment

| Product Feature | OpenSea Integration |
|-----------------|---------------------|
| **Portfolio Tracking** | NFT holdings and valuations |
| **Market Analysis** | Floor prices, volume trends |
| **Collection Insights** | Rarity, traits, statistics |
| **Multi-Chain NFTs** | Support NFTs on all chains |

### Business Objectives Alignment

- **Portfolio Completeness**: Full picture including NFTs
- **NFT Traders**: Serve growing NFT user segment
- **Collateral Awareness**: NFT-backed lending context

---

## Requirements

### Requirement 1: NFT Portfolio Retrieval

**User Story:** As a user, I want to see all NFTs in my wallet, so that I can manage my complete portfolio.

#### Acceptance Criteria

1. WHEN user provides wallet address THEN the system SHALL return owned NFTs
2. WHEN NFT data is returned THEN it SHALL include: collection, token ID, image, traits
3. IF chain is specified THEN the system SHALL filter by that chain
4. WHEN displaying NFTs THEN the system SHALL group by collection
5. IF user owns many NFTs (>100) THEN the system SHALL paginate results
6. WHEN images are returned THEN the system SHALL provide optimized URLs

---

### Requirement 2: Collection Information

**User Story:** As a user, I want to see collection details, so that I can understand my NFT holdings.

#### Acceptance Criteria

1. WHEN user queries collection THEN the system SHALL return collection metadata
2. WHEN collection data is returned THEN it SHALL include: name, description, image, supply
3. IF collection has verified status THEN the system SHALL indicate verification
4. WHEN displaying contracts THEN the system SHALL show all chain deployments
5. IF collection is flagged THEN the system SHALL show warning
6. WHEN created date exists THEN the system SHALL show collection age

---

### Requirement 3: Floor Price & Statistics

**User Story:** As a user, I want to see collection floor prices and statistics, so that I can value my holdings.

#### Acceptance Criteria

1. WHEN user queries collection stats THEN the system SHALL return market data
2. WHEN stats are returned THEN they SHALL include: floor price, total volume, num owners
3. IF price history exists THEN the system SHALL show 24h and 7d changes
4. WHEN calculating portfolio value THEN the system SHALL use floor prices
5. IF floor price drops significantly THEN the system SHALL flag for attention
6. WHEN comparing collections THEN the system SHALL rank by market cap

---

### Requirement 4: NFT Details & Traits

**User Story:** As a user, I want to see detailed NFT information including traits and rarity, so that I can understand my asset's value.

#### Acceptance Criteria

1. WHEN user queries specific NFT THEN the system SHALL return full details
2. WHEN NFT data is returned THEN it SHALL include: metadata, image, traits, rarity
3. IF trait rarity data exists THEN the system SHALL show rarity percentages
4. WHEN displaying rarity THEN the system SHALL show overall rarity rank
5. IF NFT has animation/video THEN the system SHALL include animation URL
6. WHEN last sale exists THEN the system SHALL show sale price and date

---

### Requirement 5: Active Listings

**User Story:** As a user, I want to see active listings for a collection, so that I can find buying opportunities.

#### Acceptance Criteria

1. WHEN user queries listings THEN the system SHALL return active listings
2. WHEN listings are returned THEN they SHALL be sorted by price (low to high)
3. IF specific traits requested THEN the system SHALL filter by traits
4. WHEN displaying listings THEN the system SHALL show price in ETH and USD
5. IF listing is expiring soon THEN the system SHALL indicate urgency
6. WHEN showing maker THEN the system SHALL show seller address

---

### Requirement 6: Portfolio Valuation

**User Story:** As a user, I want my NFT portfolio valued in USD, so that I can understand my total net worth.

#### Acceptance Criteria

1. WHEN user requests portfolio value THEN the system SHALL calculate total
2. WHEN calculating value THEN the system SHALL use floor prices by default
3. IF trait-based pricing exists THEN the system SHALL optionally use rarity-adjusted
4. WHEN displaying total THEN the system SHALL show breakdown by collection
5. IF some NFTs can't be valued THEN the system SHALL indicate and exclude
6. WHEN showing changes THEN the system SHALL calculate 24h/7d portfolio change

---

### Requirement 7: Agent Integration

**User Story:** As a user chatting with Portfolio Agent, I want my NFTs included in portfolio analysis, so that I get complete advice.

#### Acceptance Criteria

1. WHEN user asks about portfolio THEN agent SHALL include NFT holdings
2. IF NFT portfolio is significant (>10% of total) THEN agent SHALL mention
3. WHEN user asks about specific collection THEN agent SHALL provide stats
4. IF floor price drops THEN agent SHALL proactively alert user
5. WHEN discussing diversification THEN agent SHALL consider NFT allocation
6. IF user asks "what do I own" THEN agent SHALL list NFTs along with tokens

---

### Requirement 8: Multi-Chain Support

**User Story:** As a user, I want to see NFTs across all chains I use, so that I have complete visibility.

#### Acceptance Criteria

1. WHEN user queries NFTs THEN the system SHALL support multiple chains
2. WHEN aggregating cross-chain THEN the system SHALL convert values to USD
3. IF chain is not specified THEN the system SHALL query all supported chains
4. WHEN displaying results THEN the system SHALL indicate chain per NFT
5. IF same collection exists on multiple chains THEN the system SHALL differentiate

Supported chains: Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche

---

### Requirement 9: Caching & Performance

**User Story:** As a developer, I want OpenSea data appropriately cached, so that the system remains responsive.

#### Acceptance Criteria

1. WHEN collection data is requested THEN the system SHALL cache for 15 minutes
2. WHEN floor price is requested THEN the system SHALL cache for 5 minutes
3. IF NFT portfolio is requested THEN the system SHALL cache for 10 minutes
4. WHEN listing data is requested THEN the system SHALL cache for 1 minute
5. IF OpenSea API is slow (>3s) THEN the system SHALL return cached with warning

---

## Non-Functional Requirements

### Code Architecture and Modularity

- **Domain Port**: `NFTMarketplaceGateway` interface in domain layer
- **Infrastructure Adapter**: Enhanced `OpenSeaClient` implementing port
- **Application Interactors**: `GetNFTPortfolio`, `GetCollectionStats`, `GetNFTDetails`
- **HTTP Controllers**: REST endpoints under `/api/v1/nft/`

### Performance

- **Portfolio Query**: < 2s for up to 100 NFTs
- **Collection Stats**: < 500ms response time
- **Floor Price**: < 300ms response time
- **Concurrent Requests**: Support 30+ concurrent requests (API key dependent)

### Security

- **API Key Protection**: Never expose OpenSea API key to frontend
- **Address Validation**: Validate wallet addresses
- **Rate Limiting**: Per-user limits respecting OpenSea tiers
- **No Trading**: Read-only, no purchase operations

### Reliability

- **Graceful Degradation**: Return cached data on API failure
- **Circuit Breaker**: Prevent cascading failures
- **Retry Logic**: Automatic retry for transient failures
- **Fallback**: Consider alternative APIs (Alchemy, Reservoir)

### Usability

- **Clear Pricing**: Always show ETH and USD values
- **Image Optimization**: Provide appropriately sized images
- **Documentation**: OpenAPI spec for all endpoints

---

## Technical Context

### Existing Infrastructure

```
src/app/infrastructure/adapters/external/
├── opensea_client.py    # Basic OpenSea API v2 client ✅
```

### Required New Components

```
src/app/domain/
├── entities/
│   └── nft_asset.py             # NFT entity
├── value_objects/
│   ├── nft_collection.py        # Collection VO
│   └── nft_traits.py            # Traits VO
└── ports/
    └── nft_marketplace_gateway.py  # Port interface

src/app/application/
├── queries/
│   ├── get_nft_portfolio.py     # User's NFTs
│   ├── get_nft_collection.py    # Collection info
│   ├── get_collection_stats.py  # Market stats
│   ├── get_nft_details.py       # Single NFT
│   └── get_nft_listings.py      # Active listings

src/app/presentation/http/controllers/nft/
└── opensea_router.py            # HTTP endpoints
```

---

## Dependencies

- **Existing**: `OpenSeaClient` in infrastructure layer
- **OpenSea API v2**: `https://api.opensea.io/api/v2`
- **API Key**: Required for production use (rate limits)

---

## Out of Scope

- NFT purchasing/selling (requires wallet interaction)
- NFT minting
- Auction bidding
- OpenSea account management
- NFT-backed lending operations (separate integration)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Portfolio Query Latency | < 2s (p95) |
| Floor Price Freshness | < 5 min staleness |
| Collection Coverage | 95%+ of major collections |
| Image Load Success | 99%+ availability |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenSea API rate limits | High | Medium | Caching, request queuing |
| API key revocation | Low | High | Multiple keys, fallback APIs |
| Image CDN issues | Low | Low | Fallback URLs, caching |
| Collection flagging | Medium | Low | Show warnings, still display |
