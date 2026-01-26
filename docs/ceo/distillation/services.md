# Distillation System Services & Components

> **Complete service reference organized by hexagonal architecture layers**
> **Version:** 2.0 (Intent-Free Routing)
> **Last Updated:** 2026-01-26

---

## Table of Contents

- [Overview](#overview)
- [Architecture Layers](#architecture-layers)
- [Domain Services](#domain-services)
- [Application Services](#application-services)
- [Infrastructure Services](#infrastructure-services)
- [Service Dependencies](#service-dependencies)
- [Integration Patterns](#integration-patterns)

---

## Overview

The Distillation System follows **Hexagonal Architecture** with clear separation of concerns across four layers:

1. **Domain Layer** - Core business logic (intent-free routing, complexity assessment)
2. **Application Layer** - Use case orchestration (request distillator)
3. **Infrastructure Layer** - External integrations (cache, repositories, LLM providers)
4. **Presentation Layer** - HTTP controllers (admin endpoints)

### Service Count by Layer

| Layer | Services | Purpose |
|-------|----------|---------|
| **Domain** | 6 | Business logic |
| **Application** | 4 | Use case coordination |
| **Infrastructure** | 8 | External dependencies |
| **Presentation** | 2 | HTTP endpoints |
| **Total** | 20 | Complete system |

---

## Architecture Layers

### Dependency Flow

```
Presentation Layer (HTTP Controllers)
         ↓
Application Layer (Use Cases)
         ↓
Domain Layer (Business Logic)
         ↓
Infrastructure Layer (Adapters)
```

**Key Principle:** Dependencies point **inward** (toward domain)

```
┌─────────────────────────────────────┐
│      Presentation Layer              │
│  - distillation_router.py            │
│  - distillation_validation_router.py │
└─────────────┬───────────────────────┘
              │ calls
┌─────────────▼───────────────────────┐
│      Application Layer               │
│  - request_distillator.py            │
│  - get_health.py                     │
│  - get_metrics.py                    │
│  - update_config.py                  │
└─────────────┬───────────────────────┘
              │ uses
┌─────────────▼───────────────────────┐
│         Domain Layer                 │
│  Services:                           │
│  - engine.py (main orchestrator)     │
│  - router.py (routing logic)         │
│  - complexity_assessor.py            │
│  - entity_extractor.py               │
│  - intent_classifier.py              │
│  - telemetry_collector.py            │
│  Ports:                              │
│  - distillation_repository.py        │
│  - distillator.py                    │
└─────────────┬───────────────────────┘
              │ implemented by
┌─────────────▼───────────────────────┐
│     Infrastructure Layer             │
│  Adapters:                           │
│  - cache_manager.py                  │
│  - static_responder.py               │
│  - vertex_ai_distillator.py          │
│  - deepinfra_distillator.py          │
│  Repositories:                       │
│  - distillation_cache_repository.py  │
│  - distillation_config_repository.py │
│  - distillation_static_repository.py │
│  - distillation_telemetry_repository.│
└─────────────────────────────────────┘
```

---

## Domain Services

### 1. DistillationEngine

**Location:** `/home/ubuntu/anvil_backend/src/app/domain/services/distillation/engine.py:25`

**Purpose:** Main orchestrator for the distillation pass. Coordinates all distillation operations.

**Responsibilities:**
1. Check if distillation is enabled
2. Assess query complexity (query length heuristic)
3. Extract entities (tokens, protocols, chains)
4. Check cache (exact → semantic → miss)
5. Route decision (cache/light LLM/full LLM)
6. Log telemetry

**Key Methods:**

```python
class DistillationEngine:
    async def distill(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        user_context: Optional[dict] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> DistillationResult:
        """
        Run distillation pass on query.

        Returns:
            DistillationResult with routing decision
        """

    async def cache_response(
        self,
        query: str,
        intent: str,
        entities: dict,
        response_content: str,
        source_model: Optional[str] = None,
        source_request_id: Optional[UUID] = None,
    ) -> None:
        """Cache a response for future requests."""
```

**Dependencies:**
- `IntentClassifier` (optional, for analytics)
- `ComplexityAssessor` (query complexity)
- `EntityExtractor` (entity extraction)
- `DistillationRouter` (routing logic)
- `CacheManager` (cache lookup/store)
- `StaticResponder` (static templates)
- `DistillationConfigRepository` (configuration)
- `DistillationTelemetryRepository` (telemetry)

**Dependents:**
- `RequestDistillator` (application layer orchestrator)
- `send_message_with_distillation` (chat integration)

**Business Logic Flow:**

```python
# 1. Check if enabled
config = await self.config_repo.get_config()
if not config.enabled:
    return DistillationResult(should_process=True, route_type=RouteType.FULL_LLM)

# 2. Assess complexity (NO INTENT CLASSIFICATION)
query_length = len(query.split())
if query_length <= 3:
    complexity = ComplexityLevel.SIMPLE
elif query_length <= 10:
    complexity = ComplexityLevel.MODERATE
else:
    complexity = ComplexityLevel.COMPLEX

# 3. Extract entities (for cache key)
entities = self.entity_extractor.extract(query)

# 4. Check cache
cache_hit_content, cache_level = await self.cache_manager.get(
    cache_key=cache_key,
    query=query,
    semantic_threshold=config.semantic_similarity_threshold,
)

# 5. Route decision
if cache_hit_content:
    return DistillationResult(route_type=RouteType.CACHE, cached_response=cache_hit_content)
elif complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]:
    return DistillationResult(route_type=RouteType.LIGHT_LLM, suggested_model_tier="economy")
else:
    return DistillationResult(route_type=RouteType.FULL_LLM, suggested_model_tier="standard")
```

**Performance:**
- Target latency: <50ms (complexity assessment + cache lookup)
- Cache hit latency: <5ms (exact), <20ms (semantic)
- No LLM calls during distillation pass

---

### 2. DistillationRouter

**Location:** `/home/ubuntu/anvil_backend/src/app/domain/services/distillation/router.py:20`

**Purpose:** Route requests based on complexity (NOT intent).

**Responsibilities:**
1. Normalize query text
2. Assess complexity (query length)
3. Extract entities (for cache key)
4. Generate cache key (without intent)
5. Return routing decision

**Key Methods:**

```python
class DistillationRouter:
    async def route(
        self,
        text: str,
        cache_lookup: Optional[str] = None,
        static_available: bool = False,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> DistillationResult:
        """Determine optimal route for request."""
```

**Routing Decision Matrix:**

```python
# Complexity-based routing (NO INTENT)
if cache_lookup is not None:
    return DistillationResult(route_type=RouteType.CACHE)

if complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]:
    return DistillationResult(
        route_type=RouteType.LIGHT_LLM,
        suggested_model_tier="economy",
        suggested_agent="chat"
    )
else:
    return DistillationResult(
        route_type=RouteType.FULL_LLM,
        suggested_model_tier="standard",
        suggested_agent="chat"
    )
```

**Cache Key Generation (v2.0 - Intent-Free):**

```python
def _build_cache_key_no_intent(
    self,
    entities: ExtractedEntities,
    normalized_query: str,
) -> str:
    """Generate cache key without intent."""
    # Build key components (no intent in v2.0)
    components = [
        ",".join(sorted(entities.tokens)),
        ",".join(sorted(entities.protocols)),
        normalized_query,
    ]

    # Hash for compact key
    key_string = "|".join(components)
    hash_digest = hashlib.sha256(key_string.encode()).hexdigest()

    return f"distill:v2:{hash_digest[:16]}"
```

**Dependencies:**
- `IntentClassifier` (kept for compatibility)
- `ComplexityAssessor` (complexity assessment)
- `EntityExtractor` (entity extraction)
- `DistillationConfig` (thresholds)

**Dependents:**
- `DistillationEngine` (main orchestrator)

---

### 3. ComplexityAssessor

**Location:** `/home/ubuntu/anvil_backend/src/app/domain/services/distillation/complexity_assessor.py:8`

**Purpose:** Assess query complexity to determine processing needs.

**Responsibilities:**
1. Analyze query text factors
2. Calculate complexity score
3. Return complexity level

**Key Methods:**

```python
class ComplexityAssessor:
    def assess(self, text: str, intent: Intent) -> ComplexityLevel:
        """
        Determine complexity level of request.

        Args:
            text: User query text
            intent: Classified intent (ignored in v2.0)

        Returns:
            ComplexityLevel
        """
```

**Complexity Factors:**

```python
factors = {
    "token_count": len(text.split()),
    "question_count": text.count("?"),
    "requires_calculation": self._needs_calculation(text),
    "requires_comparison": self._needs_comparison(text),
    "multi_step": self._is_multi_step(text),
    "requires_tools": self._needs_tools(intent),
    "requires_context": self._needs_context(text),
}
```

**Complexity Score Calculation:**

```python
def _calculate_complexity_score(self, factors: Dict) -> float:
    """
    Calculate overall complexity score.

    Weights:
    - token_count: 0.1 (normalized, max 100 tokens = 1.0)
    - question_count: 0.1 (normalized, max 3 questions = 1.0)
    - requires_calculation: 0.15
    - requires_comparison: 0.15
    - multi_step: 0.2
    - requires_tools: 0.15
    - requires_context: 0.15
    """
    score = 0.0
    score += min(factors["token_count"] / 100, 1.0) * 0.1
    score += min(factors["question_count"] / 3, 1.0) * 0.1
    score += float(factors["requires_calculation"]) * 0.15
    score += float(factors["requires_comparison"]) * 0.15
    score += float(factors["multi_step"]) * 0.2
    score += float(factors["requires_tools"]) * 0.15
    score += float(factors["requires_context"]) * 0.15
    return score
```

**Complexity Thresholds:**

```python
if score < 0.2:
    return ComplexityLevel.TRIVIAL
elif score < 0.4:
    return ComplexityLevel.SIMPLE
elif score < 0.6:
    return ComplexityLevel.MODERATE
elif score < 0.8:
    return ComplexityLevel.COMPLEX
else:
    return ComplexityLevel.EXPERT
```

**Dependencies:** None (pure business logic)

**Dependents:**
- `DistillationRouter` (routing decisions)
- `DistillationEngine` (complexity assessment)

---

### 4. EntityExtractor

**Location:** `/home/ubuntu/anvil_backend/src/app/domain/services/distillation/entity_extractor.py`

**Purpose:** Extract structured entities from user queries.

**Responsibilities:**
1. Extract tokens (ETH, USDC, AAVE)
2. Extract protocols (Uniswap, Aave, Compound)
3. Extract chains (Ethereum, Arbitrum, Polygon)
4. Extract amounts (100, 0.5, 1000)
5. Extract addresses (0x...)
6. Extract time references (today, last week)

**Key Methods:**

```python
class EntityExtractor:
    def extract(self, text: str) -> ExtractedEntities:
        """Extract entities from query text."""
```

**Extracted Entities:**

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

**Extraction Patterns (Regex):**

```python
# Token patterns
TOKEN_PATTERNS = [
    r'\b(ETH|ETHEREUM)\b',
    r'\b(BTC|BITCOIN)\b',
    r'\b(USDC|USD COIN)\b',
    r'\b(USDT|TETHER)\b',
    r'\b(DAI)\b',
    r'\b(AAVE)\b',
    r'\b(UNI|UNISWAP)\b',
]

# Protocol patterns
PROTOCOL_PATTERNS = [
    r'\b(UNISWAP)\b',
    r'\b(AAVE)\b',
    r'\b(COMPOUND)\b',
    r'\b(CURVE)\b',
    r'\b(YEARN)\b',
]

# Chain patterns
CHAIN_PATTERNS = [
    r'\b(ETHEREUM|ETH MAINNET)\b',
    r'\b(ARBITRUM|ARB)\b',
    r'\b(OPTIMISM|OP)\b',
    r'\b(POLYGON|MATIC)\b',
    r'\b(BASE)\b',
]

# Amount patterns
AMOUNT_PATTERNS = [
    r'\b(\d+\.?\d*)\s*(USD|USDC|ETH|BTC)?\b',
]
```

**Use Cases:**
- Cache key generation (distillation v2.0)
- Static response template injection
- Analytics (entity distribution)

**Dependencies:** None (pure regex logic)

**Dependents:**
- `DistillationRouter` (cache key generation)
- `StaticResponder` (template variable injection)

---

### 5. IntentClassifier

**Location:** `/home/ubuntu/anvil_backend/src/app/domain/services/distillation/intent_classifier.py:11`

**Purpose:** Classify user intent using hybrid approach (rule-based + LLM-based).

**Note:** In v2.0, intent classification is **optional** and **not used for routing**. It's kept for:
- Analytics (understanding user queries)
- Future features (personalization)
- Backward compatibility

**Responsibilities:**
1. Try rule-based patterns first (fast)
2. Fall back to LLM if ambiguous (context-aware)
3. Return intent + confidence

**Key Methods:**

```python
class IntentClassifier:
    async def classify(
        self,
        text: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Intent, float]:
        """
        Classify intent with confidence score.

        Uses hybrid approach:
        1. Rule-based patterns (fast, high confidence)
        2. LLM-based classification (for ambiguous queries)
        """
```

**Classification Flow:**

```python
# Step 1: Try rule-based patterns first (fastest)
for intent, patterns in self.INTENT_PATTERNS.items():
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return intent, 0.95  # High confidence

# Step 2: If no rule match and LLM available, use LLM
if self._use_llm_for_ambiguous and self._llm_client:
    llm_intent, llm_confidence = await self._classify_with_llm(text, conversation_history)
    if llm_confidence >= self._llm_confidence_threshold:
        return llm_intent, llm_confidence

# Step 3: Fallback to UNCLEAR
return Intent.UNCLEAR, 0.5
```

**Intent Patterns (Rule-Based):**

```python
INTENT_PATTERNS = {
    Intent.PRICE_CHECK: [
        r"\b(price|cost|worth|value) of (\w+|ETH|BTC|USDC)",
        r"what('s| is) (\w+|ETH|BTC) (price|worth|trading at)",
        r"how much is (\w+|ETH|BTC)",
    ],
    Intent.BALANCE_CHECK: [
        r"\b(my )?(balance|holdings|portfolio)\b",
        r"what do i (have|own)",
    ],
    Intent.SWAP_REQUEST: [
        r"\b(swap|exchange|trade|convert) \d+",
        r"buy (\w+) with (\w+)",
        r"sell \d+ (\w+)",
    ],
    ...
}
```

**LLM-Based Classification (Optional):**

```python
async def _classify_with_llm(
    self,
    text: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Intent, float]:
    """
    Classify intent using LLM (Vertex AI with DeepInfra fallback).

    Returns:
        Tuple of (Intent, confidence)
    """
    prompt = self._build_classification_prompt(text, conversation_history)
    response = await self._llm_client.classify_intent(
        prompt=prompt,
        model="gemini-2.0-flash",
    )

    intent_str = response.get("intent", "unclear")
    confidence = float(response.get("confidence", 0.5))

    return Intent(intent_str), confidence
```

**Dependencies:**
- `LLMClientGateway` (optional, for LLM-based classification)

**Dependents:**
- `DistillationRouter` (kept for compatibility, not used in v2.0)

---

### 6. TelemetryCollector

**Location:** `/home/ubuntu/anvil_backend/src/app/domain/services/distillation/telemetry_collector.py`

**Purpose:** Collect and log distillation telemetry for analytics.

**Responsibilities:**
1. Log distillation requests
2. Record routing decisions
3. Track cache hits/misses
4. Calculate cost savings

**Key Methods:**

```python
class DistillationTelemetryCollector:
    async def record(
        self,
        request: DistillationRequest,
        result: DistillationResult,
    ) -> None:
        """Record distillation request telemetry."""
```

**Logged Data:**

```python
@dataclass
class DistillationTelemetry:
    request_id: str
    user_id: Optional[UUID]
    original_query: str
    normalized_query: str

    # Classification
    intent: Intent
    intent_confidence: float
    complexity: ComplexityLevel
    entities: ExtractedEntities

    # Routing
    route_type: RouteType
    routing_reason: str
    suggested_model_tier: Optional[str]
    suggested_agent: Optional[str]

    # Cache
    cache_key: Optional[str]
    cache_hit: bool
    cache_level: CacheLevel

    # Performance
    classification_latency_ms: int
    total_latency_ms: int

    # Outcome
    was_processed: bool
    llm_request_id: Optional[UUID]

    created_at: datetime
```

**Dependencies:**
- `DistillationTelemetryRepository` (persistence)

**Dependents:**
- `DistillationEngine` (telemetry logging)

---

## Application Services

### 1. RequestDistillator

**Location:** `/home/ubuntu/anvil_backend/src/app/application/distillation/request_distillator.py:24`

**Purpose:** Main orchestrator for request distillation (application layer).

**Responsibilities:**
1. Coordinate primary + fallback providers
2. Handle fail-open logic
3. Record telemetry
4. Health checking

**Key Methods:**

```python
class RequestDistillator:
    async def validate(
        self,
        user_message: str,
        conversation_history: List[Message],
        user_id: UUID,
        conversation_id: UUID,
    ) -> DistillationResult:
        """
        Validate a user request.

        Returns:
            DistillationResult with validation decision
        """

    async def check_health(self) -> dict:
        """Check health of distillation system."""
```

**Validation Flow:**

```python
# 1. Check if enabled
if not self.settings.enabled:
    return self._create_bypass_result()

# 2. Preprocess request
request = self.preprocessor.preprocess(
    user_message=user_message,
    conversation_history=conversation_history,
)

# 3. Try primary provider
result = await self._validate_with_provider(
    request=request,
    provider=self.primary_provider,
    is_fallback=False,
)

# 4. Try fallback if primary failed
if result.error and self.fallback_provider:
    fallback_result = await self._validate_with_provider(
        request=request,
        provider=self.fallback_provider,
        is_fallback=True,
    )
    if not fallback_result.error:
        result = fallback_result

# 5. Fail-open: allow request if both failed
if result.error and self.settings.fail_open:
    result = self._create_fallback_result(result.detected_language)

# 6. Record telemetry
if self.telemetry_collector:
    await self.telemetry_collector.record(request, result)

return result
```

**Dependencies:**
- `DistillationSettings` (configuration)
- `Distillator` (primary provider - Vertex AI)
- `Distillator` (fallback provider - DeepInfra)
- `DistillationTelemetryCollector` (telemetry)
- `RequestPreprocessor` (request normalization)
- `ResponseValidator` (response validation)

**Dependents:**
- `send_message_with_distillation` (chat integration)
- Admin endpoints (health check)

---

### 2. GetHealth

**Location:** `/home/ubuntu/anvil_backend/src/app/application/distillation/get_health.py`

**Purpose:** Health check use case for distillation system.

**Key Methods:**

```python
async def get_health(
    distillator: RequestDistillator,
) -> dict:
    """Get health status of distillation system."""
    return await distillator.check_health()
```

**Response:**

```python
{
    "enabled": true,
    "primary_provider": {
        "name": "vertex_ai",
        "healthy": true,
        "latency_ms": 287.5,
        "error_rate": 0.02
    },
    "fallback_provider": {
        "name": "deepinfra",
        "healthy": true,
        "latency_ms": 412.3,
        "error_rate": 0.03
    }
}
```

---

### 3. GetMetrics

**Location:** `/home/ubuntu/anvil_backend/src/app/application/distillation/get_metrics.py`

**Purpose:** Retrieve distillation metrics for monitoring.

**Key Methods:**

```python
async def get_metrics(
    telemetry_repo: DistillationTelemetryRepository,
    hours: int = 24,
) -> List[TelemetryMetrics]:
    """Get hourly telemetry metrics."""
    return await telemetry_repo.get_hourly_summary(hours=hours)
```

---

### 4. UpdateConfig

**Location:** `/home/ubuntu/anvil_backend/src/app/application/distillation/update_config.py`

**Purpose:** Update distillation configuration use case.

**Key Methods:**

```python
async def update_config(
    config_repo: DistillationConfigRepository,
    updates: DistillationConfigUpdate,
) -> DistillationConfig:
    """Update distillation configuration."""
    config = await config_repo.get_config()

    # Apply updates
    if updates.enabled is not None:
        config.enabled = updates.enabled
    if updates.cache_enabled is not None:
        config.cache_enabled = updates.cache_enabled
    # ...

    await config_repo.update_config(config)
    return config
```

---

## Infrastructure Services

### 1. CacheManager

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/distillation/cache_manager.py:14`

**Purpose:** Hierarchical caching with 2-level fallback.

**Responsibilities:**
1. L1: Exact match cache (hash-based, <5ms)
2. L2: Semantic match cache (vector similarity, <20ms)
3. Cache storage and invalidation
4. Hit count tracking

**Key Methods:**

```python
class CacheManager:
    async def get(
        self,
        cache_key: str,
        query: str,
        semantic_threshold: float = 0.95,
    ) -> tuple[Optional[str], CacheLevel]:
        """
        Get cached response with level indicator.

        Returns:
            Tuple of (cached_content, cache_level)
        """

    async def set(
        self,
        cache_key: str,
        query: str,
        intent: Intent,
        response_content: str,
        ttl_seconds: int,
        entities: Optional[dict] = None,
        source_model: Optional[str] = None,
        source_request_id: Optional[str] = None,
    ) -> None:
        """Store response in both exact and semantic caches."""

    async def invalidate(
        self,
        cache_type: str = "all",
        filters: Optional[dict] = None,
    ) -> int:
        """Invalidate cache entries."""

    async def warm_cache(
        self,
        queries: List[str],
        responses: List[str],
        intents: List[Intent],
        ttl_seconds: int = 3600,
    ) -> int:
        """Pre-warm cache with common queries."""
```

**Cache Lookup Flow:**

```python
# L1: Try exact match first (fastest)
exact_hit = await self.cache_repo.get_exact(cache_key)
if exact_hit and exact_hit.expires_at > datetime.now(UTC):
    await self._increment_hit_count(exact_hit)
    return exact_hit.response_content, CacheLevel.EXACT

# L2: Try semantic match (slower but still fast)
if self.embedding_service:
    embedding = await self._get_embedding(query)
    semantic_hit = await self.cache_repo.get_semantic(
        query_embedding=embedding,
        threshold=semantic_threshold,
    )
    if semantic_hit and semantic_hit.expires_at > datetime.now(UTC):
        await self._increment_hit_count(semantic_hit)
        return semantic_hit.response_content, CacheLevel.SEMANTIC

# L3: Cache miss
return None, CacheLevel.NONE
```

**Cache Storage:**

```python
async def set(self, ...):
    # Store in exact cache
    await self.cache_repo.set_exact(
        cache_key=cache_key,
        normalized_query=normalized_query,
        intent=intent,
        response_content=response_content,
        ttl_seconds=ttl_seconds,
    )

    # Store in semantic cache (if embedding service available)
    if self.embedding_service:
        embedding = await self._get_embedding(query)
        await self.cache_repo.set_semantic(
            query_embedding=embedding,
            original_query=query,
            intent=intent,
            response_content=response_content,
            ttl_seconds=ttl_seconds,
        )
```

**Dependencies:**
- `CacheRepository` (persistence port)
- `EmbeddingService` (optional, for semantic cache)

**Dependents:**
- `DistillationEngine` (cache lookup/store)

---

### 2. StaticResponder

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/distillation/static_responder.py:10`

**Purpose:** Generate static responses from templates (deprecated in v2.0).

**Note:** Static responses are **disabled** in v2.0. Infrastructure kept for future use.

**Responsibilities:**
1. Select appropriate template variant
2. Fetch dynamic data from external sources
3. Inject variables into template
4. Return generated response

**Key Methods:**

```python
class StaticResponder:
    async def generate(
        self,
        intent: Intent,
        entities: ExtractedEntities,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Generate static response for intent."""

    async def check_available(
        self,
        intent: Intent,
        entities: ExtractedEntities,
    ) -> bool:
        """Check if static response is available for intent."""
```

**Template Variable Injection:**

```python
def _inject_variables(
    self,
    template: str,
    variables: list,
    entities: ExtractedEntities,
    data: Dict[str, Any],
) -> str:
    """Inject variables into template."""
    replacements = {}

    for var in variables:
        # Try data source first
        if var in data:
            replacements[var] = str(data[var])
        # Try entities
        elif value := self._get_entity_value(var, entities):
            replacements[var] = value
        # Default placeholder
        else:
            replacements[var] = f"[{var}]"

    # Replace all variables
    result = template
    for var, value in replacements.items():
        result = result.replace(f"{{{var}}}", value)

    return result
```

**Data Source Fetchers:**
- `CoinGeckoDataFetcher` (price data)
- `GasDataFetcher` (gas prices)
- `PortfolioDataFetcher` (user portfolio)

**Dependencies:**
- `StaticResponseRepository` (template storage)
- `DataSourceFetchers` (dynamic data)

**Dependents:**
- `DistillationEngine` (static response generation)

---

### 3. VertexAIDistillator

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/distillation/providers/vertex_ai_distillator.py`

**Purpose:** Primary LLM provider for distillation (Gemini 2.0 Flash).

**Responsibilities:**
1. Validate requests with Vertex AI
2. Detect language
3. Calculate costs
4. Health checking

**Key Methods:**

```python
class VertexAIDistillator:
    async def validate(
        self,
        request: DistillationRequest,
    ) -> DistillationResult:
        """Validate request using Vertex AI."""

    async def check_health(self) -> dict:
        """Check Vertex AI health."""

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "vertex_ai"

    def get_model_name(self) -> str:
        """Get model name."""
        return "gemini-2.0-flash"
```

**Dependencies:**
- Vertex AI SDK
- `DistillationSettings`

**Dependents:**
- `RequestDistillator` (primary provider)

---

### 4. DeepInfraDistillator

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/distillation/providers/deepinfra_distillator.py`

**Purpose:** Fallback LLM provider for distillation.

**Responsibilities:**
1. Validate requests with DeepInfra
2. Provide fallback when Vertex AI fails
3. Cost calculation
4. Health checking

**Dependencies:**
- DeepInfra API
- `DistillationSettings`

**Dependents:**
- `RequestDistillator` (fallback provider)

---

### 5-8. Repositories

**Purpose:** Implement domain ports for data persistence.

#### DistillationCacheRepository

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/persistence_sqla/repositories/distillation_cache_repository.py`

**Responsibilities:**
- Exact cache CRUD
- Semantic cache CRUD
- Cache invalidation
- Statistics aggregation

#### DistillationConfigRepository

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/persistence_sqla/repositories/distillation_config_repository.py`

**Responsibilities:**
- Get configuration
- Update configuration

#### DistillationStaticRepository

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/persistence_sqla/repositories/distillation_static_repository.py`

**Responsibilities:**
- Static response CRUD
- List by intent/variant

#### DistillationTelemetryRepository

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/persistence_sqla/repositories/distillation_telemetry_repository.py`

**Responsibilities:**
- Log requests
- Get recent requests
- Hourly aggregation

---

## Service Dependencies

### Dependency Graph

```
┌────────────────────────────────┐
│    DistillationEngine          │ (Domain)
│  - Main orchestrator           │
└──────────┬─────────────────────┘
           │ uses
     ┌─────┴──────┬──────────┬──────────┬──────────┬──────────┐
     ▼            ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Router   │ │Complexity│ │  Entity  │ │  Cache   │ │  Static  │ │Telemetry │
│          │ │Assessor  │ │Extractor │ │ Manager  │ │Responder │ │Collector │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘

┌────────────────────────────────┐
│    RequestDistillator          │ (Application)
│  - Use case orchestrator       │
└──────────┬─────────────────────┘
           │ uses
     ┌─────┴──────┬──────────┐
     ▼            ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Vertex   │ │DeepInfra │ │Telemetry │
│   AI     │ │ (fallback│ │Collector │
│Distillato│ │)         │ │          │
└──────────┘ └──────────┘ └──────────┘

┌────────────────────────────────┐
│       CacheManager             │ (Infrastructure)
│  - Hierarchical caching        │
└──────────┬─────────────────────┘
           │ uses
     ┌─────┴──────┐
     ▼            ▼
┌──────────┐ ┌──────────┐
│  Cache   │ │Embedding │
│   Repo   │ │ Service  │
└──────────┘ └──────────┘
```

### Dependency Injection (Dishka)

**Provider:** `/home/ubuntu/anvil_backend/src/app/setup/ioc/distillation.py`

```python
class DistillationProvider(Provider):
    scope = Scope.REQUEST

    # Domain services
    engine = provide(DistillationEngine)
    router = provide(DistillationRouter)
    complexity_assessor = provide(ComplexityAssessor)
    entity_extractor = provide(EntityExtractor)
    intent_classifier = provide(IntentClassifier)
    telemetry_collector = provide(DistillationTelemetryCollector)

    # Application services
    request_distillator = provide(RequestDistillator)

    # Infrastructure adapters
    cache_manager = provide(CacheManager)
    static_responder = provide(StaticResponder)

    # Ports → Adapters
    cache_repo = provide(
        source=DistillationCacheRepositorySqla,
        provides=CacheRepository,
    )
    config_repo = provide(
        source=DistillationConfigRepositorySqla,
        provides=DistillationConfigRepository,
    )
    static_repo = provide(
        source=DistillationStaticRepositorySqla,
        provides=StaticResponseRepository,
    )
    telemetry_repo = provide(
        source=DistillationTelemetryRepositorySqla,
        provides=DistillationTelemetryRepository,
    )
```

---

## Integration Patterns

### Pattern 1: Chat Message Integration

**Flow:** User sends message → Distillation pass → LLM call

```python
# File: send_message_with_distillation.py

async def send_message_with_distillation(
    user_message: str,
    conversation_id: UUID,
    user_id: UUID,
    conversation_history: List[Message],
    distillation_engine: DistillationEngine,
) -> Message:
    """
    Send message with optional distillation pass.
    """
    # 1. Run distillation pass
    distillation_result = await distillation_engine.distill(
        query=user_message,
        user_id=user_id,
        conversation_history=conversation_history,
    )

    # 2. Check if cache hit
    if distillation_result.cache_hit:
        # Return cached response (no LLM call)
        return Message(
            role="assistant",
            content=distillation_result.cached_response,
            metadata={"distillation": distillation_result},
        )

    # 3. Route to appropriate LLM
    if distillation_result.route_type == RouteType.LIGHT_LLM:
        model = "gemini-2.0-flash"
    else:
        model = "claude-3-5-sonnet-20241022"

    # 4. Call LLM
    response = await llm_client.chat(
        model=model,
        messages=[...],
    )

    # 5. Cache response for future requests
    await distillation_engine.cache_response(
        query=user_message,
        intent=distillation_result.intent,
        entities=distillation_result.entities,
        response_content=response.content,
        source_model=model,
    )

    return Message(
        role="assistant",
        content=response.content,
        metadata={"distillation": distillation_result},
    )
```

### Pattern 2: Admin Configuration

**Flow:** Admin updates config → Runtime effect (no restart)

```python
# File: distillation_router.py

@router.patch("/config")
@inject
async def update_distillation_config(
    data: DistillationConfigUpdate,
    repository: FromDishka[DistillationConfigRepositorySqla],
) -> DistillationConfigResponse:
    """Update distillation configuration."""
    # 1. Get current config
    config = await repository.get_config()

    # 2. Apply updates (partial)
    if data.enabled is not None:
        config.enabled = data.enabled
    if data.cache_enabled is not None:
        config.cache_enabled = data.cache_enabled
    # ...

    # 3. Save to database
    await repository.update_config(config)

    # 4. Config takes effect immediately (read from DB)
    return DistillationConfigResponse(**config.dict())
```

### Pattern 3: Cache Invalidation

**Flow:** Admin invalidates cache → All entries deleted

```python
# File: distillation_router.py

@router.post("/cache/invalidate")
@inject
async def invalidate_cache(
    data: CacheInvalidateRequest,
    repository: FromDishka[DistillationCacheRepositorySqla],
):
    """Invalidate cache entries."""
    if data.cache_type == "exact":
        await repository.invalidate_exact_cache(data.filters or {})
    elif data.cache_type == "semantic":
        await repository.invalidate_semantic_cache(data.filters or {})
    elif data.cache_type == "all":
        await repository.invalidate_exact_cache(data.filters or {})
        await repository.invalidate_semantic_cache(data.filters or {})
```

---

## Performance Considerations

### Service Latency Targets

| Service | Target Latency | Notes |
|---------|----------------|-------|
| `DistillationEngine.distill()` | <50ms | Complexity + cache lookup |
| `CacheManager.get()` (exact) | <5ms | Hash lookup |
| `CacheManager.get()` (semantic) | <20ms | Vector similarity |
| `ComplexityAssessor.assess()` | <5ms | Pure logic, no I/O |
| `EntityExtractor.extract()` | <10ms | Regex matching |
| `RequestDistillator.validate()` | <100ms | Full validation flow |

### Optimization Strategies

**1. Cache Warm-Up:**

```python
# Pre-warm cache with common queries
await cache_manager.warm_cache(
    queries=["what is ETH", "current gas price", "my balance"],
    responses=["Ethereum (ETH) is...", "Current gas: 20 gwei", "Your balance: $1,234"],
    intents=[Intent.EXPLAIN_CONCEPT, Intent.GAS_CHECK, Intent.BALANCE_CHECK],
    ttl_seconds=86400,  # 24 hours
)
```

**2. Complexity Assessment Caching:**

```python
# Cache complexity assessment results (in-memory)
complexity_cache = {}

def assess_with_cache(text: str) -> ComplexityLevel:
    key = hash(text)
    if key in complexity_cache:
        return complexity_cache[key]

    complexity = complexity_assessor.assess(text)
    complexity_cache[key] = complexity
    return complexity
```

**3. Database Query Optimization:**

```sql
-- Index for fast cache lookup
CREATE UNIQUE INDEX idx_exact_cache_key ON distillation_cache_exact(cache_key);

-- Index for semantic similarity
CREATE INDEX idx_semantic_cache_embedding
ON distillation_cache_semantic
USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for telemetry queries
CREATE INDEX idx_distillation_requests_created_at
ON distillation_requests(created_at DESC);
```

---

## Error Handling

### Domain Layer Errors

```python
class DistillationError(Exception):
    """Base distillation error."""
    pass

class CacheError(DistillationError):
    """Cache operation failed."""
    pass

class ClassificationError(DistillationError):
    """Intent classification failed."""
    pass
```

### Application Layer Error Handling

```python
async def validate(self, ...):
    try:
        result = await self.primary_provider.validate(request)
    except DistillationError as e:
        logger.error(f"Primary provider failed: {e}")

        # Try fallback
        if self.fallback_provider:
            result = await self.fallback_provider.validate(request)

        # Fail-open if enabled
        if self.settings.fail_open:
            return self._create_fallback_result()

        raise
```

### Infrastructure Layer Resilience

```python
# Retry logic for cache operations
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def get_exact(self, cache_key: str) -> Optional[CachedResponse]:
    """Get exact cache with retries."""
    try:
        return await self._execute_query(...)
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")
        raise
```

---

## Testing

### Unit Test Examples

**1. Test Complexity Assessment:**

```python
def test_complexity_assessment_simple():
    assessor = ComplexityAssessor()
    complexity = assessor.assess("what is ETH", Intent.EXPLAIN_CONCEPT)
    assert complexity == ComplexityLevel.SIMPLE

def test_complexity_assessment_complex():
    assessor = ComplexityAssessor()
    complexity = assessor.assess(
        "analyze my portfolio and suggest optimal yield farming strategies",
        Intent.PORTFOLIO_ANALYSIS
    )
    assert complexity == ComplexityLevel.COMPLEX
```

**2. Test Cache Manager:**

```python
@pytest.mark.asyncio
async def test_cache_hit_exact():
    cache_manager = CacheManager(cache_repo, embedding_service)

    # Store in cache
    await cache_manager.set(
        cache_key="test_key",
        query="what is ETH",
        intent=Intent.EXPLAIN_CONCEPT,
        response_content="Ethereum (ETH) is...",
        ttl_seconds=3600,
    )

    # Retrieve from cache
    cached, level = await cache_manager.get(
        cache_key="test_key",
        query="what is ETH",
    )

    assert cached == "Ethereum (ETH) is..."
    assert level == CacheLevel.EXACT
```

**3. Test Distillation Engine:**

```python
@pytest.mark.asyncio
async def test_distillation_engine_cache_hit():
    engine = DistillationEngine(...)

    # First request (cache miss)
    result1 = await engine.distill(query="what is ETH")
    assert result1.route_type == RouteType.LIGHT_LLM

    # Cache response
    await engine.cache_response(
        query="what is ETH",
        intent=Intent.EXPLAIN_CONCEPT,
        entities={},
        response_content="Ethereum is...",
    )

    # Second request (cache hit)
    result2 = await engine.distill(query="what is ETH")
    assert result2.route_type == RouteType.CACHE
    assert result2.cache_hit == True
    assert result2.cached_response == "Ethereum is..."
```

---

## Changelog

### v2.0 (2026-01-26)
- **BREAKING:** Removed intent-based routing
- Switched to complexity-based routing
- Intent classification kept for compatibility (not used)
- Cache key generation updated (no intent)
- Static responses disabled (infrastructure kept)

### v1.0 (2025-12-01)
- Initial release
- Intent classification + routing
- 2-level caching
- Static response templates
- 6 domain services
- 4 application services
- 8 infrastructure services

---

**Document Version:** 2.0
**Last Updated:** 2026-01-26
**Status:** Production-Ready
