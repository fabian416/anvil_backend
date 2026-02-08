# Discovery Module — Document 2: C4 Model Diagrams

## Level 1: System Context

```mermaid
C4Context
    title Discovery Module - System Context

    Person(user, "Anvil User", "Mobile/web user browsing news and vault opportunities")
    Person(admin, "Content Admin", "Manages categories, sections, providers")

    System(discovery, "Discovery Module", "Content aggregation layer: personalized news feed + DeFi vault opportunities")

    System_Ext(perplexity, "Perplexity Sonar API", "Primary news intelligence engine - real-time web search with citations")
    System_Ext(newsapi, "NewsAPI.org", "General news aggregator - fallback provider")
    System_Ext(cryptopanic, "CryptoPanic API", "Crypto-specific news - fallback for DeFi sections")
    System_Ext(rss, "RSS Feeds", "Reuters, CoinDesk - last resort fallback")
    System_Ext(defillama, "DeFiLlama API", "DeFi yield/TVL data - free, no API key")
    System_Ext(vaultsfyi, "Vaults.fyi API", "Vault data - Morpho, Aave, 75+ protocols")
    System_Ext(gemini, "Google Gemini API", "LLM for GraphRAG entity extraction")

    Rel(user, discovery, "Browses news, searches, views vaults", "HTTPS/REST")
    Rel(admin, discovery, "Manages categories, sections, providers", "HTTPS/REST + Admin Auth")
    Rel(discovery, perplexity, "Fetches news (primary)", "HTTPS")
    Rel(discovery, newsapi, "Fetches news (fallback)", "HTTPS")
    Rel(discovery, cryptopanic, "Fetches crypto news (fallback)", "HTTPS")
    Rel(discovery, rss, "Parses RSS feeds (last resort)", "HTTP/XML")
    Rel(discovery, defillama, "Fetches vault yields", "HTTPS")
    Rel(discovery, vaultsfyi, "Fetches vault data", "HTTPS")
    Rel(discovery, gemini, "Extracts entities/relationships from articles", "HTTPS")
```

## Level 2: Container Diagram

```mermaid
C4Container
    title Discovery Module - Container Diagram

    Person(user, "Anvil User")
    Person(admin, "Content Admin")

    System_Boundary(discovery_system, "Discovery Module") {
        Container(api, "FastAPI Application", "Python/FastAPI", "REST API: news feed, search, interests, vaults, admin CRUD")
        Container(celery_news, "Celery News Worker", "Python/Celery+Gevent", "Collects news every 15min from providers. Queue: news-collection. Concurrency: 4")
        Container(celery_vaults, "Celery Vault Worker", "Python/Celery+Gevent", "Refreshes vault snapshots every 5min. Queue: vault-refresh. Concurrency: 2")
        Container(celery_graphrag, "Celery GraphRAG Worker", "Python/Celery+Gevent", "Extracts entities/relationships from new articles. Queue: graphrag-extraction. Concurrency: 3")
        Container(celery_beat, "Celery Beat", "Python/Celery", "Scheduler: triggers collection cycles, cleanup, graph maintenance")
        ContainerDb(postgres, "PostgreSQL + TimescaleDB + AGE", "PostgreSQL 14", "Tables: categories, sections, interests, articles, vaults, providers. Graph: discovery_graph (Apache AGE)")
        ContainerDb(redis, "Redis", "Redis 7", "Cache (60s-300s TTL), rate limit counters, Celery broker/results")
    }

    System_Ext(perplexity, "Perplexity Sonar")
    System_Ext(newsapi, "NewsAPI.org")
    System_Ext(cryptopanic, "CryptoPanic")
    System_Ext(defillama, "DeFiLlama")
    System_Ext(gemini, "Google Gemini")
    System_Ext(agent_squad, "Anvil Agent Squad", "Other agents consume Discovery Intelligence context")

    Rel(user, api, "REST API calls", "HTTPS")
    Rel(admin, api, "Admin API calls", "HTTPS + Admin JWT")
    Rel(api, postgres, "Reads feed, interests, vaults", "SQLAlchemy async")
    Rel(api, redis, "Caches responses", "Redis async")
    Rel(celery_beat, celery_news, "Triggers every 15min", "Redis broker")
    Rel(celery_beat, celery_vaults, "Triggers every 5min", "Redis broker")
    Rel(celery_news, perplexity, "Fetches news (primary)", "HTTPS")
    Rel(celery_news, newsapi, "Fallback fetch", "HTTPS")
    Rel(celery_news, cryptopanic, "Crypto fallback", "HTTPS")
    Rel(celery_news, postgres, "Stores articles", "SQLAlchemy")
    Rel(celery_news, celery_graphrag, "Chains extraction for new articles", "Redis broker")
    Rel(celery_graphrag, gemini, "Entity extraction LLM calls", "HTTPS")
    Rel(celery_graphrag, postgres, "Writes to Apache AGE graph", "Cypher via SQL")
    Rel(celery_vaults, defillama, "Fetches yield data", "HTTPS")
    Rel(celery_vaults, postgres, "Stores vault snapshots", "SQLAlchemy")
    Rel(agent_squad, api, "DiscoveryIntelligenceAgent.get_context_for_agent()", "Internal")
```

## Level 3: Component Diagram (FastAPI Application)

```mermaid
C4Component
    title Discovery Module - FastAPI Application Components

    Container_Boundary(api, "FastAPI Application") {

        Component_Ext(auth, "Auth Middleware", "Validates JWT, resolves user_id, checks admin roles")

        Component(cat_ctrl, "CategoriesController", "GET /api/v1/discovery/categories")
        Component(int_ctrl, "InterestsController", "GET + PUT /api/v1/discovery/interests")
        Component(feed_ctrl, "NewsFeedController", "GET /api/v1/discovery/news")
        Component(search_ctrl, "SearchController", "GET /api/v1/discovery/news/search")
        Component(vault_ctrl, "VaultsController", "GET /api/v1/discovery/vaults")
        Component(admin_ctrl, "AdminControllers", "POST/PATCH/DELETE /api/v1/admin/discovery/*")

        Component(get_cat_q, "GetCategoriesQuery", "Returns active categories list")
        Component(get_int_q, "GetInterestsQuery", "Section tree + user toggle state")
        Component(get_feed_q, "GetNewsFeedQuery", "3-tier: personalized → adjacent → trending")
        Component(search_q, "SearchNewsQuery", "Hybrid: DB FTS + Sonar real-time")
        Component(get_vault_q, "GetVaultsQuery", "Sorted vault snapshots")
        Component(save_int_cmd, "SaveInterestsCommand", "UPSERT user interests")
        Component(admin_cmd, "AdminManageCommand", "CRUD categories/sections/providers")

        Component(cat_repo, "CategoryRepository", "SQLAlchemy + Redis cache")
        Component(sec_repo, "SectionRepository", "SQLAlchemy + hierarchical queries")
        Component(int_repo, "InterestRepository", "SQLAlchemy + per-user lookups")
        Component(news_repo, "NewsRepository", "SQLAlchemy + FTS + GIN indexes")
        Component(vault_repo, "VaultRepository", "SQLAlchemy + APY/TVL sorting")

        Component(sonar, "PerplexitySonarAdapter", "Primary news fetcher - chat/completions API")
        Component(hybrid_ret, "HybridRetriever", "Graph (60%) + Vector (40%) combined search")
        Component(graph_repo, "GraphRepository", "Apache AGE Cypher queries")
        Component(disc_agent, "DiscoveryIntelligenceAgent", "GraphRAG-powered contextualizer")
    }

    Rel(auth, cat_ctrl, "")
    Rel(auth, int_ctrl, "")
    Rel(auth, feed_ctrl, "")
    Rel(auth, search_ctrl, "")
    Rel(auth, vault_ctrl, "")
    Rel(auth, admin_ctrl, "Requires system_admin/content_admin role")

    Rel(cat_ctrl, get_cat_q, "")
    Rel(int_ctrl, get_int_q, "")
    Rel(int_ctrl, save_int_cmd, "")
    Rel(feed_ctrl, get_feed_q, "")
    Rel(search_ctrl, search_q, "")
    Rel(vault_ctrl, get_vault_q, "")
    Rel(admin_ctrl, admin_cmd, "")

    Rel(get_cat_q, cat_repo, "")
    Rel(get_int_q, sec_repo, "")
    Rel(get_int_q, int_repo, "")
    Rel(get_feed_q, int_repo, "")
    Rel(get_feed_q, news_repo, "")
    Rel(get_feed_q, sec_repo, "")
    Rel(search_q, news_repo, "FTS search")
    Rel(search_q, sonar, "Real-time search")
    Rel(get_vault_q, vault_repo, "")

    Rel(disc_agent, hybrid_ret, "")
    Rel(hybrid_ret, graph_repo, "Cypher queries")
    Rel(hybrid_ret, news_repo, "Vector similarity")
```

## Level 4: Code Diagram — News Collection Flow

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant FanOut as collect_news_all_sections
    participant Worker as collect_section_news
    participant Sonar as PerplexitySonarAdapter
    participant NewsAPI as NewsAPIAdapter
    participant DB as PostgreSQL
    participant GraphRAG as extract_article_graph
    participant Gemini as Gemini 2.0 Flash
    participant AGE as Apache AGE Graph

    Beat->>FanOut: Every 15 minutes
    FanOut->>DB: Get all active leaf sections
    DB-->>FanOut: 30+ sections with keywords

    loop For each section
        FanOut->>Worker: .delay(section_id, keywords)
    end

    Note over Worker: Rate limited: 4/min

    Worker->>Sonar: fetch_news(keywords, section_slug)
    alt Sonar OK (200)
        Sonar-->>Worker: RawArticle[] (5-15 articles)
    else Sonar 429 / Error
        Worker->>NewsAPI: fetch_news(keywords) [fallback]
        NewsAPI-->>Worker: RawArticle[]
    end

    loop For each RawArticle
        Worker->>Worker: compute_hash(title, url)
        Worker->>DB: UPSERT article (skip if hash exists)
        DB-->>Worker: was_new: bool
    end

    Worker->>GraphRAG: .delay(new_article_ids) [chained, 5s delay]

    GraphRAG->>DB: Load articles by IDs
    DB-->>GraphRAG: NewsArticle[]

    loop Batch of 5 articles
        GraphRAG->>Gemini: Extract entities + relationships
        Gemini-->>GraphRAG: ArticleGraphExtraction
        GraphRAG->>AGE: MERGE entities (nodes)
        GraphRAG->>AGE: MERGE relationships (edges)
        GraphRAG->>AGE: CREATE mentioned_in edges
    end
```

## Level 4: Code Diagram — User Feed Request

```mermaid
sequenceDiagram
    participant User as Mobile App
    participant API as FastAPI Controller
    participant Cache as Redis
    participant Query as GetNewsFeedQuery
    participant IntRepo as InterestRepository
    participant NewsRepo as NewsRepository
    participant SecRepo as SectionRepository

    User->>API: GET /api/v1/discovery/news?page=1&section=crypto_defi
    API->>Cache: Check discovery:feed:{user_id}:1:crypto_defi
    alt Cache HIT
        Cache-->>API: Cached NewsFeedResponseDTO
        API-->>User: 200 OK (< 50ms)
    else Cache MISS
        API->>Query: execute(user_id, page=1, section_filter="crypto_defi")

        Query->>IntRepo: get_enabled_section_ids(user_id)
        IntRepo-->>Query: [bitcoin_id, ethereum_id, defi_protocols_id]

        Query->>SecRepo: get_by_slug("crypto_defi")
        SecRepo-->>Query: Section(is_top_level=True)
        Query->>SecRepo: get_children(crypto_defi_id)
        SecRepo-->>Query: [bitcoin, ethereum, defi_protocols, regulation, ...]

        Query->>NewsRepo: get_feed(section_ids, limit=20, offset=0)
        NewsRepo-->>Query: 15 articles (personalized)

        Note over Query: Only 15 articles, need 20 → Adjacent fill

        Query->>SecRepo: get_parent_slugs(section_ids)
        Query->>NewsRepo: get_adjacent_articles(exclude, parent_slugs, limit=5)
        NewsRepo-->>Query: 5 adjacent articles

        Note over Query: 20 articles total → done

        Query->>SecRepo: get_slug_name_map()
        Query-->>API: NewsFeedResponseDTO(articles=20, feed_type="personalized")
        API->>Cache: SET discovery:feed:{user_id}:1:crypto_defi TTL=60s
        API-->>User: 200 OK (< 800ms)
    end
```

## Level 4: Code Diagram — Hybrid Search

```mermaid
sequenceDiagram
    participant User as Mobile App
    participant API as SearchController
    participant Query as SearchNewsQuery
    participant DB as NewsRepository (FTS)
    participant Sonar as PerplexitySonarAdapter
    participant Merge as Dedup + Merge

    User->>API: GET /api/v1/discovery/news/search?q=aave+oracle+issue

    par Parallel Execution
        API->>Query: execute(query="aave oracle issue")
        Query->>DB: search(query, FTS) [fast, cached articles]
        Query->>Sonar: search_news(query) [real-time, fresh]
    end

    DB-->>Query: (db_articles, total_count) [< 500ms]
    Sonar-->>Query: sonar_raw_articles [< 2s]

    Query->>Merge: DB results first (fast), then Sonar (fresh)
    Note over Merge: Dedup by content_hash, skip duplicates
    Merge-->>Query: merged_articles (max page_size)

    Query-->>API: NewsFeedResponseDTO(feed_type="search")
    API-->>User: 200 OK
```

## Level 4: Code Diagram — Discovery Intelligence Agent (Inter-Agent)

```mermaid
sequenceDiagram
    participant Portfolio as PortfolioAgent
    participant DIA as DiscoveryIntelligenceAgent
    participant Hybrid as HybridRetriever
    participant Vector as pgvector Search
    participant Graph as Apache AGE
    participant LLM as Gemini 2.0 Flash

    Portfolio->>DIA: get_portfolio_news_context(tokens=["ETH","USDC"], protocols=["Aave"])

    DIA->>Hybrid: retrieve(query="ETH USDC Aave", entity_names=["ETH","USDC","Aave"])

    par Parallel Retrieval
        Hybrid->>Vector: similarity_search("ETH USDC Aave", limit=10)
        Hybrid->>Graph: query_entity_context("Aave", depth=2)
        Hybrid->>Graph: query_entity_context("ETH", depth=2)
        Hybrid->>Graph: query_risk_propagation("Aave")
        Hybrid->>Graph: query_recent_events(entity="Aave")
    end

    Vector-->>Hybrid: 10 related articles
    Graph-->>Hybrid: Aave entity graph (relationships, dependencies)
    Graph-->>Hybrid: ETH entity graph
    Graph-->>Hybrid: Risk paths: Aave→Chainlink, Aave→USDT
    Graph-->>Hybrid: Recent events: oracle_delay (high severity)

    Hybrid-->>DIA: HybridRetrievalResult

    DIA->>DIA: Filter to portfolio-relevant results only
    DIA-->>Portfolio: {portfolio_risks, portfolio_events, portfolio_sentiment, relevant_articles}

    Portfolio->>LLM: Generate response with enriched context
    LLM-->>Portfolio: "Aave paused USDT lending due to oracle delays. Your $5,200 USDT supply position may be affected..."
```
