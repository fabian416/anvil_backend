# AI Brain Module - Quick Reference Guide

**1-Page Overview for Developers**

---

## What is AI Brain?

**Centralized knowledge and configuration system** that makes agents aware of:
- Which features are enabled/disabled
- Which integrations are healthy/down
- User context (guest vs authenticated)
- Real-time configuration changes

**Result:** Agents give accurate, context-aware responses without hardcoded knowledge.

---

## Core Concept

### Before (Static JSON)
```
User asks: "Can I swap ETH?"
Agent loads: swap.json (always says "yes")
Reality: Hyperliquid is down
Result: ❌ Agent gives wrong answer
```

### After (Dynamic Database)
```
User asks: "Can I swap ETH?"
Agent queries: ai_brain database
Database checks: Is Hyperliquid healthy?
Result: ✅ Agent says "Hyperliquid is down, try 1inch instead"
```

---

## 6 Database Tables

### 1. agent_configurations
**What:** Master settings for all agents  
**Key Info:** Enable/disable agents, model settings, dependencies  
**Example:**
```sql
agent_type = 'swap_workflow'
is_enabled = TRUE
depends_on_integrations = ['hyperliquid', '1inch']
```

### 2. agent_prompts
**What:** System prompts with A/B testing  
**Key Info:** Versioned prompts, performance tracking  
**Example:**
```sql
agent_type = 'knowledge'
prompt_type = 'system'
variant_name = 'variant_a'
traffic_percentage = 50.00
```

### 3. agent_knowledge
**What:** Dynamic knowledge entries (replaces JSON files)  
**Key Info:** Integration dependencies, fallback knowledge  
**Example:**
```sql
knowledge_key = 'swap_overview'
depends_on_integrations = ['hyperliquid']
fallback_knowledge_id = <1inch_swap_knowledge>
```

### 4. integration_configurations
**What:** External integration health tracking  
**Key Info:** Health status, error rates, feature impact  
**Example:**
```sql
integration_key = 'hyperliquid'
health_status = 'healthy'
impacts_features = ['swap', 'trading']
```

### 5. supervisor_config
**What:** Supervisor orchestration settings  
**Key Info:** Agent priorities, routing rules  
**Example:**
```sql
supervisor_type = 'authenticated'
max_agents_per_request = 5
agent_priorities = {"swap_workflow": 200}
```

### 6. knowledge_cache_metadata
**What:** Redis cache tracking  
**Key Info:** Hit rates, TTL, invalidation triggers  
**Example:**
```sql
cache_key = 'ai_brain:knowledge:swap_overview:guest:en'
hit_rate = 95.50
ttl_seconds = 3600
```

---

## Redis Cache Keys

### Pattern
```
ai_brain:{component}:{identifier}:{context}
```

### Examples
```redis
# Knowledge entries
ai_brain:knowledge:swap_overview:guest:en
ai_brain:knowledge:hunter_ai_sentiment:authenticated:es

# Agent configs
ai_brain:config:agent:swap_workflow
ai_brain:config:agent:knowledge

# Integration status
ai_brain:integration:hyperliquid:status
ai_brain:integration:1inch:status
```

---

## Common Operations

### 1. Disable Swap Feature
```sql
-- Database
UPDATE agent_configurations 
SET is_enabled = FALSE 
WHERE agent_type = 'swap_workflow';

-- Redis
DEL ai_brain:knowledge:swap_overview:*:*
DEL ai_brain:config:agent:swap_workflow
```

**Result:** Agents stop mentioning swap in responses

### 2. Mark Integration as Down
```sql
-- Database
UPDATE integration_configurations
SET health_status = 'down',
    health_check_error = 'API timeout'
WHERE integration_key = 'hyperliquid';

-- Redis (auto-invalidated)
DEL ai_brain:integration:hyperliquid:status
```

**Result:** Agents use fallback integrations

### 3. Add New Knowledge
```sql
-- Insert knowledge
INSERT INTO agent_knowledge (
    knowledge_key, knowledge_category, agent_types,
    intent_patterns, title, content
) VALUES (
    'new_feature', 'feature', ARRAY['knowledge', 'chat'],
    ARRAY['NEW_FEATURE'], 'New Feature', '{"data": "..."}'
);

-- Cache (auto-warmed on first request)
```

**Result:** Agents can answer questions about new feature

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Knowledge retrieval (p95) | <50ms |
| Cache hit rate | >90% |
| Database query | <20ms |
| Integration health check | Every 1 minute |

---

## Access Control

| Role | Read | Write |
|------|------|-------|
| Guest | Basic knowledge only | ❌ |
| Authenticated | Full knowledge (non-premium) | ❌ |
| Premium | All knowledge | ❌ |
| Admin | All tables | ✅ |
| System | All tables | Cache metadata only |

---

## Migration Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| 1. Schema Deployment | Week 1 | 🔵 Planned |
| 2. Data Migration | Week 2 | 🔵 Planned |
| 3. Code Integration | Week 3 | 🔵 Planned |
| 4. Feature Flag Rollout | Week 4 | 🔵 Planned |
| 5. Integration-Aware | Week 5 | 🔵 Planned |

---

## Key Code Files

### Infrastructure
```
src/app/infrastructure/adapters/knowledge_repository_sqla.py
src/app/infrastructure/persistence_sqla/mappings/ai_brain.py
```

### Application
```
src/app/application/chat/services/knowledge_injector.py
src/app/application/chat/services/integration_health_checker.py
```

### Domain
```
src/app/domain/ports/knowledge_repository.py
src/app/domain/entities/agent_configuration.py
```

### Setup/Config
```
src/app/setup/ioc/chat.py (dependency injection)
src/app/setup/config/agent_squad.py (current TOML config)
```

---

## Quick Queries

### Check Agent Status
```sql
SELECT agent_type, is_enabled, depends_on_integrations
FROM agent_configurations
ORDER BY priority DESC;
```

### Check Integration Health
```sql
SELECT integration_key, health_status, last_health_check_at
FROM integration_configurations
WHERE health_status != 'healthy';
```

### Check Cache Performance
```sql
SELECT cache_type, AVG(hit_rate) as avg_hit_rate
FROM knowledge_cache_metadata
GROUP BY cache_type;
```

### Find Slow Knowledge Queries
```sql
SELECT knowledge_key, avg_retrieval_time_ms, access_count
FROM agent_knowledge
WHERE avg_retrieval_time_ms > 100
ORDER BY access_count DESC;
```

---

## Rollback Procedure

**If issues arise:**

```python
# 1. Immediate: Disable feature flag
use_database_knowledge = False  # Reverts to JSON files

# 2. Redis: Flush AI Brain cache
redis-cli --scan --pattern "ai_brain:*" | xargs redis-cli del

# 3. Database: Rollback migration
alembic downgrade -1
```

---

## Links

- **Full Schema:** [database_schema.md](./database_schema.md) (2,020 lines)
- **README:** [README.md](./README.md) (485 lines)
- **Knowledge Injector:** `src/app/application/chat/services/knowledge_injector.py`
- **Agent Config:** `src/app/setup/config/agent_squad.py`

---

**Last Updated:** 2026-01-26  
**Version:** 1.0.0  
**Print this page for quick reference during implementation!**
