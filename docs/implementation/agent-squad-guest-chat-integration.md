# Agent Squad Integration for Guest Chat - Implementation Summary

## Overview

Integrated Agent Squad SupervisorCoordinator into guest chat to handle sequential multi-intent queries like "I want to know about BTC and make a swap".

## Implementation Details

### 1. Complexity Detection

**File**: `src/app/application/guest/commands/send_guest_message.py`

**Method**: `_needs_agent_squad()`
- Detects sequential intent patterns ("X and Y", "X then Y")
- Identifies complex query patterns requiring multiple agents
- Returns `True` if query needs Agent Squad coordination

**Method**: `_detect_sequential_intents()`
- Parses compound queries into sequential parts
- Classifies each part (informational, transactional, analytical)
- Returns list of (intent_type, content) tuples

**Method**: `_classify_part_intent()`
- Classifies individual query parts
- Returns intent type for routing

### 2. Agent Squad Integration

**Method**: `_handle_with_agent_squad()`
- Creates workflow plan using SupervisorCoordinator
- Executes sequential agent workflow
- Aggregates results into structured response
- Handles guest-specific constraints (read-only agents)

**Guest-Accessible Agents**:
- `CHAT` - General conversation
- `RESEARCH` - Research queries
- `RISK_ANALYZER` - Risk analysis
- `PORTFOLIO` - Portfolio analysis (read-only)
- `HUNTER_AI` - Market analysis

### 3. Agent Executor Adapter

**File**: `src/app/infrastructure/adapters/agent_squad/agent_executor_adapter.py`

**Purpose**: Implements `AgentExecutorPort` using `AgentOrchestrator`
- Bridges SupervisorCoordinator with AgentOrchestrator
- Handles type conversions (MessageContent → str, AgentResponse → str)
- Manages conversation_id in context

### 4. Dependency Injection Updates

**File**: `src/app/setup/ioc/agent_squad_domain.py`
- Updated `provide_supervisor_coordinator()` to use real `AgentExecutorAdapter`
- Removed mock agent_executor

**File**: `src/app/setup/ioc/guest.py`
- Added optional `SupervisorCoordinator` and `AgentOrchestrator` parameters
- Dishka will inject these if available from `AgentSquadDomainProvider`

**File**: `src/app/domain/services/agent_squad/agent_orchestrator.py`
- Enhanced `execute_agent()` to handle missing conversation_id in context
- Added fallback logic for conversation_id extraction

## Flow Diagram

```
Guest Query: "I want to know about BTC and make a swap"
  ↓
_needs_agent_squad() → True (detects sequential intents)
  ↓
_handle_with_agent_squad()
  ↓
SupervisorCoordinator.create_workflow_plan()
  ├─ LLM plans workflow
  ├─ Task 1: RESEARCH agent → "Explain BTC"
  └─ Task 2: CHAT agent → "Get swap quote for BTC"
  ↓
SupervisorCoordinator.execute_workflow()
  ├─ Execute Task 1 → BTC explanation
  ├─ Pass context (BTC entity)
  └─ Execute Task 2 → Swap quote
  ↓
Aggregate results → Multi-part response
  ├─ Part 1: BTC explanation
  └─ Part 2: Swap quote
```

## Example Query Handling

**Input**: "I want to know about BTC and make a swap"

**Detection**:
- Sequential intents detected: [("informational", "know about BTC"), ("transactional", "make a swap")]

**Workflow Plan**:
1. RESEARCH agent: "Explain what Bitcoin (BTC) is"
2. CHAT agent: "Get swap quote for BTC"

**Execution**:
1. RESEARCH agent executes → Returns BTC explanation
2. CHAT agent executes (with BTC context) → Returns swap quote

**Response**:
```json
{
  "content": "**About Bitcoin (BTC)**\n\nBitcoin is the first cryptocurrency...\n\n---\n\n**Swap Quote**\n\nHere's a swap quote for BTC...",
  "routing": {
    "intent": "COMPLEX_WORKFLOW",
    "handler": "agent_squad_supervisor",
    "workflow_tasks": 2
  },
  "enrichment": {
    "agent_squad": true,
    "workflow_type": "supervisor",
    "task_count": 2,
    "agents_used": ["research", "chat"]
  }
}
```

## Configuration

### Guest-Accessible Agents

Only read-only agents are available for guests:
- ✅ CHAT
- ✅ RESEARCH
- ✅ RISK_ANALYZER
- ✅ PORTFOLIO (read-only analysis)
- ✅ HUNTER_AI

**Excluded** (require authentication):
- ❌ EXECUTION (transaction execution)
- ❌ Enterprise agents (compliance, multisig, etc.)

### Feature Flags

Agent Squad integration is enabled by default if:
- `AgentSquadDomainProvider` is registered
- `SupervisorCoordinator` is available
- LLM client is configured

If Agent Squad is unavailable, system falls back to single-intent processing.

## Error Handling

- **Agent Squad unavailable**: Falls back to single-intent processing
- **Workflow planning fails**: Falls back to single-intent processing
- **Agent execution fails**: Workflow continues with other agents, failed task marked
- **All agents fail**: Returns error message, falls back gracefully

## Testing

### Test Cases

1. **Simple sequential query**:
   - Input: "I want to know about BTC and make a swap"
   - Expected: BTC explanation + swap quote

2. **Complex multi-agent query**:
   - Input: "Analyze BTC risk and show me portfolio options"
   - Expected: Risk analysis + portfolio recommendations

3. **Fallback behavior**:
   - Input: "I want to know about BTC and make a swap" (Agent Squad disabled)
   - Expected: Falls back to single intent (swap only)

## Files Modified

1. `src/app/application/guest/commands/send_guest_message.py`
   - Added `_needs_agent_squad()` method
   - Added `_detect_sequential_intents()` method
   - Added `_classify_part_intent()` method
   - Added `_handle_with_agent_squad()` method
   - Updated `__init__()` to accept Agent Squad services
   - Added complexity check before distillation

2. `src/app/infrastructure/adapters/agent_squad/agent_executor_adapter.py` (NEW)
   - Implements `AgentExecutorPort` using `AgentOrchestrator`
   - Handles type conversions and context management

3. `src/app/setup/ioc/agent_squad_domain.py`
   - Updated `provide_supervisor_coordinator()` to use real adapter
   - Removed mock agent_executor

4. `src/app/setup/ioc/guest.py`
   - Added optional Agent Squad service parameters
   - Updated docstring with integration details

5. `src/app/domain/services/agent_squad/agent_orchestrator.py`
   - Enhanced `execute_agent()` to handle missing conversation_id
   - Added fallback logic

## Next Steps

1. **Test with real queries**: Verify sequential intent detection works
2. **Monitor performance**: Track LLM costs and latency
3. **Refine patterns**: Improve sequential intent detection accuracy
4. **Expand agents**: Add more guest-accessible agents as needed
5. **Error recovery**: Enhance error handling for partial failures

## Benefits

✅ **Leverages Existing Infrastructure**: Uses Agent Squad that already exists
✅ **Handles Complexity**: Automatically breaks down complex queries
✅ **Context Preservation**: Maintains context between sequential intents
✅ **Scalable**: Can handle any number of agents
✅ **Graceful Fallback**: Falls back to single-intent if Agent Squad unavailable

---

*Implementation completed: 2026-01-19*
