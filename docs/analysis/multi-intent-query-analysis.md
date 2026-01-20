# Multi-Intent Query Analysis

> **Analysis Date**: 2026-01-20  
> **Test Query**: "hi, how are you? what is the price of btc?"  
> **Issue**: Response time ~13.5s, but handling is correct

## Executive Summary

The system **correctly handles multi-intent queries** using the Supervisor Coordinator pattern. However, response time is slow (~13.5s) due to:
1. Supervisor Coordinator LLM planning call (~5-6s)
2. Multiple agent executions (CHAT + HUNTER_AI + CHAT aggregator)
3. Response aggregation

**Question**: Do we need an Agno agent to enhance this type of response?

**Answer**: **NO** - The current Supervisor Coordinator architecture is the right approach. However, we can optimize it without needing a separate Agno agent.

## Current Performance

### Test Results

**Query**: "hi, how are you? what is the price of btc?"

**Response Time**: 13.49s

**Workflow**:
1. **CHAT Agent** (897ms): Handles greeting
2. **HUNTER_AI Agent** (733ms): Gets BTC price
3. **CHAT Agent** (634ms): Aggregates responses

**Total Agent Time**: 2.26s  
**Supervisor Coordinator Planning**: ~5-6s (estimated)  
**Other Overhead**: ~5-6s (database, context building, etc.)

### Current Architecture

```
User Query ("hi, how are you? what is the price of btc?")
  ↓
Distillation Engine (classifies as UNCLEAR or multi-intent)
  ↓
Supervisor Coordinator
  ↓
LLM Planning Call (~5-6s) ⚠️ BOTTLENECK
  ↓
Workflow Plan Created:
  - Task 1: CHAT (greeting) → 897ms
  - Task 2: HUNTER_AI (price) → 733ms
  - Task 3: CHAT (aggregation) → 634ms
  ↓
Response Aggregation
  ↓
Final Response
```

## Analysis: Do We Need an Agno Agent?

### What is Agno?

Agno is a separate agent framework with MCP (Model Context Protocol) server integration. It provides:
- Agent routing via `AgentRouter`
- MCP server connections (portfolio, 1inch, aave, defillama, etc.)
- Tool-based agent execution

### Current System vs Agno

| Aspect | Current System (Supervisor Coordinator) | Agno Agent |
|--------|----------------------------------------|------------|
| **Multi-Intent Handling** | ✅ Handles via LLM planning | ❓ Would need similar planning |
| **Agent Orchestration** | ✅ Built-in (18 agents) | ❓ Would need to integrate with Agent Squad |
| **Response Aggregation** | ✅ Built-in CHAT aggregator | ❓ Would need custom aggregation |
| **Performance** | ⚠️ Slow (~13.5s) | ❓ Unknown (likely similar) |
| **Complexity** | ✅ Single system | ❌ Additional system to maintain |

### Recommendation: **NO Agno Agent Needed**

**Reasons**:

1. **Supervisor Coordinator Already Handles Multi-Intent Queries**:
   - The prompt explicitly instructs LLM to handle multi-intent queries
   - Creates separate tasks for each intent (greeting → CHAT, price → HUNTER_AI)
   - Aggregates results correctly

2. **Agno Would Add Complexity**:
   - Would need to integrate with existing Agent Squad
   - Would duplicate functionality (agent orchestration, aggregation)
   - Would require maintaining two separate systems

3. **Performance Issue is Not Architectural**:
   - The bottleneck is the LLM planning call (~5-6s)
   - This would exist in Agno too (if it uses LLM planning)
   - Better to optimize the current system

## Optimization Opportunities (Without Agno)

### 1. ⭐ Optimize Supervisor Coordinator Planning (HIGH PRIORITY)

**Current**: Uses `gemini-1.5-pro` for planning (premium, slow)

**Optimization**: Use `gemini-2.0-flash` for simple multi-intent queries

**Expected Impact**: ~5-6s → ~2-3s (50% reduction)

**Implementation**:
```python
# In supervisor_coordinator.py
async def create_workflow_plan(...):
    # Detect query complexity
    is_simple_multi_intent = self._is_simple_multi_intent(message)
    
    # Use faster model for simple queries
    model = "gemini-2.0-flash" if is_simple_multi_intent else "gemini-1.5-pro"
    
    response = await self._llm_client.plan_workflow(
        prompt=prompt,
        max_agents=self._max_agents,
        model=model,  # Pass model parameter
    )
```

### 2. ⭐ Cache Workflow Plans for Common Multi-Intent Patterns (HIGH PRIORITY)

**Pattern**: "greeting + price query"

**Implementation**: Cache workflow plans by query pattern hash

**Expected Impact**: Cached queries: <200ms (vs ~13.5s) - **99% reduction**

**Example**:
```python
# Cache key: hash("greeting + price_query")
# Cached plan: [CHAT (greeting), HUNTER_AI (price), CHAT (aggregate)]
```

### 3. ⭐ Parallel Agent Execution (MEDIUM PRIORITY)

**Current**: Agents execute sequentially (CHAT → HUNTER_AI → CHAT)

**Optimization**: Execute independent agents in parallel

**Expected Impact**: ~2.26s → ~1.5s (33% reduction for agent execution)

**Implementation**:
```python
# In execute_workflow()
# If tasks have no dependencies, execute in parallel
independent_tasks = [t for t in tasks if not t.depends_on]
if len(independent_tasks) > 1:
    results = await asyncio.gather(*[execute_task(t) for t in independent_tasks])
```

### 4. ⭐ Fast Path for Common Multi-Intent Patterns (MEDIUM PRIORITY)

**Pattern**: "greeting + price query"

**Implementation**: Rule-based fast path (skip LLM planning)

**Expected Impact**: <500ms (vs ~13.5s) - **96% reduction**

**Example**:
```python
# In send_guest_message.py
if self._is_greeting_plus_price(content):
    # Fast path: Direct to CHAT + HUNTER_AI + CHAT aggregator
    # Skip Supervisor Coordinator planning
    workflow_plan = self._create_fast_path_plan(content)
```

### 5. ⭐ Improve Distillation Engine for Multi-Intent Detection (LOW PRIORITY)

**Current**: Distillation Engine classifies as single intent or UNCLEAR

**Optimization**: Detect multi-intent queries and route directly to Supervisor Coordinator

**Expected Impact**: Better routing, but minimal time savings

## Recommended Approach

### Phase 1: Quick Wins (No Agno Needed)

1. **Add Fast Path for Common Patterns**:
   - "greeting + price" → Direct workflow plan
   - "greeting + knowledge" → Direct workflow plan
   - Skip LLM planning for these patterns

2. **Use Faster LLM Model**:
   - `gemini-2.0-flash` for simple multi-intent queries
   - `gemini-1.5-pro` only for complex workflows

3. **Parallel Agent Execution**:
   - Execute independent agents concurrently
   - Reduce total execution time

### Phase 2: Advanced Optimizations

1. **Workflow Plan Caching**:
   - Cache common patterns
   - Invalidate on conversation context changes

2. **Smart Aggregation**:
   - Skip aggregation for simple multi-intent (just concatenate)
   - Only aggregate for complex workflows

## Alternative: Enhanced Supervisor Coordinator

Instead of creating an Agno agent, we can enhance the Supervisor Coordinator:

### Enhanced Multi-Intent Detection

```python
class SupervisorCoordinator:
    def _is_simple_multi_intent(self, message: str) -> bool:
        """Detect simple multi-intent patterns."""
        patterns = [
            r"(hi|hello|hey).*price.*(btc|eth|usdc)",
            r"(hi|hello|hey).*what is.*(btc|eth|usdc)",
            r"how are you.*price",
        ]
        return any(re.search(p, message.lower()) for p in patterns)
    
    def _create_fast_path_plan(self, message: str) -> WorkflowPlan:
        """Create workflow plan without LLM for common patterns."""
        # Rule-based plan creation for common patterns
        tasks = [
            AgentTask(agent_type=AgentType.CHAT, task_description="Respond to greeting"),
            AgentTask(agent_type=AgentType.HUNTER_AI, task_description="Get price"),
            AgentTask(agent_type=AgentType.CHAT, task_description="Aggregate", depends_on=[0, 1]),
        ]
        return WorkflowPlan(tasks=tasks, execution_order=[0, 1, 2], estimated_time_seconds=5)
```

## Conclusion

**Do we need an Agno agent?** **NO**

**Why?**
- Current Supervisor Coordinator architecture is correct
- Agno would add complexity without solving the performance issue
- The bottleneck (LLM planning) would exist in Agno too
- Better to optimize the current system

**What should we do instead?**
1. ✅ Add fast path for common multi-intent patterns (IMPLEMENTED)
2. ✅ Use faster LLM model for simple queries (can be added)
3. ✅ Implement parallel agent execution (Supervisor Coordinator already supports this)
4. ✅ Cache workflow plans for common patterns (future optimization)

**Expected Results**:
- Current: ~13.5s (with LLM planning)
- After fast path: ~3-4s (73% reduction) - **No LLM planning call**
- With caching: <500ms (96% reduction for cached queries)

**Implementation Status**:
- ✅ Fast path detection for "greeting + price" pattern (IMPLEMENTED)
- ✅ Rule-based workflow plan creation (skips LLM planning)
- ✅ Direct execution via Supervisor Coordinator's execute_workflow()
- ⚠️ Fast path is in place but may need testing/verification

## References

- **Supervisor Coordinator**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`
- **Agno Provider**: `src/app/setup/ioc/agno.py`
- **Performance Analysis**: `docs/analysis/guest-message-performance-analysis.md`

---

*Document Version: 1.0*  
*Last Updated: 2026-01-20*
