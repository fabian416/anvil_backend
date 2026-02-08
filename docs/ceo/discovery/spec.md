# Discovery Module — Enterprise Implementation Specification

**Version**: 2.0 (Enterprise)  
**Date**: February 8, 2026  
**Author**: Matias Baglieri  
**Module**: Discovery (News, Vaults, extensible categories)  
**Architecture**: Hexagonal (Clean Architecture)  
**Stack**: FastAPI + PostgreSQL + Redis + Celery + Perplexity Sonar API

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Database Schema (PostgreSQL)](#3-database-schema)
4. [Domain Entities](#4-domain-entities)
5. [Ports (Interfaces)](#5-ports)
6. [Infrastructure Adapters](#6-infrastructure-adapters)
7. [Application Layer (Queries & Commands)](#7-application-layer)
8. [Presentation Layer (API Endpoints)](#8-presentation-layer)
9. [Celery Workers (News Collection Pipeline)](#9-celery-workers)
10. [Perplexity Sonar Integration](#10-perplexity-sonar-integration)
11. [Admin Endpoints](#11-admin-endpoints)
12. [Caching Strategy](#12-caching-strategy)
13. [Performance Targets](#13-performance-targets)
14. [Deployment Configuration](#14-deployment-configuration)
15. [GraphRAG News Contextualization](#15-graphrag-news-contextualization)
16. [Discovery Intelligence Agent](#16-discovery-intelligence-agent)
17. [Open Items & Roadmap](#17-open-items)

---

## 1. Executive Summary

The Discovery module is Anvil's content aggregation layer that surfaces personalized news and DeFi vault opportunities to users through admin-configurable interest categories. The system uses **Perplexity Sonar API** as its primary news intelligence engine (real-time web search with citations at $1/M input tokens), supplemented by traditional providers (NewsAPI, CryptoPanic, RSS feeds) for redundancy. DeFi vault data comes from DeFiLlama and protocol-specific APIs.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary news engine | Perplexity Sonar | Real-time web grounding, citations, $1/M tokens, 50 RPM |
| Fallback providers | NewsAPI + CryptoPanic + RSS | Redundancy when Sonar quota exceeded or offline |
| Category system | Admin-managed DB rows | No code changes to add/remove categories |
| User interests | Per-section toggles with defaults | Onboarding-friendly, respects admin toggles |
| Feed algorithm | Personalized → Adjacent → Trending | Always fills the page |
| Search | Perplexity Sonar (live) + PostgreSQL FTS (cached) | Best of both: real-time + fast |
| Vault data | DeFiLlama + Vaults.fyi | Broadest protocol coverage |

### Cost Projection (Perplexity Sonar)

| Usage | Volume | Cost |
|-------|--------|------|
| News collection (15 min intervals × 30 sections) | ~2,880 requests/day | ~$14.40/day ($5/1K req) |
| User search (est. 500 searches/day) | ~500 requests/day | ~$2.50/day |
| Input tokens (~200 tokens avg/req) | ~676K tokens/day | ~$0.68/day |
| Output tokens (~800 tokens avg/req) | ~2.7M tokens/day | ~$2.70/day |
| **Monthly total** | | **~$609/mo** |

---

## 2. Architecture Overview

### File Structure

```
src/app/
├── domain/
│   ├── entities/discovery/
│   │   ├── __init__.py
│   │   ├── category.py              # DiscoveryCategory entity
│   │   ├── section.py               # DiscoverySection entity
│   │   ├── user_interest.py         # UserInterest entity
│   │   ├── news_article.py          # NewsArticle entity
│   │   ├── vault_snapshot.py        # VaultSnapshot entity
│   │   └── news_provider.py         # NewsProvider entity
│   │
│   └── ports/discovery/
│       ├── __init__.py
│       ├── category_repository.py   # CategoryRepositoryPort
│       ├── section_repository.py    # SectionRepositoryPort
│       ├── interest_repository.py   # InterestRepositoryPort
│       ├── news_repository.py       # NewsRepositoryPort
│       ├── vault_repository.py      # VaultRepositoryPort
│       ├── news_fetcher_port.py     # NewsFetcherPort (adapter interface)
│       └── vault_fetcher_port.py    # VaultFetcherPort (adapter interface)
│
├── application/
│   ├── queries/discovery/
│   │   ├── __init__.py
│   │   ├── get_categories.py        # GetDiscoveryCategoriesQuery
│   │   ├── get_interests.py         # GetUserInterestsQuery
│   │   ├── get_news_feed.py         # GetNewsFeedQuery
│   │   ├── search_news.py           # SearchNewsQuery
│   │   └── get_vaults.py            # GetVaultsQuery
│   │
│   └── commands/discovery/
│       ├── __init__.py
│       ├── save_interests.py        # SaveUserInterestsCommand
│       ├── collect_news.py          # CollectNewsCommand (Celery)
│       ├── collect_vaults.py        # CollectVaultsCommand (Celery)
│       └── admin_manage.py          # AdminManageCategoryCommand, etc.
│
├── infrastructure/
│   ├── adapters/discovery/
│   │   ├── __init__.py
│   │   ├── perplexity_sonar.py      # PRIMARY — Perplexity Sonar adapter
│   │   ├── newsapi_adapter.py       # FALLBACK — NewsAPI.org
│   │   ├── cryptopanic_adapter.py   # FALLBACK — CryptoPanic
│   │   ├── rss_adapter.py           # FALLBACK — RSS feeds
│   │   ├── defillama_adapter.py     # Vault data from DeFiLlama
│   │   └── vaultsfyi_adapter.py     # Vault data from Vaults.fyi
│   │
│   └── persistence/discovery/
│       ├── __init__.py
│       ├── category_sqla.py         # SQLAlchemy CategoryRepository
│       ├── section_sqla.py          # SQLAlchemy SectionRepository
│       ├── interest_sqla.py         # SQLAlchemy InterestRepository
│       ├── news_sqla.py             # SQLAlchemy NewsRepository
│       └── vault_sqla.py            # SQLAlchemy VaultRepository
│
├── presentation/http/controllers/discovery/
│   ├── __init__.py
│   ├── categories.py                # GET /discovery/categories
│   ├── interests.py                 # GET + PUT /discovery/interests
│   ├── news_feed.py                 # GET /discovery/news
│   ├── news_search.py              # GET /discovery/news/search
│   ├── vaults.py                    # GET /discovery/vaults
│   └── admin/
│       ├── __init__.py
│       ├── categories_admin.py      # Admin CRUD categories
│       ├── sections_admin.py        # Admin CRUD sections
│       └── providers_admin.py       # Admin CRUD providers
│
└── tasks/
    └── discovery_tasks.py           # Celery beat + workers
```

### Dependency Flow

```
Presentation (Controllers)
    │
    ▼
Application (Queries / Commands)
    │
    ▼
Domain (Entities + Ports)
    │
    ▼
Infrastructure (Adapters + Persistence)
    │
    ├── Perplexity Sonar API
    ├── NewsAPI / CryptoPanic / RSS
    ├── DeFiLlama / Vaults.fyi
    └── PostgreSQL + Redis
```

---

## 3. Database Schema

### 3.1 discovery_categories

```sql
-- ============================================================================
-- MODULE: DISCOVERY — Admin-Managed Content Categories
-- ============================================================================

CREATE TABLE discovery_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_discovery_categories_active
    ON discovery_categories (is_active, sort_order);

CREATE TRIGGER update_discovery_categories_updated_at
    BEFORE UPDATE ON discovery_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Seed
INSERT INTO discovery_categories (slug, name, icon, sort_order, is_active, is_default) VALUES
    ('news',   'News',           'newspaper', 1, true, true),
    ('vaults', 'Today''s Vaults', 'vault',     2, true, true);
```

### 3.2 discovery_sections

```sql
CREATE TABLE discovery_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES discovery_categories(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES discovery_sections(id) ON DELETE CASCADE,
    slug VARCHAR(100) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_section_category_slug UNIQUE (category_id, slug)
);

CREATE INDEX idx_sections_category_active
    ON discovery_sections (category_id, is_active, sort_order);
CREATE INDEX idx_sections_parent
    ON discovery_sections (parent_id);

CREATE TRIGGER update_discovery_sections_updated_at
    BEFORE UPDATE ON discovery_sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.3 Seed: All News Sections & Subsections

```sql
-- ─── POLITICS ────────────────────────────────────────────────
DO $$
DECLARE
    cat_news UUID := (SELECT id FROM discovery_categories WHERE slug = 'news');
    sec_politics UUID;
    sec_tech UUID;
    sec_crypto UUID;
    sec_economy UUID;
    sec_world UUID;
BEGIN
    -- Top-level sections
    INSERT INTO discovery_sections (id, category_id, parent_id, slug, name, icon, sort_order, is_active, is_default, metadata)
    VALUES
        (gen_random_uuid(), cat_news, NULL, 'politics',        'Politics',          'landmark',     1, true, true,  '{"keywords":["politics","government","policy","legislation"]}'),
        (gen_random_uuid(), cat_news, NULL, 'tech_science',    'Tech & Science',    'cpu',          2, true, true,  '{"keywords":["technology","science","innovation"]}'),
        (gen_random_uuid(), cat_news, NULL, 'crypto_defi',     'Crypto & DeFi',     'bitcoin',      3, true, true,  '{"keywords":["cryptocurrency","defi","blockchain","web3"]}'),
        (gen_random_uuid(), cat_news, NULL, 'economy_finance', 'Economy & Finance', 'trending-up',  4, true, false, '{"keywords":["economy","finance","markets","stocks"]}'),
        (gen_random_uuid(), cat_news, NULL, 'world',           'World',             'globe',        5, true, false, '{"keywords":["world","international","global"]}')
    ON CONFLICT (category_id, slug) DO NOTHING;

    -- Get parent IDs
    sec_politics := (SELECT id FROM discovery_sections WHERE slug = 'politics' AND parent_id IS NULL);
    sec_tech     := (SELECT id FROM discovery_sections WHERE slug = 'tech_science' AND parent_id IS NULL);
    sec_crypto   := (SELECT id FROM discovery_sections WHERE slug = 'crypto_defi' AND parent_id IS NULL);
    sec_economy  := (SELECT id FROM discovery_sections WHERE slug = 'economy_finance' AND parent_id IS NULL);
    sec_world    := (SELECT id FROM discovery_sections WHERE slug = 'world' AND parent_id IS NULL);

    -- ─── Politics subsections ───
    INSERT INTO discovery_sections (category_id, parent_id, slug, name, sort_order, is_active, is_default, metadata)
    VALUES
        (cat_news, sec_politics, 'world_affairs',  'World Affairs',      1,  true, true,  '{"keywords":["world affairs","international relations","diplomacy","foreign policy"]}'),
        (cat_news, sec_politics, 'us_politics',    'US Politics',        2,  true, true,  '{"keywords":["us politics","congress","white house","senate","supreme court"]}'),
        (cat_news, sec_politics, 'europe',         'Europe',             3,  true, false, '{"keywords":["europe","eu","european union","brexit","nato"]}'),
        (cat_news, sec_politics, 'asia',           'Asia',               4,  true, false, '{"keywords":["asia","china","japan","india","south korea","taiwan"]}'),
        (cat_news, sec_politics, 'middle_east',    'Middle East',        5,  true, false, '{"keywords":["middle east","israel","iran","saudi arabia","palestine"]}'),
        (cat_news, sec_politics, 'latin_america',  'Latin America',      6,  true, false, '{"keywords":["latin america","brazil","mexico","argentina","colombia"]}'),
        (cat_news, sec_politics, 'africa',         'Africa',             7,  true, false, '{"keywords":["africa","nigeria","south africa","kenya","egypt"]}'),
        (cat_news, sec_politics, 'elections',      'Elections',          8,  true, false, '{"keywords":["elections","vote","polls","campaign","ballot"]}'),
        (cat_news, sec_politics, 'government',     'Government',         9,  true, false, '{"keywords":["government","legislation","regulation","executive order"]}'),
        (cat_news, sec_politics, 'military',       'Military & Defense', 10, true, false, '{"keywords":["military","defense","army","navy","air force","nato"]}'),
        (cat_news, sec_politics, 'geopolitics',    'Geopolitics',        11, true, false, '{"keywords":["geopolitics","sanctions","trade war","diplomacy","alliances"]}')
    ON CONFLICT (category_id, slug) DO NOTHING;

    -- ─── Tech & Science subsections ───
    INSERT INTO discovery_sections (category_id, parent_id, slug, name, sort_order, is_active, is_default, metadata)
    VALUES
        (cat_news, sec_tech, 'tech',          'Technology',          1,  true, true,  '{"keywords":["technology","tech","innovation","gadgets"]}'),
        (cat_news, sec_tech, 'science',       'Science',             2,  true, true,  '{"keywords":["science","research","discovery","physics","chemistry"]}'),
        (cat_news, sec_tech, 'big_tech',      'Big Tech',            3,  true, false, '{"keywords":["apple","google","microsoft","amazon","meta","nvidia","openai"]}'),
        (cat_news, sec_tech, 'startups',      'Startups',            4,  true, false, '{"keywords":["startup","funding","venture capital","seed round","series a"]}'),
        (cat_news, sec_tech, 'ai_ml',         'AI & Machine Learning', 5, true, true,  '{"keywords":["ai","artificial intelligence","machine learning","llm","gpt","claude"]}'),
        (cat_news, sec_tech, 'robotics',      'Robotics',            6,  true, false, '{"keywords":["robotics","robots","automation","humanoid"]}'),
        (cat_news, sec_tech, 'medical',       'Medical & Health',    7,  true, false, '{"keywords":["medical","health","pharma","fda","clinical trial"]}'),
        (cat_news, sec_tech, 'electronics',   'Electronics',         8,  true, false, '{"keywords":["electronics","semiconductor","chips","hardware","intel","tsmc"]}'),
        (cat_news, sec_tech, 'energy',        'Energy',              9,  true, false, '{"keywords":["energy","solar","wind","oil","renewable","battery"]}'),
        (cat_news, sec_tech, 'agriculture',   'Agriculture',         10, true, false, '{"keywords":["agriculture","farming","food tech","agritech"]}'),
        (cat_news, sec_tech, 'climate',       'Climate',             11, true, false, '{"keywords":["climate","climate change","global warming","carbon emissions"]}'),
        (cat_news, sec_tech, 'environment',   'Environment',         12, true, false, '{"keywords":["environment","pollution","conservation","biodiversity"]}'),
        (cat_news, sec_tech, 'nuclear',       'Nuclear',             13, true, false, '{"keywords":["nuclear","nuclear energy","fusion","fission","reactor"]}'),
        (cat_news, sec_tech, 'space',         'Space',               14, true, false, '{"keywords":["space","nasa","spacex","astronomy","mars","moon","satellite"]}'),
        (cat_news, sec_tech, 'programming',   'Programming',         15, true, false, '{"keywords":["programming","software","coding","developer","open source","github"]}'),
        (cat_news, sec_tech, 'biotech',       'Biotech',             16, true, false, '{"keywords":["biotech","biotechnology","genetics","crispr","gene therapy"]}')
    ON CONFLICT (category_id, slug) DO NOTHING;

    -- ─── Crypto & DeFi subsections ───
    INSERT INTO discovery_sections (category_id, parent_id, slug, name, sort_order, is_active, is_default, metadata)
    VALUES
        (cat_news, sec_crypto, 'bitcoin',         'Bitcoin',            1,  true, true,  '{"keywords":["bitcoin","btc","halving","mining"]}'),
        (cat_news, sec_crypto, 'ethereum',        'Ethereum',           2,  true, true,  '{"keywords":["ethereum","eth","layer 2","rollup"]}'),
        (cat_news, sec_crypto, 'defi_protocols',  'DeFi Protocols',     3,  true, true,  '{"keywords":["defi","aave","morpho","uniswap","compound","lending","yield"]}'),
        (cat_news, sec_crypto, 'regulation',      'Regulation',         4,  true, false, '{"keywords":["sec","crypto regulation","securities","compliance"]}'),
        (cat_news, sec_crypto, 'nft_gaming',      'NFT & Gaming',       5,  true, false, '{"keywords":["nft","gaming","metaverse","play to earn"]}'),
        (cat_news, sec_crypto, 'meme_coins',      'Meme Coins',         6,  true, false, '{"keywords":["meme coin","doge","shiba","pepe","memecoin"]}'),
        (cat_news, sec_crypto, 'stablecoins',     'Stablecoins',        7,  true, false, '{"keywords":["stablecoin","usdc","usdt","dai","tether"]}')
    ON CONFLICT (category_id, slug) DO NOTHING;

    -- ─── Economy & Finance subsections ───
    INSERT INTO discovery_sections (category_id, parent_id, slug, name, sort_order, is_active, is_default, metadata)
    VALUES
        (cat_news, sec_economy, 'markets',         'Markets',            1,  true, false, '{"keywords":["stock market","nasdaq","s&p 500","dow jones"]}'),
        (cat_news, sec_economy, 'central_banks',   'Central Banks',      2,  true, false, '{"keywords":["federal reserve","ecb","interest rates","monetary policy"]}'),
        (cat_news, sec_economy, 'commodities',     'Commodities',        3,  true, false, '{"keywords":["gold","oil","commodities","wheat","copper"]}'),
        (cat_news, sec_economy, 'real_estate',     'Real Estate',        4,  true, false, '{"keywords":["real estate","housing","mortgage","property"]}')
    ON CONFLICT (category_id, slug) DO NOTHING;
END $$;
```

### 3.4 discovery_user_interests

```sql
CREATE TABLE discovery_user_interests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES discovery_sections(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_user_section UNIQUE (user_id, section_id)
);

CREATE INDEX idx_user_interests_user ON discovery_user_interests (user_id);
CREATE INDEX idx_user_interests_lookup ON discovery_user_interests (user_id, section_id, is_enabled);
```

### 3.5 discovery_news_providers

```sql
CREATE TYPE news_provider_type_enum AS ENUM ('sonar', 'api', 'rss', 'scraper');

CREATE TABLE discovery_news_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    provider_type news_provider_type_enum NOT NULL,
    base_url TEXT,
    api_key_ref VARCHAR(100),
    config JSONB DEFAULT '{}',
    supported_sections JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 0,
    rate_limit_per_minute INTEGER DEFAULT 50,
    rate_limit_per_day INTEGER DEFAULT 5000,
    daily_request_count INTEGER DEFAULT 0,
    daily_count_reset_at TIMESTAMPTZ DEFAULT NOW(),
    last_fetched_at TIMESTAMPTZ,
    consecutive_errors INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed providers
INSERT INTO discovery_news_providers
    (slug, name, provider_type, base_url, api_key_ref, config, supported_sections, is_active, is_primary, priority, rate_limit_per_minute, rate_limit_per_day)
VALUES
    ('perplexity_sonar', 'Perplexity Sonar', 'sonar',
     'https://api.perplexity.ai', 'PERPLEXITY_API_KEY',
     '{"model":"sonar","search_context_size":"low","temperature":0.1,"max_tokens":1024}',
     '["politics","tech_science","crypto_defi","economy_finance","world"]',
     true, true, 100, 50, 5000),

    ('newsapi', 'NewsAPI', 'api',
     'https://newsapi.org', 'NEWSAPI_KEY',
     '{"page_size":50,"sort_by":"publishedAt"}',
     '["politics","tech_science","economy_finance","world"]',
     true, false, 50, 100, 10000),

    ('cryptopanic', 'CryptoPanic', 'api',
     'https://cryptopanic.com/api/v1', 'CRYPTOPANIC_KEY',
     '{"filter":"important"}',
     '["crypto_defi"]',
     true, false, 50, 30, 5000),

    ('rss_coindesk', 'CoinDesk RSS', 'rss',
     'https://www.coindesk.com/arc/outboundfeeds/rss/', NULL,
     '{}', '["crypto_defi"]',
     true, false, 20, 10, 1000),

    ('rss_reuters', 'Reuters RSS', 'rss',
     NULL, NULL,
     '{"feeds":{"world":"https://feeds.reuters.com/reuters/worldNews","tech":"https://feeds.reuters.com/reuters/technologyNews","business":"https://feeds.reuters.com/reuters/businessNews"}}',
     '["politics","tech_science","economy_finance","world"]',
     true, false, 20, 10, 1000),

    ('defillama', 'DeFiLlama', 'api',
     'https://yields.llama.fi', NULL,
     '{"min_tvl":100000}',
     '["vaults"]',
     true, false, 80, 30, 5000),

    ('vaultsfyi', 'Vaults.fyi', 'api',
     'https://api.vaults.fyi/v2', 'VAULTSFYI_KEY',
     '{}', '["vaults"]',
     true, false, 70, 20, 3000);
```

### 3.6 discovery_news_articles

```sql
CREATE TABLE discovery_news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES discovery_news_providers(id),
    external_id VARCHAR(500),

    -- Content
    title TEXT NOT NULL,
    summary TEXT,
    image_url TEXT,
    source_name VARCHAR(200) NOT NULL,
    source_url TEXT NOT NULL,
    author VARCHAR(200),
    citations JSONB DEFAULT '[]',

    -- Classification
    section_id UUID REFERENCES discovery_sections(id),
    parent_section_slug VARCHAR(100),
    section_slug VARCHAR(100),
    tags TEXT[] DEFAULT '{}',
    language VARCHAR(10) DEFAULT 'en',
    sentiment VARCHAR(20) DEFAULT 'neutral',

    -- Timestamps
    published_at TIMESTAMPTZ NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup & quality
    content_hash VARCHAR(64) NOT NULL,
    relevance_score FLOAT DEFAULT 0.5,
    view_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_news_content_hash ON discovery_news_articles (content_hash);
CREATE INDEX idx_news_section_published ON discovery_news_articles (section_id, published_at DESC) WHERE is_active = true;
CREATE INDEX idx_news_published ON discovery_news_articles (published_at DESC) WHERE is_active = true;
CREATE INDEX idx_news_parent_section ON discovery_news_articles (parent_section_slug, published_at DESC) WHERE is_active = true;
CREATE INDEX idx_news_relevance ON discovery_news_articles (relevance_score DESC, published_at DESC) WHERE is_active = true;
CREATE INDEX idx_news_tags ON discovery_news_articles USING GIN (tags);
CREATE INDEX idx_news_fts ON discovery_news_articles USING GIN (
    to_tsvector('english', title || ' ' || COALESCE(summary, ''))
);

-- TimescaleDB: 30-day retention
SELECT add_retention_policy('discovery_news_articles', INTERVAL '30 days');
```

### 3.7 discovery_vault_snapshots

```sql
CREATE TABLE discovery_vault_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID REFERENCES discovery_news_providers(id),

    -- Protocol
    protocol VARCHAR(50) NOT NULL,
    protocol_display VARCHAR(100) NOT NULL,
    vault_name VARCHAR(200) NOT NULL,
    vault_address VARCHAR(42),
    chain VARCHAR(50) NOT NULL,
    chain_name VARCHAR(50) NOT NULL,

    -- Metrics
    asset_symbol VARCHAR(20) NOT NULL,
    supply_apy NUMERIC(10,4) NOT NULL,
    reward_apy NUMERIC(10,4) DEFAULT 0,
    total_apy NUMERIC(10,4) GENERATED ALWAYS AS (supply_apy + reward_apy) STORED,
    tvl_usd NUMERIC(18,2),

    -- Risk
    risk_level VARCHAR(20) DEFAULT 'low',
    is_curated BOOLEAN DEFAULT true,

    -- Meta
    snapshot_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_vaults_apy ON discovery_vault_snapshots (total_apy DESC) WHERE is_active = true;
CREATE INDEX idx_vaults_time ON discovery_vault_snapshots (snapshot_at DESC);
CREATE INDEX idx_vaults_protocol ON discovery_vault_snapshots (protocol, asset_symbol) WHERE is_active = true;
```

---

## 4. Domain Entities

### 4.1 entities/discovery/category.py

```python
"""Discovery Category domain entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DiscoveryCategory:
    """Admin-managed content tab in Discovery."""

    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    icon: str | None = None
    sort_order: int = 0
    is_active: bool = True
    is_default: bool = False
    config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_user_preferences(self) -> bool:
        """Categories like 'news' have user interest toggles; 'vaults' doesn't."""
        return self.slug in {"news"}
```

### 4.2 entities/discovery/section.py

```python
"""Discovery Section domain entity — hierarchical interest node."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DiscoverySection:
    """A section or subsection within a category."""

    id: uuid.UUID
    category_id: uuid.UUID
    parent_id: uuid.UUID | None
    slug: str
    name: str
    description: str | None = None
    icon: str | None = None
    sort_order: int = 0
    is_active: bool = True
    is_default: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_top_level(self) -> bool:
        return self.parent_id is None

    @property
    def keywords(self) -> list[str]:
        return self.metadata.get("keywords", [])
```

### 4.3 entities/discovery/news_article.py

```python
"""NewsArticle domain entity."""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NewsArticle:
    """A single news article in the discovery feed."""

    id: uuid.UUID
    title: str
    source_name: str
    source_url: str
    published_at: datetime
    content_hash: str

    # Optional
    summary: str | None = None
    image_url: str | None = None
    author: str | None = None
    citations: list[str] = field(default_factory=list)

    # Classification
    section_id: uuid.UUID | None = None
    section_slug: str | None = None
    parent_section_slug: str | None = None
    tags: list[str] = field(default_factory=list)
    sentiment: str = "neutral"

    # Quality
    relevance_score: float = 0.5
    view_count: int = 0

    @staticmethod
    def compute_hash(title: str, source_url: str) -> str:
        """Dedup hash: SHA-256 of normalized title + URL."""
        raw = (title.strip().lower() + "|" + source_url.strip()).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @property
    def time_ago(self) -> str:
        """Human-readable time delta."""
        delta = datetime.utcnow() - self.published_at
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        return f"{days}d ago"
```

### 4.4 entities/discovery/vault_snapshot.py

```python
"""VaultSnapshot domain entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class VaultSnapshot:
    """A point-in-time snapshot of a DeFi vault opportunity."""

    id: uuid.UUID
    protocol: str
    protocol_display: str
    vault_name: str
    chain: str
    chain_name: str
    asset_symbol: str
    supply_apy: float
    reward_apy: float = 0.0
    tvl_usd: float = 0.0
    risk_level: str = "low"
    is_curated: bool = True
    vault_address: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_apy(self) -> float:
        return self.supply_apy + self.reward_apy

    @property
    def cta(self) -> str:
        return f"Deposit {self.asset_symbol} to earn {self.total_apy:.1f}% APY"

    @property
    def intent_trigger(self) -> str:
        return "lending_deposit"
```

---

## 5. Ports (Interfaces)

### 5.1 ports/discovery/news_fetcher_port.py

```python
"""Port for all news fetching adapters — Perplexity, NewsAPI, RSS, etc."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawArticle:
    """Adapter-agnostic article coming from any provider."""

    title: str
    source_name: str
    source_url: str
    published_at: datetime
    summary: str | None = None
    image_url: str | None = None
    author: str | None = None
    external_id: str | None = None
    citations: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    relevance_score: float = 0.5


class NewsFetcherPort(abc.ABC):
    """Interface that all news adapters implement."""

    @abc.abstractmethod
    async def fetch_news(
        self,
        keywords: list[str],
        section_slug: str,
        max_results: int = 20,
    ) -> list[RawArticle]:
        """Fetch news articles matching keywords for a section."""
        ...

    @abc.abstractmethod
    async def search_news(
        self,
        query: str,
        max_results: int = 20,
    ) -> list[RawArticle]:
        """Real-time search for articles matching a user query."""
        ...

    @property
    @abc.abstractmethod
    def provider_slug(self) -> str:
        """Unique identifier for this provider."""
        ...

    @property
    @abc.abstractmethod
    def is_available(self) -> bool:
        """Whether this provider is currently operational."""
        ...
```

### 5.2 ports/discovery/vault_fetcher_port.py

```python
"""Port for vault data fetching adapters."""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class RawVault:
    """Adapter-agnostic vault data."""

    protocol: str
    vault_name: str
    chain: str
    asset_symbol: str
    supply_apy: float
    reward_apy: float = 0.0
    tvl_usd: float = 0.0
    vault_address: str | None = None
    risk_level: str = "low"
    is_curated: bool = True


class VaultFetcherPort(abc.ABC):
    """Interface for all vault data adapters."""

    @abc.abstractmethod
    async def fetch_vaults(
        self,
        protocols: list[str] | None = None,
        chains: list[str] | None = None,
        min_tvl: float = 100_000,
    ) -> list[RawVault]:
        ...
```

### 5.3 ports/discovery/news_repository.py

```python
"""Port for news article persistence."""
from __future__ import annotations

import abc
import uuid

from domain.entities.discovery.news_article import NewsArticle


class NewsRepositoryPort(abc.ABC):

    @abc.abstractmethod
    async def upsert_article(self, article: NewsArticle, provider_id: uuid.UUID) -> bool:
        """Insert or skip duplicate. Returns True if new."""
        ...

    @abc.abstractmethod
    async def get_feed(
        self,
        section_ids: list[uuid.UUID],
        limit: int = 20,
        offset: int = 0,
        exclude_ids: set[uuid.UUID] | None = None,
    ) -> list[NewsArticle]:
        ...

    @abc.abstractmethod
    async def search(
        self,
        query: str,
        section_ids: list[uuid.UUID] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[NewsArticle], int]:
        """Full-text search. Returns (articles, total_count)."""
        ...

    @abc.abstractmethod
    async def get_adjacent_articles(
        self,
        exclude_section_ids: list[uuid.UUID],
        parent_section_slugs: list[str],
        limit: int = 10,
    ) -> list[NewsArticle]:
        """Get articles from sibling sections for feed padding."""
        ...

    @abc.abstractmethod
    async def get_trending(self, limit: int = 10) -> list[NewsArticle]:
        """Get top articles by relevance_score across all sections."""
        ...
```

---

## 6. Infrastructure Adapters

### 6.1 Perplexity Sonar Adapter (PRIMARY)

```python
"""
Perplexity Sonar API adapter — PRIMARY news intelligence engine.

API: https://api.perplexity.ai/chat/completions
Model: sonar (base) — $1/M input, $1/M output, $5/1K requests
Rate: 50 RPM (standard), 150 RPM (Growth), 500 RPM (Business)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from domain.ports.discovery.news_fetcher_port import NewsFetcherPort, RawArticle
from infrastructure.config import settings

logger = logging.getLogger(__name__)

SONAR_SYSTEM_PROMPT = """You are a news intelligence API. Return ONLY valid JSON.
For the given topic keywords, find the most recent and important news articles.

Return a JSON array of objects with these exact fields:
{
  "articles": [
    {
      "title": "Article headline",
      "summary": "2-3 sentence summary of the article",
      "source_name": "Publisher name (e.g. Reuters, Bloomberg)",
      "source_url": "https://...",
      "published_date": "YYYY-MM-DD",
      "sentiment": "positive|negative|neutral",
      "tags": ["tag1", "tag2"],
      "image_url": null
    }
  ]
}

Rules:
- Return 5-15 articles, prioritize last 24 hours
- Only include articles from reputable sources
- Include the actual source URL, not a search result URL
- Keep summaries factual and concise
- Sentiment: positive/negative/neutral based on content tone
- Return ONLY the JSON, no markdown fences, no commentary"""


class PerplexitySonarAdapter(NewsFetcherPort):
    """Perplexity Sonar API adapter for real-time news with citations."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "sonar",
        search_context_size: str = "low",
        timeout: float = 30.0,
    ):
        self._api_key = api_key or settings.PERPLEXITY_API_KEY
        self._model = model
        self._search_context_size = search_context_size
        self._base_url = "https://api.perplexity.ai"
        self._timeout = timeout
        self._available = True
        self._consecutive_errors = 0

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout),
        )

    @property
    def provider_slug(self) -> str:
        return "perplexity_sonar"

    @property
    def is_available(self) -> bool:
        return self._available and self._api_key is not None

    async def fetch_news(
        self,
        keywords: list[str],
        section_slug: str,
        max_results: int = 15,
    ) -> list[RawArticle]:
        """Fetch news via Sonar chat completion with web search."""
        if not self.is_available:
            return []

        user_prompt = (
            f"Find the latest news about: {', '.join(keywords)}. "
            f"Topic category: {section_slug.replace('_', ' ')}. "
            f"Return {max_results} most recent and important articles from today and yesterday."
        )

        try:
            response = await self._client.post(
                "/chat/completions",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SONAR_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2048,
                    "search_context_size": self._search_context_size,
                    "search_recency_filter": "day",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Extract citations from Sonar response
            citations = data.get("citations", [])
            search_results = data.get("search_results", [])

            # Parse the structured JSON from content
            content = data["choices"][0]["message"]["content"]
            articles_data = self._parse_json_response(content)

            # Log token usage for cost tracking
            usage = data.get("usage", {})
            logger.info(
                "Sonar fetch: section=%s, articles=%d, tokens_in=%d, tokens_out=%d, cost=$%.4f",
                section_slug,
                len(articles_data),
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
                usage.get("cost", {}).get("total_cost", 0),
            )

            self._consecutive_errors = 0
            return self._map_articles(articles_data, citations, search_results)

        except httpx.HTTPStatusError as e:
            self._handle_error(e)
            if e.response.status_code == 429:
                logger.warning("Sonar rate limited for section=%s", section_slug)
            elif e.response.status_code == 402:
                logger.critical("Sonar insufficient credits!")
                self._available = False
            return []

        except Exception as e:
            self._handle_error(e)
            logger.error("Sonar fetch failed for section=%s: %s", section_slug, e)
            return []

    async def search_news(
        self,
        query: str,
        max_results: int = 15,
    ) -> list[RawArticle]:
        """Real-time news search using Sonar."""
        if not self.is_available:
            return []

        user_prompt = (
            f"Search for recent news about: {query}. "
            f"Return {max_results} most relevant and recent articles."
        )

        try:
            response = await self._client.post(
                "/chat/completions",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SONAR_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2048,
                    "search_context_size": "medium",  # Higher context for search
                    "search_recency_filter": "week",
                },
            )
            response.raise_for_status()
            data = response.json()

            citations = data.get("citations", [])
            search_results = data.get("search_results", [])
            content = data["choices"][0]["message"]["content"]
            articles_data = self._parse_json_response(content)

            self._consecutive_errors = 0
            return self._map_articles(articles_data, citations, search_results)

        except Exception as e:
            self._handle_error(e)
            logger.error("Sonar search failed for query=%s: %s", query, e)
            return []

    def _parse_json_response(self, content: str) -> list[dict[str, Any]]:
        """Parse structured JSON from Sonar response, handling edge cases."""
        # Strip markdown fences if present
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "articles" in parsed:
                return parsed["articles"]
            if isinstance(parsed, list):
                return parsed
            return []
        except json.JSONDecodeError:
            logger.warning("Failed to parse Sonar JSON response: %s...", cleaned[:200])
            return []

    def _map_articles(
        self,
        articles_data: list[dict],
        citations: list[str],
        search_results: list[dict],
    ) -> list[RawArticle]:
        """Map Sonar response to RawArticle domain objects."""
        articles = []
        for art in articles_data:
            try:
                published_str = art.get("published_date", "")
                try:
                    published_at = datetime.strptime(published_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    published_at = datetime.now(timezone.utc)

                # Try to find image from search_results
                image_url = art.get("image_url")
                if not image_url:
                    for sr in search_results:
                        if sr.get("url") == art.get("source_url"):
                            image_url = sr.get("image_url")
                            break

                articles.append(
                    RawArticle(
                        title=art["title"],
                        summary=art.get("summary"),
                        source_name=art.get("source_name", "Unknown"),
                        source_url=art.get("source_url", ""),
                        published_at=published_at,
                        image_url=image_url,
                        citations=citations,
                        tags=art.get("tags", []),
                        sentiment=art.get("sentiment", "neutral"),
                        relevance_score=0.8,  # Sonar articles are high quality
                    )
                )
            except (KeyError, TypeError) as e:
                logger.debug("Skipping malformed Sonar article: %s", e)
                continue

        return articles

    def _handle_error(self, error: Exception) -> None:
        """Circuit breaker: disable after 10 consecutive errors."""
        self._consecutive_errors += 1
        if self._consecutive_errors >= 10:
            self._available = False
            logger.critical(
                "Sonar adapter disabled after %d consecutive errors: %s",
                self._consecutive_errors,
                error,
            )

    async def close(self) -> None:
        await self._client.aclose()
```

### 6.2 NewsAPI Adapter (FALLBACK)

```python
"""NewsAPI.org adapter — fallback news provider."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from domain.ports.discovery.news_fetcher_port import NewsFetcherPort, RawArticle
from infrastructure.config import settings

logger = logging.getLogger(__name__)


class NewsAPIAdapter(NewsFetcherPort):
    """NewsAPI.org — general news aggregator. Free: 100 req/day, Paid: 1000 req/day."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.NEWSAPI_KEY
        self._base_url = "https://newsapi.org/v2"
        self._available = self._api_key is not None
        self._client = httpx.AsyncClient(timeout=15.0)

    @property
    def provider_slug(self) -> str:
        return "newsapi"

    @property
    def is_available(self) -> bool:
        return self._available

    async def fetch_news(
        self,
        keywords: list[str],
        section_slug: str,
        max_results: int = 20,
    ) -> list[RawArticle]:
        if not self.is_available:
            return []

        try:
            query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
            resp = await self._client.get(
                f"{self._base_url}/everything",
                params={
                    "q": query,
                    "pageSize": min(max_results, 50),
                    "sortBy": "publishedAt",
                    "language": "en",
                    "apiKey": self._api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            return [
                RawArticle(
                    title=a["title"],
                    summary=a.get("description"),
                    source_name=a.get("source", {}).get("name", "Unknown"),
                    source_url=a["url"],
                    published_at=datetime.fromisoformat(
                        a["publishedAt"].replace("Z", "+00:00")
                    ),
                    image_url=a.get("urlToImage"),
                    author=a.get("author"),
                    external_id=a["url"],
                    relevance_score=0.6,
                )
                for a in data.get("articles", [])
                if a.get("title") and a["title"] != "[Removed]"
            ]

        except Exception as e:
            logger.error("NewsAPI fetch failed: %s", e)
            return []

    async def search_news(self, query: str, max_results: int = 20) -> list[RawArticle]:
        return await self.fetch_news([query], "search", max_results)

    async def close(self) -> None:
        await self._client.aclose()
```

### 6.3 CryptoPanic Adapter (FALLBACK — Crypto)

```python
"""CryptoPanic adapter — crypto-specific news."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from domain.ports.discovery.news_fetcher_port import NewsFetcherPort, RawArticle
from infrastructure.config import settings

logger = logging.getLogger(__name__)


class CryptoPanicAdapter(NewsFetcherPort):
    """CryptoPanic — crypto-focused news aggregator."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.CRYPTOPANIC_KEY
        self._base_url = "https://cryptopanic.com/api/v1"
        self._available = self._api_key is not None
        self._client = httpx.AsyncClient(timeout=15.0)

    @property
    def provider_slug(self) -> str:
        return "cryptopanic"

    @property
    def is_available(self) -> bool:
        return self._available

    async def fetch_news(
        self,
        keywords: list[str],
        section_slug: str,
        max_results: int = 20,
    ) -> list[RawArticle]:
        if not self.is_available:
            return []

        try:
            params: dict = {
                "auth_token": self._api_key,
                "filter": "important",
                "public": "true",
            }
            # CryptoPanic supports currency filtering
            crypto_keywords = [k for k in keywords if len(k) <= 5 and k.isupper()]
            if crypto_keywords:
                params["currencies"] = ",".join(crypto_keywords[:5])

            resp = await self._client.get(f"{self._base_url}/posts/", params=params)
            resp.raise_for_status()
            data = resp.json()

            articles = []
            for post in data.get("results", [])[:max_results]:
                try:
                    articles.append(
                        RawArticle(
                            title=post["title"],
                            summary=None,
                            source_name=post.get("source", {}).get("title", "CryptoPanic"),
                            source_url=post.get("url", post.get("domain", "")),
                            published_at=datetime.fromisoformat(
                                post["published_at"].replace("Z", "+00:00")
                            ),
                            external_id=str(post.get("id")),
                            tags=["crypto"],
                            sentiment=self._map_sentiment(post.get("votes", {})),
                            relevance_score=0.7,
                        )
                    )
                except (KeyError, TypeError):
                    continue

            return articles

        except Exception as e:
            logger.error("CryptoPanic fetch failed: %s", e)
            return []

    async def search_news(self, query: str, max_results: int = 20) -> list[RawArticle]:
        return await self.fetch_news([query], "search", max_results)

    @staticmethod
    def _map_sentiment(votes: dict) -> str:
        positive = votes.get("positive", 0)
        negative = votes.get("negative", 0)
        if positive > negative * 2:
            return "positive"
        if negative > positive * 2:
            return "negative"
        return "neutral"

    async def close(self) -> None:
        await self._client.aclose()
```

### 6.4 DeFiLlama Adapter (Vaults)

```python
"""DeFiLlama adapter — vault/yield data."""
from __future__ import annotations

import logging

import httpx

from domain.ports.discovery.vault_fetcher_port import VaultFetcherPort, RawVault

logger = logging.getLogger(__name__)

PROTOCOL_DISPLAY = {
    "morpho": "Morpho",
    "aave-v3": "Aave V3",
    "compound-v3": "Compound V3",
    "yearn-v3": "Yearn V3",
    "spark": "Spark",
}

CHAIN_DISPLAY = {
    "Base": "Base",
    "Ethereum": "Ethereum",
    "Arbitrum": "Arbitrum",
    "Polygon": "Polygon",
    "Optimism": "Optimism",
}


class DeFiLlamaAdapter(VaultFetcherPort):
    """DeFiLlama yield pools — free, no API key, rate limited."""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=20.0)
        self._base_url = "https://yields.llama.fi"

    async def fetch_vaults(
        self,
        protocols: list[str] | None = None,
        chains: list[str] | None = None,
        min_tvl: float = 100_000,
    ) -> list[RawVault]:
        protocols = protocols or ["morpho", "aave-v3", "compound-v3"]
        chains = chains or ["Base", "Ethereum"]

        try:
            resp = await self._client.get(f"{self._base_url}/pools")
            resp.raise_for_status()
            pools = resp.json().get("data", [])

            vaults = []
            for pool in pools:
                if (
                    pool.get("project") in protocols
                    and pool.get("chain") in chains
                    and (pool.get("tvlUsd") or 0) >= min_tvl
                    and pool.get("apy") is not None
                    and pool["apy"] > 0
                ):
                    # Extract asset symbol from pool symbol
                    symbol_raw = pool.get("symbol", "")
                    asset = symbol_raw.split("-")[0].split("/")[0].upper() if symbol_raw else "UNKNOWN"

                    vaults.append(
                        RawVault(
                            protocol=pool["project"],
                            vault_name=f"{PROTOCOL_DISPLAY.get(pool['project'], pool['project'])} {asset}",
                            chain=pool["chain"].lower(),
                            asset_symbol=asset,
                            supply_apy=round(pool["apy"], 4),
                            reward_apy=round(pool.get("apyReward") or 0, 4),
                            tvl_usd=pool.get("tvlUsd", 0),
                            vault_address=pool.get("pool"),
                            risk_level=self._classify_risk(pool),
                            is_curated=pool["project"] in {"morpho", "aave-v3"},
                        )
                    )

            # Sort by total APY desc, keep top 50
            vaults.sort(key=lambda v: v.supply_apy + v.reward_apy, reverse=True)
            return vaults[:50]

        except Exception as e:
            logger.error("DeFiLlama fetch failed: %s", e)
            return []

    @staticmethod
    def _classify_risk(pool: dict) -> str:
        apy = pool.get("apy", 0)
        tvl = pool.get("tvlUsd", 0)
        if apy > 100 or tvl < 500_000:
            return "high"
        if apy > 20 or tvl < 5_000_000:
            return "medium"
        return "low"

    async def close(self) -> None:
        await self._client.aclose()
```

---

## 7. Application Layer

### 7.1 queries/discovery/get_interests.py

```python
"""Get user interests with section tree, respecting admin toggles."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from domain.ports.discovery.section_repository import SectionRepositoryPort
from domain.ports.discovery.interest_repository import InterestRepositoryPort


@dataclass
class InterestSubsectionDTO:
    id: str
    slug: str
    name: str
    is_enabled: bool


@dataclass
class InterestSectionDTO:
    id: str
    slug: str
    name: str
    icon: str | None
    is_enabled: bool
    subsections: list[InterestSubsectionDTO]


@dataclass
class InterestsResponseDTO:
    sections: list[InterestSectionDTO]


class GetUserInterestsQuery:
    """Returns the full section tree with user's enabled/disabled state."""

    def __init__(
        self,
        section_repo: SectionRepositoryPort,
        interest_repo: InterestRepositoryPort,
    ):
        self._section_repo = section_repo
        self._interest_repo = interest_repo

    async def execute(self, user_id: uuid.UUID, category_slug: str = "news") -> InterestsResponseDTO:
        # 1. Get all ACTIVE sections for this category (admin-controlled)
        top_level = await self._section_repo.get_active_top_level(category_slug)
        all_subsections = await self._section_repo.get_active_subsections(category_slug)

        # 2. Get user's explicit preferences
        user_interests = await self._interest_repo.get_user_interests(user_id)
        user_map: dict[uuid.UUID, bool] = {
            ui.section_id: ui.is_enabled for ui in user_interests
        }

        # 3. Build tree — if no explicit preference, use section default
        result_sections: list[InterestSectionDTO] = []

        for section in top_level:
            children = [s for s in all_subsections if s.parent_id == section.id]

            sub_dtos = [
                InterestSubsectionDTO(
                    id=str(sub.id),
                    slug=sub.slug,
                    name=sub.name,
                    is_enabled=user_map.get(sub.id, sub.is_default),
                )
                for sub in children
            ]

            result_sections.append(
                InterestSectionDTO(
                    id=str(section.id),
                    slug=section.slug,
                    name=section.name,
                    icon=section.icon,
                    is_enabled=user_map.get(section.id, section.is_default),
                    subsections=sub_dtos,
                )
            )

        return InterestsResponseDTO(sections=result_sections)
```

### 7.2 queries/discovery/get_news_feed.py

```python
"""Personalized news feed: user interests → adjacent → trending."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from domain.entities.discovery.news_article import NewsArticle
from domain.ports.discovery.interest_repository import InterestRepositoryPort
from domain.ports.discovery.news_repository import NewsRepositoryPort
from domain.ports.discovery.section_repository import SectionRepositoryPort


@dataclass
class NewsArticleDTO:
    id: str
    title: str
    summary: str | None
    image_url: str | None
    source_name: str
    source_url: str
    section_slug: str | None
    section_name: str | None
    parent_section_slug: str | None
    published_at: str
    time_ago: str
    tags: list[str]
    sentiment: str


@dataclass
class NewsFeedResponseDTO:
    articles: list[NewsArticleDTO]
    page: int
    page_size: int
    total: int
    has_more: bool
    feed_type: str  # "personalized" | "adjacent" | "trending"


class GetNewsFeedQuery:
    """Three-tier feed: personalized → adjacent → trending."""

    def __init__(
        self,
        interest_repo: InterestRepositoryPort,
        news_repo: NewsRepositoryPort,
        section_repo: SectionRepositoryPort,
    ):
        self._interest_repo = interest_repo
        self._news_repo = news_repo
        self._section_repo = section_repo

    async def execute(
        self,
        user_id: uuid.UUID | None,
        page: int = 1,
        page_size: int = 20,
        section_filter: str | None = None,
    ) -> NewsFeedResponseDTO:
        page_size = min(page_size, 50)
        offset = (page - 1) * page_size

        # 1. Get user's enabled section IDs
        user_section_ids: list[uuid.UUID] = []
        parent_slugs: list[str] = []
        feed_type = "trending"

        if user_id:
            enabled_interests = await self._interest_repo.get_enabled_section_ids(user_id)
            if enabled_interests:
                user_section_ids = enabled_interests
                feed_type = "personalized"

        # 2. If section filter, narrow to that section
        if section_filter:
            section = await self._section_repo.get_by_slug(section_filter)
            if section:
                if section.is_top_level:
                    # Get all subsection IDs under this parent
                    subsections = await self._section_repo.get_children(section.id)
                    user_section_ids = [s.id for s in subsections]
                else:
                    user_section_ids = [section.id]

        # 3. Fetch personalized articles
        articles: list[NewsArticle] = []
        if user_section_ids:
            articles = await self._news_repo.get_feed(
                section_ids=user_section_ids,
                limit=page_size,
                offset=offset,
            )

        # 4. Adjacent fill — sibling sections
        if len(articles) < page_size and user_section_ids:
            remaining = page_size - len(articles)
            existing_ids = {a.id for a in articles}
            parent_slugs = await self._section_repo.get_parent_slugs(user_section_ids)

            adjacent = await self._news_repo.get_adjacent_articles(
                exclude_section_ids=user_section_ids,
                parent_section_slugs=parent_slugs,
                limit=remaining,
            )
            articles.extend([a for a in adjacent if a.id not in existing_ids])
            if adjacent:
                feed_type = "adjacent" if not articles[:page_size] else feed_type

        # 5. Trending fill — highest relevance across all sections
        if len(articles) < page_size:
            remaining = page_size - len(articles)
            existing_ids = {a.id for a in articles}
            trending = await self._news_repo.get_trending(limit=remaining)
            articles.extend([a for a in trending if a.id not in existing_ids])
            if not user_section_ids:
                feed_type = "trending"

        # 6. Section name resolution
        section_names = await self._section_repo.get_slug_name_map()

        # 7. Map to DTOs
        article_dtos = [
            NewsArticleDTO(
                id=str(a.id),
                title=a.title,
                summary=a.summary,
                image_url=a.image_url,
                source_name=a.source_name,
                source_url=a.source_url,
                section_slug=a.section_slug,
                section_name=section_names.get(a.section_slug),
                parent_section_slug=a.parent_section_slug,
                published_at=a.published_at.isoformat(),
                time_ago=a.time_ago,
                tags=a.tags,
                sentiment=a.sentiment,
            )
            for a in articles[:page_size]
        ]

        return NewsFeedResponseDTO(
            articles=article_dtos,
            page=page,
            page_size=page_size,
            total=len(article_dtos),  # Approximate; exact count is expensive
            has_more=len(articles) >= page_size,
            feed_type=feed_type,
        )
```

### 7.3 queries/discovery/search_news.py

```python
"""Search news — hybrid: Perplexity Sonar (real-time) + PostgreSQL FTS (cached)."""
from __future__ import annotations

import asyncio
import uuid

from domain.ports.discovery.news_fetcher_port import NewsFetcherPort
from domain.ports.discovery.news_repository import NewsRepositoryPort

from .get_news_feed import NewsArticleDTO, NewsFeedResponseDTO


class SearchNewsQuery:
    """Hybrid search: fast DB results + Sonar real-time enrichment."""

    def __init__(
        self,
        news_repo: NewsRepositoryPort,
        sonar_adapter: NewsFetcherPort,
    ):
        self._news_repo = news_repo
        self._sonar = sonar_adapter

    async def execute(
        self,
        query: str,
        user_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
        section_filter: str | None = None,
    ) -> NewsFeedResponseDTO:
        page_size = min(page_size, 50)
        offset = (page - 1) * page_size

        # Parallel: DB full-text + Sonar real-time
        db_task = self._news_repo.search(
            query=query,
            section_ids=None,
            limit=page_size,
            offset=offset,
        )
        sonar_task = self._sonar.search_news(query=query, max_results=10)

        (db_articles, db_total), sonar_raw = await asyncio.gather(
            db_task,
            sonar_task,
            return_exceptions=True,
        )

        # Handle exceptions gracefully
        if isinstance(db_articles, Exception):
            db_articles, db_total = [], 0
        if isinstance(sonar_raw, Exception):
            sonar_raw = []

        # Merge: DB results first (fast), then Sonar results (fresh)
        seen_hashes: set[str] = set()
        merged: list[NewsArticleDTO] = []

        for a in db_articles:
            h = a.content_hash if hasattr(a, "content_hash") else a.title
            if h not in seen_hashes:
                seen_hashes.add(h)
                merged.append(
                    NewsArticleDTO(
                        id=str(a.id),
                        title=a.title,
                        summary=a.summary,
                        image_url=a.image_url,
                        source_name=a.source_name,
                        source_url=a.source_url,
                        section_slug=a.section_slug,
                        section_name=None,
                        parent_section_slug=a.parent_section_slug,
                        published_at=a.published_at.isoformat(),
                        time_ago=a.time_ago,
                        tags=a.tags,
                        sentiment=a.sentiment,
                    )
                )

        # Append fresh Sonar results not in DB
        for raw in sonar_raw:
            from domain.entities.discovery.news_article import NewsArticle
            h = NewsArticle.compute_hash(raw.title, raw.source_url)
            if h not in seen_hashes and len(merged) < page_size:
                seen_hashes.add(h)
                merged.append(
                    NewsArticleDTO(
                        id="sonar-" + h[:12],
                        title=raw.title,
                        summary=raw.summary,
                        image_url=raw.image_url,
                        source_name=raw.source_name,
                        source_url=raw.source_url,
                        section_slug=None,
                        section_name=None,
                        parent_section_slug=None,
                        published_at=raw.published_at.isoformat(),
                        time_ago="",
                        tags=raw.tags,
                        sentiment=raw.sentiment,
                    )
                )

        return NewsFeedResponseDTO(
            articles=merged[:page_size],
            page=page,
            page_size=page_size,
            total=db_total + len(sonar_raw),
            has_more=db_total > offset + page_size,
            feed_type="search",
        )
```

---

## 8. Presentation Layer (API Endpoints)

### 8.1 controllers/discovery/interests.py

```python
"""GET + PUT user interests endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from application.queries.discovery.get_interests import GetUserInterestsQuery
from application.commands.discovery.save_interests import SaveUserInterestsCommand
from presentation.http.dependencies import get_current_user, get_query, get_command

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


# ─── Response Models ───

class SubsectionResponse(BaseModel):
    id: str
    slug: str
    name: str
    is_enabled: bool


class SectionResponse(BaseModel):
    id: str
    slug: str
    name: str
    icon: str | None = None
    is_enabled: bool
    subsections: list[SubsectionResponse]


class InterestsResponse(BaseModel):
    sections: list[SectionResponse]


# ─── Request Models ───

class InterestToggle(BaseModel):
    section_id: str
    is_enabled: bool


class SaveInterestsRequest(BaseModel):
    interests: list[InterestToggle] = Field(..., min_length=1, max_length=200)


class SaveInterestsResponse(BaseModel):
    saved: int
    message: str


# ─── Endpoints ───

@router.get("/interests", response_model=InterestsResponse)
async def get_user_interests(
    user=Depends(get_current_user),
    query: GetUserInterestsQuery = Depends(get_query(GetUserInterestsQuery)),
):
    """Get user's interest tree with enabled/disabled states."""
    result = await query.execute(user_id=user.id)
    return InterestsResponse(
        sections=[
            SectionResponse(
                id=s.id,
                slug=s.slug,
                name=s.name,
                icon=s.icon,
                is_enabled=s.is_enabled,
                subsections=[
                    SubsectionResponse(
                        id=sub.id,
                        slug=sub.slug,
                        name=sub.name,
                        is_enabled=sub.is_enabled,
                    )
                    for sub in s.subsections
                ],
            )
            for s in result.sections
        ]
    )


@router.put("/interests", response_model=SaveInterestsResponse)
async def save_user_interests(
    body: SaveInterestsRequest,
    user=Depends(get_current_user),
    command: SaveUserInterestsCommand = Depends(get_command(SaveUserInterestsCommand)),
):
    """Save user's interest preferences (UPSERT)."""
    saved = await command.execute(
        user_id=user.id,
        interests=[
            {"section_id": t.section_id, "is_enabled": t.is_enabled}
            for t in body.interests
        ],
    )
    return SaveInterestsResponse(saved=saved, message="Interests updated successfully")
```

### 8.2 controllers/discovery/news_feed.py

```python
"""GET /discovery/news — personalized news feed."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from application.queries.discovery.get_news_feed import GetNewsFeedQuery
from presentation.http.dependencies import get_current_user_optional, get_query

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


@router.get("/news")
async def get_news_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    section: str | None = Query(None, description="Filter by section slug"),
    user=Depends(get_current_user_optional),
    query: GetNewsFeedQuery = Depends(get_query(GetNewsFeedQuery)),
):
    """Personalized news feed with adjacent/trending fallback."""
    user_id = user.id if user else None
    return await query.execute(
        user_id=user_id,
        page=page,
        page_size=page_size,
        section_filter=section,
    )
```

### 8.3 controllers/discovery/news_search.py

```python
"""GET /discovery/news/search — hybrid search endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException

from application.queries.discovery.search_news import SearchNewsQuery
from presentation.http.dependencies import get_current_user_optional, get_query

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


@router.get("/news/search")
async def search_news(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    section: str | None = Query(None),
    user=Depends(get_current_user_optional),
    query: SearchNewsQuery = Depends(get_query(SearchNewsQuery)),
):
    """Hybrid search: PostgreSQL FTS (cached) + Perplexity Sonar (real-time)."""
    user_id = user.id if user else None
    return await query.execute(
        query=q,
        user_id=user_id,
        page=page,
        page_size=page_size,
        section_filter=section,
    )
```

### 8.4 controllers/discovery/vaults.py

```python
"""GET /discovery/vaults — DeFi vault opportunities."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from application.queries.discovery.get_vaults import GetVaultsQuery
from presentation.http.dependencies import get_query

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


class VaultCardResponse(BaseModel):
    id: str
    protocol: str
    protocol_display: str
    vault_name: str
    chain: str
    chain_name: str
    asset_symbol: str
    supply_apy: float
    reward_apy: float
    total_apy: float
    tvl_usd: str
    risk_level: str
    is_curated: bool
    cta: str
    intent_trigger: str


class VaultsResponse(BaseModel):
    vaults: list[VaultCardResponse]
    updated_at: str


@router.get("/vaults", response_model=VaultsResponse)
async def get_vaults(
    sort: str = Query("apy_desc", regex="^(apy_desc|tvl_desc|risk_asc)$"),
    chain: str | None = Query(None),
    asset: str | None = Query(None),
    query: GetVaultsQuery = Depends(get_query(GetVaultsQuery)),
):
    """Today's DeFi vault opportunities sorted by APY, TVL, or risk."""
    return await query.execute(sort=sort, chain=chain, asset=asset)
```

---

## 9. Celery Workers

### 9.1 tasks/discovery_tasks.py

```python
"""
Discovery module Celery workers — news collection & vault snapshot pipeline.

Architecture:
  Beat → collect_news_all_sections (fan-out) → collect_section_news (per-section)
  Beat → collect_vault_snapshots
  Beat → cleanup_expired_articles
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from celery.schedules import crontab

from infrastructure.adapters.discovery.perplexity_sonar import PerplexitySonarAdapter
from infrastructure.adapters.discovery.newsapi_adapter import NewsAPIAdapter
from infrastructure.adapters.discovery.cryptopanic_adapter import CryptoPanicAdapter
from infrastructure.adapters.discovery.defillama_adapter import DeFiLlamaAdapter
from infrastructure.config import settings

logger = logging.getLogger(__name__)


# ─── Beat Schedule ───

DISCOVERY_BEAT_SCHEDULE = {
    "discovery-collect-news": {
        "task": "tasks.discovery_tasks.collect_news_all_sections",
        "schedule": crontab(minute="*/15"),  # Every 15 min
    },
    "discovery-collect-vaults": {
        "task": "tasks.discovery_tasks.collect_vault_snapshots",
        "schedule": crontab(minute="*/5"),   # Every 5 min
    },
    "discovery-cleanup-expired": {
        "task": "tasks.discovery_tasks.cleanup_expired_articles",
        "schedule": crontab(hour=3, minute=0),  # Daily 3 AM
    },
}


# ─── Fan-Out: Dispatch per-section collection ───

@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def collect_news_all_sections(self):
    """Fan-out: spawn one collect_section_news per active leaf section."""
    from infrastructure.persistence.discovery.section_sqla import SectionSQLARepository

    repo = SectionSQLARepository()
    sections = asyncio.get_event_loop().run_until_complete(
        repo.get_active_leaf_sections()
    )

    dispatched = 0
    for section in sections:
        collect_section_news.delay(
            section_id=str(section.id),
            section_slug=section.slug,
            parent_slug=section.parent_id and str(section.parent_id),
            keywords=section.keywords,
        )
        dispatched += 1

    logger.info("Dispatched %d section collection tasks", dispatched)
    return dispatched


# ─── Per-Section Collection ───

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    rate_limit="4/m",  # Max 4 sections/minute to respect Sonar RPM
    queue="news-collection",
)
def collect_section_news(
    self,
    section_id: str,
    section_slug: str,
    parent_slug: str | None,
    keywords: list[str],
):
    """
    Collect news for ONE section from providers in priority order:
    1. Perplexity Sonar (primary) — real-time, high quality
    2. NewsAPI / CryptoPanic (fallback) — if Sonar fails or rate limited
    3. RSS (last resort) — always available
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(
            _collect_section_async(section_id, section_slug, parent_slug, keywords)
        )
    finally:
        loop.close()


async def _collect_section_async(
    section_id: str,
    section_slug: str,
    parent_slug: str | None,
    keywords: list[str],
) -> int:
    """Async news collection with provider failover."""
    from infrastructure.persistence.discovery.news_sqla import NewsSQLARepository
    from domain.entities.discovery.news_article import NewsArticle
    import uuid

    news_repo = NewsSQLARepository()
    articles_saved = 0

    # Provider chain: Sonar → fallback
    providers = []

    # 1. Perplexity Sonar (primary)
    sonar = PerplexitySonarAdapter()
    if sonar.is_available:
        providers.append(("sonar", sonar))

    # 2. Fallbacks based on section type
    if parent_slug in ("crypto_defi",):
        crypto = CryptoPanicAdapter()
        if crypto.is_available:
            providers.append(("cryptopanic", crypto))
    else:
        newsapi = NewsAPIAdapter()
        if newsapi.is_available:
            providers.append(("newsapi", newsapi))

    # Fetch from first available provider
    raw_articles = []
    provider_used = "none"

    for slug, provider in providers:
        try:
            raw_articles = await provider.fetch_news(
                keywords=keywords,
                section_slug=section_slug,
                max_results=15,
            )
            if raw_articles:
                provider_used = slug
                break
        except Exception as e:
            logger.warning("Provider %s failed for %s: %s", slug, section_slug, e)
            continue
        finally:
            await provider.close()

    # Deduplicate and store
    for raw in raw_articles:
        content_hash = NewsArticle.compute_hash(raw.title, raw.source_url)

        article = NewsArticle(
            id=uuid.uuid4(),
            title=raw.title,
            summary=raw.summary,
            image_url=raw.image_url,
            source_name=raw.source_name,
            source_url=raw.source_url,
            author=raw.author,
            citations=raw.citations,
            published_at=raw.published_at,
            content_hash=content_hash,
            section_id=uuid.UUID(section_id),
            section_slug=section_slug,
            parent_section_slug=parent_slug,
            tags=raw.tags,
            sentiment=raw.sentiment,
            relevance_score=raw.relevance_score,
        )

        was_new = await news_repo.upsert_article(article, provider_id=None)
        if was_new:
            articles_saved += 1

    logger.info(
        "Section %s: fetched=%d saved=%d provider=%s",
        section_slug,
        len(raw_articles),
        articles_saved,
        provider_used,
    )
    return articles_saved


# ─── Vault Snapshots ───

@shared_task(bind=True, max_retries=2, queue="vault-refresh")
def collect_vault_snapshots(self):
    """Fetch vault data from DeFiLlama + Vaults.fyi."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_collect_vaults_async())
    finally:
        loop.close()


async def _collect_vaults_async() -> int:
    from infrastructure.persistence.discovery.vault_sqla import VaultSQLARepository
    from domain.entities.discovery.vault_snapshot import VaultSnapshot
    import uuid

    vault_repo = VaultSQLARepository()
    llama = DeFiLlamaAdapter()

    try:
        raw_vaults = await llama.fetch_vaults(
            protocols=["morpho", "aave-v3", "compound-v3"],
            chains=["Base", "Ethereum"],
            min_tvl=100_000,
        )
    finally:
        await llama.close()

    # Mark old snapshots inactive
    await vault_repo.deactivate_old_snapshots(max_age_hours=1)

    # Insert new snapshots
    saved = 0
    chain_display = {"base": "Base", "ethereum": "Ethereum"}

    for raw in raw_vaults:
        snapshot = VaultSnapshot(
            id=uuid.uuid4(),
            protocol=raw.protocol,
            protocol_display=raw.vault_name.split(" ")[0],
            vault_name=raw.vault_name,
            chain=raw.chain,
            chain_name=chain_display.get(raw.chain, raw.chain.title()),
            asset_symbol=raw.asset_symbol,
            supply_apy=raw.supply_apy,
            reward_apy=raw.reward_apy,
            tvl_usd=raw.tvl_usd,
            risk_level=raw.risk_level,
            is_curated=raw.is_curated,
            vault_address=raw.vault_address,
        )
        await vault_repo.upsert_snapshot(snapshot)
        saved += 1

    logger.info("Vault snapshots: fetched=%d saved=%d", len(raw_vaults), saved)
    return saved


# ─── Cleanup ───

@shared_task(queue="default")
def cleanup_expired_articles():
    """Remove articles older than 30 days."""
    from infrastructure.persistence.discovery.news_sqla import NewsSQLARepository

    repo = NewsSQLARepository()
    loop = asyncio.new_event_loop()
    deleted = loop.run_until_complete(repo.delete_older_than(days=30))
    loop.close()

    logger.info("Cleaned up %d expired articles", deleted)
    return deleted
```

---

## 10. Perplexity Sonar Integration — Key Details

### 10.1 API Contract

```
POST https://api.perplexity.ai/chat/completions
Authorization: Bearer {PERPLEXITY_API_KEY}

Request:
{
  "model": "sonar",
  "messages": [
    {"role": "system", "content": "...structured JSON prompt..."},
    {"role": "user", "content": "Find latest news about: AI, machine learning"}
  ],
  "temperature": 0.1,
  "max_tokens": 2048,
  "search_context_size": "low",        // "low"|"medium"|"high"
  "search_recency_filter": "day"        // "day"|"week"|"month"|"year"
}

Response:
{
  "id": "...",
  "model": "sonar",
  "choices": [{"message": {"role": "assistant", "content": "{...JSON...}"}}],
  "citations": ["https://reuters.com/...", "https://bbc.com/..."],
  "search_results": [{"title":"...","url":"...","snippet":"..."}],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 800,
    "search_context_size": "low",
    "cost": {"total_cost": 0.006}
  }
}
```

### 10.2 Cost Optimization Strategy

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| Use `search_context_size: "low"` for collection | Lower retrieval cost per request | ~40% |
| Use `search_context_size: "medium"` for user search | Better results when user is waiting | Acceptable |
| Batch by parent section | "politics" keywords combined, not per-subsection | ~60% fewer requests |
| Cache search results 30s | Redis cache on search query hash | ~50% fewer search calls |
| Circuit breaker on 402 | Stop immediately if credits run out | Prevents runaway cost |
| Rate limit: 4 sections/min in Celery | Stay under 50 RPM | Prevents 429s |

### 10.3 Provider Failover Chain

```
Request → Perplexity Sonar (primary)
             │
             ├── 200 OK → Use articles ✓
             │
             ├── 429 Rate Limited → NewsAPI/CryptoPanic (fallback)
             │                          │
             │                          ├── 200 OK → Use articles ✓
             │                          └── Failed → RSS feeds (last resort)
             │
             ├── 402 Insufficient Credits → Disable Sonar, alert admin
             │                              └── Fallback chain continues
             │
             └── 5xx / Timeout → Increment error counter
                                  │
                                  ├── < 10 errors → Retry with backoff
                                  └── ≥ 10 errors → Disable Sonar (circuit breaker)
```

---

## 11. Admin Endpoints

### 11.1 Category Management

```python
# POST /api/v1/admin/discovery/categories
{
    "slug": "alpha_signals",
    "name": "Alpha Signals",
    "icon": "signal",
    "is_active": true,
    "is_default": false
}

# PATCH /api/v1/admin/discovery/categories/{slug}
{
    "is_active": false  # Disables entire tab for ALL users
}
```

### 11.2 Section Management

```python
# POST /api/v1/admin/discovery/sections
{
    "category_slug": "news",
    "parent_slug": "tech_science",   # null = top-level
    "slug": "quantum_computing",
    "name": "Quantum Computing",
    "is_active": true,
    "metadata": {"keywords": ["quantum", "qubit", "quantum computing", "ibm quantum"]}
}

# PATCH /api/v1/admin/discovery/sections/{id}
{
    "is_active": false,    # Hides from ALL users
    "is_default": true     # Auto-enable for new users
}

# DELETE /api/v1/admin/discovery/sections/{id}  — soft delete
```

### 11.3 Provider Management

```python
# PATCH /api/v1/admin/discovery/providers/{slug}
{
    "is_active": false,              # Disable provider
    "rate_limit_per_minute": 30,     # Throttle
    "config": {"model": "sonar-pro"} # Upgrade model
}

# GET /api/v1/admin/discovery/providers
# Returns: all providers with health stats (error_count, last_fetched_at, daily_request_count)
```

Admin auth requires `system_admin` or `content_admin` role from `admin_roles` table.

---

## 12. Caching Strategy

```python
# Redis key patterns and TTLs

CACHE_KEYS = {
    # Static config (admin-controlled)
    "discovery:categories":              {"ttl": 300,  "desc": "Active categories list"},
    "discovery:sections:{category}":     {"ttl": 300,  "desc": "Section tree per category"},

    # User-specific
    "discovery:interests:{user_id}":     {"ttl": 120,  "desc": "User interest toggles"},

    # Feed pages
    "discovery:feed:{user_id}:{page}:{section}": {"ttl": 60, "desc": "Personalized feed page"},

    # Search
    "discovery:search:{query_hash}":     {"ttl": 30,   "desc": "Search results"},

    # Vault snapshots
    "discovery:vaults:{sort}:{chain}":   {"ttl": 60,   "desc": "Vault list"},

    # Provider state
    "discovery:provider:{slug}:rpm":     {"ttl": 60,   "desc": "Rate limit counter (sliding window)"},
    "discovery:provider:{slug}:daily":   {"ttl": 86400, "desc": "Daily request counter"},
}
```

### Cache Invalidation

| Event | Invalidation |
|-------|-------------|
| User saves interests | Delete `discovery:interests:{user_id}`, `discovery:feed:{user_id}:*` |
| Admin toggles section | Delete `discovery:sections:*`, `discovery:feed:*` |
| Admin toggles category | Delete `discovery:categories`, `discovery:sections:*` |
| New articles collected | No explicit invalidation — feed TTL handles it (60s) |
| Vault snapshot refresh | Delete `discovery:vaults:*` |

---

## 13. Performance Targets

| Endpoint | Target | Strategy |
|----------|--------|----------|
| `GET /discovery/categories` | < 100ms | Redis cache 5 min |
| `GET /discovery/interests` | < 300ms | Redis cache 2 min |
| `PUT /discovery/interests` | < 200ms | Direct DB upsert |
| `GET /discovery/news` | < 800ms | Redis cache 1 min + indexed queries |
| `GET /discovery/news/search` | < 2s | Parallel: DB FTS + Sonar |
| `GET /discovery/vaults` | < 400ms | Redis cache 1 min |
| Celery: per-section collect | < 15s | Sonar timeout 30s, fallback 15s |
| Celery: full collection cycle | < 10 min | Fan-out, 4 sections/min rate |

---

## 14. Deployment Configuration

### 14.1 Environment Variables

```bash
# ─── Perplexity Sonar (PRIMARY) ───
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxx
PERPLEXITY_MODEL=sonar
PERPLEXITY_SEARCH_CONTEXT=low
PERPLEXITY_RPM_LIMIT=50

# ─── Fallback Providers ───
NEWSAPI_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CRYPTOPANIC_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VAULTSFYI_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ─── Celery ───
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

### 14.2 Celery Workers (x2gd EC2)

```bash
# News collection — rate-limited, IO bound
celery -A tasks worker -Q news-collection --concurrency=4 --pool=gevent -n news@%h

# Vault refresh — lighter load
celery -A tasks worker -Q vault-refresh --concurrency=2 --pool=gevent -n vaults@%h

# Default queue (cleanup, etc.)
celery -A tasks worker -Q default --concurrency=2 -n default@%h

# Beat scheduler
celery -A tasks beat --scheduler celery.beat:PersistentScheduler
```

### 14.3 Monitoring

```python
# Structured logging for cost tracking
{
    "event": "sonar_request",
    "section": "us_politics",
    "tokens_in": 150,
    "tokens_out": 800,
    "cost_usd": 0.006,
    "articles_returned": 12,
    "latency_ms": 2400,
    "provider": "perplexity_sonar"
}
```

---

## 15. GraphRAG News Contextualization

### 15.1 Why GraphRAG for Discovery News

The Discovery module collects thousands of news articles daily. Without contextualization, these are **flat text blobs** — agents can only do keyword matching. With GraphRAG, every article is decomposed into entities and relationships that feed the DeFi knowledge graph, enabling systemic reasoning across the entire agent squad.

**Before (flat):**
```
Article: "Aave pauses USDT lending after oracle delay"
Agent: Returns the article text verbatim. No deeper understanding.
```

**After (GraphRAG-contextualized):**
```
Article: "Aave pauses USDT lending after oracle delay"
Extracted:
  ├─ Entity: Aave (protocol, lending)
  ├─ Entity: USDT (token, stablecoin)
  ├─ Entity: Chainlink (oracle)
  ├─ Relationship: Aave --[USES_ORACLE]--> Chainlink
  ├─ Relationship: Aave --[PAUSED_ASSET]--> USDT
  ├─ Event: oracle_delay (risk_type: oracle_risk, severity: high)
  └─ Impact: All USDT positions on Aave at risk

Agent (to user with USDT on Aave):
  "Aave just paused USDT lending due to oracle delays.
   Your $5,200 USDT supply position may be affected.
   Consider withdrawing to avoid potential liquidation."
```

### 15.2 Architecture: News → Graph Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DISCOVERY → GRAPHRAG PIPELINE                         │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────┐
│ Celery Worker   │     │ Entity Extractor │     │ Knowledge Graph         │
│ (collect news)  │────▶│ (LLM extraction) │────▶│ (Neo4j / Apache AGE)   │
└─────────────────┘     └─────────────────┘     └────────────┬────────────┘
                                                              │
                                                              ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────┐
│ Agent Squad     │◀────│ Hybrid Retriever │◀────│ Graph + Vector Search   │
│ (all agents)    │     │ (graph + pgvec)  │     │                         │
└─────────────────┘     └─────────────────┘     └─────────────────────────┘
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Discovery Intelligence Agent (NEW)                                      │
│ - Contextualizes news for other agents                                  │
│ - Provides risk propagation analysis                                    │
│ - Surfaces non-obvious connections                                      │
│ - Feeds personalized alerts based on user portfolio                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 15.3 DeFi News Ontology (Entity Types + Relationships)

```python
# src/app/domain/services/graph/news_ontology.py

from enum import Enum


class NewsEntityType(Enum):
    """Entity types extracted from Discovery news articles."""

    PROTOCOL = "protocol"           # Aave, Compound, Uniswap, Morpho
    TOKEN = "token"                 # ETH, USDC, USDT, BTC
    CHAIN = "chain"                 # Ethereum, Base, Arbitrum, Polygon
    PERSON = "person"               # Vitalik, CZ, SBF, Gary Gensler
    ORGANIZATION = "organization"   # SEC, CFTC, Circle, Tether, BlackRock
    EVENT = "event"                 # Hack, exploit, upgrade, launch, airdrop
    RISK = "risk"                   # Oracle risk, smart contract risk, depeg risk
    REGULATION = "regulation"       # MiCA, SEC ruling, executive order
    METRIC = "metric"              # TVL, APY, volume, market cap
    AUDIT = "audit"                 # Trail of Bits, OpenZeppelin audit result


class NewsRelationshipType(Enum):
    """Relationships between entities extracted from news."""

    # Protocol relationships
    USES_ORACLE = "uses_oracle"             # Aave → Chainlink
    ACCEPTS_COLLATERAL = "accepts_collateral"  # Aave → USDC
    DEPENDS_ON = "depends_on"               # Protocol → Protocol
    COMPETES_WITH = "competes_with"         # Aave ↔ Compound
    DEPLOYED_ON = "deployed_on"             # Aave → Ethereum
    FORKED_FROM = "forked_from"             # Morpho → Aave

    # Event relationships
    AFFECTED_BY = "affected_by"             # Protocol → Event (hack, exploit)
    TRIGGERED_BY = "triggered_by"           # Event → Event (cascade)
    PAUSED_ASSET = "paused_asset"           # Protocol → Token
    UPGRADED_TO = "upgraded_to"             # Protocol v2 → v3

    # Regulatory
    REGULATED_BY = "regulated_by"           # Protocol → Organization
    SUBJECT_OF = "subject_of"              # Protocol → Regulation

    # Risk
    EXPOSES_RISK = "exposes_risk"           # Protocol → Risk type
    MITIGATES_RISK = "mitigates_risk"       # Audit → Risk

    # People & Orgs
    FOUNDED_BY = "founded_by"              # Protocol → Person
    INVESTED_IN = "invested_in"             # Organization → Protocol
    ANNOUNCED = "announced"                 # Person/Org → Event

    # News-specific
    MENTIONED_IN = "mentioned_in"           # Entity → Article
    SENTIMENT_ABOUT = "sentiment_about"     # Article → Entity (positive/negative)
```

### 15.4 Entity Extraction Adapter (LLM-Powered)

```python
# src/app/infrastructure/adapters/discovery/graphrag_extractor.py

"""
LLM-powered entity & relationship extractor for news articles.
Runs as Celery task after article collection.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from domain.entities.discovery.news_article import NewsArticle
from domain.services.graph.news_ontology import NewsEntityType, NewsRelationshipType
from infrastructure.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a DeFi knowledge graph extraction engine.
Given a news article, extract ALL entities and relationships.

Return ONLY valid JSON with this structure:
{
  "entities": [
    {
      "name": "Aave",
      "type": "protocol",
      "properties": {"tvl": "10B", "category": "lending", "chains": ["ethereum", "base"]}
    }
  ],
  "relationships": [
    {
      "source": "Aave",
      "target": "Chainlink",
      "type": "uses_oracle",
      "properties": {"confidence": 0.95, "context": "Aave relies on Chainlink for price feeds"}
    }
  ],
  "events": [
    {
      "name": "oracle_delay",
      "type": "risk_event",
      "severity": "high",
      "affected_entities": ["Aave", "USDT"],
      "timestamp": "2026-02-08"
    }
  ],
  "sentiment": {
    "overall": "negative",
    "entity_sentiments": [
      {"entity": "Aave", "sentiment": "negative", "reason": "paused lending"},
      {"entity": "USDT", "sentiment": "negative", "reason": "oracle concerns"}
    ]
  }
}

Entity types: protocol, token, chain, person, organization, event, risk, regulation, metric, audit
Relationship types: uses_oracle, accepts_collateral, depends_on, competes_with, deployed_on,
  forked_from, affected_by, triggered_by, paused_asset, upgraded_to, regulated_by, subject_of,
  exposes_risk, mitigates_risk, founded_by, invested_in, announced, mentioned_in, sentiment_about

Rules:
- Extract ALL entities mentioned, even if only referenced
- Include confidence score (0.0-1.0) on relationships
- Detect risk events and their severity (low/medium/high/critical)
- Identify sentiment per entity, not just overall
- Return ONLY the JSON, no markdown, no commentary"""


@dataclass
class ExtractedEntity:
    name: str
    entity_type: NewsEntityType
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedRelationship:
    source: str
    target: str
    relationship_type: NewsRelationshipType
    confidence: float = 0.8
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedEvent:
    name: str
    event_type: str
    severity: str
    affected_entities: list[str] = field(default_factory=list)
    timestamp: str | None = None


@dataclass
class ArticleGraphExtraction:
    """Complete extraction result from a single article."""

    article_id: str
    article_title: str
    entities: list[ExtractedEntity] = field(default_factory=list)
    relationships: list[ExtractedRelationship] = field(default_factory=list)
    events: list[ExtractedEvent] = field(default_factory=list)
    sentiment: dict[str, Any] = field(default_factory=dict)


class GraphRAGExtractor:
    """Extracts entities and relationships from news articles using LLM."""

    def __init__(
        self,
        llm_client=None,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ):
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def extract_from_article(self, article: NewsArticle) -> ArticleGraphExtraction:
        """Extract entities, relationships, and events from a single article."""
        user_prompt = f"""Article Title: {article.title}
Article Summary: {article.summary or 'N/A'}
Source: {article.source_name}
Section: {article.section_slug or 'general'}
Published: {article.published_at.isoformat()}
Tags: {', '.join(article.tags)}"""

        try:
            response = await self._llm_client.generate(
                model=self._model,
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                user_message=user_prompt,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )

            parsed = self._parse_response(response.content)
            return ArticleGraphExtraction(
                article_id=str(article.id),
                article_title=article.title,
                entities=parsed["entities"],
                relationships=parsed["relationships"],
                events=parsed["events"],
                sentiment=parsed["sentiment"],
            )

        except Exception as e:
            logger.error("GraphRAG extraction failed for article %s: %s", article.id, e)
            return ArticleGraphExtraction(
                article_id=str(article.id),
                article_title=article.title,
            )

    async def extract_batch(
        self,
        articles: list[NewsArticle],
        batch_size: int = 10,
    ) -> list[ArticleGraphExtraction]:
        """Extract from multiple articles in batches."""
        import asyncio

        results = []
        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]
            batch_results = await asyncio.gather(
                *[self.extract_from_article(a) for a in batch],
                return_exceptions=True,
            )
            for r in batch_results:
                if isinstance(r, ArticleGraphExtraction):
                    results.append(r)
                else:
                    logger.error("Batch extraction error: %s", r)

        return results

    def _parse_response(self, content: str) -> dict:
        """Parse LLM JSON response into structured extraction result."""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse extraction JSON: %s...", cleaned[:200])
            return {"entities": [], "relationships": [], "events": [], "sentiment": {}}

        entities = []
        for e in data.get("entities", []):
            try:
                entities.append(
                    ExtractedEntity(
                        name=e["name"],
                        entity_type=NewsEntityType(e["type"]),
                        properties=e.get("properties", {}),
                    )
                )
            except (KeyError, ValueError):
                continue

        relationships = []
        for r in data.get("relationships", []):
            try:
                relationships.append(
                    ExtractedRelationship(
                        source=r["source"],
                        target=r["target"],
                        relationship_type=NewsRelationshipType(r["type"]),
                        confidence=r.get("confidence", 0.8),
                        properties=r.get("properties", {}),
                    )
                )
            except (KeyError, ValueError):
                continue

        events = []
        for ev in data.get("events", []):
            try:
                events.append(
                    ExtractedEvent(
                        name=ev["name"],
                        event_type=ev.get("type", "unknown"),
                        severity=ev.get("severity", "medium"),
                        affected_entities=ev.get("affected_entities", []),
                        timestamp=ev.get("timestamp"),
                    )
                )
            except (KeyError, ValueError):
                continue

        return {
            "entities": entities,
            "relationships": relationships,
            "events": events,
            "sentiment": data.get("sentiment", {}),
        }
```

### 15.5 Graph Repository (Apache AGE / Neo4j)

```python
# src/app/infrastructure/persistence/discovery/graph_repository.py

"""
Knowledge graph persistence using Apache AGE (PostgreSQL extension).
Alternative: Neo4j if deployed separately.

Apache AGE runs INSIDE PostgreSQL — no extra infrastructure.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from infrastructure.adapters.discovery.graphrag_extractor import (
    ArticleGraphExtraction,
    ExtractedEntity,
    ExtractedRelationship,
)

logger = logging.getLogger(__name__)


class DiscoveryGraphRepository:
    """
    Persists extracted entities and relationships into the knowledge graph.
    Uses Apache AGE (graph extension for PostgreSQL) or Neo4j.
    """

    def __init__(self, db_session, graph_name: str = "discovery_graph"):
        self._session = db_session
        self._graph_name = graph_name

    async def initialize_graph(self) -> None:
        """Create the graph if it doesn't exist."""
        await self._session.execute(
            f"SELECT create_graph('{self._graph_name}');"
        )

    async def upsert_extraction(self, extraction: ArticleGraphExtraction) -> int:
        """
        Upsert all entities and relationships from an article extraction.
        Returns count of new edges created.
        """
        edges_created = 0

        # 1. Upsert entities (nodes)
        for entity in extraction.entities:
            await self._upsert_entity(entity, extraction.article_id)

        # 2. Upsert relationships (edges)
        for rel in extraction.relationships:
            was_new = await self._upsert_relationship(rel, extraction.article_id)
            if was_new:
                edges_created += 1

        # 3. Create MENTIONED_IN edges (article → entity)
        for entity in extraction.entities:
            await self._create_mention_edge(
                entity.name,
                extraction.article_id,
                extraction.sentiment.get("entity_sentiments", []),
            )

        logger.info(
            "Graph upsert: article=%s entities=%d relationships=%d edges_new=%d",
            extraction.article_id[:8],
            len(extraction.entities),
            len(extraction.relationships),
            edges_created,
        )
        return edges_created

    async def _upsert_entity(self, entity: ExtractedEntity, article_id: str) -> None:
        """MERGE entity node — creates if new, updates properties if exists."""
        cypher = f"""
        SELECT * FROM cypher('{self._graph_name}', $$
            MERGE (e:{entity.entity_type.value} {{name: '{entity.name}'}})
            SET e.last_seen = '{datetime.now(timezone.utc).isoformat()}'
            SET e.mention_count = COALESCE(e.mention_count, 0) + 1
            SET e.properties = '{self._escape_json(entity.properties)}'
            RETURN e
        $$) AS (v agtype);
        """
        await self._session.execute(cypher)

    async def _upsert_relationship(
        self, rel: ExtractedRelationship, article_id: str
    ) -> bool:
        """MERGE relationship edge between two entities."""
        cypher = f"""
        SELECT * FROM cypher('{self._graph_name}', $$
            MATCH (s {{name: '{rel.source}'}}), (t {{name: '{rel.target}'}})
            MERGE (s)-[r:{rel.relationship_type.value}]->(t)
            SET r.confidence = {rel.confidence}
            SET r.last_article = '{article_id}'
            SET r.updated_at = '{datetime.now(timezone.utc).isoformat()}'
            RETURN r
        $$) AS (e agtype);
        """
        result = await self._session.execute(cypher)
        return result.rowcount > 0

    async def _create_mention_edge(
        self,
        entity_name: str,
        article_id: str,
        entity_sentiments: list[dict],
    ) -> None:
        """Create MENTIONED_IN edge from entity to article."""
        sentiment = "neutral"
        for es in entity_sentiments:
            if es.get("entity") == entity_name:
                sentiment = es.get("sentiment", "neutral")
                break

        cypher = f"""
        SELECT * FROM cypher('{self._graph_name}', $$
            MATCH (e {{name: '{entity_name}'}})
            MERGE (a:article {{id: '{article_id}'}})
            MERGE (e)-[r:mentioned_in]->(a)
            SET r.sentiment = '{sentiment}'
            SET r.created_at = '{datetime.now(timezone.utc).isoformat()}'
            RETURN r
        $$) AS (e agtype);
        """
        await self._session.execute(cypher)

    async def query_entity_context(
        self, entity_name: str, depth: int = 2
    ) -> dict:
        """
        Get full context for an entity: direct relationships + N-hop neighbors.
        Used by DiscoveryIntelligenceAgent to contextualize queries.
        """
        cypher = f"""
        SELECT * FROM cypher('{self._graph_name}', $$
            MATCH path = (e {{name: '{entity_name}'}})-[*1..{depth}]-(related)
            RETURN e, relationships(path), nodes(path)
        $$) AS (entity agtype, rels agtype, nodes agtype);
        """
        result = await self._session.execute(cypher)
        return self._format_context(result)

    async def query_risk_propagation(
        self, entity_name: str
    ) -> list[dict]:
        """
        Trace risk propagation paths from an entity.
        Follows: depends_on, uses_oracle, accepts_collateral chains.
        """
        cypher = f"""
        SELECT * FROM cypher('{self._graph_name}', $$
            MATCH path = (source {{name: '{entity_name}'}})
                -[:depends_on|:uses_oracle|:accepts_collateral*1..3]->(target)
            RETURN target.name AS affected,
                   length(path) AS hops,
                   [r IN relationships(path) | type(r)] AS chain
            ORDER BY hops ASC
        $$) AS (affected agtype, hops agtype, chain agtype);
        """
        result = await self._session.execute(cypher)
        return [
            {"affected": row.affected, "hops": row.hops, "chain": row.chain}
            for row in result
        ]

    async def query_recent_events(
        self, entity_name: str | None = None, severity: str | None = None, limit: int = 10
    ) -> list[dict]:
        """Get recent events affecting an entity or across the graph."""
        where_clause = ""
        if entity_name:
            where_clause = f"WHERE '{entity_name}' IN ev.affected_entities"
        elif severity:
            where_clause = f"WHERE ev.severity = '{severity}'"

        cypher = f"""
        SELECT * FROM cypher('{self._graph_name}', $$
            MATCH (ev:event)
            {where_clause}
            RETURN ev
            ORDER BY ev.timestamp DESC
            LIMIT {limit}
        $$) AS (event agtype);
        """
        result = await self._session.execute(cypher)
        return [dict(row) for row in result]

    @staticmethod
    def _escape_json(data: dict) -> str:
        import json
        return json.dumps(data).replace("'", "\\'")

    def _format_context(self, result) -> dict:
        """Format raw graph query result into structured context."""
        entities = []
        relationships = []
        for row in result:
            if row.entity:
                entities.append(dict(row.entity))
            if row.rels:
                for rel in row.rels:
                    relationships.append(dict(rel))
        return {"entities": entities, "relationships": relationships}
```

### 15.6 Celery Task: Post-Collection Extraction

```python
# Addition to src/app/tasks/discovery_tasks.py

@shared_task(
    bind=True,
    max_retries=2,
    queue="graphrag-extraction",
    rate_limit="10/m",  # LLM rate limiting
)
def extract_article_graph(self, article_ids: list[str]):
    """
    Post-collection task: extract entities & relationships from new articles.
    Triggered after collect_section_news completes.

    Pipeline: collect_section_news → extract_article_graph → graph upsert
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_extract_graph_async(article_ids))
    finally:
        loop.close()


async def _extract_graph_async(article_ids: list[str]) -> int:
    from infrastructure.persistence.discovery.news_sqla import NewsSQLARepository
    from infrastructure.persistence.discovery.graph_repository import DiscoveryGraphRepository
    from infrastructure.adapters.discovery.graphrag_extractor import GraphRAGExtractor

    news_repo = NewsSQLARepository()
    graph_repo = DiscoveryGraphRepository(db_session=news_repo.session)
    extractor = GraphRAGExtractor()

    # Load articles
    articles = await news_repo.get_by_ids(article_ids)
    if not articles:
        return 0

    # Extract entities & relationships
    extractions = await extractor.extract_batch(articles, batch_size=5)

    # Upsert to graph
    total_edges = 0
    for extraction in extractions:
        edges = await graph_repo.upsert_extraction(extraction)
        total_edges += edges

    logger.info(
        "GraphRAG extraction: articles=%d extractions=%d edges=%d",
        len(articles),
        len(extractions),
        total_edges,
    )
    return total_edges


# Updated beat schedule
DISCOVERY_BEAT_SCHEDULE["discovery-graph-maintenance"] = {
    "task": "tasks.discovery_tasks.graph_maintenance",
    "schedule": crontab(hour=4, minute=0),  # Daily 4 AM
}


@shared_task(queue="graphrag-extraction")
def graph_maintenance():
    """
    Nightly graph maintenance:
    - Prune entities not mentioned in 30 days
    - Recalculate centrality scores
    - Update risk propagation caches
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_graph_maintenance_async())
    finally:
        loop.close()


async def _graph_maintenance_async() -> dict:
    from infrastructure.persistence.discovery.graph_repository import DiscoveryGraphRepository

    graph_repo = DiscoveryGraphRepository(db_session=None)  # TODO: inject session

    # Prune stale entities (not mentioned in 30 days)
    # Recalculate PageRank centrality for entity importance
    # Pre-compute risk propagation paths for top 50 protocols

    logger.info("Graph maintenance completed")
    return {"status": "ok"}
```

### 15.7 Hybrid Retriever (Graph + Vector)

```python
# src/app/infrastructure/adapters/discovery/hybrid_retriever.py

"""
Hybrid retriever: combines pgvector similarity search with graph traversal.
Used by DiscoveryIntelligenceAgent and any agent needing contextualized knowledge.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from infrastructure.persistence.discovery.graph_repository import DiscoveryGraphRepository

logger = logging.getLogger(__name__)


@dataclass
class HybridRetrievalResult:
    """Combined result from vector + graph search."""

    # Direct matches (pgvector)
    vector_results: list[dict] = field(default_factory=list)

    # Graph context (entity relationships, risk paths)
    graph_context: dict = field(default_factory=dict)

    # Risk analysis (from graph traversal)
    risk_analysis: list[dict] = field(default_factory=list)

    # Recent events affecting mentioned entities
    recent_events: list[dict] = field(default_factory=list)

    # Sentiment summary across entities
    sentiment_summary: dict = field(default_factory=dict)


class HybridRetriever:
    """
    Combines vector similarity search with graph-based contextual retrieval.

    Weight distribution:
    - vector_weight: 0.4 (fast, keyword-relevant results)
    - graph_weight: 0.6 (deep contextual understanding)
    """

    def __init__(
        self,
        graph_repo: DiscoveryGraphRepository,
        vector_repo=None,  # pgvector-based article search
        vector_weight: float = 0.4,
        graph_weight: float = 0.6,
        graph_depth: int = 2,
    ):
        self._graph_repo = graph_repo
        self._vector_repo = vector_repo
        self._vector_weight = vector_weight
        self._graph_weight = graph_weight
        self._graph_depth = graph_depth

    async def retrieve(
        self,
        query: str,
        entity_names: list[str] | None = None,
        limit: int = 10,
    ) -> HybridRetrievalResult:
        """
        Execute hybrid retrieval:
        1. Vector search for relevant articles
        2. Extract entity names from query (or use provided)
        3. Graph traversal for each entity (context, risk, events)
        4. Merge and rank results
        """
        import asyncio

        # 1. Vector search (pgvector)
        vector_task = (
            self._vector_repo.similarity_search(query, limit=limit)
            if self._vector_repo
            else asyncio.coroutine(lambda: [])()
        )

        # 2. Entity extraction from query (simple keyword match for speed)
        entities = entity_names or self._extract_entity_names(query)

        # 3. Graph context for each entity (parallel)
        graph_tasks = [
            self._graph_repo.query_entity_context(name, depth=self._graph_depth)
            for name in entities[:5]  # Limit to 5 entities per query
        ]

        # 4. Risk propagation for DeFi-specific entities
        risk_tasks = [
            self._graph_repo.query_risk_propagation(name)
            for name in entities[:3]  # Top 3 only
        ]

        # 5. Recent events
        event_tasks = [
            self._graph_repo.query_recent_events(entity_name=name, limit=5)
            for name in entities[:3]
        ]

        # Execute all in parallel
        all_results = await asyncio.gather(
            vector_task,
            asyncio.gather(*graph_tasks, return_exceptions=True),
            asyncio.gather(*risk_tasks, return_exceptions=True),
            asyncio.gather(*event_tasks, return_exceptions=True),
            return_exceptions=True,
        )

        vector_results = all_results[0] if not isinstance(all_results[0], Exception) else []
        graph_contexts = all_results[1] if not isinstance(all_results[1], Exception) else []
        risk_results = all_results[2] if not isinstance(all_results[2], Exception) else []
        event_results = all_results[3] if not isinstance(all_results[3], Exception) else []

        # Merge graph contexts
        merged_graph = {"entities": [], "relationships": []}
        for ctx in graph_contexts:
            if isinstance(ctx, dict):
                merged_graph["entities"].extend(ctx.get("entities", []))
                merged_graph["relationships"].extend(ctx.get("relationships", []))

        # Flatten risk and events
        flat_risks = [r for sublist in risk_results if isinstance(sublist, list) for r in sublist]
        flat_events = [e for sublist in event_results if isinstance(sublist, list) for e in sublist]

        return HybridRetrievalResult(
            vector_results=vector_results if isinstance(vector_results, list) else [],
            graph_context=merged_graph,
            risk_analysis=flat_risks,
            recent_events=flat_events,
        )

    @staticmethod
    def _extract_entity_names(query: str) -> list[str]:
        """
        Fast entity extraction from query using known entity dictionary.
        For production: replace with NER model or LLM extraction.
        """
        # Known DeFi entities (loaded from graph on startup)
        KNOWN_ENTITIES = {
            "aave", "compound", "uniswap", "morpho", "maker", "makerdao",
            "chainlink", "ethereum", "bitcoin", "base", "arbitrum", "polygon",
            "usdc", "usdt", "dai", "eth", "btc", "weth", "wbtc",
            "sec", "cftc", "blackrock", "circle", "tether",
        }

        words = query.lower().split()
        return [w for w in words if w in KNOWN_ENTITIES]
```

### 15.8 Updated Celery Worker Chain

The extraction runs as a **chain** after each section collection:

```python
# In collect_section_news, after saving articles:

from celery import chain

# After storing new articles, trigger GraphRAG extraction
if new_article_ids:
    chain(
        extract_article_graph.si(new_article_ids),
    ).apply_async(countdown=5)  # 5s delay to let DB commit
```

**Updated Beat Schedule:**

| Task | Schedule | Queue | Purpose |
|------|----------|-------|---------|
| collect_news_all_sections | */15 min | default | Fan-out news collection |
| collect_section_news | per-section | news-collection | Fetch + store articles |
| extract_article_graph | chained | graphrag-extraction | LLM entity extraction |
| graph_maintenance | daily 4 AM | graphrag-extraction | Prune + recalculate |
| collect_vault_snapshots | */5 min | vault-refresh | Vault data |
| cleanup_expired_articles | daily 3 AM | default | 30-day retention |

### 15.9 Cost Impact (GraphRAG Extraction)

| Item | Volume | Cost |
|------|--------|------|
| LLM extraction (Gemini 2.0 Flash) | ~500 articles/day × 2K tokens | ~$0.15/day |
| Apache AGE queries | Runs inside PostgreSQL | $0 (no extra infra) |
| Graph maintenance (nightly) | 1 run/day | ~$0.01/day |
| **Monthly GraphRAG total** | | **~$5/mo** |

Using **Gemini 2.0 Flash** at $0.10/1M tokens keeps extraction nearly free. Apache AGE runs as a PostgreSQL extension — no Neo4j license or extra infrastructure needed.

---

## 16. Discovery Intelligence Agent

### 16.1 Agent Specification

A new agent type that contextualizes Discovery news using GraphRAG for consumption by the entire agent squad.

```python
# src/app/domain/enums/agent_type.py (addition)

class AgentType(Enum):
    # ... existing agents ...

    # Discovery
    DISCOVERY_INTELLIGENCE = "discovery_intelligence"  # News contextualizer (GraphRAG)
```

### 16.2 Intent Classification

```python
# src/app/domain/services/agent_squad/intent_classifier.py (addition)

AGENT_MAPPING = {
    # ... existing mappings ...

    # Discovery Intelligence
    "news_context": AgentType.DISCOVERY_INTELLIGENCE,
    "market_context": AgentType.DISCOVERY_INTELLIGENCE,
    "risk_news": AgentType.DISCOVERY_INTELLIGENCE,
    "what_happened": AgentType.DISCOVERY_INTELLIGENCE,
    "news_impact": AgentType.DISCOVERY_INTELLIGENCE,
}
```

### 16.3 Keyword Detection

```python
# src/app/infrastructure/adapters/chat/keyword_intent_detection_adapter.py (addition)

if any(kw in message_lower for kw in [
    "what happened", "latest news", "news about", "any news",
    "what's going on with", "impact of", "how does this affect",
    "market context", "news summary", "breaking news",
    "risk update", "security alert", "hack news",
]):
    return "news_context"
```

### 16.4 Agent Implementation

```python
# src/app/infrastructure/adapters/agent_squad/agents/discovery_intelligence_agent.py

"""
Discovery Intelligence Agent — GraphRAG-powered news contextualizer.

This agent:
1. Receives user queries about news, market events, or risk situations
2. Searches Discovery news articles (vector) + knowledge graph (graph)
3. Provides contextualized, relationship-aware analysis
4. Can be called by OTHER agents for context enrichment

Implements: AgentGateway
Model: gemini-2.0-flash (fast, cost-effective)
Architecture: Hexagonal (Clean Architecture)
"""
from __future__ import annotations

import logging
import time
from decimal import Decimal

from domain.ports.agent_squad.agent_gateway import AgentGateway
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.message_content import MessageContent
from infrastructure.adapters.discovery.hybrid_retriever import HybridRetriever, HybridRetrievalResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Discovery Intelligence Agent for Anvil, a DeFi assistant.

You have access to a KNOWLEDGE GRAPH of the DeFi ecosystem with real-time news contextualization.
Your responses combine:
1. Latest news articles (from Discovery module)
2. Entity relationships (protocols, tokens, chains, organizations)
3. Risk propagation analysis (dependency chains, contagion paths)
4. Sentiment analysis (market mood per entity)

When answering:
- Lead with the most impactful news
- Explain HOW events connect to the user's portfolio (if context available)
- Highlight risk implications using graph relationships
- Cite sources when referencing specific articles
- Use concrete numbers (TVL, APY changes, price impact)
- If the user has positions in affected protocols, flag them explicitly

Response format:
- Start with a 1-sentence headline summary
- Then provide detailed analysis with entity relationships
- End with actionable recommendations if applicable

Never speculate beyond what the knowledge graph supports.
Always distinguish between confirmed facts and potential implications."""


class DiscoveryIntelligenceAgent:
    """
    GraphRAG-powered news contextualizer.

    Capabilities:
    - "What happened with Aave?" → Graph context + recent articles
    - "How does the USDT news affect my portfolio?" → Risk propagation + user positions
    - "Latest DeFi security alerts" → Event graph + severity ranking
    - "Market context for ETH" → Sentiment + relationships + price context

    Also callable by other agents:
    - PortfolioAgent: "Get news context for user's held tokens"
    - RiskAnalyzerAgent: "Get risk events for protocol X"
    - HunterAI: "Get market sentiment for token Y"
    """

    def __init__(
        self,
        llm_client,
        hybrid_retriever: HybridRetriever,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        self._llm_client = llm_client
        self._retriever = hybrid_retriever
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context=None,
    ):
        """Main agent entry point — handles user-facing news queries."""
        start_time = time.time()

        # 1. Hybrid retrieval: vector + graph
        retrieval = await self._retriever.retrieve(
            query=str(message),
            limit=10,
        )

        # 2. Build enriched context for LLM
        context = self._build_context(retrieval, conversation_context)

        # 3. Generate response
        response = await self._llm_client.generate(
            model=self._model,
            system_prompt=SYSTEM_PROMPT,
            user_message=f"{context}\n\nUser question: {message}",
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "DiscoveryIntelligence: query=%s latency=%dms entities=%d",
            str(message)[:50],
            elapsed_ms,
            len(retrieval.graph_context.get("entities", [])),
        )

        return self._build_agent_response(response.content, retrieval, elapsed_ms)

    async def get_context_for_agent(
        self,
        entity_names: list[str],
        context_type: str = "full",
    ) -> dict:
        """
        Called by OTHER agents to get news context.
        This is the inter-agent API.

        Args:
            entity_names: Entities to get context for (e.g., ["Aave", "ETH"])
            context_type: "full" | "risk_only" | "sentiment_only" | "events_only"

        Returns:
            Structured context dict for injection into the calling agent's prompt.
        """
        retrieval = await self._retriever.retrieve(
            query=" ".join(entity_names),
            entity_names=entity_names,
            limit=5,
        )

        if context_type == "risk_only":
            return {
                "risk_analysis": retrieval.risk_analysis,
                "recent_events": [
                    e for e in retrieval.recent_events
                    if e.get("severity") in ("high", "critical")
                ],
            }
        elif context_type == "sentiment_only":
            return {"sentiment": retrieval.sentiment_summary}
        elif context_type == "events_only":
            return {"events": retrieval.recent_events}
        else:
            return {
                "graph_context": retrieval.graph_context,
                "risk_analysis": retrieval.risk_analysis,
                "recent_events": retrieval.recent_events,
                "sentiment": retrieval.sentiment_summary,
                "vector_articles": [
                    {"title": a.get("title"), "summary": a.get("summary")}
                    for a in retrieval.vector_results[:5]
                ],
            }

    async def get_portfolio_news_context(
        self,
        user_tokens: list[str],
        user_protocols: list[str],
    ) -> dict:
        """
        Get news context specifically relevant to a user's portfolio.
        Called by PortfolioAgent for personalized risk alerts.

        Args:
            user_tokens: Tokens user holds (e.g., ["ETH", "USDC", "AAVE"])
            user_protocols: Protocols user has positions in (e.g., ["Aave", "Morpho"])

        Returns:
            Structured context with portfolio-relevant news and risks.
        """
        all_entities = user_tokens + user_protocols
        retrieval = await self._retriever.retrieve(
            query=" ".join(all_entities),
            entity_names=all_entities,
            limit=10,
        )

        # Filter to only portfolio-relevant results
        relevant_risks = [
            r for r in retrieval.risk_analysis
            if r.get("affected") in all_entities
        ]

        relevant_events = [
            e for e in retrieval.recent_events
            if any(ent in all_entities for ent in e.get("affected_entities", []))
        ]

        return {
            "portfolio_risks": relevant_risks,
            "portfolio_events": relevant_events,
            "portfolio_sentiment": {
                entity: retrieval.sentiment_summary.get(entity, "neutral")
                for entity in all_entities
            },
            "relevant_articles": retrieval.vector_results[:5],
        }

    def _build_context(self, retrieval: HybridRetrievalResult, user_context) -> str:
        """Build enriched context string for LLM prompt."""
        parts = []

        # Graph context
        if retrieval.graph_context.get("entities"):
            entities = retrieval.graph_context["entities"]
            parts.append(f"## Knowledge Graph Context ({len(entities)} entities)")
            for e in entities[:10]:
                parts.append(f"- {e.get('name', 'Unknown')} ({e.get('type', 'entity')})")

        if retrieval.graph_context.get("relationships"):
            rels = retrieval.graph_context["relationships"]
            parts.append(f"\n## Relationships ({len(rels)} connections)")
            for r in rels[:10]:
                parts.append(
                    f"- {r.get('source', '?')} --[{r.get('type', '?')}]--> {r.get('target', '?')}"
                )

        # Risk analysis
        if retrieval.risk_analysis:
            parts.append(f"\n## Risk Propagation ({len(retrieval.risk_analysis)} paths)")
            for risk in retrieval.risk_analysis[:5]:
                parts.append(
                    f"- {risk.get('affected', '?')} (hops: {risk.get('hops', '?')}, "
                    f"chain: {' → '.join(risk.get('chain', []))})"
                )

        # Recent events
        if retrieval.recent_events:
            parts.append(f"\n## Recent Events ({len(retrieval.recent_events)} events)")
            for ev in retrieval.recent_events[:5]:
                parts.append(
                    f"- [{ev.get('severity', 'medium').upper()}] {ev.get('name', 'Unknown')} "
                    f"(affects: {', '.join(ev.get('affected_entities', []))})"
                )

        # Article results
        if retrieval.vector_results:
            parts.append(f"\n## Related Articles ({len(retrieval.vector_results)} found)")
            for art in retrieval.vector_results[:5]:
                parts.append(
                    f"- [{art.get('source_name', 'Unknown')}] {art.get('title', 'Untitled')}"
                )

        # User portfolio context (if available)
        if user_context and hasattr(user_context, "portfolio"):
            parts.append("\n## User Portfolio")
            parts.append(f"- Tokens: {', '.join(user_context.portfolio.get('tokens', []))}")
            parts.append(f"- Protocols: {', '.join(user_context.portfolio.get('protocols', []))}")

        return "\n".join(parts) if parts else "No additional context available."

    def _build_agent_response(self, content: str, retrieval: HybridRetrievalResult, latency_ms: int):
        """Build standard AgentResponse."""
        from domain.value_objects.agent_response import AgentResponse

        # Build citations from articles
        citations = []
        for art in retrieval.vector_results[:5]:
            if art.get("source_url"):
                citations.append({
                    "title": art.get("title", ""),
                    "url": art.get("source_url", ""),
                    "source": art.get("source_name", "Unknown"),
                })

        return AgentResponse(
            content=content,
            agent_type="discovery_intelligence",
            metadata={
                "latency_ms": latency_ms,
                "entities_found": len(retrieval.graph_context.get("entities", [])),
                "risk_paths": len(retrieval.risk_analysis),
                "events_found": len(retrieval.recent_events),
                "citations": citations,
            },
        )
```

### 16.5 Inter-Agent Integration

Other agents call `DiscoveryIntelligenceAgent.get_context_for_agent()`:

```python
# Example: PortfolioAgent enrichment

class PortfolioAgent:
    def __init__(self, ..., discovery_intelligence: DiscoveryIntelligenceAgent):
        self._discovery = discovery_intelligence

    async def execute(self, conversation_id, message, context):
        # Get user's held tokens
        user_tokens = context.portfolio.get("tokens", [])
        user_protocols = context.portfolio.get("protocols", [])

        # Enrich with news context from Discovery Intelligence
        news_context = await self._discovery.get_portfolio_news_context(
            user_tokens=user_tokens,
            user_protocols=user_protocols,
        )

        # Inject into LLM prompt
        if news_context.get("portfolio_risks"):
            context.add_context("portfolio_risks", news_context["portfolio_risks"])
        if news_context.get("portfolio_events"):
            context.add_context("portfolio_events", news_context["portfolio_events"])

        # Continue with portfolio analysis...
```

```python
# Example: RiskAnalyzerAgent enrichment

class RiskAnalyzerAgent:
    async def _get_risk_context(self, protocol_name: str) -> dict:
        return await self._discovery.get_context_for_agent(
            entity_names=[protocol_name],
            context_type="risk_only",
        )
```

### 16.6 DI Registration

```python
# src/app/setup/ioc/agent_squad_infrastructure.py (addition)

from infrastructure.adapters.agent_squad.agents.discovery_intelligence_agent import (
    DiscoveryIntelligenceAgent,
)
from infrastructure.adapters.discovery.hybrid_retriever import HybridRetriever
from infrastructure.persistence.discovery.graph_repository import DiscoveryGraphRepository


def register_discovery_intelligence(container):
    graph_repo = DiscoveryGraphRepository(db_session=container.db_session)
    hybrid_retriever = HybridRetriever(
        graph_repo=graph_repo,
        vector_repo=container.pgvector_repo,
        vector_weight=0.4,
        graph_weight=0.6,
    )

    discovery_agent = DiscoveryIntelligenceAgent(
        llm_client=container.llm_client,
        hybrid_retriever=hybrid_retriever,
        model="gemini-2.0-flash",
        temperature=0.3,
    )

    container.register(AgentType.DISCOVERY_INTELLIGENCE, discovery_agent)
```

### 16.7 File Structure Addition

```
src/app/
├── domain/
│   └── services/graph/
│       └── news_ontology.py                    # Entity types + relationships
│
├── infrastructure/
│   ├── adapters/
│   │   ├── agent_squad/agents/
│   │   │   └── discovery_intelligence_agent.py # NEW AGENT
│   │   └── discovery/
│   │       ├── graphrag_extractor.py           # LLM entity extraction
│   │       └── hybrid_retriever.py             # Graph + vector retriever
│   │
│   └── persistence/discovery/
│       └── graph_repository.py                 # Apache AGE graph queries
│
└── tasks/
    └── discovery_tasks.py                      # +extract_article_graph, +graph_maintenance
```

### 16.8 Deployment: Celery Worker Addition

```bash
# Existing workers (unchanged)
celery -A tasks worker -Q news-collection --concurrency=4 --pool=gevent
celery -A tasks worker -Q vault-refresh --concurrency=2 --pool=gevent

# NEW: GraphRAG extraction worker
celery -A tasks worker -Q graphrag-extraction --concurrency=3 --pool=gevent -n graphrag@%h
```

### 16.9 Apache AGE Setup (PostgreSQL Extension)

```bash
# Install Apache AGE (runs inside PostgreSQL — no extra database)
sudo apt-get install postgresql-14-age

# Enable extension
psql -U anvil -d anvil -c "CREATE EXTENSION IF NOT EXISTS age;"
psql -U anvil -d anvil -c "LOAD 'age';"
psql -U anvil -d anvil -c "SET search_path = ag_catalog, public;"

# Create the discovery graph
psql -U anvil -d anvil -c "SELECT create_graph('discovery_graph');"
```

No Neo4j license, no extra infrastructure. Apache AGE runs as a PostgreSQL extension using the same database instance.

---

## 17. Open Items & Roadmap

### Phase 1 (Current)
- [x] Database schema design
- [x] Perplexity Sonar integration
- [x] Provider failover chain
- [x] API endpoints (interests, feed, search, vaults)
- [x] Celery collection pipeline
- [x] GraphRAG news ontology design
- [x] Discovery Intelligence Agent specification
- [x] Hybrid retriever (graph + vector) design
- [ ] Deploy schema + seed data
- [ ] Install Apache AGE extension
- [ ] Configure API keys (Perplexity, NewsAPI, CryptoPanic)
- [ ] Launch Celery workers (news + graphrag-extraction)
- [ ] Integration tests

### Phase 2 (GraphRAG Foundation)
- [ ] Entity extraction pipeline (Gemini 2.0 Flash)
- [ ] Apache AGE graph queries + indexes
- [ ] Hybrid retriever implementation
- [ ] Discovery Intelligence Agent implementation
- [ ] Inter-agent integration (Portfolio, Risk, Hunter)
- [ ] Graph maintenance nightly job
- [ ] A/B test: responses with vs without GraphRAG

### Phase 3 (Content Enrichment)
- [ ] News image proxy/CDN (avoid hotlinking)
- [ ] Push notifications on new articles matching interests
- [ ] Read/bookmark tracking per user
- [ ] AI-generated article summaries (Sonar → shorter summary)
- [ ] Trending section (based on view_count)

### Phase 4 (Advanced Graph)
- [ ] Sentiment analysis signals (bullish/bearish for crypto)
- [ ] Risk propagation pre-computation (nightly cache)
- [ ] PageRank centrality for entity importance
- [ ] Graph-powered "What if?" scenario analysis
- [ ] More providers: Bloomberg, AP News, The Block, Decrypt
- [ ] Localized news sources (Spanish, Portuguese, Chinese)
- [ ] Admin analytics dashboard (articles/day, provider health, graph stats)
- [ ] Share article to chat ("ask about this article")

### Future Categories
- [ ] "Alpha Signals" — on-chain whale alerts, smart money flows
- [ ] "Airdrops" — upcoming/active airdrop tracker
- [ ] "Research" — curated DeFi research papers and threads
- [ ] "Events" — crypto conferences, governance votes

---

*End of specification — Matias Baglieri*