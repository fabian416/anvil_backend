# Discovery Module — Document 1: Architecture Specification

## 1. Architecture Pattern: Hexagonal (Clean Architecture)

The Discovery module follows Anvil's hexagonal architecture with strict dependency inversion. External systems (Perplexity, NewsAPI, DeFiLlama) are isolated behind ports, making providers swappable without touching business logic.

### Layer Responsibilities

| Layer | Responsibility | Depends On |
|-------|---------------|------------|
| **Presentation** | HTTP controllers, request/response models, auth | Application |
| **Application** | Use cases (queries + commands), DTOs, orchestration | Domain |
| **Domain** | Entities, value objects, ports (interfaces) | Nothing (pure) |
| **Infrastructure** | Adapters (API clients, DB repos, cache) | Domain (implements ports) |

### Dependency Rule
Dependencies flow INWARD only: `Presentation → Application → Domain ← Infrastructure`

Infrastructure implements Domain ports. Application orchestrates. Presentation exposes.

## 2. File Structure

```
src/app/
├── domain/
│   ├── entities/discovery/
│   │   ├── category.py              # DiscoveryCategory (frozen dataclass)
│   │   ├── section.py               # DiscoverySection (hierarchical, frozen)
│   │   ├── user_interest.py         # UserInterest (user↔section toggle)
│   │   ├── news_article.py          # NewsArticle (mutable, has compute_hash)
│   │   ├── vault_snapshot.py        # VaultSnapshot (frozen, point-in-time)
│   │   └── news_provider.py         # NewsProvider (runtime state)
│   │
│   ├── ports/discovery/
│   │   ├── category_repository.py   # CategoryRepositoryPort (ABC)
│   │   ├── section_repository.py    # SectionRepositoryPort (ABC)
│   │   ├── interest_repository.py   # InterestRepositoryPort (ABC)
│   │   ├── news_repository.py       # NewsRepositoryPort (ABC)
│   │   ├── vault_repository.py      # VaultRepositoryPort (ABC)
│   │   ├── news_fetcher_port.py     # NewsFetcherPort (adapter interface)
│   │   └── vault_fetcher_port.py    # VaultFetcherPort (adapter interface)
│   │
│   └── services/graph/
│       └── news_ontology.py         # NewsEntityType + NewsRelationshipType enums
│
├── application/
│   ├── queries/discovery/
│   │   ├── get_categories.py        # GetDiscoveryCategoriesQuery
│   │   ├── get_interests.py         # GetUserInterestsQuery (section tree + user state)
│   │   ├── get_news_feed.py         # GetNewsFeedQuery (3-tier: personal→adjacent→trending)
│   │   ├── search_news.py           # SearchNewsQuery (hybrid: DB FTS + Sonar real-time)
│   │   └── get_vaults.py            # GetVaultsQuery (sorted vault snapshots)
│   │
│   └── commands/discovery/
│       ├── save_interests.py        # SaveUserInterestsCommand (UPSERT)
│       ├── collect_news.py          # CollectNewsCommand (Celery-triggered)
│       ├── collect_vaults.py        # CollectVaultsCommand (Celery-triggered)
│       └── admin_manage.py          # Admin CRUD commands
│
├── infrastructure/
│   ├── adapters/discovery/
│   │   ├── perplexity_sonar.py      # PRIMARY — chat/completions + search
│   │   ├── newsapi_adapter.py       # FALLBACK — NewsAPI.org
│   │   ├── cryptopanic_adapter.py   # FALLBACK — crypto-specific
│   │   ├── rss_adapter.py           # FALLBACK — RSS feeds
│   │   ├── defillama_adapter.py     # Vault data (free, no key)
│   │   ├── vaultsfyi_adapter.py     # Vault data (API key)
│   │   ├── graphrag_extractor.py    # LLM entity/relationship extraction
│   │   └── hybrid_retriever.py      # Graph + vector combined search
│   │
│   ├── adapters/agent_squad/agents/
│   │   └── discovery_intelligence_agent.py  # GraphRAG-powered agent
│   │
│   └── persistence/discovery/
│       ├── category_sqla.py         # SQLAlchemy CategoryRepository
│       ├── section_sqla.py          # SQLAlchemy SectionRepository
│       ├── interest_sqla.py         # SQLAlchemy InterestRepository
│       ├── news_sqla.py             # SQLAlchemy NewsRepository
│       ├── vault_sqla.py            # SQLAlchemy VaultRepository
│       └── graph_repository.py      # Apache AGE graph queries
│
├── presentation/http/controllers/discovery/
│   ├── categories.py                # GET /discovery/categories
│   ├── interests.py                 # GET + PUT /discovery/interests
│   ├── news_feed.py                 # GET /discovery/news
│   ├── news_search.py              # GET /discovery/news/search
│   ├── vaults.py                    # GET /discovery/vaults
│   └── admin/
│       ├── categories_admin.py      # Admin CRUD categories
│       ├── sections_admin.py        # Admin CRUD sections
│       └── providers_admin.py       # Admin CRUD providers
│
└── tasks/
    └── discovery_tasks.py           # Celery beat + workers
```

## 3. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary news engine | Perplexity Sonar (sonar model) | Real-time web search, citations, $1/M tokens, 50 RPM |
| Fallback news | NewsAPI + CryptoPanic + RSS | Redundancy when Sonar rate-limited or down |
| Category system | Admin-managed DB rows | No code deploy to add/remove topics |
| User interests | Per-section toggles with defaults | Onboarding-friendly |
| Feed algorithm | Personalized → Adjacent → Trending | Always fills the page |
| Search | Sonar (live) + PostgreSQL FTS (cached) | Real-time freshness + fast cached results |
| Vault data | DeFiLlama (free) + Vaults.fyi (key) | Broadest protocol coverage |
| Knowledge graph | Apache AGE (PostgreSQL extension) | No extra infra vs Neo4j |
| Graph extraction LLM | Gemini 2.0 Flash | $0.10/1M tokens, fast, sufficient quality |
| Graph+vector retrieval | 40% vector / 60% graph weighting | Graph gives deeper contextual understanding |

## 4. External System Integrations

```
Discovery Module
    │
    ├── Perplexity Sonar API (https://api.perplexity.ai)
    │     ├── POST /chat/completions (news fetch + search)
    │     ├── Rate: 50 RPM standard, configurable
    │     └── Cost: $1/M input, $1/M output, $5/1K requests
    │
    ├── NewsAPI.org (https://newsapi.org/v2)
    │     ├── GET /everything (keyword search)
    │     └── Rate: 100 req/day free, 1000/day paid
    │
    ├── CryptoPanic (https://cryptopanic.com/api/v1)
    │     ├── GET /posts/ (crypto news)
    │     └── Rate: 100 req/day free
    │
    ├── DeFiLlama (https://yields.llama.fi)
    │     ├── GET /pools (yield data)
    │     └── Rate: Free, no key required
    │
    ├── Vaults.fyi (https://api.vaults.fyi/v2)
    │     ├── GET /vaults (vault data)
    │     └── Rate: Free with API key
    │
    ├── Google Gemini (entity extraction)
    │     └── Used for GraphRAG extraction pipeline
    │
    ├── PostgreSQL + TimescaleDB
    │     ├── All relational data
    │     ├── Full-text search (GIN indexes)
    │     ├── 30-day retention policy (TimescaleDB)
    │     └── Apache AGE graph extension
    │
    └── Redis
          ├── Feed/search caching (120s-300s TTL)
          ├── Provider rate limit counters
          └── Celery broker + result backend
```

## 5. Provider Failover Architecture

```
Request → Perplexity Sonar (primary, priority=100)
             │
             ├── 200 OK → Use articles ✓
             ├── 429 Rate Limited → Fallback chain
             ├── 402 No Credits → Disable + alert + Fallback chain
             └── 5xx/Timeout → Error counter
                   ├── < 10 errors → Retry with backoff
                   └── ≥ 10 errors → Circuit breaker (disable)

Fallback chain:
  ├── NewsAPI (priority=50) — general news
  ├── CryptoPanic (priority=50) — crypto-specific
  └── RSS feeds (priority=20) — always available, last resort
```

## 6. Caching Strategy Summary

| Key Pattern | TTL | Invalidation |
|-------------|-----|-------------|
| `discovery:categories` | 300s | Admin toggle |
| `discovery:sections:{category}` | 300s | Admin toggle |
| `discovery:interests:{user_id}` | 120s | User saves interests |
| `discovery:feed:{user_id}:{page}:{section}` | 60s | TTL-based |
| `discovery:search:{query_hash}` | 30s | TTL-based |
| `discovery:vaults:{sort}:{chain}` | 60s | Vault refresh |
| `discovery:provider:{slug}:rpm` | 60s | Sliding window |

## 7. Performance Targets

| Endpoint | Target | Strategy |
|----------|--------|----------|
| GET /discovery/categories | < 100ms | Redis 5m cache |
| GET /discovery/interests | < 300ms | Redis 2m cache |
| PUT /discovery/interests | < 200ms | Direct DB UPSERT |
| GET /discovery/news | < 800ms | Redis 1m cache + indexed queries |
| GET /discovery/news/search | < 2s | Parallel DB FTS + Sonar |
| GET /discovery/vaults | < 400ms | Redis 1m cache |
