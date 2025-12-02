# Distillation Pass System

## Overview

The Distillation Pass is an intelligent pre-processing layer that analyzes incoming user requests to determine the optimal handling path before engaging the full LLM pipeline.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DISTILLATION PASS PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                                                           │
│  │ User Request │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      DISTILLATION ENGINE                              │   │
│  │                                                                       │   │
│  │  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐     │   │
│  │  │    INTENT      │    │  COMPLEXITY    │    │    ENTITY      │     │   │
│  │  │  CLASSIFIER    │    │   ASSESSOR     │    │   EXTRACTOR    │     │   │
│  │  │                │    │                │    │                │     │   │
│  │  │ • Query Type   │    │ • Token Count  │    │ • Tokens       │     │   │
│  │  │ • Action Need  │    │ • Context Req  │    │ • Protocols    │     │   │
│  │  │ • Domain       │    │ • Tool Usage   │    │ • Amounts      │     │   │
│  │  │ • Urgency      │    │ • Reasoning    │    │ • Addresses    │     │   │
│  │  └────────────────┘    └────────────────┘    └────────────────┘     │   │
│  │                                                                       │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │                    ┌────────────────┐                                │   │
│  │                    │  ROUTE DECISION │                                │   │
│  │                    │                │                                │   │
│  │                    │ • should_process│                                │   │
│  │                    │ • route_type   │                                │   │
│  │                    │ • model_tier   │                                │   │
│  │                    │ • cache_key    │                                │   │
│  │                    └────────────────┘                                │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│         ┌────────────────────┼────────────────────┬──────────────────┐      │
│         ▼                    ▼                    ▼                  ▼      │
│  ┌─────────────┐    ┌─────────────┐     ┌─────────────┐    ┌─────────────┐ │
│  │   REJECT    │    │    CACHE    │     │   STATIC    │    │  PROCESS    │ │
│  │             │    │   LOOKUP    │     │  RESPONSE   │    │             │ │
│  │ • Off-topic │    │             │     │             │    │ • Light LLM │ │
│  │ • Harmful   │    │ • Exact hit │     │ • FAQ       │    │ • Full LLM  │ │
│  │ • Policy    │    │ • Semantic  │     │ • Price     │    │ • Multi-LLM │ │
│  │             │    │   similar   │     │ • Status    │    │             │ │
│  └─────────────┘    └─────────────┘     └─────────────┘    └─────────────┘ │
│        │                  │                   │                  │          │
│        ▼                  ▼                   ▼                  ▼          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         RESPONSE TO USER                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Distillation Decision

Every request produces a `DistillationResult` that determines handling:

```python
@dataclass
class DistillationResult:
    """Result of the distillation pass."""
    
    # Should we process this request?
    should_process: bool
    
    # Routing decision
    route_type: RouteType  # REJECT, CACHE, STATIC, LIGHT_LLM, FULL_LLM
    
    # Classification results
    intent: Intent
    complexity: ComplexityLevel
    entities: ExtractedEntities
    
    # Processing hints
    suggested_model_tier: str  # economy, standard, premium
    suggested_agent: str
    cache_key: Optional[str]
    
    # Rejection details (if applicable)
    rejection_reason: Optional[str]
    rejection_code: Optional[str]
    
    # Confidence scores
    classification_confidence: float
    routing_confidence: float
```

### 2. Route Types

| Route Type | Description | Latency | Cost |
|------------|-------------|---------|------|
| `REJECT` | Request blocked (off-topic, harmful, policy) | <10ms | $0 |
| `CACHE` | Exact or semantic cache hit | <20ms | $0 |
| `STATIC` | Pre-defined response (FAQ, prices, status) | <50ms | $0 |
| `LIGHT_LLM` | Simple query, small/fast model | 200-500ms | $0.001 |
| `FULL_LLM` | Complex query, full orchestration | 1-5s | $0.01+ |

### 3. Intent Categories

```python
class Intent(Enum):
    # Informational
    PRICE_CHECK = "price_check"           # "What's ETH price?"
    BALANCE_CHECK = "balance_check"       # "What's my balance?"
    APY_CHECK = "apy_check"               # "What's AAVE USDC APY?"
    GAS_CHECK = "gas_check"               # "Current gas prices?"
    STATUS_CHECK = "status_check"         # "Is Uniswap working?"
    
    # Educational
    EXPLAIN_CONCEPT = "explain_concept"   # "What is impermanent loss?"
    HOW_TO = "how_to"                     # "How do I stake ETH?"
    COMPARE = "compare"                   # "Compare AAVE vs Compound"
    
    # Transactional
    SWAP_REQUEST = "swap_request"         # "Swap 1 ETH to USDC"
    STAKE_REQUEST = "stake_request"       # "Stake 100 MATIC"
    LEND_REQUEST = "lend_request"         # "Deposit USDC on AAVE"
    BORROW_REQUEST = "borrow_request"     # "Borrow DAI against ETH"
    BRIDGE_REQUEST = "bridge_request"     # "Bridge ETH to Arbitrum"
    
    # Analytical
    PORTFOLIO_ANALYSIS = "portfolio"      # "Analyze my portfolio"
    RISK_ASSESSMENT = "risk_assessment"   # "Is this position risky?"
    YIELD_OPTIMIZATION = "yield_optimize" # "Best yield for USDC?"
    STRATEGY_ADVICE = "strategy"          # "DCA strategy for BTC?"
    
    # Administrative
    SETTINGS_CHANGE = "settings"          # "Change my slippage"
    ALERT_SETUP = "alert_setup"           # "Alert when ETH > 3000"
    
    # Off-topic / Other
    GREETING = "greeting"                 # "Hello", "Hi"
    SMALL_TALK = "small_talk"             # "How are you?"
    OFF_TOPIC = "off_topic"               # Unrelated to DeFi
    UNCLEAR = "unclear"                   # Cannot determine intent
```

### 4. Complexity Levels

```python
class ComplexityLevel(Enum):
    TRIVIAL = "trivial"      # Single fact lookup, no reasoning
    SIMPLE = "simple"        # Basic query, minimal context
    MODERATE = "moderate"    # Multi-step, some reasoning
    COMPLEX = "complex"      # Deep analysis, tool usage
    EXPERT = "expert"        # Multi-domain, extensive reasoning
```

---

## Classification Pipeline

### Stage 1: Intent Classification

Uses a lightweight classifier (distilled model or rules-based) to determine user intent:

```python
class IntentClassifier:
    """Classify user intent using lightweight model."""
    
    def __init__(self):
        # Load distilled classifier (fine-tuned small model)
        self.model = load_intent_model("anvil-intent-classifier-v1")
        
        # Fallback rules for common patterns
        self.rules = {
            r"price|cost|worth": Intent.PRICE_CHECK,
            r"balance|holdings|portfolio": Intent.BALANCE_CHECK,
            r"swap|exchange|trade|convert": Intent.SWAP_REQUEST,
            r"stake|staking": Intent.STAKE_REQUEST,
            r"hello|hi|hey": Intent.GREETING,
            # ... more rules
        }
    
    def classify(self, text: str) -> Tuple[Intent, float]:
        """
        Classify intent with confidence score.
        
        Returns:
            Tuple of (Intent, confidence)
        """
        # Try rules first (fastest)
        rule_match = self._match_rules(text)
        if rule_match and rule_match[1] > 0.9:
            return rule_match
        
        # Use ML model
        prediction = self.model.predict(text)
        intent = Intent(prediction.label)
        confidence = prediction.confidence
        
        return intent, confidence
```

### Stage 2: Complexity Assessment

Evaluates request complexity to determine processing needs:

```python
class ComplexityAssessor:
    """Assess request complexity."""
    
    def assess(self, text: str, intent: Intent) -> ComplexityLevel:
        """Determine complexity level."""
        
        factors = {
            "token_count": len(text.split()),
            "question_count": text.count("?"),
            "requires_calculation": self._needs_calculation(text),
            "requires_comparison": self._needs_comparison(text),
            "multi_step": self._is_multi_step(text),
            "requires_tools": self._needs_tools(intent),
            "requires_context": self._needs_context(text),
        }
        
        score = self._calculate_complexity_score(factors)
        
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

### Stage 3: Entity Extraction

Extracts relevant entities for routing and caching:

```python
@dataclass
class ExtractedEntities:
    """Entities extracted from request."""
    tokens: List[str]           # ETH, USDC, AAVE
    protocols: List[str]        # Uniswap, Aave, Compound
    chains: List[str]           # Ethereum, Arbitrum, Polygon
    amounts: List[Decimal]      # 100, 0.5, 1000
    addresses: List[str]        # 0x...
    time_references: List[str]  # today, last week, 30 days
    
class EntityExtractor:
    """Extract DeFi-relevant entities."""
    
    def extract(self, text: str) -> ExtractedEntities:
        """Extract all relevant entities from text."""
        return ExtractedEntities(
            tokens=self._extract_tokens(text),
            protocols=self._extract_protocols(text),
            chains=self._extract_chains(text),
            amounts=self._extract_amounts(text),
            addresses=self._extract_addresses(text),
            time_references=self._extract_time_refs(text)
        )
```

---

## Routing Logic

### Route Decision Matrix

| Intent | Complexity | Route | Model Tier |
|--------|------------|-------|------------|
| `PRICE_CHECK` | Any | STATIC | - |
| `BALANCE_CHECK` | Trivial | STATIC | - |
| `GAS_CHECK` | Any | STATIC | - |
| `GREETING` | Any | STATIC | - |
| `EXPLAIN_CONCEPT` | Simple | CACHE → LIGHT_LLM | economy |
| `HOW_TO` | Simple | CACHE → LIGHT_LLM | economy |
| `HOW_TO` | Moderate | CACHE → FULL_LLM | standard |
| `SWAP_REQUEST` | Any | FULL_LLM | standard |
| `PORTFOLIO_ANALYSIS` | Any | FULL_LLM | premium |
| `STRATEGY_ADVICE` | Complex | FULL_LLM | premium |
| `OFF_TOPIC` | Any | REJECT | - |

### Router Implementation

```python
class DistillationRouter:
    """Route requests based on classification."""
    
    def __init__(
        self,
        cache_manager: CacheManager,
        static_responder: StaticResponder,
        config: DistillationConfig
    ):
        self.cache = cache_manager
        self.static = static_responder
        self.config = config
    
    async def route(
        self,
        text: str,
        intent: Intent,
        complexity: ComplexityLevel,
        entities: ExtractedEntities
    ) -> DistillationResult:
        """Determine optimal route for request."""
        
        # Check for rejection first
        if self._should_reject(intent, text):
            return DistillationResult(
                should_process=False,
                route_type=RouteType.REJECT,
                rejection_reason=self._get_rejection_reason(intent),
                rejection_code="DISTILL_REJECTED"
            )
        
        # Check static responses
        static_response = self.static.get_response(intent, entities)
        if static_response:
            return DistillationResult(
                should_process=False,
                route_type=RouteType.STATIC,
                static_response=static_response
            )
        
        # Check cache
        cache_key = self._build_cache_key(intent, entities, text)
        cached = await self.cache.get(cache_key)
        if cached:
            return DistillationResult(
                should_process=False,
                route_type=RouteType.CACHE,
                cached_response=cached,
                cache_key=cache_key
            )
        
        # Determine LLM tier
        model_tier = self._select_model_tier(intent, complexity)
        
        if complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]:
            route_type = RouteType.LIGHT_LLM
        else:
            route_type = RouteType.FULL_LLM
        
        return DistillationResult(
            should_process=True,
            route_type=route_type,
            intent=intent,
            complexity=complexity,
            entities=entities,
            suggested_model_tier=model_tier,
            suggested_agent=self._suggest_agent(intent),
            cache_key=cache_key
        )
    
    def _select_model_tier(
        self,
        intent: Intent,
        complexity: ComplexityLevel
    ) -> str:
        """Select appropriate model tier."""
        
        # High-stakes intents always get premium
        high_stakes = {
            Intent.SWAP_REQUEST,
            Intent.BORROW_REQUEST,
            Intent.RISK_ASSESSMENT
        }
        if intent in high_stakes:
            return "premium"
        
        # Complexity-based selection
        tier_map = {
            ComplexityLevel.TRIVIAL: "economy",
            ComplexityLevel.SIMPLE: "economy",
            ComplexityLevel.MODERATE: "standard",
            ComplexityLevel.COMPLEX: "premium",
            ComplexityLevel.EXPERT: "premium"
        }
        return tier_map.get(complexity, "standard")
```

---

## Static Response Library

Pre-defined responses for common queries:

```python
STATIC_RESPONSES = {
    # Greetings
    Intent.GREETING: {
        "default": "Hello! I'm Anvil, your DeFi assistant. How can I help you today?",
        "morning": "Good morning! Ready to help with your DeFi needs.",
        "evening": "Good evening! What can I help you with?"
    },
    
    # Price checks (dynamic data fetched)
    Intent.PRICE_CHECK: {
        "template": "The current price of {token} is ${price} ({change_24h}% 24h).",
        "source": "coingecko_api"
    },
    
    # Gas prices
    Intent.GAS_CHECK: {
        "template": "Current gas prices on {chain}:\n• Low: {low} gwei\n• Average: {avg} gwei\n• High: {high} gwei",
        "source": "gas_api"
    },
    
    # Balance (requires auth)
    Intent.BALANCE_CHECK: {
        "template": "Your portfolio value: ${total_value}\n\nTop holdings:\n{holdings_list}",
        "source": "portfolio_service"
    },
    
    # APY checks
    Intent.APY_CHECK: {
        "template": "Current APY for {token} on {protocol}:\n• Supply APY: {supply_apy}%\n• Borrow APY: {borrow_apy}%",
        "source": "defi_llama_api"
    }
}
```

---

## Caching Strategy

### Cache Levels

```
┌─────────────────────────────────────────────────────────────┐
│                    CACHE HIERARCHY                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  L1: Exact Match Cache (Redis)                              │
│  ├── Key: hash(normalized_query)                            │
│  ├── TTL: 5 minutes (prices), 1 hour (explanations)         │
│  └── Hit Rate Target: 15%                                   │
│                                                              │
│  L2: Semantic Cache (Vector DB)                             │
│  ├── Key: embedding(query)                                  │
│  ├── Similarity Threshold: 0.95                             │
│  ├── TTL: 24 hours                                          │
│  └── Hit Rate Target: 20%                                   │
│                                                              │
│  L3: Response Templates (Static)                            │
│  ├── Intent-based templates                                 │
│  ├── Dynamic data injection                                 │
│  └── Always available                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Cache Key Generation

```python
def build_cache_key(
    intent: Intent,
    entities: ExtractedEntities,
    query: str
) -> str:
    """Generate cache key from distillation results."""
    
    # Normalize query
    normalized = normalize_query(query)
    
    # Build key components
    components = [
        intent.value,
        ",".join(sorted(entities.tokens)),
        ",".join(sorted(entities.protocols)),
        normalized
    ]
    
    # Hash for compact key
    key_string = "|".join(components)
    return f"distill:v1:{hashlib.sha256(key_string.encode()).hexdigest()[:16]}"
```

---

## Performance Metrics

### Distillation Telemetry

```python
# Metrics to track
DISTILLATION_METRICS = {
    "distillation_requests_total": Counter("Total requests processed"),
    "distillation_route_type": Counter("Routes by type", ["route_type"]),
    "distillation_intent": Counter("Intents classified", ["intent"]),
    "distillation_latency_ms": Histogram("Classification latency"),
    "distillation_cache_hits": Counter("Cache hits", ["cache_level"]),
    "distillation_cost_saved_usd": Counter("Cost saved by routing"),
    "distillation_confidence": Histogram("Classification confidence"),
}
```

### Expected Performance

| Metric | Target |
|--------|--------|
| Classification Latency | <50ms |
| Cache Lookup Latency | <10ms |
| Static Response Latency | <20ms |
| Overall Distillation Pass | <100ms |
| Cache Hit Rate | >30% |
| Static Response Rate | >20% |
| Cost Savings | >40% |

---

## Integration with LLM Orchestrator

```python
class AnvilChatService:
    """Main chat service with distillation."""
    
    def __init__(
        self,
        distillation: DistillationEngine,
        orchestrator: LLMOrchestrator,
        static_responder: StaticResponder
    ):
        self.distillation = distillation
        self.orchestrator = orchestrator
        self.static = static_responder
    
    async def process_message(
        self,
        message: str,
        user_id: str,
        project_id: Optional[str] = None
    ) -> ChatResponse:
        """Process user message with distillation pass."""
        
        # Run distillation
        result = await self.distillation.distill(message)
        
        # Route based on result
        if not result.should_process:
            if result.route_type == RouteType.REJECT:
                return ChatResponse(
                    content=result.rejection_reason,
                    route="rejected"
                )
            
            elif result.route_type == RouteType.CACHE:
                return ChatResponse(
                    content=result.cached_response,
                    route="cache",
                    cache_key=result.cache_key
                )
            
            elif result.route_type == RouteType.STATIC:
                response = await self.static.generate(
                    intent=result.intent,
                    entities=result.entities
                )
                return ChatResponse(
                    content=response,
                    route="static"
                )
        
        # Process with LLM
        llm_response = await self.orchestrator.execute(
            request=self._build_llm_request(message, result),
            agent_type=result.suggested_agent,
            user_id=user_id
        )
        
        # Cache response for future
        if result.cache_key:
            await self.cache.set(
                result.cache_key,
                llm_response.content,
                ttl=self._get_cache_ttl(result.intent)
            )
        
        return ChatResponse(
            content=llm_response.content,
            route="llm",
            model=llm_response.model_id,
            latency_ms=llm_response.latency_ms
        )
```

---

## Configuration

```python
@dataclass
class DistillationConfig:
    """Configuration for distillation system."""
    
    # Feature flags
    enabled: bool = True
    cache_enabled: bool = True
    static_responses_enabled: bool = True
    
    # Classification thresholds
    min_confidence_threshold: float = 0.7
    semantic_similarity_threshold: float = 0.95
    
    # Cache settings
    exact_cache_ttl_seconds: int = 300
    semantic_cache_ttl_seconds: int = 3600
    
    # Rate limits
    max_distillation_latency_ms: int = 100
    
    # Cost optimization
    light_llm_max_tokens: int = 500
    prefer_cache_over_llm: bool = True
```
