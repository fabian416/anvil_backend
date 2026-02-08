# Discovery Module — Document 7: Celery Pipeline Specification

## Overview
The Celery pipeline handles all background data collection, GraphRAG extraction, and maintenance. Three dedicated queues with separate workers, plus Beat scheduler.

---

## 1. Queue Architecture

| Queue | Worker | Concurrency | Pool | Purpose |
|-------|--------|-------------|------|---------|
| `news-collection` | news@%h | 4 | gevent | News article collection from providers |
| `vault-refresh` | vaults@%h | 2 | gevent | DeFi vault snapshot refresh |
| `graphrag-extraction` | graphrag@%h | 3 | gevent | LLM entity extraction + graph writes |
| `default` | default@%h | 2 | prefork | Cleanup, maintenance |

### Deployment Commands
```bash
# News collection — rate-limited, IO bound
celery -A tasks worker -Q news-collection --concurrency=4 --pool=gevent -n news@%h

# Vault refresh — lighter load
celery -A tasks worker -Q vault-refresh --concurrency=2 --pool=gevent -n vaults@%h

# GraphRAG extraction — LLM calls, moderate load
celery -A tasks worker -Q graphrag-extraction --concurrency=3 --pool=gevent -n graphrag@%h

# Default queue (cleanup, maintenance)
celery -A tasks worker -Q default --concurrency=2 -n default@%h

# Beat scheduler
celery -A tasks beat --scheduler celery.beat:PersistentScheduler
```

---

## 2. Beat Schedule

| Task | Schedule | Queue | Rate Limit |
|------|----------|-------|------------|
| `collect_news_all_sections` | Every 15 min (`*/15`) | default → fans out to news-collection | None |
| `collect_vault_snapshots` | Every 5 min (`*/5`) | vault-refresh | None |
| `cleanup_expired_articles` | Daily 3:00 AM | default | None |
| `graph_maintenance` | Daily 4:00 AM | graphrag-extraction | None |

```python
DISCOVERY_BEAT_SCHEDULE = {
    "discovery-collect-news": {
        "task": "tasks.discovery_tasks.collect_news_all_sections",
        "schedule": crontab(minute="*/15"),
    },
    "discovery-collect-vaults": {
        "task": "tasks.discovery_tasks.collect_vault_snapshots",
        "schedule": crontab(minute="*/5"),
    },
    "discovery-cleanup-expired": {
        "task": "tasks.discovery_tasks.cleanup_expired_articles",
        "schedule": crontab(hour=3, minute=0),
    },
    "discovery-graph-maintenance": {
        "task": "tasks.discovery_tasks.graph_maintenance",
        "schedule": crontab(hour=4, minute=0),
    },
}
```

---

## 3. Task: collect_news_all_sections (Fan-Out)

**Trigger:** Beat every 15 minutes
**Queue:** default
**Retries:** 2, delay 60s

### Flow
1. Query DB for all active leaf sections (sections with no children that have is_active=true)
2. For each section: dispatch `collect_section_news.delay(section_id, slug, parent_slug, keywords)`
3. Return count of dispatched tasks

**Expected volume:** ~30-50 sections dispatched per cycle.

---

## 4. Task: collect_section_news (Per-Section)

**Trigger:** Dispatched by fan-out
**Queue:** news-collection
**Retries:** 3, delay 30s
**Rate limit:** `4/m` (max 4 sections/minute → stays under Sonar 50 RPM)

### Flow
```
1. Build provider chain based on section type:
   ├── All sections: PerplexitySonarAdapter (primary, priority=100)
   ├── crypto_defi sections: + CryptoPanicAdapter (fallback, priority=50)
   └── Other sections: + NewsAPIAdapter (fallback, priority=50)

2. Try providers in priority order:
   ├── Call provider.fetch_news(keywords, section_slug, max_results=15)
   ├── If returns articles → stop, use these
   ├── If fails → try next provider
   └── If all fail → log warning, return 0

3. For each RawArticle:
   ├── Compute content_hash = SHA-256(lower(title) + "|" + source_url)
   ├── Map to NewsArticle domain entity
   ├── UPSERT to DB (skip if hash exists)
   └── Track new_article_ids

4. Chain GraphRAG extraction for new articles:
   └── extract_article_graph.si(new_article_ids).apply_async(countdown=5)
       (5s delay to let DB commit)

5. Return articles_saved count
```

### Provider Failover Details
- **Sonar 200 OK** → use articles, done
- **Sonar 429** → skip to fallback, log warning
- **Sonar 402** → disable Sonar permanently, log CRITICAL, continue with fallback
- **Sonar 5xx/timeout** → increment consecutive_errors counter
  - < 10 errors → retry with backoff
  - ≥ 10 errors → circuit breaker trips, disable Sonar
- **All providers fail** → log error, return 0 (beat will retry in 15 min)

### Structured Logging
```json
{
  "event": "section_collection_complete",
  "section_slug": "us_politics",
  "provider_used": "perplexity_sonar",
  "articles_fetched": 12,
  "articles_saved": 8,
  "articles_duplicate": 4,
  "latency_ms": 3200
}
```

---

## 5. Task: extract_article_graph (GraphRAG)

**Trigger:** Chained from collect_section_news (5s delay)
**Queue:** graphrag-extraction
**Retries:** 2
**Rate limit:** `10/m` (LLM rate limiting)

### Flow
```
1. Load articles from DB by IDs

2. Extract in batches of 5:
   ├── For each article:
   │   ├── Build prompt: title + summary + source + section + tags
   │   ├── Call Gemini 2.0 Flash → structured JSON
   │   └── Parse: entities, relationships, events, sentiment
   │
   └── asyncio.gather for batch parallelism

3. Upsert to Apache AGE graph:
   ├── MERGE entity nodes (create if new, update last_seen + mention_count)
   ├── MERGE relationship edges (update confidence + last_article)
   └── CREATE mentioned_in edges (article → entity, with sentiment)

4. Return total_edges_created
```

### Cost per extraction
- Input: ~200 tokens (article title + summary + metadata)
- Output: ~500 tokens (entities + relationships JSON)
- Cost per article: ~$0.00007 (Gemini 2.0 Flash at $0.10/1M tokens)
- Daily volume: ~500 articles → ~$0.035/day → ~$1/month

### Structured Logging
```json
{
  "event": "graphrag_extraction_complete",
  "articles_processed": 8,
  "entities_extracted": 24,
  "relationships_extracted": 18,
  "events_detected": 2,
  "edges_created": 42,
  "latency_ms": 4500,
  "llm_tokens_in": 1600,
  "llm_tokens_out": 4000
}
```

---

## 6. Task: collect_vault_snapshots

**Trigger:** Beat every 5 minutes
**Queue:** vault-refresh
**Retries:** 2

### Flow
```
1. Fetch from DeFiLlama:
   ├── GET https://yields.llama.fi/pools
   ├── Filter: protocol ∈ {morpho, aave-v3, compound-v3}
   ├── Filter: chain ∈ {Base, Ethereum}
   ├── Filter: tvl_usd ≥ 100,000
   └── Sort by total APY desc, keep top 50

2. Deactivate old snapshots (is_active=false where snapshot_at < 1h ago)

3. Insert new VaultSnapshot rows (is_active=true)

4. Invalidate cache: discovery:vaults:*

5. Return saved count
```

---

## 7. Task: cleanup_expired_articles

**Trigger:** Beat daily at 3:00 AM
**Queue:** default

### Flow
```
1. DELETE FROM discovery_news_articles WHERE created_at < NOW() - INTERVAL '30 days'
   (TimescaleDB retention policy also handles this, but explicit cleanup catches edge cases)
2. Log deleted count
3. Return count
```

---

## 8. Task: graph_maintenance

**Trigger:** Beat daily at 4:00 AM
**Queue:** graphrag-extraction

### Flow
```
1. Prune stale entities:
   └── DELETE nodes where last_seen < NOW() - 30 days AND mention_count < 3

2. Recalculate entity importance:
   └── PageRank centrality across graph → update importance_score on nodes

3. Pre-compute risk propagation:
   └── For top 50 protocols by mention_count:
       └── Run query_risk_propagation() → cache results in Redis (TTL 24h)

4. Graph stats logging:
   └── Count total nodes, edges, entity types → structured log
```

---

## 9. Monitoring & Alerting

### Key Metrics to Track
| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| Sonar consecutive_errors | ≥ 5 | Warning: provider degraded |
| Sonar consecutive_errors | ≥ 10 | Critical: circuit breaker tripped |
| Sonar 402 response | Any | Critical: credits exhausted |
| Daily Sonar cost | > $25/day | Warning: unexpected cost spike |
| Articles collected/day | < 100 | Warning: collection may be broken |
| GraphRAG extraction failures | > 20% | Warning: LLM issues |
| Celery task queue depth | > 100 | Warning: workers falling behind |
| Feed cache miss rate | > 80% | Info: may need longer TTL |

### Cost Tracking
Every Sonar request logs token usage:
```json
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

Aggregate daily via log queries → dashboard.

---

## 10. Environment Variables

```bash
# Perplexity Sonar (PRIMARY)
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxx
PERPLEXITY_MODEL=sonar
PERPLEXITY_SEARCH_CONTEXT=low
PERPLEXITY_RPM_LIMIT=50

# Fallback Providers
NEWSAPI_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CRYPTOPANIC_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VAULTSFYI_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# GraphRAG (Gemini)
GOOGLE_AI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GRAPHRAG_MODEL=gemini-2.0-flash
GRAPHRAG_BATCH_SIZE=5
```

---

## 11. Full Pipeline Timeline (15-min cycle)

```
T+0:00  Beat triggers collect_news_all_sections
T+0:01  Fan-out: 30 collect_section_news tasks dispatched
T+0:01  Rate limit: 4 sections/min → first 4 start immediately
T+0:02  Sonar returns articles for section 1-4
T+0:02  UPSERT articles to DB
T+0:07  extract_article_graph chained (5s delay after each section)
T+0:07  GraphRAG: Gemini extracts entities for batch 1
T+0:08  Apache AGE: MERGE entities + relationships
T+7:30  All 30 sections collected (~7.5 min at 4/min)
T+8:00  All GraphRAG extractions complete
T+8:00  Pipeline idle until T+15:00

T+5:00  (parallel) collect_vault_snapshots runs
T+5:02  DeFiLlama returns 50 vaults
T+5:03  Deactivate old → insert new → cache invalidated
```
