# AI Brain Module Documentation

**Purpose:** Centralized knowledge and configuration management system for AI agents

## Documents

### 1. [Database Schema Architecture](./database_schema.md)
**Status:** Design Specification  
**Size:** 2,020 lines | 63 KB

Comprehensive database architecture for the AI Brain module, including:
- **6 Core Tables**: agent_configurations, agent_prompts, agent_knowledge, integration_configurations, supervisor_config, knowledge_cache_metadata
- **Redis Cache Layer**: High-performance caching with invalidation strategies
- **Access Control**: RBAC policies and row-level security
- **Migration Strategy**: 5-phase rollout plan with rollback procedures
- **Performance Optimization**: Query optimization, indexing, cache warming

## Quick Start

### View Full Schema
```bash
cat docs/ceo/ai_brain/database_schema.md
```

### Key Features

**1. Dynamic Knowledge Management**
- Agents access real-time knowledge based on enabled features
- When swap is disabled → agents don't mention swap capabilities
- Integration-aware responses (1inch, Hyperliquid, Morpho)

**2. Context-Aware Delivery**
- Different knowledge for guest vs authenticated users
- Portfolio state affects agent responses
- Multi-language support

**3. Configuration Versioning**
- Track all configuration changes
- Rollback capability
- Audit trail for compliance

**4. Redis Cache Layer**
- <50ms knowledge retrieval (p95)
- >90% cache hit rate target
- Event-driven invalidation

## Database Tables Overview

### Core Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| **agent_configurations** | Master agent settings | Enable/disable agents, LLM config, dependencies |
| **agent_prompts** | System prompts with versioning | A/B testing, multi-language, performance tracking |
| **agent_knowledge** | Dynamic knowledge entries | Integration dependencies, fallback knowledge, hierarchical |
| **integration_configurations** | External integration health | Health status, rate limits, feature impact |
| **supervisor_config** | Supervisor orchestration | Agent priorities, routing rules, timeouts |
| **knowledge_cache_metadata** | Redis cache tracking | Hit/miss rates, TTL, invalidation rules |

## Implementation Status

### Current State (JSON-based)
```
anvil_knowledge/features/*.json
├── swap.json
├── hunter_ai.json
├── ultra.json
├── lending_morpho.json
├── portfolio.json
├── wallet.json
├── gas_optimizer.json
└── risk_analyzer.json
```

**Limitations:**
- Static knowledge (no feature awareness)
- Filesystem I/O on every request
- No versioning or A/B testing
- No integration dependencies

### Future State (Database-driven)
```
PostgreSQL + Redis Cache
├── agent_configurations (19 agents)
├── agent_knowledge (100+ entries)
├── integration_configurations (11 integrations)
└── Redis cache (>90% hit rate)
```

**Benefits:**
- Dynamic knowledge based on enabled features
- <50ms retrieval time (p95)
- Configuration versioning
- Integration-aware responses
- A/B testing support

## Migration Plan

### Phase 1: Schema Deployment (Week 1)
- Create database tables
- Add indexes and constraints
- Seed initial data

### Phase 2: Data Migration (Week 2)
- Migrate JSON files to database
- Validate data integrity
- Create fallback knowledge entries

### Phase 3: Code Integration (Week 3)
- Update `KnowledgeInjector` to use database
- Add Redis caching layer
- Update dependency injection

### Phase 4: Feature Flag Rollout (Week 4)
- Gradual rollout: 10% → 25% → 50% → 100%
- Monitor performance metrics
- Validate cache hit rates

### Phase 5: Integration-Aware Responses (Week 5)
- Enable dynamic knowledge selection
- Integration health checks
- Fallback logic

## Use Cases

### Use Case 1: Swap Feature Disabled
**Scenario:** Admin disables swap feature

**Database Change:**
```sql
UPDATE agent_configurations 
SET is_enabled = FALSE 
WHERE agent_type = 'swap_workflow';
```

**Redis Invalidation:**
```redis
DEL ai_brain:knowledge:swap_overview:*:*
DEL ai_brain:config:agent:swap_workflow
```

**Agent Response:**
- Before: "You can swap tokens using Hyperliquid..."
- After: "Swap feature is currently unavailable. You can check prices and portfolio instead."

### Use Case 2: Hyperliquid Integration Down
**Scenario:** Hyperliquid API returns 503 error

**Database Update:**
```sql
UPDATE integration_configurations
SET health_status = 'down',
    health_check_error = 'API timeout'
WHERE integration_key = 'hyperliquid';
```

**Agent Response:**
- Swap knowledge shows only 1inch provider
- Fallback to alternative integrations
- User notified of limited swap options

### Use Case 3: Guest vs Authenticated User
**Scenario:** Same query from different user types

**Knowledge Retrieval:**
```sql
-- Guest user (user_type = 'guest')
SELECT content FROM agent_knowledge
WHERE knowledge_key = 'swap_overview'
  AND (user_type IS NULL OR user_type = 'guest');

-- Authenticated user (user_type = 'authenticated')
SELECT content FROM agent_knowledge
WHERE knowledge_key = 'swap_overview'
  AND (user_type IS NULL OR user_type IN ('guest', 'authenticated'));
```

**Agent Response:**
- Guest: "To swap tokens, you need to sign in first..."
- Authenticated: "Ready to swap! Connect your wallet to get started..."

## Performance Benchmarks

### Target Metrics

| Metric | Target | Current (JSON) | Future (DB + Cache) |
|--------|--------|----------------|---------------------|
| Knowledge Retrieval (p50) | <10ms | ~50ms (disk I/O) | <5ms (cache hit) |
| Knowledge Retrieval (p95) | <50ms | ~200ms | <20ms |
| Knowledge Retrieval (p99) | <100ms | ~500ms | <50ms |
| Cache Hit Rate | >90% | N/A (no cache) | >90% |
| Database Query | <20ms | N/A | <15ms |

### Load Testing Results (Projected)

**Test Scenario:** 1M knowledge queries per hour

| Component | Throughput | Latency (p95) | Resource Usage |
|-----------|------------|---------------|----------------|
| Redis Cache | 990K queries (99%) | 5ms | <1 GB RAM |
| PostgreSQL | 10K queries (1%) | 15ms | <20% CPU |
| Total | 1M queries/hour | <50ms | Efficient |

## Monitoring & Alerts

### Key Metrics

**1. Cache Performance**
```sql
SELECT 
    cache_type,
    AVG(hit_rate) as avg_hit_rate,
    SUM(hit_count) as total_hits
FROM knowledge_cache_metadata
GROUP BY cache_type;
```

**2. Knowledge Retrieval Performance**
```sql
SELECT 
    knowledge_key,
    avg_retrieval_time_ms,
    access_count
FROM agent_knowledge
WHERE avg_retrieval_time_ms > 100
ORDER BY access_count DESC;
```

**3. Integration Health**
```sql
SELECT 
    integration_key,
    health_status,
    last_health_check_at,
    error_rate
FROM integration_configurations
ORDER BY priority DESC;
```

### Alerts

| Alert | Threshold | Severity | Action |
|-------|-----------|----------|--------|
| Low cache hit rate | <80% for 5 min | Warning | Investigate cache config |
| Slow knowledge query | >100ms (p95) | Warning | Optimize query/index |
| Integration down | >5 minutes | Critical | Failover to backup |
| Database connection pool exhausted | >90% usage | Critical | Scale up connections |

## API Examples

### Get Agent Configuration
```python
from app.infrastructure.adapters.knowledge_repository_sqla import KnowledgeRepositorySQLA

# Get agent config with caching
repository = KnowledgeRepositorySQLA(db, redis)
config = await repository.get_agent_config("swap_workflow")

# Response
{
    "agent_type": "swap_workflow",
    "is_enabled": True,
    "model_name": "gemini-2.0-flash",
    "depends_on_integrations": ["hyperliquid", "1inch"],
    "version": 1
}
```

### Get Knowledge for Intent
```python
# Get knowledge with integration awareness
knowledge = await repository.get_knowledge_for_intent(
    user_query="swap 100 USDC to PURR",
    detected_intent="SWAP",
    user_type="authenticated"
)

# Response (Hyperliquid available)
{
    "feature_name": "Token Swap",
    "supported_provider": {
        "name": "Hyperliquid Spot",
        "gas_fees": "ZERO"
    },
    "supported_tokens": ["USDC", "PURR", "TRUMP", ...]
}

# Response (Hyperliquid down, fallback to 1inch)
{
    "feature_name": "Token Swap",
    "supported_provider": {
        "name": "1inch DEX Aggregator",
        "gas_fees": "Variable"
    },
    "supported_tokens": ["USDC", "ETH", "BTC", ...]
}
```

### Check Integration Health
```python
# Real-time integration health
health = await repository.get_integration_health("hyperliquid")

# Response
{
    "integration_key": "hyperliquid",
    "health_status": "healthy",
    "last_health_check_at": "2026-01-26T00:00:00Z",
    "avg_response_time_ms": 45,
    "error_rate": 0.01,
    "uptime_percentage": 99.95
}
```

## Security

### Access Control Matrix

| Role | agent_configurations | agent_prompts | agent_knowledge | integration_configurations |
|------|---------------------|---------------|-----------------|---------------------------|
| Guest | Read (views) | No access | Read (guest only) | No access |
| Authenticated | Read (views) | No access | Read (guest + auth) | No access |
| Premium | Read (views) | No access | Read (all) | No access |
| Admin | Full access | Full access | Full access | Full access |
| Supervisor (System) | Read | Read | Read | Read + Update (health) |

### Row-Level Security (RLS)

**Example: Guest users can only access guest knowledge**
```sql
CREATE POLICY guest_knowledge_read ON agent_knowledge
    FOR SELECT
    TO guest_role
    USING (
        is_enabled = TRUE AND 
        (user_type IS NULL OR user_type = 'guest')
    );
```

### Audit Logging

**All configuration changes are logged:**
```sql
SELECT 
    agent_type,
    updated_at,
    updated_by,
    version
FROM agent_configurations
WHERE updated_at > NOW() - INTERVAL '7 days'
ORDER BY updated_at DESC;
```

## Troubleshooting

### Issue: Low Cache Hit Rate (<80%)

**Diagnosis:**
```sql
SELECT cache_key, hit_count, miss_count, hit_rate
FROM knowledge_cache_metadata
WHERE hit_rate < 80
ORDER BY (hit_count + miss_count) DESC;
```

**Solutions:**
1. Increase TTL for stable knowledge
2. Pre-warm cache on startup
3. Check cache key consistency

### Issue: Slow Knowledge Queries (>100ms)

**Diagnosis:**
```sql
EXPLAIN ANALYZE
SELECT content FROM agent_knowledge
WHERE :intent = ANY(intent_patterns)
  AND is_enabled = TRUE;
```

**Solutions:**
1. Add missing indexes
2. Optimize query predicates
3. Partition large tables

### Issue: Integration Health Check Failures

**Diagnosis:**
```sql
SELECT 
    integration_key,
    health_status,
    health_check_error,
    last_health_check_at
FROM integration_configurations
WHERE health_status != 'healthy';
```

**Solutions:**
1. Check circuit breaker status
2. Verify API credentials
3. Review rate limits
4. Enable fallback integration

## Contributing

### Adding New Knowledge Entry

1. **Insert into Database**
   ```sql
   INSERT INTO agent_knowledge (
       knowledge_key, knowledge_category, agent_types,
       intent_patterns, title, content, depends_on_integrations
   ) VALUES (
       'new_feature',
       'feature',
       ARRAY['knowledge', 'chat'],
       ARRAY['NEW_FEATURE'],
       'New Feature Title',
       '{"feature_name": "New Feature", ...}',
       ARRAY['integration_name']
   );
   ```

2. **Invalidate Cache**
   ```redis
   DEL ai_brain:knowledge:new_feature:*:*
   ```

3. **Test Knowledge Retrieval**
   ```python
   knowledge = await repository.get_knowledge_for_intent(
       user_query="tell me about new feature",
       detected_intent="NEW_FEATURE",
       user_type="authenticated"
   )
   ```

### Adding New Agent Configuration

1. **Insert into Database**
   ```sql
   INSERT INTO agent_configurations (
       agent_type, agent_name, agent_category,
       is_enabled, model_name, depends_on_integrations
   ) VALUES (
       'new_agent',
       'New Agent',
       'core',
       TRUE,
       'gemini-2.0-flash',
       ARRAY['required_integration']
   );
   ```

2. **Add Agent Prompt**
   ```sql
   INSERT INTO agent_prompts (
       agent_type, prompt_type, prompt_content, is_active
   ) VALUES (
       'new_agent',
       'system',
       'You are a specialized agent for...',
       TRUE
   );
   ```

3. **Warm Cache**
   ```python
   await repository.warm_agent_config_cache("new_agent")
   ```

## References

- [Main Database Architecture Document](./database_schema.md)
- [Agent Squad Configuration](../../src/app/setup/config/agent_squad.py)
- [Knowledge Injector Service](../../src/app/application/chat/services/knowledge_injector.py)
- [User Context Aware Entity](../../src/app/domain/chat/entities/user_context_aware.py)

---

**Last Updated:** 2026-01-26  
**Version:** 1.0.0  
**Status:** Design Specification  
**Maintainer:** Database Architect (Claude Sonnet 4.5)
