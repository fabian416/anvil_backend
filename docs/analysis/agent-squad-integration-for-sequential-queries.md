# Agent Squad Integration for Sequential Multi-Intent Queries - CTO Analysis

> **Key Insight**: Agent Squad with SupervisorCoordinator CAN handle sequential multi-intent queries, but it's **not currently integrated** into guest chat.

## Current State Analysis

### What Agent Squad Has

**SupervisorCoordinator** (`src/app/domain/services/agent_squad/supervisor_coordinator.py`):
- ✅ Can break down complex tasks into multiple agent subtasks
- ✅ Handles task dependencies and execution order
- ✅ Executes agents sequentially with context preservation
- ✅ Aggregates results from multiple agents
- ✅ Uses LLM for workflow planning

**Example Capability:**
```python
# SupervisorCoordinator can handle:
User: "Create a balanced DeFi portfolio"
  ↓
Supervisor Plan:
  1. Research agent: Find top protocols
  2. Risk analyzer: Assess protocol risks  
  3. Portfolio agent: Create optimal allocation
  4. Tax optimizer: Suggest tax-efficient timing
  5. Chat agent: Summarize recommendations
```

### What Guest Chat Has

**Guest Handler Service** (`src/app/application/guest/handlers/guest_handler_service.py`):
- ❌ `_handle_complex_workflow()` - Only returns **demo/promotional messages**
- ❌ `_handle_specialist_task()` - Only returns **demo/promotional messages**
- ❌ **No actual integration** with SupervisorCoordinator
- ❌ **No routing** to Agent Squad for complex queries

**Current Flow:**
```
Guest: "I want to know about BTC and make a swap"
  ↓
Intent Detection → Picks one intent (SWAP)
  ↓
Guest Handler → Executes only swap
  ↓
Response → Only swap quote (BTC info lost)
```

## The Gap

**Problem**: Agent Squad exists and can handle sequential multi-intent, but:
1. Guest chat doesn't use it
2. Guest handlers return demo messages instead of real Agent Squad execution
3. No routing logic to detect when to use Agent Squad

## Solution: Integrate Agent Squad into Guest Chat

### Phase 1: Route Complex Queries to Agent Squad

**Detection Logic:**
```python
# In send_guest_message.py

# Check if query is complex (multiple intents)
sequential_intents = self._detect_sequential_intents(content, language)

if len(sequential_intents) > 1:
    # Route to Agent Squad SupervisorCoordinator
    supervisor = SupervisorCoordinator(...)
    workflow_plan = await supervisor.create_workflow_plan(
        message=content,
        conversation_context=context,
        available_agents=[...]
    )
    result = await supervisor.execute_workflow(workflow_plan)
    return result
```

### Phase 2: Enhance Intent Detection for Agent Squad

**Current**: Intent detection picks ONE intent
**Needed**: Detect when query needs multiple agents

**Patterns to detect:**
- "I want to [X] and [Y]" → Multiple intents
- "[Informational query] then [Action]" → Sequential workflow
- Complex queries requiring multiple specialist agents

### Phase 3: Guest Chat → Agent Squad Bridge

**Architecture:**
```
Guest Chat Handler
  ↓
Sequential Intent Detector
  ↓ (if multiple intents detected)
Agent Squad SupervisorCoordinator
  ↓
Multi-Agent Workflow Execution
  ↓
Aggregated Response
```

## Implementation Plan

### Option A: Use Agent Squad for All Complex Queries (Recommended)

**Pros:**
- ✅ Leverages existing Agent Squad infrastructure
- ✅ Handles any complexity automatically
- ✅ Context preservation built-in
- ✅ Multi-agent coordination ready

**Cons:**
- ⚠️ LLM costs for workflow planning
- ⚠️ Slightly higher latency
- ⚠️ Requires Agent Squad to be enabled

**Implementation:**
1. Detect sequential/complex queries in guest chat
2. Route to SupervisorCoordinator
3. Let SupervisorCoordinator plan and execute workflow
4. Return aggregated response

### Option B: Hybrid Approach

**Simple queries** (single intent) → Existing guest handlers
**Complex queries** (multiple intents) → Agent Squad SupervisorCoordinator

**Implementation:**
1. Detect query complexity
2. Route simple → guest handlers
3. Route complex → Agent Squad
4. Unified response formatting

## Code Changes Required

### 1. Add Agent Squad Integration to Guest Chat

```python
# src/app/application/guest/commands/send_guest_message.py

from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator
from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator

class SendGuestMessage:
    def __init__(
        self,
        # ... existing dependencies ...
        supervisor_coordinator: SupervisorCoordinator | None = None,
        agent_orchestrator: AgentOrchestrator | None = None,
    ):
        self._supervisor_coordinator = supervisor_coordinator
        self._agent_orchestrator = agent_orchestrator
    
    async def execute(self, ...):
        # ... existing code ...
        
        # Check if query needs Agent Squad
        if self._needs_agent_squad(content, language):
            return await self._handle_with_agent_squad(
                content, language, context, conversation
            )
        
        # ... continue with existing flow ...
    
    def _needs_agent_squad(
        self, content: str, language: str
    ) -> bool:
        """Check if query needs Agent Squad coordination."""
        # Detect sequential intents
        sequential_intents = self._detect_sequential_intents(content, language)
        
        if len(sequential_intents) > 1:
            return True
        
        # Detect complex queries requiring multiple agents
        complex_patterns = [
            r"analyze.*and.*optimize",
            r"research.*then.*execute",
            r"assess.*risk.*and.*create",
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, content.lower()):
                return True
        
        return False
    
    async def _handle_with_agent_squad(
        self,
        content: str,
        language: str,
        context: list,
        conversation: GuestConversation,
    ) -> GuestMessageResult:
        """Handle complex query with Agent Squad SupervisorCoordinator."""
        if not self._supervisor_coordinator:
            # Fallback to single intent if Agent Squad not available
            return await self._handle_single_intent(...)
        
        # Create workflow plan
        workflow_plan = await self._supervisor_coordinator.create_workflow_plan(
            conversation_id=conversation.id,
            message=MessageContent(content),
            conversation_context=ConversationContext(...),
            available_agents=[...],  # Guest-accessible agents
        )
        
        # Execute workflow
        aggregated_response = await self._supervisor_coordinator.execute_workflow(
            conversation_id=conversation.id,
            workflow_plan=workflow_plan,
            conversation_context=ConversationContext(...),
        )
        
        # Format response
        agent_message = GuestMessage.create_assistant_message(
            conversation_id=conversation.id,
            content=aggregated_response,
            intent="COMPLEX_WORKFLOW",
            handler="agent_squad_supervisor",
            language=language,
        )
        
        # ... save and return ...
```

### 2. Configure Guest-Accessible Agents

```python
# Only allow read-only agents for guests
GUEST_ACCESSIBLE_AGENTS = [
    AgentType.CHAT,           # General chat
    AgentType.RESEARCH,        # Research queries
    AgentType.RISK_ANALYZER,   # Risk analysis
    AgentType.PORTFOLIO,       # Portfolio analysis (read-only)
    # No execution agents for guests
]
```

## Benefits of Using Agent Squad

✅ **Already Built**: SupervisorCoordinator exists and works
✅ **Handles Complexity**: Automatically breaks down complex queries
✅ **Context Preservation**: Built-in context management
✅ **Multi-Agent Coordination**: Handles dependencies automatically
✅ **Scalable**: Can handle any number of agents
✅ **LLM-Powered**: Natural language understanding for workflow planning

## Trade-offs

| Aspect | Agent Squad | Custom Sequential Handler |
|--------|-------------|---------------------------|
| **Development Time** | ⭐ Low (already exists) | ⭐⭐⭐ High (build from scratch) |
| **Complexity Handling** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good |
| **LLM Costs** | ⭐⭐ Medium | ⭐ Low |
| **Latency** | ⭐⭐ Medium (workflow planning) | ⭐⭐⭐ Fast |
| **Maintainability** | ⭐⭐⭐⭐ Good | ⭐⭐⭐ Medium |

## Recommendation

**Use Agent Squad SupervisorCoordinator** for complex/sequential queries because:
1. It already exists and works
2. Handles any complexity automatically
3. Better long-term scalability
4. Less code to maintain

**Implementation Priority:**
1. **Phase 1** (2-3 days): Add Agent Squad routing to guest chat
2. **Phase 2** (1-2 days): Configure guest-accessible agents
3. **Phase 3** (1 day): Test and refine

## Updated Architecture

```
Guest Chat Message
  ↓
Complexity Detector
  ├─ Simple Query → Guest Handlers (existing)
  └─ Complex Query → Agent Squad SupervisorCoordinator
       ↓
    SupervisorCoordinator
       ├─ Plan workflow (LLM)
       ├─ Execute agents sequentially
       └─ Aggregate results
       ↓
    Multi-Part Response
```

---

*Analysis updated based on Agent Squad capabilities*
*Date: 2026-01-19*
