# CTO Response: LLM Strategy for Anvil MVP

**Date:** 2025-12-12
**From:** CTO
**To:** CEO
**Re:** LLM Integration Strategy & Technical Architecture

---

## Executive Summary

Based on Anvil's current hexagonal architecture, existing MCP infrastructure, and DeFi focus, I'm providing strategic recommendations that balance performance, cost, and user experience for our MVP. Our existing telemetry and adapter patterns give us a strong foundation to build upon.

---

## 1. Latencia: ¿Cuánto va a tardar en el MVP y por qué?

### Current State Analysis
Looking at our existing infrastructure:
- **MCP Servers**: Already have retry mechanisms with 1s initial backoff, max 30s
- **External Adapters**: DeFiLlama, CoinGecko, TheGraph, etc. with HTTP clients configured
- **Telemetry**: Infrastructure ready for observability

### Expected Latency Profile

**P50 (median):** 800-1200ms
**P95:** 2000-3000ms
**P99:** 4000-6000ms

### Why?
1. **Network Round-trips**:
   - LLM API call: 200-800ms (depending on model size and provider location)
   - Our existing DeFi data fetching: 100-500ms (already measured in our adapters)
   - Total sequential: 300-1300ms base

2. **Token Generation**:
   - Streaming responses start showing at ~200-300ms (first token)
   - Full completion for 500 tokens at 40 tokens/sec = 12.5s
   - With streaming, user sees progress immediately

3. **Context Building**:
   - RAG vector search (if implemented): +50-150ms
   - Portfolio data aggregation: +200-400ms (based on current query patterns)
   - Cached responses: <50ms

### Strategic Recommendation
**Don't optimize prematurely**. Our hexagonal architecture allows us to swap LLM providers without changing business logic. Start with Claude/GPT-4 for quality, then optimize latency in Phase 2.

---

## 2. Throughput: ¿Cuántos tokens por segundo esperamos en el MVP?

### Realistic Expectations

**Single-user streaming:**
- Claude Sonnet: 40-60 tokens/sec
- GPT-4 Turbo: 30-50 tokens/sec
- Grok 2 Fast: 60-80 tokens/sec (if we use it)

**Concurrent Users:**
- MVP target: 50-100 concurrent users
- Average query: 500-1000 output tokens
- With proper async handling (we're already using asyncio everywhere), we can handle this

### Current Architecture Advantage
Our `InstrumentedLLMGateway` (src/app/infrastructure/adapters/ai/) already supports:
- ✅ Async/await patterns
- ✅ Streaming responses
- ✅ Telemetry for monitoring
- ✅ Circuit breakers for resilience

**DX Impact**: Developers can add new LLM providers by implementing the `LLMGateway` port. No business logic changes needed.

---

## 3. Velocidad: ¿Cómo hacer que el usuario no espere?

### UX Strategy: Perceived Performance > Actual Performance

#### Immediate Feedback (0-100ms)
```
User sends message
  ↓
✅ Instant visual feedback
  - Message appears in chat
  - Typing indicator animation starts
  - Status: "Analyzing portfolio..."
```

#### Streaming Implementation (100-300ms)
```
First token arrives at ~200ms
  ↓
✅ Start rendering response word-by-word
  - Users read at ~250 words/min (4 words/sec)
  - Token arrival at 40/sec means they'll never "catch up"
  - Perception: AI is "thinking out loud"
```

#### Progressive Enhancement
```
While streaming:
  - Show data sources being consulted
  - Display mini-charts as data arrives
  - Update confidence indicators in real-time
```

### Technical Implementation
Our existing `ChatInteractor` structure already supports streaming. Add:

```python
# src/app/application/chat/stream_response_interactor.py
class StreamResponseInteractor:
    async def execute(self, query: str) -> AsyncIterator[ChatChunk]:
        # 1. Immediate acknowledgment
        yield ChatChunk(type="status", content="Processing...")

        # 2. Stream LLM response
        async for token in self.llm_gateway.stream(query):
            yield ChatChunk(type="token", content=token)

        # 3. Enrich with data (async, don't block streaming)
        await self._fetch_supporting_data_async(query)
```

**DX Note**: Developers adding new chat features just implement the interactor pattern. No frontend changes needed for streaming support.

---

## 4. Caché: Reglas y definiciones fijas

### What to Cache

**Already Implemented** (`src/app/infrastructure/cache/external_api_cache.py`):
- ✅ External API responses (DeFiLlama TVL, prices, etc.)
- ✅ TTL-based expiration
- ✅ Redis-backed

**Should Add for LLM**:

#### 1. Semantic Cache (High ROI)
```
Question: "What's the APY on Aave USDC?"
Question: "Tell me Aave USDC yield"
Question: "Aave USDC returns?"

→ Same semantic meaning → Cache the ANSWER
```

**Implementation**:
- Use embedding similarity (cosine > 0.95)
- Cache LLM response + metadata
- TTL: 5 minutes for market data answers

#### 2. Prompt Templates Cache (Zero Cost)
```
System prompts, role definitions, tool descriptions
→ Never change during runtime
→ Load once at startup
→ Infinite TTL
```

#### 3. RAG Document Cache
```
DeFi protocol docs, smart contract ABIs, methodology
→ Changes rarely
→ TTL: 24 hours
→ Invalidate on protocol upgrades
```

### Who Manages It?

**Application Layer** decides what to cache
**Infrastructure Layer** handles caching mechanism
**Domain Layer** stays cache-agnostic ✅ (clean architecture preserved)

---

## 5. Plantillas: ¿Qué tareas van a plantilla?

### Template-Driven Tasks (High Certainty, Low Creativity)

#### Tier 1: Zero LLM Needed
```
❌ Don't waste tokens on:
- Wallet balance queries → Direct blockchain RPC
- Price lookups → CoinGecko API
- TVL checks → DeFiLlama API
```

Our existing MCP servers already handle these!

#### Tier 2: Structured LLM Queries (Use Templates)
```
✅ Portfolio summaries
✅ Risk assessments
✅ Yield comparisons
✅ Transaction explanations
```

**Template Structure**:
```python
# src/app/application/chat/templates/portfolio_summary.py
PORTFOLIO_SUMMARY_TEMPLATE = """
You are a DeFi portfolio analyst. Analyze this portfolio:

Holdings: {holdings_json}
Total Value: ${total_value_usd}
Risk Score: {risk_score}/10

Provide:
1. Asset allocation breakdown
2. Top 3 risks
3. Rebalancing suggestion

Format: {output_format}
"""
```

#### Who Creates Templates?

**Phase 1 (MVP)**: CTO + Lead Engineer define templates
**Phase 2**: Product team can modify templates via config (no code deploy)
**Phase 3**: A/B testing different templates for conversion optimization

---

## 6. Inteligencia vs Obediencia: ¿Qué métrica priorizamos?

### The Trade-off

**Intelligence** (Reasoning, creativity, edge cases)
vs
**Obedience** (Following instructions, structured output)

### My Recommendation: **Obedience First for MVP**

**Why?**
1. **Financial Domain = Zero tolerance for hallucinations**
   - Wrong APY = user loses money
   - Wrong risk assessment = regulatory exposure

2. **Structured Output = Better UX**
   - We can render charts, tables, action buttons
   - Intelligence without structure = chatbot, not product

3. **Easier to Measure**
   - Obedience: Schema validation pass rate (measurable)
   - Intelligence: Subjective, requires human eval

### Metrics to Track

```python
# Primary (Obedience)
- schema_validation_rate: >99%
- hallucination_rate: <0.1% (fact-checked against APIs)
- structured_output_success: >95%

# Secondary (Intelligence)
- user_satisfaction_score: >4.2/5
- query_resolution_rate: >85% (no follow-up needed)
- edge_case_handling: Evaluated monthly
```

**Model Selection Criteria**:
1. ✅ Supports function calling / structured output
2. ✅ Low hallucination rate on financial data
3. ✅ Fast inference (<2s P95)
4. ⚠️ Reasoning ability (nice-to-have, not critical for MVP)

---

## 7. Alucinaciones: ¿Cómo evitamos inventar números?

### Multi-Layer Defense Strategy

#### Layer 1: Never Ask LLM for Numbers
```python
# ❌ BAD: LLM generates numbers
"What's the current APY on Aave USDC?"

# ✅ GOOD: LLM formats numbers we provide
context = {
    "aave_usdc_apy": await self.aave_gateway.get_apy("USDC"),  # Real API
    "source": "Aave Protocol API",
    "timestamp": datetime.utcnow()
}
prompt = f"Explain this APY to the user: {context}"
```

#### Layer 2: Structured Output with Validation
```python
from pydantic import BaseModel, Field, validator

class PortfolioAnalysis(BaseModel):
    total_value_usd: float = Field(..., ge=0)  # Must be >= 0
    risk_score: int = Field(..., ge=1, le=10)   # 1-10 only
    data_sources: List[str]  # Must cite sources

    @validator('total_value_usd')
    def check_against_api(cls, v, values):
        # Cross-check LLM output against our API data
        if abs(v - values.get('_api_value', 0)) > 0.01:
            raise ValueError("LLM value doesn't match API")
        return v
```

#### Layer 3: Fact-Checking Pipeline
```python
async def verify_llm_response(response: str, context: Dict) -> bool:
    """Post-process verification"""

    # Extract numbers from LLM response
    numbers = extract_financial_figures(response)

    # Compare against ground truth
    for number in numbers:
        api_value = context.get(number.key)
        if not api_value:
            log_warning(f"LLM mentioned {number.key} not in context")
            return False

        if abs(number.value - api_value) / api_value > 0.05:  # 5% tolerance
            log_error(f"Hallucination detected: {number.key}")
            return False

    return True
```

#### Layer 4: UI Transparency
```
┌─────────────────────────────────────┐
│ Your Aave position yields 4.2% APY │
│                                     │
│ 📊 Data from: Aave Protocol API     │
│ ⏰ Updated: 2 minutes ago           │
│ ✓ Verified                          │
└─────────────────────────────────────┘
```

**DX Impact**: Developers adding new financial features must provide ground-truth data sources. LLM only formats/explains, never generates.

---

## 8. RAG: ¿Vamos a usarlo? ¿Cómo lo implementamos?

### Yes, But Strategically

**Don't RAG everything**. Use it for:
1. ✅ Protocol documentation (Aave, Curve mechanics)
2. ✅ Smart contract explainers
3. ✅ Historical analysis ("How did Aave handle the March 2023 USDC depeg?")
4. ❌ Real-time data (use APIs instead)

### Implementation Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Chat Query                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  Query Router (New Component)                          │
│  - Classify query type                                 │
│  - Real-time → API call                                │
│  - Knowledge → RAG                                     │
│  - Hybrid → Both                                       │
└────────────┬───────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────┐    ┌─────────────┐
│ API Call │    │ RAG Search  │
│ (Exists) │    │ (New)       │
└──────────┘    └──────┬──────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Vector Store     │
              │ (Pinecone/Weaviate)│
              │                  │
              │ Documents:       │
              │ - Protocol docs  │
              │ - Contract ABIs  │
              │ - DeFi guides    │
              └─────────────────┘
```

### Hexagonal Architecture Fit

```python
# src/app/domain/ports/knowledge_gateway.py
class KnowledgeGateway(Protocol):
    async def search(self, query: str, top_k: int = 5) -> List[Document]:
        """Search knowledge base"""
        ...

# src/app/infrastructure/adapters/rag/pinecone_adapter.py
class PineconeKnowledgeAdapter(KnowledgeGateway):
    async def search(self, query: str, top_k: int = 5):
        embedding = await self.embedding_model.embed(query)
        results = await self.pinecone_index.query(embedding, top_k=top_k)
        return [self._to_document(r) for r in results]
```

**Clean separation**: Domain doesn't care if knowledge comes from Pinecone, Weaviate, or a JSON file.

### MVP Scope
**Phase 1**: Static docs only (Aave, Compound, Curve guides)
**Phase 2**: User-specific data (their transaction history)
**Phase 3**: Real-time indexed blockchain data

---

## 9. Circuit Breakers: ¿Cuándo frenar ejecución?

### Current Implementation
We already have retry logic in `MCPServerRetry` (src/app/infrastructure/mcp/). Extend this pattern for LLMs.

### Kill Switch Triggers

#### 1. Cost Explosion
```python
class LLMCircuitBreaker:
    def __init__(self):
        self.hourly_cost_limit = 50.00  # $50/hour MVP budget
        self.user_cost_limit = 0.50     # $0.50 per user per session

    async def check(self, user_id: str, estimated_cost: float):
        if await self.redis.get(f"cost:hour") > self.hourly_cost_limit:
            raise CircuitBreakerOpen("Hourly cost limit exceeded")

        if await self.redis.get(f"cost:user:{user_id}") > self.user_cost_limit:
            raise CircuitBreakerOpen("User cost limit exceeded")
```

#### 2. Latency Degradation
```python
# Open circuit if P95 > 5 seconds for 2 minutes
if p95_latency > 5000 and duration > 120:
    switch_to_fallback()  # Cached responses or simpler model
```

#### 3. Error Rate Spike
```python
# 5xx errors > 10% in last 100 requests
if error_rate > 0.10:
    pause_llm_calls(duration=300)  # 5 min cooldown
    alert_on_call_engineer()
```

#### 4. Hallucination Detection
```python
# If fact-check fails on 3 consecutive responses
if consecutive_hallucinations >= 3:
    fallback_to_template_responses()
    trigger_incident_review()
```

### Metrics Dashboard (Grafana)

```
┌─────────────────────────────────────────────────┐
│ LLM Health Dashboard                            │
├─────────────────────────────────────────────────┤
│ 🟢 Circuit Status: CLOSED                       │
│ 💰 Cost (hour): $12.40 / $50.00 (24.8%)        │
│ ⏱️  P95 Latency: 1,842ms                        │
│ ✅ Success Rate: 98.2%                          │
│ ⚠️  Hallucination Rate: 0.04%                   │
│ 🔥 Requests/min: 45                             │
└─────────────────────────────────────────────────┘
```

**Integration Point**: Our existing `InstrumentedLLMGateway` already has hooks for telemetry. Add circuit breaker middleware.

---

## 10. Costos: ¿Por qué Grok 4 Fast es tan barato?

### The Economics

**Grok 2 Fast pricing** (as of Dec 2024):
- ~$0.50 per 1M input tokens
- ~$1.50 per 1M output tokens

**Why so cheap?**
1. **Optimized for throughput over quality**
   - Smaller model size (likely 70B params vs GPT-4's rumored 1.7T)
   - Aggressive quantization (INT8/INT4 vs FP16)
   - Purpose-built for speed, not reasoning

2. **X.AI's strategy**
   - Loss leader to compete with OpenAI/Anthropic
   - They have Grok 3 as premium tier
   - Training on Twitter data = unique moat, lower data costs

3. **Infrastructure arbitrage**
   - Custom silicon rumors (like Google's TPUs)
   - Better GPU utilization (batching, caching)

### Should We Use It for MVP?

**Recommendation: Yes, but strategically**

```
┌──────────────────────────────────────────────┐
│ Query Routing Strategy                       │
├──────────────────────────────────────────────┤
│                                              │
│ Grok 2 Fast ($)                              │
│ ├─ Simple queries (What is APY?)            │
│ ├─ Formatting tasks                         │
│ └─ High-volume, low-stakes                  │
│                                              │
│ Claude Sonnet ($$)                           │
│ ├─ Portfolio analysis                       │
│ ├─ Risk assessment                          │
│ └─ Financial advice                         │
│                                              │
│ Claude Opus ($$$)                            │
│ ├─ Complex DeFi strategies                  │
│ ├─ Multi-protocol optimization              │
│ └─ Premium users only                       │
└──────────────────────────────────────────────┘
```

**Cost Optimization**: Our hexagonal architecture makes swapping models trivial. Start with Claude, A/B test Grok on 20% of traffic.

---

## 11. División de Modelos: ¿Cómo separamos Premium y Base?

### Tiered Model Strategy

```python
# src/app/domain/value_objects/subscription_tier.py
class SubscriptionTier(Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

# src/app/application/chat/model_selector.py
class ModelSelector:
    MODEL_MAP = {
        SubscriptionTier.FREE: {
            "model": "grok-2-fast",
            "max_tokens": 500,
            "requests_per_hour": 10,
            "features": ["basic_analysis"]
        },
        SubscriptionTier.BASIC: {
            "model": "claude-3-haiku",
            "max_tokens": 1000,
            "requests_per_hour": 50,
            "features": ["basic_analysis", "portfolio_insights"]
        },
        SubscriptionTier.PREMIUM: {
            "model": "claude-3.5-sonnet",
            "max_tokens": 4000,
            "requests_per_hour": 200,
            "features": ["all", "priority_support", "advanced_strategies"]
        },
        SubscriptionTier.ENTERPRISE: {
            "model": "gpt-4-turbo",  # or Claude Opus
            "max_tokens": 8000,
            "requests_per_hour": 1000,
            "features": ["all", "custom_models", "api_access"]
        }
    }
```

### Feature Gating

```python
async def execute_chat_query(
    query: str,
    user: User
) -> ChatResponse:

    tier = user.subscription.tier
    config = ModelSelector.get_config(tier)

    # Rate limiting
    if await self.rate_limiter.is_exceeded(user.id, config["requests_per_hour"]):
        raise RateLimitExceeded(
            f"Upgrade to {tier.next()} for more requests"
        )

    # Feature gating
    requested_feature = self.detect_feature(query)
    if requested_feature not in config["features"]:
        return UpsellResponse(
            message=f"{requested_feature} is only available in {tier.next()}",
            upgrade_cta="Try Premium for 7 days free"
        )

    # Execute with appropriate model
    return await self.llm_gateway.query(
        query=query,
        model=config["model"],
        max_tokens=config["max_tokens"]
    )
```

### UX Differentiation

**Free Tier**:
- ⚡ Fast responses (Grok 2 Fast)
- 📊 Basic portfolio summary
- 🚫 No advanced strategies

**Premium Tier**:
- 🧠 Deep analysis (Claude Sonnet)
- 📈 Custom strategies
- 🔮 Predictive insights
- ⚡ Priority processing (separate queue)

**Visual Indicator**:
```
┌─────────────────────────────────────┐
│ 💎 Premium Analysis                 │
│ Powered by Claude 3.5 Sonnet        │
└─────────────────────────────────────┘
```

---

## 12. Métricas: ¿Qué medimos y cómo?

### Dashboard Architecture

Our existing telemetry infrastructure (`src/app/infrastructure/telemetry/`) can be extended:

```python
# src/app/infrastructure/telemetry/llm_metrics.py
class LLMMetricsCollector:
    """Collects LLM-specific metrics"""

    METRICS = {
        # Performance
        "llm_latency_ms": Histogram(buckets=[100, 500, 1000, 2000, 5000]),
        "first_token_latency_ms": Histogram(buckets=[50, 100, 200, 500]),
        "tokens_per_second": Gauge(),

        # Cost
        "cost_per_request_usd": Histogram(buckets=[0.001, 0.01, 0.1, 1.0]),
        "hourly_cost_usd": Gauge(),
        "cost_per_user_usd": Histogram(),

        # Quality
        "hallucination_rate": Gauge(),
        "schema_validation_success_rate": Gauge(),
        "user_satisfaction_score": Histogram(buckets=[1, 2, 3, 4, 5]),

        # Business
        "query_resolution_rate": Gauge(),  # No follow-up needed
        "conversion_to_premium": Gauge(),  # Free users upgrading
        "feature_usage": Counter(labels=["feature", "tier"]),
    }
```

### Real-Time Dashboard (Grafana)

```
┌────────────────────────────────────────────────────────────┐
│ Anvil LLM Performance Dashboard                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│ │ P50: 842ms  │  │ P95: 2.1s   │  │ P99: 4.8s   │        │
│ └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                            │
│ Cost & Usage                                               │
│ ┌────────────────────────────────────────────────┐        │
│ │ Hour: $8.40  │ Day: $156  │ Month: $3,200 📉   │        │
│ └────────────────────────────────────────────────┘        │
│                                                            │
│ Quality Metrics                                            │
│ ┌────────────────────────────────────────────────┐        │
│ │ ✅ Validation: 99.2%  ⚠️ Hallucinations: 0.08% │        │
│ │ 😊 Satisfaction: 4.3/5  🎯 Resolution: 87%     │        │
│ └────────────────────────────────────────────────┘        │
│                                                            │
│ Model Distribution (Last Hour)                             │
│ ┌────────────────────────────────────────────────┐        │
│ │ Grok 2 Fast: ████████░░ 42% ($2.10)            │        │
│ │ Claude Haiku: ████░░░░░░ 28% ($3.20)           │        │
│ │ Claude Sonnet: ███░░░░░░░ 25% ($8.90)          │        │
│ │ GPT-4 Turbo: █░░░░░░░░░  5% ($12.40)           │        │
│ └────────────────────────────────────────────────┘        │
└────────────────────────────────────────────────────────────┘
```

### Alert Configuration

```yaml
# alerts/llm_alerts.yml
alerts:
  - name: "Cost Spike"
    condition: hourly_cost_usd > 50
    action: circuit_breaker.open()
    notify: ["cto@anvil.com", "ops@anvil.com"]

  - name: "Latency Degradation"
    condition: p95_latency > 5000 for 5m
    action: fallback_to_faster_model()
    notify: ["engineering@anvil.com"]

  - name: "Hallucination Spike"
    condition: hallucination_rate > 0.5% for 10m
    action: pause_llm.enable_template_mode()
    notify: ["cto@anvil.com", "compliance@anvil.com"]
    severity: CRITICAL
```

---

## 13. Guardrails: ¿Qué tan complejo es implementarlos?

### Complexity Assessment

**Low Complexity** (MVP-ready):
1. ✅ Input validation (Pydantic schemas)
2. ✅ Output validation (JSON schema enforcement)
3. ✅ Rate limiting (Redis counters)
4. ✅ Cost limits (circuit breakers)

**Medium Complexity** (Phase 2):
1. ⚠️ Semantic validation (fact-checking pipeline)
2. ⚠️ Toxic content filtering (use external API like Perspective API)
3. ⚠️ PII detection (regex + NER models)

**High Complexity** (Phase 3+):
1. ❌ Adversarial prompt detection (requires ML model)
2. ❌ Multi-turn conversation safety
3. ❌ Compliance logging for financial regulations

### MVP Guardrails Implementation

```python
# src/app/application/chat/guardrails.py
class ChatGuardrails:
    """Multi-layer safety system for LLM interactions"""

    async def validate_input(self, query: str, user: User) -> ValidationResult:
        """Layer 1: Input validation"""

        # Length check
        if len(query) > 2000:
            return ValidationResult(
                valid=False,
                reason="Query too long (max 2000 chars)"
            )

        # PII detection (simple regex for MVP)
        if self.contains_pii(query):
            return ValidationResult(
                valid=False,
                reason="Please don't share sensitive information"
            )

        # Rate limiting
        if not await self.rate_limiter.check(user.id):
            return ValidationResult(
                valid=False,
                reason="Rate limit exceeded",
                retry_after=await self.rate_limiter.get_retry_after(user.id)
            )

        return ValidationResult(valid=True)

    async def validate_output(
        self,
        response: str,
        context: Dict
    ) -> ValidationResult:
        """Layer 2: Output validation"""

        # Financial data verification
        if not await self.verify_numbers(response, context):
            logger.error("Hallucination detected", extra={
                "response": response,
                "context": context
            })
            return ValidationResult(
                valid=False,
                reason="Internal validation failed",
                fallback_response=self.generate_safe_fallback(context)
            )

        # Compliance check
        if self.contains_financial_advice(response):
            # Add disclaimer
            response = self.add_disclaimer(response)

        return ValidationResult(valid=True, response=response)

    def contains_pii(self, text: str) -> bool:
        """Simple PII detection for MVP"""
        patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{16}\b',              # Credit card
            r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',  # Email
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    async def verify_numbers(
        self,
        response: str,
        context: Dict
    ) -> bool:
        """Cross-check LLM numbers against API data"""

        # Extract numbers from response
        numbers = self.extract_financial_figures(response)

        # Verify against ground truth
        for num in numbers:
            ground_truth = context.get(num.key)
            if not ground_truth:
                continue

            # 5% tolerance
            if abs(num.value - ground_truth) / ground_truth > 0.05:
                return False

        return True
```

### Recommended Guardrail Stack

**MVP (Implement Now)**:
```
┌──────────────────────────────────┐
│ 1. Input Validation              │
│    - Length, format, PII         │
│    - Rate limiting               │
│    - Cost estimation             │
├──────────────────────────────────┤
│ 2. LLM Call                      │
│    - Structured output enforced  │
│    - Temperature limits          │
│    - Token limits                │
├──────────────────────────────────┤
│ 3. Output Validation             │
│    - Schema validation           │
│    - Number verification         │
│    - Disclaimer injection        │
├──────────────────────────────────┤
│ 4. Logging & Monitoring          │
│    - All interactions logged     │
│    - Anomaly detection           │
│    - Compliance audit trail      │
└──────────────────────────────────┘
```

**Effort Estimate**: 2 weeks engineering time for MVP guardrails

---

## Strategic Recommendations Summary

### Week 1-2: Foundation
- [x] **Existing**: MCP infrastructure, telemetry, adapters
- [ ] Implement `LLMGateway` port with streaming support
- [ ] Add semantic caching layer (Redis + embeddings)
- [ ] Set up basic guardrails (input/output validation)

### Week 3-4: Integration
- [ ] Build query router (API vs RAG vs hybrid)
- [ ] Implement model selector (tier-based)
- [ ] Add circuit breakers for cost/latency/errors
- [ ] Create metrics dashboard (Grafana)

### Week 5-6: Optimization
- [ ] A/B test Grok vs Claude on 20% traffic
- [ ] Fine-tune prompt templates based on analytics
- [ ] Implement hallucination fact-checking pipeline
- [ ] Launch MVP with Free + Premium tiers

### Success Metrics (MVP)
```
✅ P95 latency: <3s
✅ Hallucination rate: <0.1%
✅ Cost per user: <$0.10
✅ User satisfaction: >4.0/5
✅ Free → Premium conversion: >5%
```

---

## Open Questions for CEO

1. **Budget**: What's our monthly LLM budget for MVP? ($1k, $5k, $10k?)
2. **Risk Tolerance**: Can we launch with Grok 2 Fast knowing it's less reliable than Claude?
3. **Compliance**: Do we need SOC2/audit trails from day 1 or can we add post-launch?
4. **Pricing**: Should Premium be $X/month or usage-based ($Y per 100 queries)?
5. **Data Privacy**: Can we log queries for improvement or strict no-logging policy?

---

**Next Steps**: Schedule 60-min technical deep-dive to align on model selection and review the Excel metrics spreadsheet you mentioned.

/CTO
