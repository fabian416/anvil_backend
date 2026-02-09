# Discovery Module — Document 3: Database Schema

## Overview
7 tables + 1 Apache AGE graph. PostgreSQL 14 with TimescaleDB + Apache AGE extensions.

## Table Inventory

| Table | Purpose | Rows (est.) | Retention |
|-------|---------|-------------|-----------|
| discovery_categories | Top-level tabs (News, Vaults) | ~5 | Permanent |
| discovery_sections | Hierarchical topics (parent→child) | ~50 | Permanent |
| discovery_user_interests | User↔section toggle state | ~users × 10 | Permanent |
| discovery_news_providers | Provider config + health state | ~7 | Permanent |
| discovery_news_articles | Collected news articles | ~100K active | 30-day retention (TimescaleDB) |
| discovery_vault_snapshots | Point-in-time vault APY/TVL data | ~1K active | Deactivate after 1h |
| discovery_graph (AGE) | Knowledge graph: entities + relationships | ~10K nodes | Prune stale 30d nightly |

---

## 1. discovery_categories

Admin-managed content tabs. Seed: "News" + "Today's Vaults".

```sql
CREATE TABLE discovery_categories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug            VARCHAR(50) UNIQUE NOT NULL,          -- 'news', 'vaults'
    name            VARCHAR(100) NOT NULL,                -- 'News', 'Today's Vaults'
    description     TEXT,
    icon            VARCHAR(50),                          -- Lucide icon name
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,                 -- Admin kill switch
    is_default      BOOLEAN DEFAULT false,                -- Show by default
    config          JSONB DEFAULT '{}',                   -- Extensible config
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    created_by      UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_discovery_categories_active ON discovery_categories (is_active, sort_order);

-- Trigger
CREATE TRIGGER update_discovery_categories_updated_at
    BEFORE UPDATE ON discovery_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Seed data
INSERT INTO discovery_categories (slug, name, icon, sort_order, is_active, is_default) VALUES
    ('news',   'News',            'newspaper', 1, true, true),
    ('vaults', 'Today''s Vaults', 'vault',     2, true, true);
```

**Key behaviors:**
- `is_active = false` → hides entire tab for ALL users
- `is_default = true` → shown to new users who haven't customized
- `config` JSONB → extensible for future tab-specific settings

---

## 2. discovery_sections

Hierarchical topics within categories. Two levels: parent section → subsections.

```sql
CREATE TABLE discovery_sections (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id     UUID NOT NULL REFERENCES discovery_categories(id) ON DELETE CASCADE,
    parent_id       UUID REFERENCES discovery_sections(id) ON DELETE CASCADE,   -- NULL = top-level
    slug            VARCHAR(100) NOT NULL,
    name            VARCHAR(150) NOT NULL,
    description     TEXT,
    icon            VARCHAR(50),                          -- Lucide icon name
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,                 -- Admin can disable
    is_default      BOOLEAN DEFAULT false,                -- Auto-enable for new users
    metadata        JSONB DEFAULT '{}',                   -- {"keywords": ["bitcoin","btc","halving"]}
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_section_category_slug UNIQUE (category_id, slug)
);

-- Indexes
CREATE INDEX idx_sections_category_active ON discovery_sections (category_id, is_active, sort_order);
CREATE INDEX idx_sections_parent ON discovery_sections (parent_id);

-- Trigger
CREATE TRIGGER update_discovery_sections_updated_at
    BEFORE UPDATE ON discovery_sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Section hierarchy (News category):**
```
News
├── Politics (parent_id=NULL, is_default=true)
│   ├── World Affairs (is_default=true)
│   ├── US Politics (is_default=true)
│   ├── Europe, Asia, Middle East, Latin America, Africa
│   ├── Elections, Government
│   ├── Military & Defense, Geopolitics
│
├── Tech & Science (parent_id=NULL, is_default=true)
│   ├── Technology (is_default=true)
│   ├── Science (is_default=true)
│   ├── AI & Machine Learning (is_default=true)
│   ├── Big Tech, Startups, Robotics, Medical, Electronics
│   ├── Energy, Agriculture, Climate, Environment, Nuclear
│   ├── Space, Programming, Biotech
│
├── Crypto & DeFi (parent_id=NULL, is_default=true)
│   ├── Bitcoin (is_default=true)
│   ├── Ethereum (is_default=true)
│   ├── DeFi Protocols (is_default=true)
│   ├── Regulation, NFT & Gaming, Meme Coins, Stablecoins
│
├── Economy & Finance (parent_id=NULL, is_default=false)
│   ├── Markets, Central Banks, Commodities, Real Estate
│
└── World (parent_id=NULL, is_default=false)
```

**metadata.keywords** drives the Celery news collection — these keywords are sent to Perplexity Sonar.

---

## 3. discovery_user_interests

Per-user section toggle state. Sparse: only stores EXPLICIT preferences. Missing = use section.is_default.

```sql
CREATE TABLE discovery_user_interests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    section_id      UUID NOT NULL REFERENCES discovery_sections(id) ON DELETE CASCADE,
    is_enabled      BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_user_section UNIQUE (user_id, section_id)
);

-- Indexes
CREATE INDEX idx_user_interests_user ON discovery_user_interests (user_id);
CREATE INDEX idx_user_interests_lookup ON discovery_user_interests (user_id, section_id, is_enabled);
```

**Interest resolution logic:**
1. Check `discovery_user_interests` for explicit `(user_id, section_id)` row
2. If found → use `is_enabled` value
3. If NOT found → use `discovery_sections.is_default` value
4. This means new users get sensible defaults without any DB writes

---

## 4. discovery_news_providers

Provider registry with health tracking and rate limiting.

```sql
CREATE TYPE news_provider_type_enum AS ENUM ('sonar', 'api', 'rss', 'scraper');

CREATE TABLE discovery_news_providers (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug                    VARCHAR(50) UNIQUE NOT NULL,          -- 'perplexity_sonar'
    name                    VARCHAR(100) NOT NULL,                -- 'Perplexity Sonar'
    provider_type           news_provider_type_enum NOT NULL,
    base_url                TEXT,
    api_key_ref             VARCHAR(100),                         -- Env var name (NOT the actual key)
    config                  JSONB DEFAULT '{}',                   -- Model, params, etc.
    supported_sections      JSONB DEFAULT '[]',                   -- Parent section slugs
    is_active               BOOLEAN DEFAULT true,
    is_primary              BOOLEAN DEFAULT false,                -- Only ONE primary
    priority                INTEGER DEFAULT 0,                    -- Higher = tried first
    rate_limit_per_minute   INTEGER DEFAULT 50,
    rate_limit_per_day      INTEGER DEFAULT 5000,
    daily_request_count     INTEGER DEFAULT 0,
    daily_count_reset_at    TIMESTAMPTZ DEFAULT NOW(),
    last_fetched_at         TIMESTAMPTZ,
    consecutive_errors      INTEGER DEFAULT 0,                    -- Circuit breaker counter
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);
```

**Seed providers (7 total):**

| slug | type | primary | priority | RPM | Daily |
|------|------|---------|----------|-----|-------|
| perplexity_sonar | sonar | ✅ | 100 | 50 | 5000 |
| newsapi | api | ❌ | 50 | 100 | 10000 |
| cryptopanic | api | ❌ | 50 | 30 | 5000 |
| rss_coindesk | rss | ❌ | 20 | 10 | 1000 |
| rss_reuters | rss | ❌ | 20 | 10 | 1000 |
| defillama | api | ❌ | 80 | 30 | 5000 |
| vaultsfyi | api | ❌ | 70 | 20 | 3000 |

---

## 5. discovery_news_articles

Main content table. High volume, 30-day retention via TimescaleDB.

```sql
CREATE TABLE discovery_news_articles (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id         UUID NOT NULL REFERENCES discovery_news_providers(id),
    external_id         VARCHAR(500),

    -- Content
    title               TEXT NOT NULL,
    summary             TEXT,
    image_url           TEXT,
    source_name         VARCHAR(200) NOT NULL,
    source_url          TEXT NOT NULL,
    author              VARCHAR(200),
    citations           JSONB DEFAULT '[]',              -- Perplexity Sonar citations

    -- Classification
    section_id          UUID REFERENCES discovery_sections(id),
    parent_section_slug VARCHAR(100),                    -- Denormalized for fast queries
    section_slug        VARCHAR(100),                    -- Denormalized for fast queries
    tags                TEXT[] DEFAULT '{}',
    language            VARCHAR(10) DEFAULT 'en',
    sentiment           VARCHAR(20) DEFAULT 'neutral',   -- positive/negative/neutral

    -- Timestamps
    published_at        TIMESTAMPTZ NOT NULL,
    fetched_at          TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup & quality
    content_hash        VARCHAR(64) NOT NULL,            -- SHA-256(normalized_title|url)
    relevance_score     FLOAT DEFAULT 0.5,               -- 0.0-1.0, Sonar=0.8, NewsAPI=0.6
    view_count          INTEGER DEFAULT 0,
    is_active           BOOLEAN DEFAULT true,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes (critical for feed performance)
CREATE UNIQUE INDEX idx_news_content_hash ON discovery_news_articles (content_hash);
CREATE INDEX idx_news_section_published ON discovery_news_articles (section_id, published_at DESC) WHERE is_active = true;
CREATE INDEX idx_news_published ON discovery_news_articles (published_at DESC) WHERE is_active = true;
CREATE INDEX idx_news_parent_section ON discovery_news_articles (parent_section_slug, published_at DESC) WHERE is_active = true;
CREATE INDEX idx_news_relevance ON discovery_news_articles (relevance_score DESC, published_at DESC) WHERE is_active = true;
CREATE INDEX idx_news_tags ON discovery_news_articles USING GIN (tags);
CREATE INDEX idx_news_fts ON discovery_news_articles USING GIN (
    to_tsvector('english', title || ' ' || COALESCE(summary, ''))
);

-- TimescaleDB 30-day retention
SELECT add_retention_policy('discovery_news_articles', INTERVAL '30 days');
```

**Deduplication:** `content_hash = SHA-256(lower(title.strip()) + "|" + source_url.strip())`
UNIQUE index prevents duplicate inserts. UPSERT skips existing.

---

## 6. discovery_vault_snapshots

Point-in-time DeFi vault data with computed total_apy.

```sql
CREATE TABLE discovery_vault_snapshots (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id         UUID REFERENCES discovery_news_providers(id),

    -- Protocol
    protocol            VARCHAR(50) NOT NULL,            -- 'morpho', 'aave-v3'
    protocol_display    VARCHAR(100) NOT NULL,           -- 'Morpho', 'Aave V3'
    vault_name          VARCHAR(200) NOT NULL,
    vault_address       VARCHAR(42),                     -- 0x...
    chain               VARCHAR(50) NOT NULL,            -- 'base', 'ethereum'
    chain_name          VARCHAR(50) NOT NULL,            -- 'Base', 'Ethereum'

    -- Metrics
    asset_symbol        VARCHAR(20) NOT NULL,            -- 'USDC', 'ETH'
    supply_apy          NUMERIC(10,4) NOT NULL,
    reward_apy          NUMERIC(10,4) DEFAULT 0,
    total_apy           NUMERIC(10,4) GENERATED ALWAYS AS (supply_apy + reward_apy) STORED,
    tvl_usd             NUMERIC(18,2),

    -- Risk
    risk_level          VARCHAR(20) DEFAULT 'low',       -- low/medium/high
    is_curated          BOOLEAN DEFAULT true,

    -- Meta
    snapshot_at         TIMESTAMPTZ DEFAULT NOW(),
    is_active           BOOLEAN DEFAULT true,            -- Deactivated after 1h
    metadata            JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_vaults_apy ON discovery_vault_snapshots (total_apy DESC) WHERE is_active = true;
CREATE INDEX idx_vaults_time ON discovery_vault_snapshots (snapshot_at DESC);
CREATE INDEX idx_vaults_protocol ON discovery_vault_snapshots (protocol, asset_symbol) WHERE is_active = true;
```

**Risk classification logic:**
- APY > 100% OR TVL < $500K → `high`
- APY > 20% OR TVL < $5M → `medium`
- Otherwise → `low`

---

## 7. Apache AGE Knowledge Graph

No separate table — Apache AGE creates graph structures within PostgreSQL.

```sql
-- Install extension
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, public;

-- Create graph
SELECT create_graph('discovery_graph');
```

**Node types (labels):**
- `protocol` — Aave, Compound, Uniswap, Morpho
- `token` — ETH, USDC, USDT, BTC
- `chain` — Ethereum, Base, Arbitrum
- `person` — Vitalik, Gary Gensler
- `organization` — SEC, BlackRock, Circle
- `event` — Hack, exploit, upgrade, launch
- `risk` — Oracle risk, smart contract risk
- `regulation` — MiCA, SEC ruling
- `article` — News article reference node

**Edge types:**
- `uses_oracle`, `accepts_collateral`, `depends_on`, `competes_with`
- `deployed_on`, `forked_from`, `affected_by`, `triggered_by`
- `paused_asset`, `upgraded_to`, `regulated_by`, `subject_of`
- `exposes_risk`, `mitigates_risk`, `founded_by`, `invested_in`
- `announced`, `mentioned_in`, `sentiment_about`

**Key graph queries:**
1. `query_entity_context(name, depth)` — N-hop traversal from entity
2. `query_risk_propagation(name)` — follows depends_on/uses_oracle/accepts_collateral chains
3. `query_recent_events(entity, severity)` — event nodes by affected entity
