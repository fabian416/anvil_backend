# Discovery Module — Document 4: Services Layer (Domain + Application + Infrastructure)

## Overview
This document covers the three inner layers of the hexagonal architecture: Domain (entities + ports), Application (queries + commands), and Infrastructure (adapters + persistence).

---

## PART A: Domain Layer (Pure — No Dependencies)

### A.1 Entities

**DiscoveryCategory** (`domain/entities/discovery/category.py`)
- Frozen dataclass (immutable)
- Fields: id (UUID), slug, name, description, icon, sort_order, is_active, is_default, config (JSONB)
- Property: `has_user_preferences` → True only for "news" category (vaults don't have user toggles)

**DiscoverySection** (`domain/entities/discovery/section.py`)
- Frozen dataclass (immutable, hierarchical)
- Fields: id (UUID), category_id, parent_id (nullable), slug, name, icon, sort_order, is_active, is_default, metadata (JSONB)
- Property: `is_top_level` → parent_id is None
- Property: `keywords` → metadata.get("keywords", []) — drives Celery collection

**NewsArticle** (`domain/entities/discovery/news_article.py`)
- Mutable dataclass (view_count changes)
- Fields: id, title, summary, image_url, source_name, source_url, author, citations[], section_id, section_slug, parent_section_slug, tags[], sentiment, relevance_score, view_count, content_hash, published_at
- Static method: `compute_hash(title, source_url)` → SHA-256 for dedup
- Property: `time_ago` → human-readable delta ("5m ago", "2h ago")

**VaultSnapshot** (`domain/entities/discovery/vault_snapshot.py`)
- Frozen dataclass (immutable point-in-time)
- Fields: id, protocol, protocol_display, vault_name, chain, chain_name, asset_symbol, supply_apy, reward_apy, tvl_usd, risk_level, is_curated, vault_address, metadata
- Property: `total_apy` → supply_apy + reward_apy
- Property: `cta` → "Deposit {asset} to earn {apy}% APY"
- Property: `intent_trigger` → "lending_deposit" (bridges to Anvil agent squad)

### A.2 Ports (Interfaces — All ABCs)

**NewsFetcherPort** (`domain/ports/discovery/news_fetcher_port.py`)
```python
class NewsFetcherPort(ABC):
    async def fetch_news(keywords: list[str], section_slug: str, max_results: int = 20) -> list[RawArticle]
    async def search_news(query: str, max_results: int = 20) -> list[RawArticle]
    provider_slug: str  # property
    is_available: bool  # property
```
- Implemented by: PerplexitySonarAdapter, NewsAPIAdapter, CryptoPanicAdapter, RSSAdapter
- `RawArticle` dataclass: adapter-agnostic article DTO (title, source_name, source_url, published_at, summary, image_url, author, citations, tags, sentiment, relevance_score)

**VaultFetcherPort** (`domain/ports/discovery/vault_fetcher_port.py`)
```python
class VaultFetcherPort(ABC):
    async def fetch_vaults(protocols: list[str], chains: list[str], min_tvl: float) -> list[RawVault]
```
- Implemented by: DeFiLlamaAdapter, VaultsFyiAdapter
- `RawVault` dataclass: protocol, vault_name, chain, asset_symbol, supply_apy, reward_apy, tvl_usd, vault_address, risk_level, is_curated

**NewsRepositoryPort** (`domain/ports/discovery/news_repository.py`)
```python
class NewsRepositoryPort(ABC):
    async def upsert_article(article: NewsArticle, provider_id: UUID) -> bool  # True if new
    async def get_feed(section_ids: list[UUID], limit, offset, exclude_ids) -> list[NewsArticle]
    async def search(query: str, section_ids, limit, offset) -> tuple[list[NewsArticle], int]
    async def get_adjacent_articles(exclude_section_ids, parent_section_slugs, limit) -> list[NewsArticle]
    async def get_trending(limit: int = 10) -> list[NewsArticle]
```

**SectionRepositoryPort** (`domain/ports/discovery/section_repository.py`)
```python
class SectionRepositoryPort(ABC):
    async def get_active_top_level(category_slug: str) -> list[DiscoverySection]
    async def get_active_subsections(category_slug: str) -> list[DiscoverySection]
    async def get_by_slug(slug: str) -> DiscoverySection | None
    async def get_children(parent_id: UUID) -> list[DiscoverySection]
    async def get_parent_slugs(section_ids: list[UUID]) -> list[str]
    async def get_slug_name_map() -> dict[str, str]
    async def get_active_leaf_sections() -> list[DiscoverySection]  # For Celery fan-out
```

**InterestRepositoryPort** (`domain/ports/discovery/interest_repository.py`)
```python
class InterestRepositoryPort(ABC):
    async def get_user_interests(user_id: UUID) -> list[UserInterest]
    async def get_enabled_section_ids(user_id: UUID) -> list[UUID]
    async def upsert_interests(user_id: UUID, interests: list[dict]) -> int
```

**CategoryRepositoryPort** + **VaultRepositoryPort** — standard CRUD patterns.

---

## PART B: Application Layer (Orchestration)

### B.1 Queries

**GetDiscoveryCategoriesQuery** (`application/queries/discovery/get_categories.py`)
- Input: None (or category_slug filter)
- Output: list of active categories with section counts
- Cache: `discovery:categories` TTL 300s
- Logic: category_repo.get_active() → map to DTOs

**GetUserInterestsQuery** (`application/queries/discovery/get_interests.py`)
- Input: user_id, category_slug="news"
- Output: `InterestsResponseDTO` — full section tree with per-user enabled/disabled state
- Logic:
  1. Get all ACTIVE top-level + subsections (admin-controlled visibility)
  2. Get user's explicit preferences from discovery_user_interests
  3. Build tree: if explicit preference exists → use it; if not → use section.is_default
- Cache: `discovery:interests:{user_id}` TTL 120s

**GetNewsFeedQuery** (`application/queries/discovery/get_news_feed.py`)
- Input: user_id (optional), page, page_size, section_filter (optional)
- Output: `NewsFeedResponseDTO` — articles + pagination + feed_type
- **Three-tier feed algorithm:**
  1. **Personalized** — articles from user's enabled sections
  2. **Adjacent** — sibling sections under same parent (fill remaining slots)
  3. **Trending** — highest relevance_score across all sections (final fill)
- If section_filter provided: narrow to that section's children
- feed_type in response: "personalized" | "adjacent" | "trending"
- Cache: `discovery:feed:{user_id}:{page}:{section}` TTL 60s

**SearchNewsQuery** (`application/queries/discovery/search_news.py`)
- Input: query, user_id, page, page_size, section_filter
- Output: `NewsFeedResponseDTO` (feed_type="search")
- **Hybrid parallel search:**
  1. PostgreSQL FTS (fast, cached articles) — `asyncio.gather` task 1
  2. Perplexity Sonar real-time search — `asyncio.gather` task 2
  3. Merge: DB results first (fast), then Sonar results (fresh)
  4. Dedup by content_hash
- Cache: `discovery:search:{query_hash}` TTL 30s

**GetVaultsQuery** (`application/queries/discovery/get_vaults.py`)
- Input: sort (apy_desc|tvl_desc|risk_asc), chain filter, asset filter
- Output: `VaultsResponse` — sorted vault cards with CTA + intent_trigger
- Cache: `discovery:vaults:{sort}:{chain}` TTL 60s

### B.2 Commands

**SaveUserInterestsCommand** (`application/commands/discovery/save_interests.py`)
- Input: user_id, list of {section_id, is_enabled}
- Output: count of saved preferences
- Logic: UPSERT into discovery_user_interests (ON CONFLICT DO UPDATE)
- Side effect: Invalidate `discovery:interests:{user_id}` + `discovery:feed:{user_id}:*` caches

**CollectNewsCommand** (`application/commands/discovery/collect_news.py`)
- Triggered by Celery worker, not HTTP endpoint
- Input: section_id, section_slug, parent_slug, keywords
- Logic: Provider failover chain → dedup → UPSERT → chain GraphRAG extraction

**CollectVaultsCommand** (`application/commands/discovery/collect_vaults.py`)
- Triggered by Celery worker
- Logic: DeFiLlama fetch → deactivate old snapshots → insert new → invalidate cache

**AdminManageCategoryCommand / AdminManageSectionCommand** (`application/commands/discovery/admin_manage.py`)
- CRUD operations with cache invalidation
- Requires admin role validation

---

## PART C: Infrastructure Layer (Implementations)

### C.1 News Fetcher Adapters

**PerplexitySonarAdapter** (PRIMARY — priority 100)
- Endpoint: `POST https://api.perplexity.ai/chat/completions`
- Model: `sonar` with `search_context_size: "low"` for collection, `"medium"` for user search
- System prompt enforces structured JSON output (articles array)
- Parses citations and search_results from Sonar response
- Circuit breaker: disables after 10 consecutive errors
- Handles 429 (rate limit) → triggers fallback
- Handles 402 (no credits) → disables permanently + admin alert
- Token usage logging for cost tracking
- `relevance_score = 0.8` (high quality)

**NewsAPIAdapter** (FALLBACK — priority 50)
- Endpoint: `GET https://newsapi.org/v2/everything`
- Keyword query with OR operators
- `relevance_score = 0.6` (lower than Sonar)

**CryptoPanicAdapter** (FALLBACK — priority 50, crypto only)
- Endpoint: `GET https://cryptopanic.com/api/v1/posts/`
- Supports currency filtering (BTC, ETH, etc.)
- Sentiment mapping from community votes
- `relevance_score = 0.7`

**RSSAdapter** (LAST RESORT — priority 20)
- Parses XML feeds (CoinDesk, Reuters)
- Always available, no API key needed

### C.2 Vault Fetcher Adapters

**DeFiLlamaAdapter**
- Endpoint: `GET https://yields.llama.fi/pools`
- Filters: protocol ∈ {morpho, aave-v3, compound-v3}, chain ∈ {Base, Ethereum}
- Risk classification: APY > 100% or TVL < $500K → high
- Returns top 50 vaults sorted by total APY

**VaultsFyiAdapter**
- Endpoint: `GET https://api.vaults.fyi/v2/vaults`
- Broader protocol coverage (75+ protocols)

### C.3 GraphRAG Adapters

**GraphRAGExtractor** (`infrastructure/adapters/discovery/graphrag_extractor.py`)
- Uses Gemini 2.0 Flash for entity/relationship extraction
- System prompt defines DeFi ontology (entity types + relationship types)
- Output: `ArticleGraphExtraction` (entities, relationships, events, sentiment)
- Batch processing: 5 articles per batch with asyncio.gather

**HybridRetriever** (`infrastructure/adapters/discovery/hybrid_retriever.py`)
- Weight: 40% vector (pgvector similarity) + 60% graph (Apache AGE traversal)
- Parallel: vector search + entity context + risk propagation + recent events
- Entity name extraction: fast dictionary lookup (known DeFi entities)
- Output: `HybridRetrievalResult` (vector_results, graph_context, risk_analysis, recent_events, sentiment)

### C.4 Persistence (SQLAlchemy)

All repositories use async SQLAlchemy with connection pooling.
- `CategorySQLARepository` — simple reads with Redis cache
- `SectionSQLARepository` — hierarchical queries (parent/child), leaf section enumeration
- `InterestSQLARepository` — user-specific UPSERT with ON CONFLICT
- `NewsSQLARepository` — UPSERT with content_hash dedup, FTS via to_tsvector, adjacent/trending queries
- `VaultSQLARepository` — deactivate old + insert new pattern, sorted queries

### C.5 Graph Repository

**DiscoveryGraphRepository** (`infrastructure/persistence/discovery/graph_repository.py`)
- Uses Apache AGE Cypher queries via SQL
- `upsert_extraction()` — MERGE entities + relationships + mentioned_in edges
- `query_entity_context(name, depth)` — N-hop graph traversal
- `query_risk_propagation(name)` — follows depends_on/uses_oracle/accepts_collateral chains
- `query_recent_events(entity, severity)` — event nodes filtered

### C.6 Discovery Intelligence Agent

**DiscoveryIntelligenceAgent** (`infrastructure/adapters/agent_squad/agents/discovery_intelligence_agent.py`)
- Model: Gemini 2.0 Flash (fast, cheap)
- Uses HybridRetriever for all queries
- **User-facing API**: `execute(conversation_id, message)` — handles "what happened with Aave?" type queries
- **Inter-agent API**: `get_context_for_agent(entity_names, context_type)` — called by PortfolioAgent, RiskAnalyzer, HunterAI
- **Portfolio API**: `get_portfolio_news_context(user_tokens, user_protocols)` — filtered to user's holdings
- System prompt emphasizes: lead with impact, explain entity connections, cite sources, flag user positions
