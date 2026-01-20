# Messaging System Architecture

> **Documentation for Guest/Message and Conversations/Message Systems**
> 
> Based on CTO Engineering Methodology: First Principles, Design Thinking, Systems Thinking

## Executive Summary

The Anvil messaging system provides a unified, multi-agent orchestration platform for handling user queries across both guest (unauthenticated) and authenticated user contexts. The architecture leverages a **Supervisor Coordinator** pattern with **18 specialized AI agents**, **distillation engine** for query optimization, and comprehensive **telemetry** for observability.

**Key Design Principles:**
- **Unified Architecture**: Same core structure for guest and authenticated users
- **Agent-Based Orchestration**: Multi-agent workflows with dependency management
- **Intelligent Routing**: Hybrid intent classification (rule-based + LLM) with conversation history
- **Context-Aware Processing**: Conversation history used for better intent detection and routing
- **Observability**: Comprehensive telemetry and agent timing tracking
- **Scalability**: Stateless design with Redis-backed session management

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Message Flow](#message-flow)
4. [Supervisor Coordinator](#supervisor-coordinator)
5. [Agent Squad](#agent-squad)
6. [Distillation Engine](#distillation-engine)
7. [Telemetry & Observability](#telemetry--observability)
8. [Guest vs Authenticated Differences](#guest-vs-authenticated-differences)
9. [Implementation Details](#implementation-details)
10. [Future Enhancements](#future-enhancements)

---

## System Overview

### Current Implementation: Guest/Message

**Endpoint**: `POST /api/v1/guest/chat`

**Flow**:
```
User Message → Guest User Creation (by IP) → Conversation Creation → 
Intent Detection → Distillation Engine → Supervisor Coordinator → 
Agent Orchestration → Response Aggregation → Telemetry Logging
```

**Key Components**:
- `SendGuestMessage` command handler
- `SupervisorCoordinator` for workflow planning
- `AgentOrchestrator` for agent execution
- `DistillationEngine` for query optimization
- `GuestRepository` for persistence

### Future Implementation: Conversations/Message

**Endpoint**: `POST /api/v1/conversations/{conversation_id}/messages`

**Flow** (Same structure as guest):
```
User Message → User Authentication → Conversation Retrieval → 
Intent Detection → Distillation Engine → Supervisor Coordinator → 
Agent Orchestration → Response Aggregation → Telemetry Logging
```

**Key Differences**:
- User identification via JWT (not IP)
- Conversation ownership verification
- Enhanced rate limits (1000/hour vs 5000/hour for guests)
- Wallet address context for authenticated users
- Portfolio/balance access (restricted for guests)

---

## Architecture Layers

### Layer 1: Presentation (HTTP Controllers)

**Guest Router** (`src/app/presentation/http/controllers/guest/router.py`):
- Extracts client IP address
- Validates request body
- Delegates to `SendGuestMessage` command
- Formats response with routing metadata

**Conversations Router** (`src/app/presentation/http/controllers/chat/conversations_router.py`):
- Authenticates user (JWT)
- Verifies conversation ownership
- Delegates to message service
- Formats response with conversation context

### Layer 2: Application (Use Cases)

**SendGuestMessage** (`src/app/application/guest/commands/send_guest_message.py`):
- **Responsibilities**:
  - Guest user creation/retrieval (by IP)
  - Conversation management
  - Conversation history building (last 5 messages)
  - Intent detection with context
  - Distillation pass (with conversation history)
  - Supervisor coordination
  - Telemetry logging
  - Rate limiting

**SendConversationMessage** (Future - same structure):
- **Responsibilities**:
  - User authentication verification
  - Conversation ownership check
  - Conversation history building (last N messages)
  - Intent detection with context
  - Distillation pass (with conversation history)
  - Supervisor coordination
  - Telemetry logging
  - Rate limiting (user-tier based)

### Layer 3: Domain (Business Logic)

**SupervisorCoordinator** (`src/app/domain/services/agent_squad/supervisor_coordinator.py`):
- **Purpose**: Plan multi-agent workflows based on query complexity
- **Input**: User message, conversation context
- **Output**: `WorkflowPlan` with agent tasks and dependencies
- **Key Methods**:
  - `create_workflow_plan()`: Generate task plan
  - `_calculate_execution_order()`: Topological sort for dependencies
  - `_aggregate_results()`: Combine agent responses

**DistillationEngine** (`src/app/domain/services/distillation/engine.py`):
- **Purpose**: Optimize query processing (cache, static responses, routing)
- **Components**:
  - `IntentClassifier`: Hybrid classification (rule-based + LLM with conversation history)
  - `ComplexityAssessor`: Assess query complexity
  - `EntityExtractor`: Extract entities (tokens, protocols, etc.)
  - `DistillationRouter`: Route decision (FULL_LLM, CACHED, STATIC)

**AgentOrchestrator** (`src/app/domain/services/agent_squad/agent_orchestrator.py`):
- **Purpose**: Execute agents based on `AgentType`
- **Responsibilities**:
  - Agent resolution (from DI container)
  - Agent execution with context
  - Error handling and fallback
  - Response collection

### Layer 4: Infrastructure (Adapters)

**Agent Implementations** (`src/app/infrastructure/adapters/agent_squad/agents/`):
- 18 specialized agents (see [Agent Squad](#agent-squad))
- Each implements `AgentGateway` protocol
- Tools integration (APIs, databases, LLMs)

**Repositories**:
- `GuestRepository`: Guest user/conversation persistence
- `ChatMessageRepositorySqla`: Authenticated message persistence
- `DistillationTelemetryRepository`: Telemetry storage

---

## Message Flow

### Detailed Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. HTTP Request Received                     │
│  Guest: POST /api/v1/guest/chat                                │
│  Auth:  POST /api/v1/conversations/{id}/messages               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. User/Conversation Resolution               │
│  Guest: Create/retrieve guest by IP                             │
│  Auth:  Verify JWT, get user, verify conversation ownership     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. Conversation Context Building              │
│  - Load last N messages (conversational memory)                 │
│  - Check continuation state (multi-step flows)                  │
│  - Build context object with metadata                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. Intent Detection                          │
│  - IntentDetectorService (LLM-based)                           │
│  - Context-aware detection                                     │
│  - Multi-language support (en, es, pt, zh)                     │
│  - Restricted action detection                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5. Distillation Engine (Optional)             │
│  - Intent classification (hybrid: rule-based + LLM)           │
│    * Rule-based patterns first (fast, high confidence)          │
│    * LLM classification for ambiguous queries                  │
│    * Uses conversation history for context-aware classification│
│  - Complexity assessment                                       │
│  - Entity extraction                                           │
│  - Cache check (exact → semantic)                              │
│  - Static response check                                       │
│  - Route decision: FULL_LLM | CACHED | STATIC                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    6. Fast Path Check                           │
│  Simple info queries → Knowledge agent (bypass workflow)        │
│  Restricted intents → Custom registration messages              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    7. Supervisor Coordinator                     │
│  - Analyze query complexity                                    │
│  - Plan multi-agent workflow                                   │
│  - Create agent tasks with dependencies                         │
│  - Calculate execution order (topological sort)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    8. Agent Orchestration                       │
│  For each task (in dependency order):                           │
│    - Resolve agent from DI container                            │
│    - Build conversation context                                 │
│    - Execute agent with message                                │
│    - Collect AgentResponse (content, sources, tools_used)      │
│    - Handle errors (continue on failure)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    9. Response Aggregation                     │
│  - If single agent: Return response directly                   │
│  - If multiple agents:                                          │
│    * Find CHAT aggregator task                                 │
│    * Build aggregation message with all responses              │
│    * Execute CHAT agent for final summary                      │
│    * Filter authentication messages                            │
│    * Deduplicate content                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    10. Telemetry & Logging                      │
│  - Log message to database                                      │
│  - Record agent timings                                         │
│  - Track tools_used and sources                                 │
│  - Update conversation metadata                                │
│  - Increment rate limit counters                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    11. Response Formatting                      │
│  - Build GuestChatResponse / ChatResponse                       │
│  - Include routing metadata                                     │
│  - Include enrichment (agent_timings, tools_used)             │
│  - Include sources (API calls, LLM providers)                   │
│  - Include registration prompts (if restricted)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    12. HTTP Response                            │
│  Status: 200 OK / 201 Created                                   │
│  Body: JSON with message, routing, enrichment, sources         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Supervisor Coordinator

### Purpose

The `SupervisorCoordinator` is the **brain** of the multi-agent system. It analyzes user queries and creates optimal workflows by:

1. **Understanding Query Intent**: LLM-based analysis of what the user wants
2. **Assessing Complexity**: Determining if single or multi-agent workflow is needed
3. **Planning Tasks**: Creating agent tasks with dependencies
4. **Optimizing Execution**: Calculating optimal execution order

### Workflow Planning Logic

**Single-Agent Workflows** (Fast Path):
- Simple informational queries → `KNOWLEDGE` agent
- Price queries → `HUNTER_AI` agent
- General questions → `CHAT` agent
- Yield farming queries → `DEFI_YIELD` agent
- Risk analysis → `RISK_ANALYZER` agent
- Gas price queries → `GAS_OPTIMIZER` agent

**Multi-Agent Workflows** (Complex Queries):
- "What is Anvil? What's the price of BTC?" → `KNOWLEDGE` + `HUNTER_AI` → `CHAT` (aggregator)
- "Show me yield opportunities and analyze risks" → `DEFI_YIELD` + `RISK_ANALYZER` → `CHAT` (aggregator)
- "Swap 100 USDC for ETH, check gas prices" → `EXECUTION` + `GAS_OPTIMIZER` → `CHAT` (aggregator)

**Task Dependencies**:
- Tasks can depend on previous tasks (e.g., `HUNTER_AI` depends on `KNOWLEDGE`)
- Topological sort ensures correct execution order
- Failed tasks don't block dependent tasks (continue on error)

### Key Methods

```python
class SupervisorCoordinator:
    async def create_workflow_plan(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> WorkflowPlan:
        """
        Create multi-agent workflow plan.
        
        Returns:
            WorkflowPlan with:
            - tasks: List of AgentTask (agent_type, task_description, depends_on)
            - execution_order: Optimal execution order (topological sort)
            - estimated_time_seconds: Estimated completion time
        """
    
    async def execute_workflow(
        self,
        workflow_plan: WorkflowPlan,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> str:
        """
        Execute workflow plan and aggregate results.
        
        Returns:
            Final aggregated response string
        """
    
    async def _aggregate_results(
        self,
        workflow_plan: WorkflowPlan,
    ) -> str:
        """
        Aggregate results from all completed tasks.
        
        - If CHAT aggregator exists: Use its response
        - Otherwise: Intelligently combine responses with deduplication
        """
```

### Workflow Plan Structure

```python
@dataclass
class WorkflowPlan:
    tasks: list[AgentTask]  # Agent tasks with dependencies
    execution_order: list[int]  # Optimal execution order
    estimated_time_seconds: int  # Estimated completion time

@dataclass
class AgentTask:
    agent_type: AgentType  # Which agent to use
    task_description: str  # What the agent should do
    depends_on: list[int]  # Task indices that must complete first
    status: TaskStatus  # pending, in_progress, completed, failed
    result: AgentResponse | str | None  # Execution result
    error: str | None  # Error message if failed
    execution_time_ms: int | None  # Execution time
```

---

## Agent Squad

### Overview

The Agent Squad consists of **18 specialized AI agents**, each designed for specific DeFi/crypto tasks:

**Core User-Facing Agents (12)**:
1. **CHAT** - General conversation, aggregation
2. **GUEST_AUTH** - Authentication requirements (guest users)
3. **KNOWLEDGE** - Educational queries, Anvil knowledge
4. **HUNTER_AI** - Market sentiment, price predictions
5. **RESEARCH** - Deep protocol analysis (Perplexity)
6. **EXECUTION** - Transaction execution (Privy wallet, 1inch)
7. **RISK_ANALYZER** - Risk assessment, TVL analysis (DeFiLlama)
8. **PORTFOLIO** - Portfolio optimization, rebalancing
9. **TAX_OPTIMIZER** - Tax-loss harvesting, reporting
10. **DEFI_YIELD** - Yield farming, APY analysis (DeFiLlama)
11. **SECURITY_AUDITOR** - Smart contract security (Slither)
12. **GAS_OPTIMIZER** - Gas fee optimization (Web3Client)

**Enterprise Agents (8)**:
13. **COMPLIANCE_MONITOR** - AML/KYC, regulatory compliance (Chainalysis)
14. **MULTISIG_COORDINATOR** - Multi-sig treasury management (Gnosis)
15. **ALERT_MONITORING** - Real-time alerts, anomaly detection (Forta)
16. **CRISIS_MANAGER** - Emergency response, circuit breaker (Forta)
17. **BRIDGE_CROSSCHAIN** - Layer 2, cross-chain operations (Axelar)
18. **LENDING_BORROWING** - Leverage, collateral optimization (Aave)
19. **NFT_ASSET_MANAGER** - NFT portfolio, valuation (OpenSea)
20. **DAO_GOVERNANCE** - Voting, proposals, delegation (Snapshot)

### Agent Tools & Data Sources

Each agent uses specific tools and data sources:

| Agent | Tools | Data Sources | LLM Provider |
|-------|-------|--------------|--------------|
| **CHAT** | LLM Gateway | Knowledge Base | Vertex AI (gemini-2.0-flash) |
| **KNOWLEDGE** | Knowledge Injector | Anvil Knowledge Base (JSON) | Vertex AI / DeepInfra |
| **HUNTER_AI** | OpenAI API, CoinGecko API | CoinGecko, RSS News, Reddit | Vertex AI |
| **RESEARCH** | Perplexity API | Perplexity Search | Perplexity |
| **EXECUTION** | Privy Wallet, 1inch API, LLM Gateway | 1inch, Privy | Vertex AI |
| **RISK_ANALYZER** | DeFiLlama API | DeFiLlama Protocol Data | Vertex AI |
| **DEFI_YIELD** | DeFiLlama API | DeFiLlama Yield Data | Vertex AI |
| **GAS_OPTIMIZER** | Web3Client (Alchemy/Infura) | Ethereum Gas Oracle | Vertex AI |
| **PORTFOLIO** | GraphRAG, Database | Multi-chain RPC, Database | Vertex AI |
| **TAX_OPTIMIZER** | Database, Transaction History | Blockchain RPC | Vertex AI |
| **SECURITY_AUDITOR** | Slither, Static Analysis | Smart Contract Code | Vertex AI |
| **GUEST_AUTH** | Auth Detection | Translation Service | Vertex AI |

### Agent Response Structure

All agents return `AgentResponse`:

```python
@dataclass
class AgentResponse:
    content: str  # Response text
    agent_type: AgentType  # Agent that generated response
    tools_used: list[str]  # Tools used (e.g., ["1inch_api", "privy_wallet"])
    sources: list[SourceInfo]  # Data sources (APIs, LLMs, databases)
    metadata: dict  # Additional metadata (tokens_used, latency_ms, etc.)
```

**SourceInfo Structure**:
```python
@dataclass
class SourceInfo:
    source_type: SourceType  # API, LLM, DATABASE, KNOWLEDGE_BASE, BLOCKCHAIN
    source_name: str  # "1inch", "CoinGecko", "gemini-2.0-flash"
    citation_text: str  # Human-readable citation
    fetched_at: datetime  # When data was fetched
    provider: str  # "Vertex AI", "CoinGecko API", etc.
    endpoint: str | None  # API endpoint if applicable
    query_params: dict | None  # Query parameters if applicable
    relevance_score: float | None  # Relevance score (0.0-1.0)
    metadata: dict | None  # Additional metadata
```

### Agent Execution Flow

```python
# 1. Agent resolved from DI container
agent = await container.get(AgentGateway, agent_type=AgentType.HUNTER_AI)

# 2. Build conversation context
context = ConversationContext(
    conversation_history=[...],  # Last N messages
    user_metadata={"language": "en", "is_guest": True},
    session_metadata={"ip_address": "..."},
)

# 3. Execute agent
response = await agent.execute(
    conversation_id=conversation_id,
    message=MessageContent("What's the price of BTC?"),
    conversation_context=context,
)

# 4. Response contains:
# - content: "Bitcoin (BTC): $89,433.00"
# - tools_used: ["coingecko_api", "openai_api"]
# - sources: [SourceInfo(source_type=API, source_name="CoinGecko", ...)]
# - metadata: {"tokens_used": 150, "latency_ms": 1835}
```

---

## Distillation Engine

### Purpose

The `DistillationEngine` optimizes query processing by:

1. **Hybrid Intent Classification**: Rule-based patterns + LLM classification with conversation history
2. **Caching**: Exact and semantic cache lookups
3. **Static Responses**: Pre-defined responses for common queries
4. **Routing**: Decision to use FULL_LLM, CACHED, or STATIC response
5. **Complexity Assessment**: Determine if query needs full LLM processing

### Components

**IntentClassifier** (`src/app/domain/services/distillation/intent_classifier.py`):
- **Hybrid Classification Approach**:
  1. **Rule-based patterns** (first tier): Fast regex matching for common queries (~90% accuracy, 0.95 confidence)
  2. **LLM-based classification** (second tier): Vertex AI (`gemini-2.0-flash`) with DeepInfra fallback for ambiguous queries
- **Conversation History Support**: Uses last 3 messages for context-aware classification
- **Benefits**:
  - Fast classification for common queries (rule-based)
  - Accurate classification for ambiguous queries (LLM)
  - Context-aware routing (conversation history)
  - Helps Supervisor Coordinator route correctly
- **Returns**: Intent and confidence score (0.0-1.0)

**ComplexityAssessor**:
- Assesses query complexity (SIMPLE, MODERATE, COMPLEX)
- Factors: query length, entity count, multi-intent detection

**EntityExtractor**:
- Extracts entities (tokens, protocols, amounts, addresses)
- Returns structured entity dictionary

**DistillationRouter**:
- Makes routing decision:
  - `FULL_LLM`: Process with Agent Squad
  - `CACHED`: Return cached response
  - `STATIC`: Return pre-defined response
- **Context-aware routing**: Uses conversation history for better classification

**CacheManager**:
- Exact cache: Hash-based lookup
- Semantic cache: Vector similarity search

**StaticResponder**:
- Pre-defined responses for common queries
- Language-specific responses

### Distillation Flow

```
Query + Conversation History
  ↓
Intent Classification (Hybrid):
  ├─ [1] Rule-based patterns (fast, 0.95 confidence)
  │   ↓ (if match)
  │   Return intent immediately
  │   ↓ (if no match)
  ├─ [2] LLM Classification (Vertex AI + DeepInfra fallback)
  │   ├─ Build prompt with conversation history
  │   ├─ Call llm_client.classify_intent()
  │   ├─ Parse JSON response
  │   └─ Return intent if confidence >= 0.85
  │   ↓ (if LLM fails or low confidence)
  └─ [3] Fallback to UNCLEAR (0.5 confidence)
  ↓
Complexity Assessment
  ↓
Entity Extraction
  ↓
Cache Check (Exact → Semantic)
  ↓
Static Response Check
  ↓
Route Decision: FULL_LLM | CACHED | STATIC
  ↓
If FULL_LLM: Continue to Supervisor Coordinator
If CACHED: Return cached response
If STATIC: Return static response
```

### Intent Classification Details

**Rule-Based Patterns** (First Tier):
- Fast regex matching for common query patterns
- ~90% accuracy for standard queries
- High confidence (0.95) when matched
- No LLM API costs
- Examples:
  - `"what is the price of BTC?"` → `PRICE_CHECK` (0.95 confidence)
  - `"swap 100 USDC for ETH"` → `SWAP_REQUEST` (0.95 confidence)

**LLM-Based Classification** (Second Tier):
- Triggered when no rule-based pattern matches
- Uses Vertex AI (`gemini-2.0-flash`) with automatic DeepInfra fallback
- Includes conversation history (last 3 messages) for context
- Helps disambiguate ambiguous queries
- Examples:
  - `"what type of swaps can I make?"` → `EXPLAIN_CONCEPT` (0.90 confidence)
  - `"what's the price?"` (after swap discussion) → `PRICE_CHECK` (context-aware)

**Conversation History Integration**:
- Last 3 messages included in classification prompt
- Provides context for ambiguous queries
- Example: If previous message was about swaps, `"what's the price?"` likely refers to swap prices

**LLM Client Integration**:
- Uses `LLMClientGateway` from `AgentSquadInfrastructureProvider`
- Automatic fallback: Vertex AI → DeepInfra (on rate limits or errors)
- Model mapping: `gemini-2.0-flash` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- Graceful degradation: Falls back to rule-based if LLM client unavailable

---

## Telemetry & Observability

### Telemetry Data Structure

**Agent Timings** (in `enrichment.agent_timings`):
```json
{
  "agent_type": "hunter_ai",
  "task_description": "Provide the current price of BTC | Tools: CoinGecko API | Data Sources: CoinGecko API",
  "execution_time_ms": 1835,
  "status": "completed",
  "provider": "vertex_ai",
  "tools_used": ["coingecko_api", "openai_api"],
  "sources": ["CoinGecko API"]
}
```

**Enrichment Metadata**:
```json
{
  "agent_squad": true,
  "workflow_type": "supervisor_coordinator",
  "task_count": 3,
  "disclaimer": "You're in demo mode. Some features require registration.",
  "agents_used": ["knowledge", "hunter_ai", "chat"],
  "agent_timings": [...]
}
```

**Sources Tracking**:
- **API Sources**: External APIs (CoinGecko, 1inch, DeFiLlama)
- **LLM Sources**: LLM providers (Vertex AI, DeepInfra, Perplexity)
- **Database Sources**: Internal database queries
- **Knowledge Base Sources**: Anvil knowledge base files
- **Blockchain Sources**: On-chain data (RPC calls)

### Telemetry Logging Points

1. **Message Sent**: Log user message with intent, language, length
2. **Agent Execution**: Log agent type, execution time, tools used, sources
3. **Workflow Completion**: Log workflow plan, task count, total time
4. **Error Events**: Log agent failures, rate limit hits, authentication failures
5. **Rate Limiting**: Track messages per hour/day, remaining quota

### Database Telemetry

**Guest Telemetry** (`guest_telemetry` table):
- `guest_user_id`: Guest user identifier
- `conversation_id`: Conversation identifier
- `event_type`: "message_sent", "registration_prompt", "rate_limit_hit"
- `event_data`: JSON with intent, is_restricted, message_length
- `ip_address`: Client IP
- `user_agent`: Browser user agent
- `referer`: HTTP referer
- `language`: User language
- `created_at`: Timestamp

**Distillation Telemetry** (`distillation_telemetry` table):
- `request_id`: Unique request identifier
- `query`: User query text
- `intent`: Detected intent
- `complexity`: Query complexity
- `entities`: Extracted entities (JSON)
- `route_type`: FULL_LLM | CACHED | STATIC
- `cache_hit`: Boolean
- `processing_time_ms`: Processing time
- `user_id`: Optional user ID

---

## Guest vs Authenticated Differences

### Guest/Message System

**User Identification**:
- IP address-based guest user creation
- No authentication required
- Session management via IP + fingerprint

**Rate Limiting**:
- 5000 messages/hour (testing)
- 10000 messages/day (testing)
- IP-based tracking

**Restricted Features**:
- Portfolio access → Registration prompt
- Balance queries → Registration prompt
- Transaction execution → Registration prompt
- Wallet address → Registration prompt

**Conversation Management**:
- Auto-create guest user on first message
- Auto-create conversation on first message
- Archive conversation after inactivity
- IP-based conversation retrieval

**Telemetry**:
- Log to `guest_telemetry` table
- Track by IP address
- No user_id (null)

### Conversations/Message System

**User Identification**:
- JWT-based authentication
- User ID from token
- Wallet address from user profile

**Rate Limiting**:
- 800 messages/hour (guest tier)
- 1000 messages/hour (authenticated tier)
- 10000 messages/hour (premium tier)
- User ID-based tracking

**Feature Access**:
- Full portfolio access
- Balance queries (with wallet connection)
- Transaction execution (with wallet connection)
- Wallet address retrieval

**Conversation Management**:
- User must create conversation explicitly
- Conversation ownership verification
- User can have multiple conversations
- Conversation metadata (title, message_count)

**Telemetry**:
- Log to `chat_message` table
- Track by user_id
- Include wallet_address in context

### Shared Components

Both systems use:
- **SupervisorCoordinator**: Same workflow planning logic
- **Agent Squad**: Same 18 agents
- **DistillationEngine**: Same optimization logic with hybrid classification
- **Intent Detection**: Same hybrid classification (rule-based + LLM with conversation history)
- **Agent Orchestration**: Same execution flow
- **Response Aggregation**: Same aggregation logic
- **Conversation History**: Both build and use conversation history for context-aware processing

---

## Implementation Details

### Guest Message Handler

**File**: `src/app/application/guest/commands/send_guest_message.py`

**Key Methods**:
```python
class SendGuestMessage:
    async def execute(
        self,
        ip_address: str,
        content: str,
        language: str = "en",
        user_agent: str | None = None,
        referer: str | None = None,
    ) -> GuestMessageResult:
        """
        Main execution flow:
        1. Get or create guest user (by IP)
        2. Get or create conversation
        3. Create user message
        4. Build conversation context (last 5 messages)
        5. Detect intent (with conversation history)
        6. Distillation pass (optional, with conversation history)
           - Hybrid intent classification (rule-based + LLM)
           - Context-aware routing
        7. Supervisor coordination
        8. Agent orchestration
        9. Response aggregation
        10. Telemetry logging
        """
    
    async def _build_conversation_context(
        self,
        conversation_id: UUID,
    ) -> list[dict]:
        """
        Build context from last N messages.
        
        Returns conversation history in format:
        [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ]
        
        This history is passed to:
        - DistillationEngine (for context-aware intent classification)
        - SupervisorCoordinator (for workflow planning)
        - Individual agents (for conversational context)
        """
    
    async def _detect_intent_with_context(
        self,
        content: str,
        context: list[dict],
        language: str,
        continuation_step: str | None,
    ) -> tuple[ChatIntent, float, str]:
        """Detect intent with conversation context."""
    
    async def _get_continuation_state(
        self,
        conversation_id: UUID,
    ) -> tuple[str | None, dict | None, ...]:
        """Get continuation state for multi-step flows."""
```

### Conversation Message Handler (Future)

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Key Methods**:
```python
@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    request_body: SendMessageRequest,
    current_user: FromDishka[CurrentUserService],
    conversation_service: FromDishka[ConversationService],
    # ... other dependencies
) -> ChatResponse:
    """
    Main execution flow (same as guest):
    1. Authenticate user (JWT)
    2. Get conversation (verify ownership)
    3. Get conversation context (last N messages)
    4. Detect intent (with conversation history)
    5. Distillation pass (optional, with conversation history)
       - Hybrid intent classification (rule-based + LLM)
       - Context-aware routing
    6. Supervisor coordination
    7. Agent orchestration
    8. Response aggregation
    9. Telemetry logging
    """
```

### Supervisor Coordinator Implementation

**File**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`

**Key Methods**:
```python
class SupervisorCoordinator:
    async def create_workflow_plan(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> WorkflowPlan:
        """
        Create workflow plan using LLM.
        
        LLM Prompt:
        - Analyze query complexity
        - Identify required agents
        - Create tasks with dependencies
        - Estimate execution time
        """
    
    async def execute_workflow(
        self,
        workflow_plan: WorkflowPlan,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> str:
        """
        Execute workflow plan:
        1. Get execution order (topological sort)
        2. For each task:
           - Wait for dependencies
           - Execute agent
           - Collect response
           - Continue on error
        3. Aggregate results
        """
```

### Agent Orchestrator Implementation

**File**: `src/app/domain/services/agent_squad/agent_orchestrator.py`

**Key Methods**:
```python
class AgentOrchestrator:
    async def execute_agent(
        self,
        conversation_id: ConversationId,
        agent_type: AgentType,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """
        Execute agent:
        1. Resolve agent from DI container
        2. Build conversation context
        3. Execute agent.execute()
        4. Return AgentResponse
        """
```

---

## Future Enhancements

### Planned Improvements

1. **Streaming Responses**:
   - WebSocket support for real-time agent responses
   - Progressive response updates
   - Token-by-token streaming

2. **Advanced Caching**:
   - Semantic cache with vector similarity
   - Multi-level caching (Redis → Database → LLM)
   - Cache invalidation strategies

3. **Agent Learning**:
   - Agent performance tracking
   - Automatic agent selection optimization
   - A/B testing for agent configurations

4. **Enhanced Telemetry**:
   - Real-time dashboard for agent performance
   - Cost tracking per agent
   - User satisfaction metrics

5. **Multi-Modal Support**:
   - Image input processing
   - Chart generation
   - Voice input/output

### Architecture Evolution

**Current**: Monolithic agent execution
**Future**: Microservices architecture with:
- Agent services as separate services
- Message queue for agent communication
- Distributed caching
- Load balancing for agent execution

---

## Conclusion

The Anvil messaging system provides a robust, scalable architecture for handling user queries across both guest and authenticated contexts. The **Supervisor Coordinator** pattern enables intelligent multi-agent workflows, while the **Distillation Engine** optimizes query processing. Comprehensive **telemetry** ensures observability and performance monitoring.

**Key Strengths**:
- Unified architecture for guest and authenticated users
- Flexible agent orchestration
- Comprehensive observability
- Scalable design

**Areas for Improvement**:
- Streaming response support
- Advanced caching strategies
- Agent performance optimization
- Multi-modal capabilities

---

## References

- **Supervisor Coordinator**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`
- **Agent Orchestrator**: `src/app/domain/services/agent_squad/agent_orchestrator.py`
- **Distillation Engine**: `src/app/domain/services/distillation/engine.py`
- **Guest Message Handler**: `src/app/application/guest/commands/send_guest_message.py`
- **Conversations Router**: `src/app/presentation/http/controllers/chat/conversations_router.py`
- **Agent Types**: `src/app/domain/enums/agent_type.py`
- **CTO Methodology**: `cto.md`

---

*Document Version: 1.1*  
*Last Updated: 2026-01-20*  
*Author: Anvil Engineering Team*

**Changelog**:
- **v1.1** (2026-01-20): Updated Distillation Engine section to reflect hybrid classification (rule-based + LLM) with conversation history support
