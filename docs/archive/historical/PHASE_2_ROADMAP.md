# Enterprise Chat Features - Phase 2 Implementation Roadmap

**Date**: December 16, 2025
**Status**: In Progress
**Phase 1 Complete**: 7,058 lines (8/8 use cases)

---

## 📋 Phase 2 Overview

Phase 2 focuses on infrastructure, integrations, and production readiness:

1. **Database Adapters** - PostgreSQL persistence for all repositories
2. **Cache Infrastructure** - Redis with vector search for semantic caching
3. **External Integrations** - LLM providers, embedding models, translation APIs
4. **WebSocket Features** - Real-time updates and streaming
5. **Pre-built Libraries** - Templates, agents, workflows
6. **Monitoring & Observability** - Dashboards, metrics, alerts

---

## 🗄️ Database Infrastructure

### Tables to Create

**1. user_chat_preferences**
```sql
CREATE TABLE user_chat_preferences (
    user_id UUID PRIMARY KEY,
    verbosity_level VARCHAR(20) NOT NULL,
    tone_style VARCHAR(20) NOT NULL,
    response_format VARCHAR(20) NOT NULL,
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    include_code_examples BOOLEAN NOT NULL DEFAULT true,
    include_references BOOLEAN NOT NULL DEFAULT true,

    -- Notifications
    notification_conversation_updates BOOLEAN NOT NULL DEFAULT true,
    notification_agent_responses BOOLEAN NOT NULL DEFAULT true,
    notification_daily_summary BOOLEAN NOT NULL DEFAULT false,
    notification_insight_alerts BOOLEAN NOT NULL DEFAULT true,

    -- Display
    display_theme VARCHAR(20) NOT NULL DEFAULT 'light',
    display_font_size INTEGER NOT NULL DEFAULT 14,
    display_show_timestamps BOOLEAN NOT NULL DEFAULT true,
    display_show_agent_names BOOLEAN NOT NULL DEFAULT true,
    display_markdown_rendering BOOLEAN NOT NULL DEFAULT true,

    -- Agents
    favorite_agents TEXT[],
    blocked_agents TEXT[],

    -- Custom
    custom_instructions TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**2. conversation_templates**
```sql
CREATE TABLE conversation_templates (
    template_id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by_user_id UUID NOT NULL,

    -- Steps stored as JSONB
    steps JSONB NOT NULL,

    -- Metadata
    tags TEXT[],
    estimated_duration_minutes INTEGER,
    difficulty_level VARCHAR(20),

    -- Usage stats
    usage_count INTEGER NOT NULL DEFAULT 0,
    avg_completion_rate REAL NOT NULL DEFAULT 0.0,
    avg_user_rating REAL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_creator FOREIGN KEY (created_by_user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_templates_category ON conversation_templates(category);
CREATE INDEX idx_templates_creator ON conversation_templates(created_by_user_id);
CREATE INDEX idx_templates_active ON conversation_templates(is_active);
```

**3. template_executions**
```sql
CREATE TABLE template_executions (
    execution_id UUID PRIMARY KEY,
    template_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,

    status VARCHAR(20) NOT NULL, -- in_progress, completed, paused, failed
    current_step_index INTEGER NOT NULL DEFAULT 0,

    -- Execution data
    step_results JSONB NOT NULL DEFAULT '[]',
    execution_time_seconds INTEGER,
    completion_rate REAL,

    -- Timestamps
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    paused_at TIMESTAMP,

    CONSTRAINT fk_template FOREIGN KEY (template_id)
        REFERENCES conversation_templates(template_id) ON DELETE CASCADE,
    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_executions_template ON template_executions(template_id);
CREATE INDEX idx_executions_user ON template_executions(user_id);
CREATE INDEX idx_executions_status ON template_executions(status);
```

**4. conversation_exports**
```sql
CREATE TABLE conversation_exports (
    export_id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,

    format VARCHAR(20) NOT NULL, -- json, markdown, pdf, html
    status VARCHAR(20) NOT NULL, -- pending, processing, completed, failed

    -- Configuration
    include_metadata BOOLEAN NOT NULL DEFAULT true,
    include_timestamps BOOLEAN NOT NULL DEFAULT true,
    include_agent_names BOOLEAN NOT NULL DEFAULT true,
    redact_pii BOOLEAN NOT NULL DEFAULT false,

    -- Output
    file_path TEXT,
    file_size_bytes INTEGER,
    download_url TEXT,
    expires_at TIMESTAMP,

    -- Timestamps
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,

    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_exports_conversation ON conversation_exports(conversation_id);
CREATE INDEX idx_exports_user ON conversation_exports(user_id);
CREATE INDEX idx_exports_status ON conversation_exports(status);
```

**5. voting_rounds**
```sql
CREATE TABLE voting_rounds (
    round_id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,

    query TEXT NOT NULL,
    strategy VARCHAR(30) NOT NULL,

    -- Results
    winning_response TEXT,
    winning_vote_count INTEGER NOT NULL DEFAULT 0,
    total_votes INTEGER NOT NULL DEFAULT 0,
    consensus_confidence REAL NOT NULL DEFAULT 0.0,

    -- Votes stored as JSONB
    votes JSONB NOT NULL DEFAULT '[]',

    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,

    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_voting_conversation ON voting_rounds(conversation_id);
CREATE INDEX idx_voting_user ON voting_rounds(user_id);
```

**6. agent_debates**
```sql
CREATE TABLE agent_debates (
    debate_id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,

    query TEXT NOT NULL,
    participating_agents TEXT[] NOT NULL,
    current_phase VARCHAR(30) NOT NULL,
    consensus_status VARCHAR(20) NOT NULL,

    -- Results
    final_consensus TEXT,
    consensus_confidence REAL NOT NULL DEFAULT 0.0,

    -- Debate data
    statements JSONB NOT NULL DEFAULT '[]',
    max_rounds INTEGER NOT NULL DEFAULT 3,
    current_round INTEGER NOT NULL DEFAULT 0,

    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,

    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_debates_conversation ON agent_debates(conversation_id);
CREATE INDEX idx_debates_user ON agent_debates(user_id);
CREATE INDEX idx_debates_status ON agent_debates(consensus_status);
```

**7. agent_performance_metrics**
```sql
CREATE TABLE agent_performance_metrics (
    agent_name VARCHAR(100) PRIMARY KEY,

    total_requests INTEGER NOT NULL DEFAULT 0,
    successful_requests INTEGER NOT NULL DEFAULT 0,
    failed_requests INTEGER NOT NULL DEFAULT 0,

    avg_response_time_ms REAL NOT NULL DEFAULT 0.0,
    avg_confidence REAL NOT NULL DEFAULT 0.0,
    avg_cost_usd REAL NOT NULL DEFAULT 0.0,
    total_cost_usd REAL NOT NULL DEFAULT 0.0,

    uptime_percentage REAL NOT NULL DEFAULT 100.0,
    last_24h_requests INTEGER NOT NULL DEFAULT 0,

    last_error TEXT,
    last_error_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_metrics_updated ON agent_performance_metrics(updated_at DESC);
```

**8. custom_agent_configs**
```sql
CREATE TABLE custom_agent_configs (
    config_id UUID PRIMARY KEY,
    created_by_user_id UUID NOT NULL,

    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,

    -- Configuration
    capabilities TEXT[] NOT NULL,
    temperature REAL NOT NULL DEFAULT 0.7,
    max_tokens INTEGER NOT NULL DEFAULT 1000,
    personality_traits JSONB NOT NULL DEFAULT '{}',
    expertise_areas TEXT[],
    response_style VARCHAR(20) NOT NULL DEFAULT 'balanced',

    -- LLM settings
    preferred_llm_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    fallback_llm_provider VARCHAR(50),

    is_active BOOLEAN NOT NULL DEFAULT true,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_creator FOREIGN KEY (created_by_user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT unique_agent_name_per_user UNIQUE (created_by_user_id, name)
);

CREATE INDEX idx_custom_agents_creator ON custom_agent_configs(created_by_user_id);
CREATE INDEX idx_custom_agents_active ON custom_agent_configs(is_active);
```

---

## 🔧 Infrastructure Adapters

### 1. Repository Adapters (PostgreSQL)

**Completed**:
- ✅ `UserPreferencesRepositoryAdapter` - User chat preferences persistence
- ✅ `RedisCacheAdapter` - High-performance caching with vector search

**To Implement**:
- ⏳ `TemplateRepositoryAdapter` - Template CRUD and search
- ⏳ `TemplateExecutionRepositoryAdapter` - Template execution tracking
- ⏳ `ConversationExportRepositoryAdapter` - Export management
- ⏳ `AgentOrchestrationRepositoryAdapter` - Voting, debates, metrics
- ⏳ `TranslationRepositoryAdapter` - Translation cache and history

### 2. External Service Adapters

**LLM Provider Integrations**:
- ⏳ `OpenAIAdapter` - GPT-4, GPT-3.5-turbo integration
- ⏳ `AnthropicAdapter` - Claude 3 integration
- ⏳ `LLMProviderFailover` - Automatic failover logic

**Embedding Services**:
- ⏳ `OpenAIEmbeddingAdapter` - text-embedding-3-large
- ⏳ `CohereEmbeddingAdapter` - embed-english-v3.0

**Translation Services**:
- ⏳ `DeepLAdapter` - Professional translation API
- ⏳ `GoogleTranslateAdapter` - Google Cloud Translation

**Vector Databases**:
- ⏳ `PineconeAdapter` - Semantic search backend
- ⏳ `WeaviateAdapter` - Alternative vector DB

### 3. Cache Infrastructure

**Redis Components**:
- ✅ `RedisCacheAdapter` - Primary cache with vector search
- ⏳ `RedisOfflineQueueAdapter` - Offline message queuing
- ⏳ `RedisSessionStore` - WebSocket session management

---

## 🌐 Real-Time Features (WebSocket)

### WebSocket Handlers

**1. Chat WebSocket**:
```python
# /ws/chat/{conversation_id}
- Real-time message streaming
- Agent typing indicators
- Multi-agent voting updates
- Debate phase notifications
```

**2. Analytics WebSocket**:
```python
# /ws/analytics/{user_id}
- Real-time metrics updates
- Performance alerts
- Cost threshold notifications
```

**3. Template Execution WebSocket**:
```python
# /ws/template/{execution_id}
- Step-by-step progress
- Real-time results
- Pause/resume controls
```

---

## 📚 Pre-Built Libraries

### 1. Template Library

**Portfolio Management Templates**:
```
- Portfolio Health Check (5 steps, 3 min)
- Risk Assessment Report (7 steps, 5 min)
- Yield Optimization Analysis (6 steps, 4 min)
- Rebalancing Recommendations (8 steps, 6 min)
```

**DeFi Protocol Analysis**:
```
- Protocol Deep Dive (10 steps, 10 min)
- Risk vs Reward Comparison (6 steps, 4 min)
- Smart Contract Security Review (8 steps, 8 min)
- Liquidity Analysis (5 steps, 3 min)
```

**Trading Strategies**:
```
- Entry/Exit Strategy Builder (7 steps, 5 min)
- Stop-Loss Optimization (4 steps, 3 min)
- Position Sizing Calculator (3 steps, 2 min)
```

### 2. Custom Agent Library

**Pre-configured Agents**:
```
- Curve Finance Expert
- Aave Specialist
- MEV Protection Advisor
- Gas Optimization Expert
- Smart Contract Auditor
- Market Sentiment Analyzer
```

### 3. Workflow Templates

**Multi-Agent Workflows**:
```
- Consensus Investment Decision (voting + debate)
- Risk Committee Review (3-agent debate)
- Strategy Validation (fallback chain)
```

---

## 📊 Monitoring & Observability

### 1. Metrics Collection

**Application Metrics**:
```
- Agent performance (response time, success rate, cost)
- Cache hit rates and memory usage
- Template execution success rates
- Translation API usage and costs
- WebSocket connection health
```

**Business Metrics**:
```
- Daily active users
- Messages per conversation
- Most popular agents
- Template usage patterns
- Export generation frequency
```

### 2. Dashboards

**Admin Dashboard** (`/admin/chat/dashboard`):
```
- Real-time usage statistics
- Agent performance leaderboard
- Cache efficiency metrics
- Cost tracking and budgets
- Error rate monitoring
```

**User Analytics Dashboard** (`/chat/my-analytics`):
```
- Personal usage statistics
- Favorite agents
- Conversation insights
- Time-to-decision metrics
- Cost breakdown
```

### 3. Alerting

**System Alerts**:
```
- Agent performance degradation
- Cache memory threshold exceeded
- High error rates
- Cost budget violations
- WebSocket connection failures
```

**User Notifications**:
```
- Template execution completed
- Export ready for download
- Daily conversation summary
- Insight discoveries
```

---

## 🚀 Deployment & Configuration

### Environment Variables

```bash
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Embedding Services
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
COHERE_API_KEY=...

# Translation
DEEPL_API_KEY=...
GOOGLE_TRANSLATE_API_KEY=...

# Vector Database
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws
WEAVIATE_URL=...

# Redis (Caching)
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=50

# Feature Flags
ENABLE_SEMANTIC_CACHING=true
ENABLE_VECTOR_SEARCH=true
ENABLE_REAL_TIME_UPDATES=true
ENABLE_AUTO_TRANSLATION=true

# Performance Budgets
MAX_RESPONSE_TIME_MS=3000
MAX_LLM_COST_PER_QUERY_USD=0.05
MAX_CACHE_MEMORY_MB=500
TARGET_CACHE_HIT_RATE=0.70
```

### Docker Compose Services

```yaml
services:
  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    environment:
      - REDIS_ARGS=--save 60 1 --loglevel warning

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: anvil_chat
      POSTGRES_USER: anvil
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres-data:/var/lib/postgresql/data

  pinecone-proxy:
    image: pinecone/pinecone-client:latest
    environment:
      PINECONE_API_KEY: ${PINECONE_API_KEY}
```

---

## 📅 Implementation Timeline

### Sprint 1: Database & Core Adapters (Week 1-2)
- ✅ User preferences adapter
- ✅ Redis cache adapter
- ⏳ Database migrations
- ⏳ Template repository adapter
- ⏳ Agent orchestration adapter

### Sprint 2: External Integrations (Week 2-3)
- ⏳ LLM provider integrations
- ⏳ Embedding service adapters
- ⏳ Translation API integrations
- ⏳ Vector database setup

### Sprint 3: Real-Time Features (Week 3-4)
- ⏳ WebSocket handlers
- ⏳ Streaming responses
- ⏳ Real-time updates
- ⏳ Session management

### Sprint 4: Libraries & Templates (Week 4-5)
- ⏳ Pre-built template library
- ⏳ Custom agent configurations
- ⏳ Workflow templates

### Sprint 5: Monitoring & Production (Week 5-6)
- ⏳ Metrics collection
- ⏳ Admin dashboard
- ⏳ Alerting system
- ⏳ Load testing

---

## ✅ Phase 2 Completion Criteria

**Infrastructure** (100%):
- All repository adapters implemented
- External service integrations complete
- Cache infrastructure operational
- WebSocket handlers deployed

**Features** (100%):
- Real-time updates working
- Template library published (15+ templates)
- Custom agent library (10+ agents)
- Export generation functional

**Production Ready** (100%):
- Monitoring dashboards live
- Alerting configured
- Load tested (1000+ concurrent users)
- Documentation complete

**Performance** (Targets):
- p50 response time < 500ms (cached)
- p95 response time < 2000ms
- Cache hit rate > 70%
- 99.9% uptime

---

## 📈 Success Metrics

**Usage Metrics**:
- 1000+ daily active users
- 10,000+ messages per day
- 70%+ cache hit rate
- 5+ templates per user

**Performance Metrics**:
- < 2s average response time
- < $0.02 average cost per conversation
- 99.9% uptime
- < 0.1% error rate

**Business Metrics**:
- 80%+ user satisfaction
- 3+ agent interactions per session
- 50%+ template adoption
- 30%+ custom agent creation

---

**Phase 2 Status**: In Progress (2% complete)
**Next Steps**: Complete database migrations and remaining adapters
