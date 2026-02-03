# Distillation System Documentation

> **Framework:** Hexagonal Architecture + CQRS + Multi-Provider LLM
> **Status:** Production-Ready
> **Version:** 2.0 (Intent-Free, Complexity-Based Routing)
> **Last Updated:** 2026-01-26

---

## Table of Contents

- [Quick Navigation](#quick-navigation)
- [What is the Distillation System?](#what-is-the-distillation-system)
- [Architecture Overview](#architecture-overview)
- [Key Concepts](#key-concepts)
- [Database Schema](#database-schema)
- [Technology Stack](#technology-stack)
- [Development Workflow](#development-workflow)
- [Related Documentation](#related-documentation)

---

## Quick Navigation

### **By Access Level**
- [**Guest Endpoints**](endpoints.md#guest-endpoints) - Unauthenticated access (currently none)
- [**User Endpoints**](endpoints.md#user-endpoints) - Authenticated users (currently none - integrated into chat)
- [**Admin Endpoints**](endpoints.md#admin-endpoints) - Configuration and monitoring

### **By Concern**
- [**API Endpoints**](endpoints.md) - Complete endpoint reference with examples
- [**Services & Components**](services.md) - Domain, Application, Infrastructure layers
- [**Background Tasks**](celery.md) - Celery tasks for cache cleanup and telemetry aggregation
- [**Caching System**](services.md#cache-manager) - 2-level cache (exact + semantic)
- [**Telemetry & Metrics**](services.md#telemetry-services) - Cost tracking and performance monitoring

### **By Layer**
- [**Domain Layer**](services.md#domain-services) - Core business logic
- [**Application Layer**](services.md#application-services) - Use case orchestration
- [**Infrastructure Layer**](services.md#infrastructure-services) - External integrations
- [**Presentation Layer**](endpoints.md) - HTTP controllers and schemas

---

## What is the Distillation System?

The **Distillation System** is a **cost-optimization layer** for LLM operations that:

1. **Reduces LLM costs by 80-95%** through intelligent caching and routing
2. **Improves response times** with multi-level caching (exact + semantic)
3. **Routes queries optimally** based on complexity (not intent classification)
4. **Provides transparent telemetry** for cost and performance tracking

### Problem Solved

**Before Distillation:**
- Every chat message = full LLM call ($$$)
- Repetitive queries waste tokens
- No cost visibility
- No performance optimization

**After Distillation:**
```
User Query → Distillation Pass → Routing Decision
             ↓
    ┌────────┴─────────┐
    │  L1: Exact Cache │ → Return cached (FREE, <5ms)
    │  L2: Semantic    │ → Return similar (FREE, <20ms)
    │  L3: Light LLM   │ → Gemini Flash (LOW COST, ~200ms)
    │  L4: Full LLM    │ → Claude Sonnet (NORMAL COST, ~500ms)
    └──────────────────┘
```

### Key Metrics (Production)

```
📊 Cost Savings:
- Cache Hit Rate: 45% (45% of queries served from cache)
- Estimated Savings: $12.50/hour
- Light LLM Usage: 20% (reduced cost)
- Full LLM Usage: 35% (only when needed)

⚡ Performance:
- Avg Classification Latency: 15ms
- Cache Hit Latency: <5ms (exact), <20ms (semantic)
- Light LLM Latency: ~200ms
- Full LLM Latency: ~500ms
```

---

## Architecture Overview

### Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                      │
│  Controllers: distillation_router.py                     │
│  Schemas: distillation.py (Pydantic)                     │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                  APPLICATION LAYER                       │
│  Use Cases:                                              │
│  - request_distillator.py (Main orchestrator)            │
│  - get_health.py, get_metrics.py                         │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                    DOMAIN LAYER                          │
│  Services:                                               │
│  - engine.py (Main distillation engine)                  │
│  - router.py (Routing logic)                             │
│  - complexity_assessor.py (Complexity assessment)        │
│  - entity_extractor.py (Entity extraction)               │
│  - intent_classifier.py (LLM-based classification)       │
│  Entities: distillation.py                               │
│  Value Objects: distillation.py (14 types)               │
│  Ports: distillation_repository.py, distillator.py       │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                     │
│  Adapters:                                               │
│  - cache_manager.py (2-level cache)                      │
│  - static_responder.py (Template responses)              │
│  - providers/vertex_ai_distillator.py                    │
│  - providers/deepinfra_distillator.py                    │
│  Repositories:                                           │
│  - distillation_cache_repository.py                      │
│  - distillation_config_repository.py                     │
│  - distillation_static_repository.py                     │
│  - distillation_telemetry_repository.py                  │
│  Persistence: SQLAlchemy + PostgreSQL + pgvector         │
└─────────────────────────────────────────────────────────┘
```

### Request Flow

```
1. User sends chat message
   ↓
2. send_message_with_distillation.py (optional distillation pass)
   ↓
3. DistillationEngine.distill() - Main orchestrator
   ↓
4. Complexity Assessment (query length-based heuristic)
   ↓
5. Entity Extraction (tokens, protocols, chains)
   ↓
6. Cache Lookup (exact → semantic → miss)
   ↓
7. Route Decision:
   - Cache Hit? → Return cached response (FREE)
   - Simple/Trivial? → Light LLM (Gemini Flash)
   - Moderate/Complex? → Full LLM (Claude Sonnet)
   ↓
8. Log Telemetry (distillation_requests table)
   ↓
9. Return DistillationResult
```

### Routing Decision Matrix

| Complexity | Query Example | Route | Model | Cost |
|------------|--------------|-------|-------|------|
| **Trivial** | "hi", "hello" | Cache/Static | N/A | FREE |
| **Simple** | "what is ETH" | Light LLM | Gemini Flash | $0.10/1M tokens |
| **Moderate** | "swap 100 USDC to ETH" | Full LLM | Claude Sonnet | $3.00/1M tokens |
| **Complex** | "analyze my portfolio and suggest yield strategies" | Full LLM | Claude Sonnet | $3.00/1M tokens |

**Note:** Intent classification is **NOT used** for routing decisions. The system uses **complexity-based routing** only:
- Short queries (≤3 words) → SIMPLE
- Medium queries (4-10 words) → MODERATE
- Long queries (>10 words) → COMPLEX

---

## Key Concepts

### 1. Intent-Free Routing (v2.0 Architecture)

**Previous Approach (v1.0):**
- Classify query intent (swap, portfolio, price check, etc.)
- Route based on intent
- Problem: Intent classification was unreliable and slow

**Current Approach (v2.0):**
- **No intent classification** for routing
- Route based on **complexity only**
- Intent is kept for compatibility but always set to `Intent.UNCLEAR`
- LLM-based intent classification available (optional) for analytics

**Why This Works Better:**
```python
# Old way (v1.0):
intent = classify_intent(query)  # Slow, unreliable
route = route_by_intent(intent)  # Rigid routing

# New way (v2.0):
complexity = assess_complexity(query)  # Fast heuristic
route = route_by_complexity(complexity)  # Flexible routing
```

### 2. Complexity Levels

```python
class ComplexityLevel(str, Enum):
    TRIVIAL = "trivial"      # Single word, greetings
    SIMPLE = "simple"        # Short queries (≤3 words)
    MODERATE = "moderate"    # Medium queries (4-10 words)
    COMPLEX = "complex"      # Long queries (>10 words)
    EXPERT = "expert"        # Reserved for future use
```

**Complexity Assessment Logic:**
```python
query_length = len(query.split())
if query_length <= 3:
    complexity = ComplexityLevel.SIMPLE
elif query_length <= 10:
    complexity = ComplexityLevel.MODERATE
else:
    complexity = ComplexityLevel.COMPLEX
```

### 3. Route Types

```python
class RouteType(str, Enum):
    REJECT = "REJECT"        # Harmful/spam queries
    CACHE = "CACHE"          # Cache hit (exact or semantic)
    STATIC = "STATIC"        # Static template response
    LIGHT_LLM = "LIGHT_LLM"  # Gemini Flash (economy tier)
    FULL_LLM = "FULL_LLM"    # Claude Sonnet (standard tier)
```

### 4. 2-Level Caching System

**L1: Exact Match Cache**
- Storage: PostgreSQL (distillation_cache_exact)
- Key: SHA256(normalized_query + entities)
- Lookup: O(1) hash lookup
- Latency: <5ms
- TTL: Configurable (default 168 hours / 7 days)

**L2: Semantic Similarity Cache**
- Storage: PostgreSQL + pgvector (distillation_cache_semantic)
- Key: Vector embedding (1536 dimensions)
- Lookup: Cosine similarity search
- Latency: <20ms
- Similarity Threshold: 0.95 (configurable)
- TTL: Configurable (default 24 hours)

**Cache Flow:**
```
1. Generate cache key (no intent)
2. Try L1 (exact match) → Hit? Return cached
3. Try L2 (semantic) → Hit? Return cached
4. Miss → Route to LLM
5. Cache response for future requests
```

### 5. Entity Extraction

```python
@dataclass(frozen=True)
class ExtractedEntities:
    tokens: List[str]           # ETH, USDC, AAVE
    protocols: List[str]        # Uniswap, Aave, Compound
    chains: List[str]           # Ethereum, Arbitrum, Polygon
    amounts: List[Decimal]      # 100, 0.5, 1000
    addresses: List[str]        # 0x...
    time_references: List[str]  # today, last week, 30 days
```

**Use Cases:**
- Cache key generation
- Static response template injection
- Analytics (not used for routing)

### 6. Static Responses (Deprecated)

Static responses are **currently disabled** in v2.0:
- No static templates are returned
- All queries go to LLM for natural, conversational responses
- Static response infrastructure kept for future use

**Rationale:**
- Static responses felt robotic and scripted
- LLM responses are more natural and context-aware
- Minimal cost difference with caching

### 7. Telemetry & Cost Tracking

**Logged Metrics:**
```sql
-- Per-request telemetry (distillation_requests)
- request_id, user_id, query
- route_type, complexity, entities
- cache_hit, cache_level
- classification_latency_ms
- was_processed, llm_request_id

-- Hourly aggregation (distillation_telemetry_hourly)
- total_requests, cache_hit_count
- light_llm_count, full_llm_count
- avg_classification_latency_ms
- estimated_cost_saved_usd
```

**Cost Calculation:**
```python
# Estimated cost saved by caching
estimated_cost_saved = (
    cache_hit_count * avg_llm_cost_per_request
)

# Per request
avg_llm_cost_per_request = {
    ComplexityLevel.SIMPLE: Decimal("0.002"),
    ComplexityLevel.MODERATE: Decimal("0.010"),
    ComplexityLevel.COMPLEX: Decimal("0.020"),
}
```

---

## Database Schema

### Core Tables (6 Tables)

| Table | Purpose | Size | Access Pattern |
|-------|---------|------|----------------|
| **distillation_config** | System configuration | Small (~10 rows) | Read-heavy |
| **distillation_static_responses** | Template responses | Small (~50 rows) | Read-heavy (deprecated in v2.0) |
| **distillation_cache_exact** | Exact match cache | Large (10k+ rows) | Read/Write balanced |
| **distillation_cache_semantic** | Semantic similarity cache | Large (10k+ rows) | Read/Write balanced |
| **distillation_requests** | Request log | Very Large (1M+ rows) | Write-heavy |
| **distillation_telemetry_hourly** | Hourly metrics | Medium (1k+ rows) | Read-heavy |

### Schema Relationships

```
distillation_config (1)
    ↓ (read configuration)
distillation_requests (∞)
    ↓ (aggregate hourly)
distillation_telemetry_hourly (∞)

distillation_cache_exact (∞)
    ← (linked by source_request_id)
distillation_requests (∞)

distillation_cache_semantic (∞)
    ← (linked by source_request_id)
distillation_requests (∞)

distillation_static_responses (∞)
    ← (read by intent + variant)
distillation_requests (∞)
```

### Key Indexes

```sql
-- Exact cache lookup (O(1))
CREATE UNIQUE INDEX idx_exact_cache_key
ON distillation_cache_exact(cache_key);

-- Semantic cache vector similarity search
CREATE INDEX idx_semantic_cache_embedding
ON distillation_cache_semantic
USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 100);

-- Telemetry time-series queries
CREATE INDEX idx_distillation_requests_created_at
ON distillation_requests(created_at DESC);

-- User telemetry queries
CREATE INDEX idx_distillation_requests_user_id
ON distillation_requests(user_id, created_at DESC);
```

### Partitioning Strategy

**Recommended Partitioning (Not Yet Implemented):**

```sql
-- Partition distillation_requests by month
CREATE TABLE distillation_requests (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE distillation_requests_2026_01
PARTITION OF distillation_requests
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE distillation_requests_2026_02
PARTITION OF distillation_requests
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

**Benefits:**
- Faster queries (scans less data)
- Easier archival (drop old partitions)
- Better index performance

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.11+ | All business logic |
| **Web Framework** | FastAPI | 0.116.1 | HTTP endpoints |
| **Database** | PostgreSQL | 16+ | Primary storage |
| **Vector Extension** | pgvector | 0.5+ | Semantic cache |
| **ORM** | SQLAlchemy | 2.0.41 | Database access |
| **DI Container** | Dishka | 1.6.0 | Dependency injection |
| **Background Tasks** | Celery | 5.3.6 | Async processing |
| **Message Broker** | Redis | 7.0+ | Celery backend |
| **Validation** | Pydantic | 2.11.7 | Schema validation |

### AI/ML Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Primary Provider** | Vertex AI | Gemini 2.0 Flash ($0.10/1M tokens) |
| **Fallback Provider** | DeepInfra | Gemini alternatives |
| **Embedding Model** | text-embedding-3-small | Semantic cache (planned) |
| **Vector Storage** | pgvector | Embedding storage |
| **Vector Similarity** | Cosine similarity | Semantic search |

### Development Tools

| Tool | Purpose |
|------|---------|
| **Ruff** | Linting + Formatting |
| **MyPy** | Static type checking |
| **Pytest** | Testing |
| **Alembic** | Database migrations |

---

## Development Workflow

### Local Setup

```bash
# 1. Setup environment
export APP_ENV=local
make dotenv  # Generate .env from TOML config

# 2. Start database
make up.db  # PostgreSQL in Docker

# 3. Apply migrations
alembic upgrade head

# 4. Start development server
make start-dev  # FastAPI + MCP + Celery + Flower

# 5. Run tests
make code.test
```

### Configuration

**Primary Config:** `src/app/setup/config/distillation.py`

```python
@dataclass
class DistillationSettings:
    enabled: bool = True
    fail_open: bool = True  # Allow requests on failure

    # Primary provider (Vertex AI)
    provider: str = "vertex_ai"
    model: str = "gemini-2.0-flash"

    # Fallback provider (DeepInfra)
    fallback_provider: str = "deepinfra"
    fallback_model: str = "google/gemma-2-9b-it"

    # LLM parameters
    temperature: float = 0.3
    max_tokens: int = 200
    timeout_seconds: float = 5.0

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_hours: int = 168  # 7 days
```

**Runtime Config:** `distillation_config` table

```sql
-- Feature flags
UPDATE distillation_config
SET config_value = '{"enabled": true, "cache_enabled": true}'::jsonb
WHERE config_key = 'feature_flags';

-- Thresholds
UPDATE distillation_config
SET config_value = '{"min_confidence": 0.7, "semantic_similarity": 0.95}'::jsonb
WHERE config_key = 'thresholds';
```

### Adding New Complexity Rules

**File:** `src/app/domain/services/distillation/complexity_assessor.py`

```python
class ComplexityAssessor:
    def assess(self, text: str, intent: Intent) -> ComplexityLevel:
        # Custom complexity rules
        if "analyze my portfolio" in text.lower():
            return ComplexityLevel.COMPLEX

        # Default to query length heuristic
        query_length = len(text.split())
        if query_length <= 3:
            return ComplexityLevel.SIMPLE
        elif query_length <= 10:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX
```

### Adding New Static Responses

**SQL:**

```sql
INSERT INTO distillation_static_responses (
    intent, variant, response_template, template_variables, data_source, priority
) VALUES (
    'price_check',
    'default',
    'The current price of {token} is ${price} ({change_24h}% 24h change).',
    '["token", "price", "change_24h"]'::jsonb,
    'coingecko_api',
    1
);
```

**Python (Admin API):**

```python
POST /api/v1/admin/distillation/static-responses

{
    "intent": "price_check",
    "variant": "default",
    "response_template": "The current price of {token} is ${price}.",
    "template_variables": ["token", "price"],
    "data_source": "coingecko_api",
    "priority": 1,
    "is_active": true
}
```

### Testing

**Unit Tests:**

```bash
# Run all distillation tests
pytest tests/unit/domain/services/distillation/ -v

# Run specific test
pytest tests/unit/domain/services/distillation/test_engine.py::test_distill_cache_hit -v
```

**Integration Tests:**

```bash
# Run integration tests
pytest tests/integration/distillation/ -v
```

**Example Test:**

```python
@pytest.mark.asyncio
async def test_distill_simple_query():
    """Test distillation of simple query."""
    engine = DistillationEngine(...)

    result = await engine.distill(
        query="what is ETH",
        user_id=uuid4(),
    )

    assert result.route_type == RouteType.LIGHT_LLM
    assert result.complexity == ComplexityLevel.SIMPLE
    assert result.suggested_model_tier == "economy"
```

### Monitoring

**Key Metrics to Watch:**

```sql
-- Cache hit rate (target: >40%)
SELECT
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as hit_rate
FROM distillation_requests
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Avg classification latency (target: <50ms)
SELECT AVG(classification_latency_ms) as avg_latency_ms
FROM distillation_requests
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Route distribution
SELECT
    route_type,
    COUNT(*) as count,
    ROUND(COUNT(*)::FLOAT / SUM(COUNT(*)) OVER () * 100, 2) as percentage
FROM distillation_requests
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY route_type;
```

**Admin Dashboard:**

```bash
# Access admin endpoints
curl http://localhost:8000/api/v1/admin/distillation/config
curl http://localhost:8000/api/v1/admin/distillation/cache/stats
curl http://localhost:8000/api/v1/admin/distillation/telemetry/summary?hours=24
```

---

## Related Documentation

### Internal Documentation
- [**endpoints.md**](endpoints.md) - Complete API endpoint reference
- [**services.md**](services.md) - Domain/Application/Infrastructure services
- [**celery.md**](celery.md) - Background tasks and scheduled jobs
- [**Database Architecture**](../database-architecture-spec.md#domain-10-distillation-system-6-tables) - Database table specifications
- [**Agent Squad**](../AGENT_SQUAD_VERTEX_DEEPINFRA.md) - AI agent configuration

### External Resources
- [pgvector Documentation](https://github.com/pgvector/pgvector) - Vector similarity search
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs) - Primary LLM provider
- [DeepInfra Documentation](https://deepinfra.com/docs) - Fallback LLM provider
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Web framework

### Related Systems
- [**Chat System**](../chat/) - Main chat system (uses distillation)
- [**LLM Orchestration**](../llm-orchestration/) - Multi-provider LLM management
- [**AI Telemetry**](../ai-telemetry/) - Agent execution tracking

---

## Quick Start Guide

### For Developers

**1. Understanding the Flow:**

Read the [Architecture Overview](#architecture-overview) to understand how requests flow through the system.

**2. Exploring the Code:**

```bash
# Start with the main orchestrator
cat src/app/domain/services/distillation/engine.py

# Then check the routing logic
cat src/app/domain/services/distillation/router.py

# Finally, explore the cache manager
cat src/app/infrastructure/distillation/cache_manager.py
```

**3. Testing Changes:**

```bash
# Run unit tests
pytest tests/unit/domain/services/distillation/ -v

# Start local server
make start-dev

# Test endpoints
curl http://localhost:8000/api/v1/admin/distillation/config
```

### For Administrators

**1. Monitoring System Health:**

```bash
# Check configuration
GET /api/v1/admin/distillation/config

# View cache statistics
GET /api/v1/admin/distillation/cache/stats

# View recent requests
GET /api/v1/admin/distillation/telemetry/requests?limit=100
```

**2. Adjusting Configuration:**

```bash
# Enable/disable distillation
PATCH /api/v1/admin/distillation/config
{
    "enabled": true,
    "cache_enabled": true,
    "semantic_cache_enabled": true
}

# Invalidate cache
POST /api/v1/admin/distillation/cache/invalidate
{
    "cache_type": "all"
}
```

**3. Viewing Metrics:**

```bash
# Hourly summary (last 24 hours)
GET /api/v1/admin/distillation/telemetry/summary?hours=24
```

### For Data Scientists

**1. Analyzing Performance:**

```sql
-- Route distribution
SELECT route_type, COUNT(*)
FROM distillation_requests
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY route_type;

-- Cache effectiveness
SELECT
    cache_level,
    COUNT(*) as hits,
    AVG(classification_latency_ms) as avg_latency
FROM distillation_requests
WHERE cache_hit = true
GROUP BY cache_level;

-- Complexity distribution
SELECT complexity, COUNT(*)
FROM distillation_requests
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY complexity;
```

**2. Cost Analysis:**

```sql
-- Estimated cost savings
SELECT
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) FILTER (WHERE cache_hit) as cached,
    COUNT(*) FILTER (WHERE route_type = 'LIGHT_LLM') as light_llm,
    COUNT(*) FILTER (WHERE route_type = 'FULL_LLM') as full_llm,
    -- Estimate cost saved (cache hits * avg LLM cost)
    COUNT(*) FILTER (WHERE cache_hit) * 0.01 as estimated_savings_usd
FROM distillation_requests
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day DESC;
```

---

## Troubleshooting

### Common Issues

**1. High Cache Miss Rate (<20%)**

**Symptoms:**
- Most queries routed to LLM
- High costs
- Cache stats show low hit rate

**Solutions:**
```bash
# Check cache configuration
GET /api/v1/admin/distillation/config

# Verify cache is enabled
PATCH /api/v1/admin/distillation/config
{
    "cache_enabled": true
}

# Check cache entries
GET /api/v1/admin/distillation/cache/stats
```

**2. Slow Classification Latency (>100ms)**

**Symptoms:**
- `classification_latency_ms` > 100ms in telemetry
- Slow response times

**Solutions:**
```sql
-- Check complexity distribution
SELECT complexity, AVG(classification_latency_ms)
FROM distillation_requests
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY complexity;

-- Identify slow queries
SELECT original_query, classification_latency_ms
FROM distillation_requests
WHERE classification_latency_ms > 100
ORDER BY classification_latency_ms DESC
LIMIT 20;
```

**3. Celery Tasks Not Running**

**Symptoms:**
- Hourly telemetry not aggregated
- Cache not cleaned up

**Solutions:**
```bash
# Check Celery worker status
make celery.worker

# Check Celery beat (scheduler) status
make celery.beat

# View Celery logs
make logs-celery

# Manually trigger tasks
celery -A src.app.infrastructure.celery.app call aggregate_distillation_telemetry
celery -A src.app.infrastructure.celery.app call cleanup_expired_cache
```

---

## Changelog

### v2.0 (2026-01-26) - Intent-Free Routing
- **BREAKING:** Removed intent-based routing
- Switched to complexity-based routing (query length heuristic)
- Intent classification kept for compatibility but not used
- All queries go to LLM for natural responses (no static templates)
- Cache key generation updated (no intent)

### v1.0 (2025-12-01) - Initial Release
- Intent classification + routing
- 2-level caching (exact + semantic)
- Static response templates
- Hourly telemetry aggregation
- Celery background tasks

---

**Document Version:** 2.0
**Last Updated:** 2026-01-26
**Status:** Production-Ready
