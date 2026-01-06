# Guest Chat Complete Flow Specification

**Version:** 1.0
**Created:** 2026-01-06
**Purpose:** Complete end-to-end flow specification for testing guest chat messages through Orchestrator, Distillation, and Agent systems.

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              GUEST CHAT COMPLETE FLOW                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   HTTP API   │───▶│   Command    │───▶│ Distillation │───▶│   Handler    │       │
│  │  Controller  │    │  Interactor  │    │    Engine    │    │   Service    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                   │               │
│         ▼                   ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Rate Limiter │    │    Intent    │    │    Router    │    │    Agent     │       │
│  │ (IP-based)   │    │   Detector   │    │  (5 routes)  │    │ Orchestrator │       │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                     │               │
│                                                                     ▼               │
│                                                              ┌──────────────┐       │
│                                                              │  18 Agents   │       │
│                                                              │  (Vertex AI) │       │
│                                                              └──────────────┘       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Request Flow Stages

### Stage 1: HTTP Controller Layer
**File:** `src/app/presentation/http/controllers/guest_controller.py`

```
POST /api/v1/guest/chat
├── Request Validation
│   ├── message: str (required, max 500 chars)
│   └── language: str (optional: en, es, pt, zh)
├── IP Extraction (X-Forwarded-For or client IP)
└── Forward to Command Interactor
```

### Stage 2: Command Interactor
**File:** `src/app/application/guest/commands/send_guest_message.py`

```
SendGuestMessageInteractor.execute()
├── Step 1: Guest Identification
│   └── get_or_create_guest(ip_address)
│       ├── Lookup existing guest by IP
│       └── Create new guest if not found (24h session)
│
├── Step 2: Rate Limiting
│   └── check_rate_limit(guest_id)
│       ├── RATE_LIMIT_MESSAGES_PER_HOUR = 20
│       ├── RATE_LIMIT_MESSAGES_PER_DAY = 50
│       └── Returns error if exceeded
│
├── Step 3: Conversation Management
│   └── get_or_create_conversation(guest_id)
│       └── conversation_history_limit = 10
│
├── Step 4: Intent Detection
│   └── IntentDetectorService.detect_intent()
│       ├── KeywordIntentDetectionAdapter (primary)
│       └── Returns: ChatIntent, confidence, entities
│
├── Step 5: Restricted Intent Check
│   └── is_restricted_action(intent)
│       ├── RESTRICTED_INTENTS:
│       │   ├── PORTFOLIO (requires registration)
│       │   ├── BALANCE (requires registration)
│       │   ├── ACTIVITY (requires registration)
│       │   └── RECEIVE (requires registration)
│       └── Returns registration prompt if restricted
│
├── Step 6: Handler Routing
│   └── GuestHandlerService.handle_intent()
│       ├── REAL_HANDLER_INTENTS → Real data handlers
│       ├── EXECUTION_INTENTS → Confirmation required
│       └── GENERAL_CONVERSATION → Chat agent
│
└── Step 7: Response Formatting
    └── Format response for guest user
```

---

## 3. Intent Classification System

### 3.1 ChatIntent Enum (23 Types)
**File:** `src/app/application/chat/services/intent_detector.py`

| Category | Intent | Description | Handler |
|----------|--------|-------------|---------|
| **GraphRAG** | PROTOCOL_SEARCH | Find protocols by criteria | GraphRAG |
| | RISK_ASSESSMENT | Evaluate protocol risks | GraphRAG |
| | SIMILAR_PROTOCOLS | Find similar protocols | GraphRAG |
| **Hunter AI** | HUNTER_SENTIMENT | Sentiment analysis | SentimentAggregator |
| | HUNTER_PRICE_PREDICTION | Price forecasting | LSTMPricePredictor |
| | HUNTER_RISK_SIGNALS | Market risk warnings | RiskAnalyzer |
| | HUNTER_TRADING_SIGNALS | Buy/sell signals | TradingSignalGenerator |
| | HUNTER_PATTERNS | Chart patterns | PatternRecognizer |
| | HUNTER_PORTFOLIO | Portfolio optimization | PortfolioOptimizer |
| **ULTRA** | ULTRA_ARBITRAGE | Arbitrage discovery | ArbitrageDiscovery |
| | ULTRA_FLASH_LOANS | Flash loan protocols | FlashLoanEngine |
| | ULTRA_MEV_PROTECTION | MEV-protected execution | MEVProtection |
| | ULTRA_AUTO_EXECUTOR | Automated trading | AutoExecutor |
| **DeFi Shortcuts** | LENDING | Deposit/earn/supply | LendingHandler |
| | MONEY_MARKET | Compare lending rates | MoneyMarketHandler |
| | SWAP | Token swaps | SwapHandler |
| | BALANCE | User balance | *Restricted* |
| | PORTFOLIO | Full portfolio | *Restricted* |
| | ACTIVITY | Transaction history | *Restricted* |
| | RECEIVE | QR/address | *Restricted* |
| **Agent Squad** | SPECIALIST_TASK | Single agent task | AgentOrchestrator |
| | COMPLEX_WORKFLOW | Multi-agent workflow | SupervisorCoordinator |
| **Fallback** | GENERAL_CONVERSATION | General chat | ChatAgent |

### 3.2 Intent Categories
**File:** `src/app/application/guest/commands/send_guest_message.py`

```python
# Intents that use real handlers (Hunter AI, ULTRA, GraphRAG, DeFi)
REAL_HANDLER_INTENTS = {
    ChatIntent.PROTOCOL_SEARCH,
    ChatIntent.RISK_ASSESSMENT,
    ChatIntent.SIMILAR_PROTOCOLS,
    ChatIntent.HUNTER_SENTIMENT,
    ChatIntent.HUNTER_PRICE_PREDICTION,
    ChatIntent.HUNTER_RISK_SIGNALS,
    ChatIntent.HUNTER_TRADING_SIGNALS,
    ChatIntent.HUNTER_PATTERNS,
    ChatIntent.HUNTER_PORTFOLIO,
    ChatIntent.ULTRA_ARBITRAGE,
    ChatIntent.ULTRA_FLASH_LOANS,
    ChatIntent.ULTRA_MEV_PROTECTION,
    ChatIntent.ULTRA_AUTO_EXECUTOR,
    ChatIntent.LENDING,
    ChatIntent.MONEY_MARKET,
    ChatIntent.SWAP,
    ChatIntent.SPECIALIST_TASK,
    ChatIntent.COMPLEX_WORKFLOW,
}

# Intents that require user registration (blocked for guests)
RESTRICTED_INTENTS = {
    ChatIntent.PORTFOLIO,
    ChatIntent.BALANCE,
    ChatIntent.ACTIVITY,
    ChatIntent.RECEIVE,
}

# Intents that require confirmation before execution
EXECUTION_INTENTS = {
    ChatIntent.SWAP,
    ChatIntent.LENDING,
    ChatIntent.MONEY_MARKET,
}
```

---

## 4. Distillation Engine Flow

### 4.1 Engine Overview
**File:** `src/app/domain/services/distillation/engine.py`

```
DistillationEngine.distill(query, user_id, user_context)
│
├── Step 1: Check Enabled
│   └── If disabled → Pass through to FULL_LLM
│
├── Step 2: Intent Classification
│   └── IntentClassifier.classify(query)
│       ├── Rule-based patterns (95% confidence)
│       └── ML fallback (if no match)
│
├── Step 3: Complexity Assessment
│   └── ComplexityAssessor.assess(query, intent)
│       ├── TRIVIAL → Economy tier
│       ├── SIMPLE → Economy tier
│       ├── MODERATE → Standard tier
│       ├── COMPLEX → Premium tier
│       └── EXPERT → Premium tier
│
├── Step 4: Entity Extraction
│   └── EntityExtractor.extract(query)
│       ├── Tokens (ETH, USDC, etc.)
│       ├── Protocols (Aave, Uniswap, etc.)
│       ├── Amounts ($1000, 100 ETH)
│       └── Chains (Ethereum, Polygon, etc.)
│
├── Step 5: Cache Lookup
│   └── CacheManager.get(cache_key, query)
│       ├── Exact match (hash-based)
│       └── Semantic match (embedding similarity)
│
├── Step 6: Static Response Check
│   └── StaticResponder.check_available(intent, entities)
│       └── Pre-defined templates for common queries
│
├── Step 7: Route Decision
│   └── DistillationRouter.route()
│       ├── REJECT → Off-topic, harmful
│       ├── CACHE → Previously seen query
│       ├── STATIC → Template response
│       ├── LIGHT_LLM → Simple, fast model
│       └── FULL_LLM → Complex, premium model
│
└── Step 8: Telemetry Logging
    └── Log request, route, latency, cost savings
```

### 4.2 Router Decision Matrix
**File:** `src/app/domain/services/distillation/router.py`

| Condition | Route | Model Tier | Cost |
|-----------|-------|------------|------|
| Off-topic intent | REJECT | None | $0 |
| Harmful patterns | REJECT | None | $0 |
| Cache hit (exact) | CACHE | None | $0 |
| Cache hit (semantic) | CACHE | None | $0 |
| Static template available | STATIC | None | $0 |
| Force full LLM intent | FULL_LLM | Premium | $0.10/1M |
| Trivial/Simple complexity | LIGHT_LLM | Economy | $0.05/1M |
| Moderate complexity | FULL_LLM | Standard | $0.10/1M |
| Complex/Expert complexity | FULL_LLM | Premium | $0.10/1M |

### 4.3 Intent Patterns (Rule-Based)
**File:** `src/app/domain/services/distillation/intent_classifier.py`

```python
INTENT_PATTERNS = {
    Intent.PRICE_CHECK: [
        r"\b(price|cost|worth|value) of (\w+|ETH|BTC|USDC)",
        r"what('s| is) (\w+|ETH|BTC) (price|worth|trading at)",
    ],
    Intent.SWAP_REQUEST: [
        r"\b(swap|exchange|trade|convert) \d+",
        r"buy (\w+) with (\w+)",
    ],
    Intent.RISK_ASSESSMENT: [
        r"(risk|risky|safe) (of|is)",
        r"(assess|check) (the )?risk",
    ],
    # ... 20+ intent patterns
}
```

---

## 5. Agent Orchestrator Flow

### 5.1 Domain Orchestrator
**File:** `src/app/domain/services/agent_squad/agent_orchestrator.py`

```
AgentOrchestrator.route_message(conversation_id, message, context)
│
├── Step 1: Intent Classification
│   └── IntentClassifierPort.classify(message, context)
│       └── Returns: intent, confidence, agent_type, reasoning
│
├── Step 2: Confidence Check
│   └── If confidence < 0.85 → Fallback to CHAT agent
│
├── Step 3: Feature Flag Validation
│   └── FeatureFlagsPort.is_agent_enabled(agent_type)
│       └── If disabled → Fallback to CHAT agent
│
└── Step 4: Return Routing Result
    └── AgentRoutingResult(agent_type, intent, fallback_used)
```

### 5.2 Application Orchestration Service
**File:** `src/app/application/chat/services/agent_orchestration_service.py`

Advanced orchestration capabilities:

```
AgentOrchestrationService
│
├── Multi-Agent Voting
│   └── conduct_multi_agent_vote(query, agents, strategy)
│       ├── Get responses from all agents concurrently
│       ├── Collect votes with confidence scores
│       ├── Apply voting strategy (WEIGHTED, MAJORITY, etc.)
│       └── Return winning response
│
├── Agent Debates
│   └── conduct_agent_debate(query, agents, max_rounds)
│       ├── Phase 1: Opening Statements
│       ├── Phase 2: Arguments
│       ├── Phase 3: Rebuttals
│       ├── Phase 4: Synthesis
│       └── Phase 5: Final Vote & Consensus
│
├── Fallback Routing
│   └── execute_with_fallback(query, fallback_chain)
│       ├── Try primary agent (30s timeout)
│       ├── Try secondary agent (45s timeout)
│       ├── Try tertiary agent (60s timeout)
│       └── Return best available response
│
└── Performance Tracking
    └── Update agent metrics (success rate, latency, cost)
```

---

## 6. Handler Service Flow

### 6.1 Guest Handler Service
**File:** `src/app/application/guest/handlers/guest_handler_service.py`

```
GuestHandlerService.handle_intent(intent, entities, context)
│
├── Hunter AI Intents
│   ├── HUNTER_SENTIMENT → SentimentAggregator
│   ├── HUNTER_PRICE_PREDICTION → LSTMPricePredictor
│   ├── HUNTER_RISK_SIGNALS → RiskAnalyzer
│   ├── HUNTER_TRADING_SIGNALS → TradingSignalGenerator
│   ├── HUNTER_PATTERNS → PatternRecognizer
│   └── HUNTER_PORTFOLIO → PortfolioOptimizer
│
├── ULTRA Intents
│   ├── ULTRA_ARBITRAGE → ArbitrageDiscovery
│   ├── ULTRA_FLASH_LOANS → FlashLoanEngine
│   ├── ULTRA_MEV_PROTECTION → MEVProtection
│   └── ULTRA_AUTO_EXECUTOR → AutoExecutor
│
├── GraphRAG Intents
│   ├── PROTOCOL_SEARCH → GraphRAGService
│   ├── RISK_ASSESSMENT → GraphRAGService
│   └── SIMILAR_PROTOCOLS → GraphRAGService
│
├── DeFi Shortcut Intents
│   ├── LENDING → LendingHandler (Morpho, Aave, Compound)
│   ├── MONEY_MARKET → MoneyMarketHandler
│   └── SWAP → SwapHandler (1inch, Hyperliquid, UniswapX)
│
├── Agent Squad Intents
│   ├── SPECIALIST_TASK → AgentOrchestrator (single agent)
│   └── COMPLEX_WORKFLOW → SupervisorCoordinator (multi-agent)
│
└── Fallback
    └── GENERAL_CONVERSATION → ChatAgent
```

---

## 7. Agent System (18 Agents)

### 7.1 Agent Types
**File:** `src/app/domain/enums/agent_type.py`

#### Core User-Facing Agents (10)
| Agent | Purpose | Model |
|-------|---------|-------|
| CHAT | General conversation | gemini-2.0-flash-exp |
| HUNTER_AI | Market sentiment & predictions | gemini-2.0-flash-exp |
| RESEARCH | Deep protocol analysis | gemini-2.0-flash-exp |
| EXECUTION | Transaction execution (Privy wallet) | gemini-2.0-flash-exp |
| RISK_ANALYZER | Risk assessment & scoring | gemini-2.0-flash-exp |
| PORTFOLIO | Portfolio optimization & rebalancing | gemini-2.0-flash-exp |
| TAX_OPTIMIZER | Tax-loss harvesting & reporting | gemini-2.0-flash-exp |
| DEFI_YIELD | Yield farming & APY analysis | gemini-2.0-flash-exp |
| SECURITY_AUDITOR | Smart contract security analysis | gemini-2.0-flash-exp |
| GAS_OPTIMIZER | Gas fee optimization & timing | gemini-2.0-flash-exp |

#### Enterprise Agents (8)
| Agent | Purpose | Default |
|-------|---------|---------|
| COMPLIANCE_MONITOR | AML/KYC, regulatory compliance | Disabled |
| MULTISIG_COORDINATOR | Multi-sig treasury management | Disabled |
| ALERT_MONITORING | Real-time alerts, anomaly detection | Disabled |
| CRISIS_MANAGER | Emergency response, circuit breaker | Disabled |
| BRIDGE_CROSSCHAIN | Layer 2, cross-chain operations | Disabled |
| LENDING_BORROWING | Leverage, collateral optimization | Disabled |
| NFT_ASSET_MANAGER | NFT portfolio, valuation | Disabled |
| DAO_GOVERNANCE | Voting, proposals, delegation | Disabled |

### 7.2 Agent Configuration
**File:** `src/app/domain/value_objects/agent_squad/agent_squad_config.py`

```python
DEFAULT_AGENT_MODEL = "gemini-2.0-flash-exp"

@dataclass(frozen=True)
class AgentConfig:
    enabled: bool
    model: str = DEFAULT_AGENT_MODEL
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: int = 60
    custom_params: dict[str, Any] = field(default_factory=dict)
```

---

## 8. LLM Provider Architecture

### 8.1 Provider Hierarchy
```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Provider Gateway                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    ┌─────────────────┐          ┌─────────────────┐             │
│    │   Vertex AI     │          │    DeepInfra    │             │
│    │   (Primary)     │   ───▶   │   (Fallback)    │             │
│    └─────────────────┘          └─────────────────┘             │
│           │                            │                         │
│           ▼                            ▼                         │
│    ┌─────────────────┐          ┌─────────────────┐             │
│    │ gemini-2.0-     │          │ meta-llama/     │             │
│    │ flash-exp       │          │ Meta-Llama-3.1- │             │
│    │ gemini-1.5-pro  │          │ 70B-Instruct    │             │
│    │ gemini-1.5-flash│          │ 405B-Instruct   │             │
│    └─────────────────┘          └─────────────────┘             │
│                                                                  │
│    Cost: $0.10/1M tokens        Cost: $0.35-1.27/1M tokens      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Model Mapping (DeepInfra Fallback)
**File:** `src/app/infrastructure/adapters/agent_squad/llm_client_deepinfra.py`

```python
VERTEX_TO_DEEPINFRA_MAPPING = {
    "gemini-2.0-flash-exp": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "gemini-1.5-flash": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "gemini-1.5-pro": "meta-llama/Meta-Llama-3.1-405B-Instruct",
}
```

---

## 9. Test Flow Sequence Diagram

```
┌────────┐     ┌──────────┐     ┌────────────┐     ┌────────────┐     ┌─────────┐
│ Client │     │Controller│     │  Interactor │     │ Distiller  │     │ Handler │
└───┬────┘     └────┬─────┘     └──────┬─────┘     └──────┬─────┘     └────┬────┘
    │               │                   │                  │                │
    │  POST /guest/chat                 │                  │                │
    │──────────────▶│                   │                  │                │
    │               │                   │                  │                │
    │               │ execute(message)  │                  │                │
    │               │──────────────────▶│                  │                │
    │               │                   │                  │                │
    │               │                   │ distill(query)   │                │
    │               │                   │─────────────────▶│                │
    │               │                   │                  │                │
    │               │                   │                  │── classify     │
    │               │                   │                  │── assess       │
    │               │                   │                  │── extract      │
    │               │                   │                  │── route        │
    │               │                   │                  │                │
    │               │                   │◀─DistillResult ──│                │
    │               │                   │                  │                │
    │               │                   │ handle_intent()                   │
    │               │                   │──────────────────────────────────▶│
    │               │                   │                                   │
    │               │                   │                   ┌───────────────┤
    │               │                   │                   │ Hunter AI     │
    │               │                   │                   │ ULTRA         │
    │               │                   │                   │ GraphRAG      │
    │               │                   │                   │ DeFi Handler  │
    │               │                   │                   │ Agent Squad   │
    │               │                   │                   └───────────────┤
    │               │                   │                                   │
    │               │                   │◀───────────response──────────────│
    │               │                   │                                   │
    │               │◀──GuestResponse───│                                   │
    │               │                   │                                   │
    │◀──JSON────────│                   │                                   │
    │               │                   │                                   │
```

---

## 10. Test Cases Matrix

### 10.1 Intent Detection Tests
| Test ID | Input | Expected Intent | Expected Entities |
|---------|-------|-----------------|-------------------|
| T001 | "deposit 100 USDC into Morpho" | LENDING | amount=100, token=USDC, protocol=Morpho |
| T002 | "compare lending rates for ETH" | MONEY_MARKET | token=ETH |
| T003 | "swap 1 ETH to USDC" | SWAP | amount=1, from=ETH, to=USDC |
| T004 | "what's the sentiment on Bitcoin" | HUNTER_SENTIMENT | token=Bitcoin |
| T005 | "predict ETH price next week" | HUNTER_PRICE_PREDICTION | token=ETH |
| T006 | "find arbitrage opportunities" | ULTRA_ARBITRAGE | - |
| T007 | "search for Aave protocol" | PROTOCOL_SEARCH | protocol=Aave |
| T008 | "analyze my portfolio" | SPECIALIST_TASK | agent=portfolio |
| T009 | "research and stake ETH" | COMPLEX_WORKFLOW | token=ETH |
| T010 | "show my balance" | BALANCE (restricted) | - |

### 10.2 Distillation Route Tests
| Test ID | Input | Expected Route | Reason |
|---------|-------|----------------|--------|
| D001 | "hello" | STATIC | Greeting template |
| D002 | "what is the weather" | REJECT | Off-topic |
| D003 | "ETH price" | CACHE/STATIC | Price check template |
| D004 | "swap 100 ETH to USDC" | FULL_LLM | Transaction intent |
| D005 | "explain DeFi" | LIGHT_LLM | Simple educational |
| D006 | "optimize my leveraged farming" | FULL_LLM | Complex strategy |

### 10.3 Handler Routing Tests
| Test ID | Intent | Expected Handler | Data Source |
|---------|--------|------------------|-------------|
| H001 | HUNTER_SENTIMENT | SentimentAggregator | Twitter, Reddit, News |
| H002 | HUNTER_PRICE_PREDICTION | LSTMPricePredictor | CoinGecko OHLCV |
| H003 | ULTRA_ARBITRAGE | ArbitrageDiscovery | DEX prices |
| H004 | PROTOCOL_SEARCH | GraphRAGService | Knowledge graph |
| H005 | LENDING | LendingHandler | Morpho/Aave API |
| H006 | SPECIALIST_TASK | AgentOrchestrator | Single agent |
| H007 | COMPLEX_WORKFLOW | SupervisorCoordinator | Multi-agent |

### 10.4 Agent Orchestration Tests
| Test ID | Message | Expected Agents | Workflow |
|---------|---------|-----------------|----------|
| A001 | "analyze ETH risk" | RISK_ANALYZER | Single agent |
| A002 | "optimize my yield" | DEFI_YIELD | Single agent |
| A003 | "research and buy ETH" | RESEARCH → EXECUTION | Multi-agent |
| A004 | "full portfolio review" | PORTFOLIO + RISK + TAX | Parallel agents |
| A005 | "debate: stake vs lend" | Multi-agent voting | Agent debate |

---

## 11. Error Handling Paths

### 11.1 Rate Limit Errors
```python
if rate_limit_exceeded:
    return GuestChatResponse(
        success=False,
        error="rate_limit_exceeded",
        message="You've reached the message limit. Please try again later.",
    )
```

### 11.2 Restricted Intent Errors
```python
if intent in RESTRICTED_INTENTS:
    return GuestChatResponse(
        success=True,
        message="To view your portfolio, please sign up for a free account.",
        requires_registration=True,
    )
```

### 11.3 Agent Fallback Chain
```python
fallback_chain = [
    FallbackAgent("primary", timeout=30s, min_confidence=0.7),
    FallbackAgent("secondary", timeout=45s, min_confidence=0.6),
    FallbackAgent("tertiary", timeout=60s, min_confidence=0.5),
]
```

### 11.4 LLM Provider Fallback
```
Vertex AI (Primary) → [Error/Timeout] → DeepInfra (Fallback)
```

---

## 12. Telemetry & Monitoring

### 12.1 Request Telemetry
**File:** `src/app/domain/value_objects/distillation.py`

```python
@dataclass
class DistillationTelemetry:
    request_id: str
    user_id: Optional[UUID]
    original_query: str
    normalized_query: str
    intent: str
    intent_confidence: float
    complexity: str
    entities: dict
    route_type: str
    routing_reason: str
    suggested_model_tier: str
    suggested_agent: str
    cache_key: str
    cache_hit: bool
    cache_level: CacheLevel
    classification_latency_ms: int
    total_latency_ms: int
    was_processed: bool
    llm_request_id: Optional[str]
    created_at: datetime
```

### 12.2 Agent Performance Metrics
```python
@dataclass
class AgentPerformanceMetrics:
    agent_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: int
    avg_confidence: float
    total_cost_usd: Decimal
```

---

## 13. Configuration Reference

### 13.1 Rate Limits
```python
RATE_LIMIT_MESSAGES_PER_HOUR = 20
RATE_LIMIT_MESSAGES_PER_DAY = 50
MAX_MESSAGE_LENGTH = 500
```

### 13.2 Agent Squad Settings
**File:** `src/app/setup/config/agent_squad.py`

```python
class AgentSquadSettings(BaseModel):
    enabled: bool = True
    enable_intent_classification: bool = True
    intent_classification_model: str = "gemini-2.0-flash-exp"
    intent_confidence_threshold: float = 0.85
    fallback_agent: str = "chat"
    enable_supervisor: bool = True
    supervisor_model: str = "gemini-2.0-flash-exp"
    supervisor_max_agents: int = 5
    supervisor_timeout_seconds: int = 120
    max_concurrent_agents: int = 3
    routing_timeout_seconds: int = 5
    execution_timeout_seconds: int = 60
```

### 13.3 Distillation Settings
```python
class DistillationConfig:
    enabled: bool = True
    cache_enabled: bool = True
    static_responses_enabled: bool = True
    semantic_similarity_threshold: float = 0.85
    force_full_llm_intents: set[Intent] = {
        Intent.SWAP_REQUEST,
        Intent.BORROW_REQUEST,
        Intent.RISK_ASSESSMENT,
        Intent.STRATEGY_ADVICE,
    }
```

---

## 14. Quick Test Commands

```bash
# Test DeFi Shortcuts
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "deposit 100 USDC into Morpho"}'

# Test Hunter AI
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what is the sentiment on Ethereum"}'

# Test ULTRA
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "find arbitrage opportunities"}'

# Test Agent Squad
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "analyze my portfolio risk and suggest optimizations"}'

# Test Restricted (should prompt registration)
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show my balance"}'
```

---

## 15. Related Documentation

- `docs/steering/guest-chat-intent-testing.md` - Full test input/output examples
- `docs/steering/llm-models-cost-analysis.md` - LLM provider comparison
- `docs/GUEST_CHAT_SYSTEM.md` - Guest chat system overview
- `docs/AGENT_SQUAD_VERTEX_DEEPINFRA.md` - Agent Squad setup guide
- `docs/HUNTER_AI_DATA_SOURCES.md` - Hunter AI data sources
