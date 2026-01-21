# Messaging System Architecture

> **Documentation for Guest/Message and Conversations/Message Systems**
> 
> Based on CTO Engineering Methodology: First Principles, Design Thinking, Systems Thinking

## Executive Summary

The Anvil messaging system provides a unified, multi-agent orchestration platform for handling user queries across both guest (unauthenticated) and authenticated user contexts. The architecture leverages a **Supervisor Coordinator** pattern with **LLM-based semantic routing** (no intent classification), **18 specialized AI agents**, and comprehensive **telemetry** for observability.

**Key Design Principles:**
- **Unified Architecture**: Same core structure for guest and authenticated users
- **LLM-Based Routing**: Pure semantic understanding - NO intent classification
- **Agent-Based Orchestration**: Multi-agent workflows with dependency management and parallel execution
- **Context-Aware Processing**: Conversation history used for better routing decisions
- **Observability**: Comprehensive telemetry and agent timing tracking
- **Scalability**: Stateless design with Redis-backed session management

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Message Flow](#message-flow)
4. [Supervisor Coordinator](#supervisor-coordinator)
5. [Agent Squad](#agent-squad)
6. [LLM-Based Routing](#llm-based-routing)
7. [Telemetry & Observability](#telemetry--observability)
8. [Guest vs Authenticated Differences](#guest-vs-authenticated-differences)
9. [Implementation Details](#implementation-details)
10. [Future Enhancements](#future-enhancements)

---

## System Overview

### Current Implementation: Guest/Message

**Endpoint**: `POST /api/v1/guest/chat`

**Flow** (LLM-Based Routing - NO Intents):
```
User Message → Guest User Creation (by IP) → Conversation Creation → 
Security Check (harmful content only) → Supervisor Coordinator (LLM Planning) → 
Agent Orchestration (Parallel Execution) → Response Aggregation → Telemetry Logging
```

**Key Components**:
- `SendGuestMessage` command handler
- `SupervisorCoordinator` for LLM-based workflow planning
- `AgentOrchestrator` for agent execution
- `GuestRepository` for persistence

### Future Implementation: Conversations/Message

**Endpoint**: `POST /api/v1/conversations/{conversation_id}/messages`

**Flow** (Same structure as guest):
```
User Message → User Authentication → Conversation Retrieval → 
Security Check → Supervisor Coordinator (LLM Planning) → 
Agent Orchestration (Parallel Execution) → Response Aggregation → Telemetry Logging
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
  - **Security check** (harmful content detection only)
  - **LLM-based routing** via Supervisor Coordinator
  - Agent orchestration with parallel execution
  - Telemetry logging
  - Rate limiting

**Key Method**: `_process_with_llm_supervisor()`
- Builds conversation context
- Calls `SupervisorCoordinator.create_workflow_plan()` for LLM-based action detection
- Calls `SupervisorCoordinator.execute_workflow()` for parallel agent execution
- Handles sources and response aggregation

**SendConversationMessage** (Future - same structure):
- **Responsibilities**:
  - User authentication verification
  - Conversation ownership check
  - Conversation history building (last N messages)
  - **Security check** (harmful content detection only)
  - **LLM-based routing** via Supervisor Coordinator
  - Agent orchestration with parallel execution
  - Telemetry logging
  - Rate limiting (user-tier based)

### Layer 3: Domain (Business Logic)

**SupervisorCoordinator** (`src/app/domain/services/agent_squad/supervisor_coordinator.py`):
- **Purpose**: Plan multi-agent workflows using LLM semantic understanding
- **Input**: User message, conversation context
- **Output**: `WorkflowPlan` with agent tasks and dependencies
- **Key Methods**:
  - `create_workflow_plan()`: LLM-based action detection and task planning
  - `execute_workflow()`: Parallel execution of independent tasks
  - `_build_planning_prompt()`: Optimized prompt for LLM routing
  - `_aggregate_results()`: Combine agent responses

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

---

## Message Flow

### Detailed Flow Diagram (LLM-Based Routing)

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
│  - Build context object with metadata                           │
│  - Include user language preference                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. Security Check (ONLY)                     │
│  - Harmful content detection (launder, exploit, rug pull, etc.) │
│  - If harmful: Block request                                    │
│  - NO intent classification - just security                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5. Supervisor Coordinator (LLM Planning)     │
│  - Build optimized planning prompt with:                        │
│    * User request                                               │
│    * Conversation context (last 3 messages)                     │
│    * Available agents                                           │
│    * Routing rules (off-topic, crypto topics)                   │
│    * Few-shot examples                                          │
│  - Call LLM to create workflow plan                            │
│  - Parse JSON response into AgentTasks                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    6. Agent Orchestration (Parallel)            │
│  For each task (parallel execution of independent tasks):       │
│    - Resolve agent from DI container                            │
│    - Build conversation context                                 │
│    - Handle off-topic: Pass [SYSTEM INSTRUCTION] to chat agent  │
│    - Execute agent with message                                │
│    - Collect AgentResponse (content, sources, tools_used)      │
│    - Handle errors (continue on failure)                        │
│                                                                 │
│  ⚡ Independent tasks execute in PARALLEL (asyncio.gather)      │
│  ⏳ Dependent tasks execute SEQUENTIALLY                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    7. Response Aggregation                     │
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
│                    8. Telemetry & Logging                      │
│  - Log message to database                                      │
│  - Record agent timings                                         │
│  - Track tools_used and sources                                 │
│  - Update conversation metadata                                │
│  - Increment rate limit counters                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    9. Response Formatting                      │
│  - Build GuestChatResponse / ChatResponse                       │
│  - Include routing metadata (handler: supervisor_llm)          │
│  - Include enrichment (agent_timings, tools_used, agents_used) │
│  - Include sources (API calls, LLM providers)                   │
│  - Include registration prompts (if restricted)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    10. HTTP Response                            │
│  Status: 200 OK / 201 Created                                   │
│  Body: JSON with message, routing, enrichment, sources         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Supervisor Coordinator

### Purpose

The `SupervisorCoordinator` is the **brain** of the multi-agent system. It uses **LLM semantic understanding** (NOT intent classification) to:

1. **Understand User Request**: Parse what the user wants naturally
2. **Detect Actions Needed**: Determine which agents should handle the request
3. **Plan Workflow**: Create agent tasks with dependencies
4. **Execute in Parallel**: Run independent tasks concurrently for speed

### LLM-Based Routing (NO Intents)

**CEO Directive**: The system does NOT use intent classification. Instead:

1. **Security Check Only**: Only pattern matching for harmful content (security)
2. **LLM Planning**: Supervisor uses LLM to semantically understand and route
3. **Dynamic Detection**: LLM determines actions based on natural understanding

**Planning Prompt Structure**:
```
You are a DeFi workflow router. Route to the correct agent. JSON only.

<request>{user_message}</request>
<context>{last_3_messages}</context>
<agents>{available_agents}</agents>

<rules>
1. OFF-TOPIC FIRST: If NOT about crypto/DeFi/blockchain/Web3, use "chat" + "Decline off-topic politely"
2. CRYPTO TOPICS:
   - Prices → "hunter_ai"
   - DeFi education → "knowledge"
   - Yield/APY → "defi_yield"
   - Risk/TVL → "risk_analyzer"
   - Gas → "gas_optimizer"
   - Wallet (balance/send/receive) → "guest_auth"
   - Greetings → "chat"
</rules>

<examples>
"hola" → {"tasks":[{"agent_type":"chat","task_description":"Greet warmly","depends_on":[]}]}
"btc price" → {"tasks":[{"agent_type":"hunter_ai","task_description":"Get BTC price","depends_on":[]}]}
"make a cake" → {"tasks":[{"agent_type":"chat","task_description":"Decline off-topic politely, I only help with DeFi","depends_on":[]}]}
</examples>

{"tasks":[{"agent_type":"...","task_description":"...","depends_on":[]}]}
```

### Parallel Execution

**New Feature**: Independent tasks execute in parallel using `asyncio.gather`:

```python
async def execute_workflow(...):
    while iteration < max_iterations:
        ready_tasks = get_ready_tasks()  # Tasks with all dependencies met
        
        if len(ready_tasks) == 1:
            await execute_single_task(ready_tasks[0])
        else:
            # ⚡ PARALLEL EXECUTION
            logger.info(f"Executing {len(ready_tasks)} tasks in parallel")
            await asyncio.gather(*[execute_single_task(task) for task in ready_tasks])
```

**Performance Impact**:
- Before: Sequential execution (~21s for multi-agent queries)
- After: Parallel execution (~6-8s for multi-agent queries)
- **~70% faster** for complex workflows

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
    task_description: str  # What the agent should do (used for off-topic handling)
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
1. **CHAT** - General conversation, off-topic handling, aggregation
2. **GUEST_AUTH** - Authentication requirements (guest users)
3. **KNOWLEDGE** - Educational queries, Anvil knowledge
4. **HUNTER_AI** - Market sentiment, price data (CoinGecko)
5. **RESEARCH** - Deep protocol analysis (Perplexity)
6. **EXECUTION** - Transaction execution (Privy wallet, 1inch)
7. **RISK_ANALYZER** - Risk assessment, TVL analysis (DeFiLlama)
8. **PORTFOLIO** - Portfolio optimization, rebalancing
9. **TAX_OPTIMIZER** - Tax-loss harvesting, reporting
10. **DEFI_YIELD** - Yield farming, APY analysis (DeFiLlama)
11. **SECURITY_AUDITOR** - Smart contract security (Slither)
12. **GAS_OPTIMIZER** - Gas fee optimization (Web3Client)

**Enterprise Agents (6)**:
13. **COMPLIANCE_MONITOR** - AML/KYC, regulatory compliance
14. **MULTISIG_COORDINATOR** - Multi-sig treasury management
15. **ALERT_MONITORING** - Real-time alerts, anomaly detection
16. **CRISIS_MANAGER** - Emergency response, circuit breaker
17. **BRIDGE_CROSSCHAIN** - Layer 2, cross-chain operations
18. **LENDING_BORROWING** - Leverage, collateral optimization

### Agent Tools & Data Sources

| Agent | Tools | Data Sources | LLM Provider |
|-------|-------|--------------|--------------|
| **CHAT** | LLM Gateway | Knowledge Base | Vertex AI (gemini-2.0-flash) |
| **KNOWLEDGE** | Knowledge Injector | Anvil Knowledge Base (JSON) | Vertex AI / DeepInfra |
| **HUNTER_AI** | CoinGecko API | CoinGecko, RSS News | Vertex AI |
| **DEFI_YIELD** | DeFiLlama API | DeFiLlama Yield Data | Vertex AI |
| **RISK_ANALYZER** | DeFiLlama API | DeFiLlama Protocol Data | Vertex AI |
| **GAS_OPTIMIZER** | Web3Client (Alchemy/Infura) | Ethereum Gas Oracle | Vertex AI |
| **GUEST_AUTH** | Auth Detection | Translation Service | N/A (rule-based) |

### Off-Topic Handling

When the LLM detects an off-topic query:

1. **LLM Planning**: Creates task with `"Decline off-topic politely"` in task_description
2. **Supervisor**: Detects `"decline"` or `"off-topic"` in task_description
3. **Message Enhancement**: Passes `[SYSTEM INSTRUCTION: {task_description}]` to chat agent
4. **Chat Agent**: Parses instruction and generates polite decline response

```python
# In supervisor_coordinator.py
if "decline" in task_desc_lower or "off-topic" in task_desc_lower or "politely" in task_desc_lower:
    logger.info(f"🚫 OFF-TOPIC detected: {task.task_description}")
    message_content = MessageContent(f"[SYSTEM INSTRUCTION: {task.task_description}]\n\nUser message: \"{original_message}\"")
```

---

## LLM-Based Routing

### Why No Intent Classification?

**CEO Directive**: Remove all intent classification in favor of pure LLM-based routing.

**Before** (Intent-Based):
1. Intent Classifier (regex + LLM) → Classify intent
2. Fast-path patterns → Shortcut common queries
3. Distillation Engine → Route based on intent
4. Supervisor → Plan based on intent

**After** (LLM-Based):
1. Security Check → Only block harmful content
2. Supervisor LLM → Semantically understand and route
3. Execute → Run planned agents

**Benefits**:
- **Simpler Architecture**: One LLM call for routing instead of multiple classification steps
- **More Natural**: LLM understands context better than regex patterns
- **Flexible**: Easy to add new agent types without adding patterns
- **Multilingual**: Works across languages without separate patterns

### Routing Rules

**Off-Topic Detection**:
- Cooking, recipes, weather, sports, general knowledge → Decline politely
- Redirect to DeFi topics

**Crypto Topics**:
- Prices, market data → `hunter_ai`
- Education, explanations → `knowledge`
- Yield/APY/lending → `defi_yield`
- Risk/TVL analysis → `risk_analyzer`
- Gas prices → `gas_optimizer`
- Wallet actions → `guest_auth`
- Greetings, general chat → `chat`

---

## Telemetry & Observability

### Response Metadata

**Routing Info**:
```json
{
  "handler": "supervisor_llm",
  "intent": "LLM_WORKFLOW",
  "workflow_type": "llm_planned"
}
```

**Enrichment Metadata**:
```json
{
  "agent_squad": true,
  "workflow_type": "supervisor_coordinator",
  "task_count": 2,
  "disclaimer": "You're in demo mode. Some features require registration.",
  "agents_used": ["hunter_ai", "chat"],
  "agent_timings": [
    {
      "agent_type": "hunter_ai",
      "task_description": "Get BTC price | Tools: CoinGecko API",
      "execution_time_ms": 2699,
      "status": "completed",
      "provider": "vertex_ai"
    }
  ]
}
```

---

## Guest vs Authenticated Differences

### Guest/Message System

**User Identification**:
- IP address-based guest user creation
- No authentication required
- Session management via IP

**Rate Limiting**:
- 5000 messages/hour (testing)
- 10000 messages/day (testing)
- IP-based tracking

**Restricted Features**:
- Portfolio access → Registration prompt via `guest_auth` agent
- Balance queries → Registration prompt
- Transaction execution → Registration prompt
- Wallet address → Registration prompt

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

### Shared Components

Both systems use:
- **SupervisorCoordinator**: Same LLM-based workflow planning
- **Agent Squad**: Same 18 agents
- **Agent Orchestration**: Same parallel execution flow
- **Response Aggregation**: Same aggregation logic
- **Conversation History**: Both build and use history for context

---

## Implementation Details

### Guest Message Handler

**File**: `src/app/application/guest/commands/send_guest_message.py`

**Key Method**: `_process_with_llm_supervisor()`

```python
async def _process_with_llm_supervisor(
    self, content: str, language: str, conversation: GuestConversation, guest: GuestUser,
    context: str, ip_address: str, user_agent: str | None = None, referer: str | None = None,
) -> GuestMessageResult | None:
    """
    Process message using LLM-based routing (NO intents).
    
    Flow:
    1. Build conversation history
    2. Create workflow plan via SupervisorCoordinator
    3. Execute workflow (parallel agent execution)
    4. Handle sources and build response
    """
    # Build conversation context
    agent_squad_context = ConversationContext(
        conversation_history=history,
        user_metadata={"language": language, "is_guest": True},
    )
    
    # LLM-based action detection
    workflow_plan = await self._supervisor_coordinator.create_workflow_plan(
        conversation_id=ConversationId(conversation.id),
        message=MessageContent(content),
        conversation_context=agent_squad_context,
        available_agents=available_agents,
    )
    
    # Execute with parallel execution
    response_content, sources_raw, agent_timings = await self._supervisor_coordinator.execute_workflow(
        workflow_plan=workflow_plan,
        conversation_id=ConversationId(conversation.id),
        message=MessageContent(content),
        conversation_context=agent_squad_context,
    )
```

### Main Execute Flow

```python
async def execute(...) -> GuestMessageResult:
    # 1. Get/create guest user
    # 2. Check rate limits
    # 3. Get/create conversation
    # 4. Build conversation history
    
    # ============================================================
    # ✨ LLM-BASED ROUTING (NO INTENTS, NO FAST-PATHS) ✨
    # ============================================================
    # The ONLY pattern check is for harmful content (security).
    
    if self._supervisor_coordinator and self._agent_orchestrator:
        # Security check only
        is_harmful = any(pattern in content_lower for pattern in harmful_patterns)
        
        if not is_harmful:
            result = await self._process_with_llm_supervisor(...)
            if result is not None:
                return result
    
    # LEGACY FLOW (FALLBACK ONLY)
    # ...
```

---

## Future Enhancements

### Planned Improvements

1. **Streaming Responses**:
   - WebSocket support for real-time agent responses
   - Progressive response updates
   - Token-by-token streaming

2. **Enhanced Parallel Execution**:
   - Wave-based execution for complex dependencies
   - Dynamic parallelism based on agent availability
   - Load balancing across LLM providers

3. **Prompt Optimization**:
   - A/B testing for prompt variants
   - Performance metrics per prompt version
   - Automated prompt tuning

4. **Context Compression**:
   - Summarize long conversation history
   - Compress knowledge base context
   - Optimize token usage

---

## Conclusion

The Anvil messaging system provides a robust, scalable architecture for handling user queries across both guest and authenticated contexts. The **LLM-based routing** (without intent classification) enables intelligent, context-aware multi-agent workflows, while **parallel execution** ensures optimal performance.

**Key Strengths**:
- Pure LLM-based semantic routing (no intents)
- Parallel agent execution for speed
- Comprehensive off-topic handling
- Unified architecture for guest and authenticated users

**Performance Metrics** (from tests):
- Average response time: ~6-8s for single-agent queries
- Parallel execution: ~70% faster than sequential
- Off-topic detection: 91% accuracy
- Agent routing: 91% pass rate

---

## References

- **Supervisor Coordinator**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`
- **Agent Orchestrator**: `src/app/domain/services/agent_squad/agent_orchestrator.py`
- **Guest Message Handler**: `src/app/application/guest/commands/send_guest_message.py`
- **Conversations Router**: `src/app/presentation/http/controllers/chat/conversations_router.py`
- **Agent Types**: `src/app/domain/enums/agent_type.py`
- **Test Results**: `docs/output/guest_input.csv`

---

*Document Version: 2.0*  
*Last Updated: 2026-01-21*  
*Author: Anvil Engineering Team*

**Changelog**:
- **v2.0** (2026-01-21): Major rewrite for LLM-based routing architecture
  - Removed intent classification (CEO directive)
  - Added parallel execution documentation
  - Updated flow diagrams for new architecture
  - Added performance metrics from test results
  - Simplified routing rules and prompt structure
- **v1.1** (2026-01-20): Updated Distillation Engine section
