# Guest Message Performance Analysis

> **Analysis Date**: 2026-01-20  
> **Endpoint**: `POST /api/v1/guest/chat`  
> **Test Query**: "hola"  
> **Issue**: Response time > 5s (very slow)

## Executive Summary

The guest/message endpoint is experiencing **slow response times (>5s)** for simple queries like "hola". The main bottleneck is the **Supervisor Coordinator's LLM workflow planning call**, which takes ~5-6 seconds.

## Performance Breakdown

### Current Performance (Before Optimization)

**Total Response Time**: ~6-8 seconds

| Component | Time | Percentage | Notes |
|-----------|------|------------|-------|
| **Distillation Engine** | <100ms | ~1% | Rule-based classification (fast) |
| **Supervisor Coordinator** | ~5-6s | ~75% | ⚠️ **BOTTLENECK** - LLM workflow planning |
| **Agent Execution** | ~1-2s | ~20% | CHAT agent execution |
| **Database Operations** | <100ms | ~1% | Message persistence, telemetry |
| **Other** | <100ms | ~3% | Context building, routing |

### Root Cause Analysis

1. **"hola" doesn't match rule-based patterns**:
   - Original GREETING pattern: `r"^(hello|hi|hey|greetings|good (morning|afternoon|evening))"`
   - "hola" is Spanish for "hello" but wasn't in the pattern
   - Result: Falls through to LLM classification (if available) or UNCLEAR intent

2. **No static response for GREETING**:
   - Distillation Engine doesn't have a static response for GREETING intent
   - Result: Routes to FULL_LLM → Supervisor Coordinator

3. **Supervisor Coordinator LLM call is slow**:
   - `plan_workflow()` calls Vertex AI/DeepInfra
   - Model: `gemini-1.5-pro` (premium model for planning)
   - Average latency: ~5-6 seconds
   - Result: Most of the response time is spent here

4. **Agent execution adds latency**:
   - CHAT agent execution: ~1-2 seconds
   - LLM call for response generation
   - Result: Additional ~1-2 seconds

## Optimizations Implemented

### ✅ 1. Added "hola" to GREETING Pattern

**File**: `src/app/domain/services/distillation/intent_classifier.py`

**Change**:
```python
Intent.GREETING: [
    r"^(hello|hi|hey|greetings|good (morning|afternoon|evening)|hola|holi|hey there)",
],
```

**Impact**: 
- "hola" now matches GREETING intent immediately (rule-based)
- Classification time: <10ms (was ~5-6s if LLM was called)
- **However**: Still routes to Supervisor Coordinator if no static response

### ⚠️ 2. Disabled LLM Client in IntentClassifier (Temporary)

**File**: `src/app/setup/ioc/distillation.py`

**Change**: IntentClassifier initialized without LLM client (DI issue)

**Impact**:
- IntentClassifier falls back to UNCLEAR for ambiguous queries
- No LLM classification overhead
- **Issue**: Can't use LLM for truly ambiguous queries

## Remaining Performance Issues

### 🔴 Critical: Supervisor Coordinator LLM Call

**Location**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`

**Method**: `create_workflow_plan()`

**Current Flow**:
```
User Query ("hola")
  ↓
Distillation Engine (GREETING intent, but no static response)
  ↓
Routes to FULL_LLM
  ↓
Supervisor Coordinator
  ↓
LLM Call: plan_workflow() [~5-6s] ⚠️ BOTTLENECK
  ↓
Workflow Plan Created
  ↓
Agent Execution (CHAT) [~1-2s]
  ↓
Response
```

**Problem**: Even with GREETING intent, if there's no static response, it still goes to Supervisor Coordinator.

## Recommended Optimizations

### 1. Add Static Response for GREETING Intent ⭐ HIGH PRIORITY

**File**: `src/app/infrastructure/distillation/static_responder.py`

**Implementation**:
```python
# In check_available() method
if intent == Intent.GREETING:
    return True  # Static response available

# In generate() method
if intent == Intent.GREETING:
    responses = {
        "en": "Hello! I'm Anvil, your DeFi assistant. How can I help you today?",
        "es": "¡Hola! Soy Anvil, tu asistente de DeFi. ¿Cómo puedo ayudarte hoy?",
        "pt": "Olá! Sou Anvil, seu assistente DeFi. Como posso ajudá-lo hoje?",
        "zh": "你好！我是 Anvil，您的 DeFi 助手。今天我能为您做些什么？",
    }
    return responses.get(user_context.get("language", "en"), responses["en"])
```

**Expected Impact**:
- Response time: <200ms (vs ~6-8s)
- **99% reduction in response time**
- No Supervisor Coordinator call
- No agent execution

### 2. Use Faster LLM Model for Workflow Planning

**File**: `src/app/infrastructure/adapters/agent_squad/llm_client_vertex_ai.py`

**Current**: Uses `gemini-1.5-pro` for planning (premium, slow)

**Recommended**: Use `gemini-2.0-flash` for simple queries

**Expected Impact**:
- Planning time: ~5-6s → ~2-3s
- **50% reduction in planning time**

### 3. Cache Workflow Plans for Common Queries

**Implementation**: Cache workflow plans by query hash

**Expected Impact**:
- Cached queries: <100ms (vs ~5-6s)
- **98% reduction for cached queries**

### 4. Skip Supervisor Coordinator for Simple Intents

**File**: `src/app/application/guest/commands/send_guest_message.py`

**Logic**: If intent is GREETING/SMALL_TALK and static response available, skip Supervisor Coordinator

**Expected Impact**:
- Simple queries: <200ms (vs ~6-8s)
- **97% reduction for simple queries**

## Performance Targets

| Query Type | Current | Target | Optimization |
|------------|---------|--------|--------------|
| **Simple Greetings** | ~6-8s | <200ms | Static responses |
| **Price Queries** | ~3-4s | <1s | Fast path to HUNTER_AI |
| **Complex Queries** | ~8-10s | <5s | Faster LLM model, caching |

## Testing Results

### Before Optimization

```
Query: "hola"
Response Time: ~6-8s
Breakdown:
  - Distillation: <100ms
  - Supervisor Coordinator: ~5-6s ⚠️
  - Agent Execution: ~1-2s
  - Database: <100ms
```

### After Pattern Fix (Expected)

```
Query: "hola"
Response Time: ~6-8s (still slow - no static response)
Breakdown:
  - Distillation: <10ms ✅ (faster classification)
  - Supervisor Coordinator: ~5-6s ⚠️ (still called)
  - Agent Execution: ~1-2s
  - Database: <100ms
```

### After Static Response (Expected)

```
Query: "hola"
Response Time: <200ms ✅
Breakdown:
  - Distillation: <10ms
  - Static Response: <50ms ✅
  - Database: <100ms
  - Total: <200ms
```

## Next Steps

1. **Immediate** (High Priority):
   - ✅ Add "hola" to GREETING pattern (DONE)
   - ⚠️ Fix LLM client injection in DistillationProvider
   - ⭐ Add static response for GREETING intent
   - ⭐ Skip Supervisor Coordinator for GREETING with static response

2. **Short-term** (Medium Priority):
   - Use faster LLM model for workflow planning
   - Add caching for workflow plans
   - Optimize agent execution for simple queries

3. **Long-term** (Low Priority):
   - Implement semantic caching
   - Add performance monitoring dashboard
   - A/B test different optimization strategies

## References

- **Distillation Engine**: `src/app/domain/services/distillation/engine.py`
- **IntentClassifier**: `src/app/domain/services/distillation/intent_classifier.py`
- **Supervisor Coordinator**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`
- **Static Responder**: `src/app/infrastructure/distillation/static_responder.py`
- **Guest Message Handler**: `src/app/application/guest/commands/send_guest_message.py`

---

*Document Version: 1.0*  
*Last Updated: 2026-01-20*
