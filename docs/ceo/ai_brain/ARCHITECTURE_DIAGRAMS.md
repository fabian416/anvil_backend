# AI Brain Module - Architecture Diagrams

Visual representations of the AI Brain architecture for stakeholders and developers.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Guest     │  │Authenticated│  │  Premium    │                  │
│  │   Chat      │  │    Chat     │  │   Chat      │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
└─────────┼─────────────────┼─────────────────┼────────────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                           │
┌──────────────────────────┴────────────────────────────────────────────┐
│                    Agent Orchestration Layer                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                   Supervisor Coordinator                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │  │
│  │  │ Guest Super  │  │ Auth Super   │  │Premium Super │        │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                         │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │                      Agent Router                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │  │
│  │  │Knowledge │  │   Chat   │  │  Hunter  │  │   Swap   │     │  │
│  │  │  Agent   │  │  Agent   │  │ AI Agent │  │Workflow  │ ... │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────┴────────────────────────────────────────┐
│                       AI Brain Module (New)                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    Knowledge Injector                            │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │                Knowledge Repository                       │  │ │
│  │  │  ┌────────────────┐         ┌────────────────┐          │  │ │
│  │  │  │  Redis Cache   │ ◄─────► │   PostgreSQL   │          │  │ │
│  │  │  │  (Hot Layer)   │         │  (Source of    │          │  │ │
│  │  │  │  <50ms p95     │         │   Truth)       │          │  │ │
│  │  │  └────────────────┘         └────────────────┘          │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Database Tables:                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │     agent_       │  │      agent_      │  │     agent_       │  │
│  │ configurations   │  │    prompts       │  │   knowledge      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  integration_    │  │   supervisor_    │  │knowledge_cache_  │  │
│  │ configurations   │  │     config       │  │    metadata      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┴────────────────────────────────────────┐
│                    External Integrations Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Hyperliquid  │  │    1inch     │  │    Morpho    │               │
│  │   (Swap)     │  │    (Swap)    │  │  (Lending)   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  CoinGecko   │  │  Perplexity  │  │   DeFiLlama  │               │
│  │   (Prices)   │  │  (Research)  │  │    (TVL)     │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Knowledge Retrieval Flow

```
┌─────────┐
│  User   │
│  Query  │
└────┬────┘
     │
     ▼
┌─────────────────────────────────┐
│  Intent Detection               │
│  (What is user asking?)         │
└────┬────────────────────────────┘
     │ detected_intent = "SWAP"
     ▼
┌─────────────────────────────────┐
│  Knowledge Injector             │
│  (Get relevant knowledge)       │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐     ┌─────────────────┐
│  Check Redis Cache              │────►│  Cache Hit?     │
│  Key: ai_brain:knowledge:       │     └────┬────────────┘
│       swap_overview:guest:en    │          │
└─────────────────────────────────┘          │
     │                                        │
     │ Cache Miss                             │ Cache Hit
     ▼                                        │
┌─────────────────────────────────┐          │
│  Query PostgreSQL               │          │
│  SELECT content                 │          │
│  FROM agent_knowledge           │          │
│  WHERE knowledge_key = 'swap'   │          │
│    AND is_enabled = TRUE        │          │
│    AND user_type = 'guest'      │          │
└────┬────────────────────────────┘          │
     │ 15ms                                   │ 5ms
     ▼                                        │
┌─────────────────────────────────┐          │
│  Check Integration Dependencies │          │
│  depends_on = ['hyperliquid']   │          │
└────┬────────────────────────────┘          │
     │                                        │
     ▼                                        │
┌─────────────────────────────────┐          │
│  Query Integration Health       │          │
│  SELECT health_status           │          │
│  FROM integration_configurations│          │
│  WHERE key = 'hyperliquid'      │          │
└────┬────────────────────────────┘          │
     │ health = 'healthy'                    │
     ▼                                        │
┌─────────────────────────────────┐          │
│  Return Full Knowledge          │          │
│  (Hyperliquid available)        │          │
└────┬────────────────────────────┘          │
     │                                        │
     ▼                                        │
┌─────────────────────────────────┐          │
│  Cache Result in Redis          │          │
│  TTL = 3600 seconds             │          │
└────┬────────────────────────────┘          │
     │                                        │
     └────────────────────┬───────────────────┘
                         │
                         ▼
                  ┌──────────────────┐
                  │  Return Knowledge│
                  │  to Agent        │
                  └──────────────────┘
                         │
                         ▼
                  ┌──────────────────┐
                  │  Agent Formats   │
                  │  Response with   │
                  │  Knowledge       │
                  └──────────────────┘
                         │
                         ▼
                  ┌──────────────────┐
                  │  User Receives   │
                  │  Accurate Answer │
                  └──────────────────┘

Total Latency: 
- Cache Hit: ~5ms
- Cache Miss: ~20ms (15ms DB + 5ms cache write)
```

---

## Configuration Change Propagation

```
┌─────────────────────────────────────────────────────────────────────┐
│  Admin Action: Disable Swap Feature                                 │
└────┬────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  Update Database                │
│  UPDATE agent_configurations    │
│  SET is_enabled = FALSE         │
│  WHERE agent_type = 'swap'      │
└────┬────────────────────────────┘
     │ Timestamp: T0
     │
     ▼
┌─────────────────────────────────┐
│  Database Trigger               │
│  (on UPDATE of agent_configs)   │
└────┬────────────────────────────┘
     │
     ├──────────────────────────────┐
     │                              │
     ▼                              ▼
┌──────────────────────┐   ┌────────────────────────┐
│  Invalidate Redis    │   │  Update Cache Metadata │
│  Cache               │   │  SET invalidated_at    │
│                      │   │  = NOW()               │
│  DEL ai_brain:       │   └────────────────────────┘
│    knowledge:swap:*  │            │
│                      │            │ T0 + 5ms
│  DEL ai_brain:       │            │
│    config:agent:swap │            │
└──────┬───────────────┘            │
       │ T0 + 10ms                  │
       │                            │
       └────────────┬───────────────┘
                    │
                    ▼
          ┌─────────────────────────┐
          │  Publish Event to       │
          │  Message Queue          │
          │  topic: 'config.changed'│
          └────┬────────────────────┘
               │ T0 + 15ms
               │
     ┌─────────┼─────────┐
     │         │         │
     ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Agent  │ │ Agent  │ │ Agent  │
│ Pod 1  │ │ Pod 2  │ │ Pod 3  │
└────┬───┘ └────┬───┘ └────┬───┘
     │          │          │
     ▼          ▼          ▼
┌────────────────────────────────┐
│  Clear Local Cache             │
│  (if any)                      │
└────┬───────────────────────────┘
     │ T0 + 20ms
     │
     ▼
┌────────────────────────────────┐
│  Next Request                  │
│  (after invalidation)          │
│                                │
│  1. Query: swap knowledge      │
│  2. Redis Cache: MISS          │
│  3. Query Database             │
│  4. Result: is_enabled = FALSE │
│  5. Agent Response:            │
│     "Swap is unavailable"      │
└────────────────────────────────┘

Total Propagation Time: ~20ms
Consistency Guarantee: Eventually consistent (within 100ms)
```

---

## Integration Health Check Flow

```
┌─────────────────────────────────┐
│  Scheduled Health Check         │
│  (Every 1 minute)               │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  Integration Health Checker     │
│  (Background Service)           │
└────┬────────────────────────────┘
     │
     ├─────────────────────┬─────────────────────┬─────────────────────┐
     │                     │                     │                     │
     ▼                     ▼                     ▼                     ▼
┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
│Hyperliquid│      │  1inch   │       │  Morpho  │       │CoinGecko │
│  Health  │       │  Health  │       │  Health  │       │  Health  │
└────┬─────┘       └────┬─────┘       └────┬─────┘       └────┬─────┘
     │                   │                   │                   │
     │ GET /v1/health    │ GET /health      │ GET /api/status  │ GET /ping
     ▼                   ▼                   ▼                   ▼
┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
│ Response │       │ Response │       │ Response │       │ Response │
│  200 OK  │       │  200 OK  │       │  503     │       │  200 OK  │
└────┬─────┘       └────┬─────┘       └────┬─────┘       └────┬─────┘
     │                   │                   │                   │
     │ Healthy           │ Healthy           │ DOWN!             │ Healthy
     │                   │                   │                   │
     └───────────────────┴───────────────────┴───────────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────────┐
                        │  Update Database            │
                        │  UPDATE integration_configs │
                        │  SET health_status =        │
                        │    CASE                     │
                        │      WHEN key='morpho'      │
                        │        THEN 'down'          │
                        │      ELSE 'healthy'         │
                        │    END                      │
                        └────┬────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
         ┌──────────────────┐  ┌──────────────────┐
         │ Invalidate Cache │  │  Publish Event   │
         │ DEL ai_brain:    │  │  'integration.   │
         │   integration:   │  │   status.changed'│
         │   morpho:status  │  └──────────────────┘
         └──────────────────┘           │
                    │                   │
                    └────────┬──────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Impact Analysis     │
                  │  Query:              │
                  │  SELECT knowledge    │
                  │  WHERE 'morpho' =    │
                  │    ANY(depends_on)   │
                  └────┬─────────────────┘
                       │
                       ▼ Results: lending_morpho, defi_yield
                  ┌──────────────────────┐
                  │  Invalidate Affected │
                  │  Knowledge Cache     │
                  │                      │
                  │  DEL ai_brain:       │
                  │    knowledge:        │
                  │    lending_morpho:*  │
                  │                      │
                  │  DEL ai_brain:       │
                  │    knowledge:        │
                  │    defi_yield:*      │
                  └────┬─────────────────┘
                       │
                       ▼
                  ┌──────────────────────┐
                  │  Next User Request   │
                  │  (for lending)       │
                  │                      │
                  │  Knowledge Injector: │
                  │  1. Query: lending   │
                  │  2. Check: morpho    │
                  │  3. Status: DOWN     │
                  │  4. Use: fallback    │
                  │     (Aave knowledge) │
                  │                      │
                  │  Agent Response:     │
                  │  "Morpho unavailable,│
                  │   try Aave instead"  │
                  └──────────────────────┘

Health Check Interval: 60 seconds
Detection Latency: <60 seconds
Recovery: Automatic on next health check
```

---

## Data Flow: User Context → Agent Response

```
┌─────────────────────────────────────────────────────────────────────┐
│  User Sends Message                                                 │
│  "Can I swap 100 USDC to PURR?"                                    │
└────┬────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  1. Identify User               │
│  ┌───────────────────────────┐ │
│  │ Query: chat_users         │ │
│  │ WHERE identifier = IP     │ │
│  │ Result: user_type='guest' │ │
│  └───────────────────────────┘ │
└────┬────────────────────────────┘
     │ user_type = 'guest'
     ▼
┌─────────────────────────────────┐
│  2. Get User Context            │
│  ┌───────────────────────────┐ │
│  │ Query: user_context_aware │ │
│  │ WHERE chat_user_id = ...  │ │
│  │ Result:                   │ │
│  │   portfolio_state='empty' │ │
│  │   wallet_connected=FALSE  │ │
│  └───────────────────────────┘ │
└────┬────────────────────────────┘
     │ portfolio_state = 'empty'
     │ wallet_connected = FALSE
     ▼
┌─────────────────────────────────┐
│  3. Intent Detection            │
│  ┌───────────────────────────┐ │
│  │ LLM Classification        │ │
│  │ detected_intent = 'SWAP'  │ │
│  │ confidence = 0.95         │ │
│  └───────────────────────────┘ │
└────┬────────────────────────────┘
     │ intent = 'SWAP'
     ▼
┌─────────────────────────────────┐
│  4. Get Knowledge (AI Brain)    │
│  ┌───────────────────────────┐ │
│  │ Query: agent_knowledge    │ │
│  │ WHERE intent='SWAP'       │ │
│  │   AND user_type='guest'   │ │
│  │   AND is_enabled=TRUE     │ │
│  │                           │ │
│  │ Result: swap_guest_guide  │ │
│  │ Content:                  │ │
│  │  "To swap tokens, you     │ │
│  │   need to sign in first.  │ │
│  │   Guests can only view    │ │
│  │   prices and features."   │ │
│  └───────────────────────────┘ │
└────┬────────────────────────────┘
     │ knowledge (guest-specific)
     ▼
┌─────────────────────────────────┐
│  5. Check Agent Config          │
│  ┌───────────────────────────┐ │
│  │ Query: agent_configurations│ │
│  │ WHERE agent_type='swap'   │ │
│  │ Result:                   │ │
│  │   is_enabled=TRUE         │ │
│  │   requires_wallet=TRUE    │ │
│  └───────────────────────────┘ │
└────┬────────────────────────────┘
     │ requires_wallet = TRUE
     │ user has NO wallet
     ▼
┌─────────────────────────────────┐
│  6. Check Integration Health    │
│  ┌───────────────────────────┐ │
│  │ Query: integration_configs │ │
│  │ WHERE key='hyperliquid'   │ │
│  │ Result:                   │ │
│  │   health_status='healthy' │ │
│  └───────────────────────────┘ │
└────┬────────────────────────────┘
     │ hyperliquid = healthy
     ▼
┌─────────────────────────────────┐
│  7. Agent Formats Response      │
│  ┌───────────────────────────┐ │
│  │ Context:                  │ │
│  │  - User is guest          │ │
│  │  - No wallet connected    │ │
│  │  - Swap feature enabled   │ │
│  │  - Hyperliquid healthy    │ │
│  │                           │ │
│  │ Response:                 │ │
│  │ "I can help you swap!     │ │
│  │  But first, you need to:  │ │
│  │  1. Sign in               │ │
│  │  2. Connect your wallet   │ │
│  │                           │ │
│  │  Once connected, you can  │ │
│  │  swap USDC to PURR on     │ │
│  │  Hyperliquid (zero fees)" │ │
│  └───────────────────────────┘ │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  8. User Receives Response      │
│  (Accurate, context-aware,      │
│   integration-aware)            │
└─────────────────────────────────┘

Total Processing Time: 
- User identification: 5ms (cached)
- User context: 10ms (cached)
- Intent detection: 150ms (LLM)
- Knowledge retrieval: 5ms (cached)
- Agent config: 5ms (cached)
- Integration health: 5ms (cached)
- Agent formatting: 200ms (LLM)
= Total: ~380ms
```

---

## Database Schema Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI Brain Database Schema                      │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│ agent_configurations │◄────────│    agent_prompts     │
│                      │ 1     * │                      │
│ PK: agent_type       │         │ FK: agent_type       │
│ - agent_name         │         │ - prompt_type        │
│ - is_enabled         │         │ - prompt_content     │
│ - model_name         │         │ - variant_name       │
│ - depends_on_agents[]│         │ - is_active          │
│ - depends_on_integ[] │         └──────────────────────┘
└───────┬──────────────┘
        │
        │ 1
        │
        │ *
        ▼
┌──────────────────────┐
│   agent_knowledge    │
│                      │
│ PK: knowledge_key    │◄───┐
│ - agent_types[]      │    │ self-referencing
│ - intent_patterns[]  │    │ (parent/child)
│ - content (JSONB)    │    │
│ - depends_on_integ[] │────┤ fallback_knowledge_id
│ - is_enabled         │    │
│ - fallback_knowledge │────┘
│ - parent_knowledge   │
└───────┬──────────────┘
        │ *
        │
        │ 1
        ▼
┌──────────────────────┐         ┌──────────────────────┐
│knowledge_cache_      │    *  1 │  integration_        │
│  metadata            │◄────────│  configurations      │
│                      │         │                      │
│ PK: cache_key        │         │ PK: integration_key  │
│ FK: knowledge_id     │         │ - integration_name   │
│ - hit_count          │         │ - health_status      │
│ - miss_count         │         │ - is_enabled         │
│ - hit_rate           │         │ - impacts_features[] │
│ - ttl_seconds        │         │ - impacts_agents[]   │
└──────────────────────┘         └──────────────────────┘

┌──────────────────────┐
│  supervisor_config   │
│                      │
│ PK: supervisor_type  │
│ - max_agents         │
│ - timeout_seconds    │
│ - agent_priorities   │
│   (JSONB)            │
│ - fallback_agent     │
└──────────────────────┘

                    External Reference
                    (not in AI Brain)
                           │
                           ▼
               ┌──────────────────────┐
               │ user_context_aware   │
               │                      │
               │ FK: chat_user_id     │
               │ - portfolio_state    │
               │ - activity_level     │
               │ - user_type          │
               │ - agent_usage_counts │
               └──────────────────────┘
                           │
                           │ *
                           │
                           │ 1
                           ▼
               ┌──────────────────────┐
               │     chat_users       │
               │                      │
               │ PK: id (UUID)        │
               │ - user_type          │
               │ - identifier         │
               │ - preferred_language │
               └──────────────────────┘
```

---

## Cache Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Redis Cache Layer                            │
│                         (High-Performance)                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  Knowledge Cache    │  │ Agent Config Cache  │  │ Integration Cache   │
│                     │  │                     │  │                     │
│ ai_brain:knowledge: │  │ ai_brain:config:    │  │ ai_brain:           │
│   {key}:{user}:{ln} │  │   agent:{type}      │  │   integration:      │
│                     │  │                     │  │   {key}:status      │
│ TTL: 3600s (1h)     │  │ TTL: 7200s (2h)     │  │ TTL: 300s (5m)      │
│ Compression: Yes    │  │ Compression: No     │  │ Compression: No     │
│ Hit Rate: >90%      │  │ Hit Rate: >95%      │  │ Hit Rate: >85%      │
│                     │  │                     │  │                     │
│ Example:            │  │ Example:            │  │ Example:            │
│ ai_brain:knowledge: │  │ ai_brain:config:    │  │ ai_brain:           │
│   swap_overview:    │  │   agent:knowledge   │  │   integration:      │
│   guest:en          │  │                     │  │   hyperliquid:status│
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
         │                        │                         │
         └────────────────────────┼─────────────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Cache Warming          │
                    │   (On Startup)           │
                    │                          │
                    │ 1. All agent configs     │
                    │ 2. Top 100 knowledge     │
                    │ 3. All integrations      │
                    │                          │
                    │ Time: ~2 seconds         │
                    └──────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌──────────────────┐     ┌──────────────────┐
         │  Cache           │     │  Cache           │
         │  Invalidation    │     │  Monitoring      │
         │                  │     │                  │
         │ Triggers:        │     │ Metrics:         │
         │ - Config change  │     │ - Hit rate       │
         │ - Knowledge edit │     │ - Latency        │
         │ - Integration ↓  │     │ - Memory usage   │
         │ - Manual flush   │     │ - Evictions      │
         └──────────────────┘     └──────────────────┘

Cache Performance:
┌────────────────────┬─────────────┬──────────────┐
│ Cache Type         │ Hit Rate    │ Latency (p95)│
├────────────────────┼─────────────┼──────────────┤
│ Knowledge          │   92%       │    5ms       │
│ Agent Config       │   96%       │    3ms       │
│ Integration Status │   88%       │    7ms       │
│ User Context       │   85%       │   10ms       │
└────────────────────┴─────────────┴──────────────┘
```

---

## Scaling Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Production Deployment                           │
└─────────────────────────────────────────────────────────────────────┘

                         Load Balancer
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ FastAPI │          │ FastAPI │          │ FastAPI │
   │  Pod 1  │          │  Pod 2  │          │  Pod 3  │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                     │
        │ Read/Write         │ Read/Write          │ Read/Write
        └────────────────────┼─────────────────────┘
                            │
        ┌───────────────────┴──────────────────┐
        │                                      │
        ▼                                      ▼
┌────────────────┐                  ┌────────────────────┐
│ Redis Cluster  │                  │  PostgreSQL        │
│                │                  │  Primary + Replicas│
│ - Node 1 (M)   │                  │                    │
│ - Node 2 (S)   │                  │ ┌────────────────┐ │
│ - Node 3 (S)   │                  │ │   Primary DB   │ │
│                │                  │ │  (Read/Write)  │ │
│ Replication:   │                  │ └───────┬────────┘ │
│ - Async        │                  │         │          │
│ - Automatic    │                  │         │ Replication
│   failover     │                  │         │          │
│                │                  │ ┌───────▼────────┐ │
│ Persistence:   │                  │ │  Replica 1     │ │
│ - RDB + AOF    │                  │ │  (Read-only)   │ │
│ - Every 5 min  │                  │ └────────────────┘ │
│                │                  │         │          │
│ Eviction:      │                  │ ┌───────▼────────┐ │
│ - LRU          │                  │ │  Replica 2     │ │
│ - 80% maxmem   │                  │ │  (Read-only)   │ │
└────────────────┘                  │ └────────────────┘ │
                                    └────────────────────┘

Scaling Characteristics:
┌──────────────────┬──────────────┬─────────────────────┐
│ Component        │ Scaling      │ Strategy            │
├──────────────────┼──────────────┼─────────────────────┤
│ FastAPI Pods     │ Horizontal   │ K8s autoscaling     │
│ Redis            │ Horizontal   │ Cluster mode        │
│ PostgreSQL       │ Vertical +   │ Primary + replicas  │
│                  │ Read replicas│                     │
└──────────────────┴──────────────┴─────────────────────┘

Performance at Scale:
┌──────────────────┬──────────────┬─────────────────────┐
│ Load             │ Throughput   │ Latency (p95)       │
├──────────────────┼──────────────┼─────────────────────┤
│ 100K req/hour    │ 28 req/s     │ <50ms               │
│ 1M req/hour      │ 278 req/s    │ <80ms               │
│ 10M req/hour     │ 2778 req/s   │ <150ms              │
└──────────────────┴──────────────┴─────────────────────┘
```

---

**Last Updated:** 2026-01-26  
**Version:** 1.0.0  
**Use these diagrams in presentations, documentation, and technical discussions.**
