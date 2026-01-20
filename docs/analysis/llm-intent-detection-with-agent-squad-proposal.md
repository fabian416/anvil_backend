# LLM-Based Generic Intent Detection with Agent Squad & Agno Integration

## Current State Analysis

### Existing Implementation

✅ **LLM Intent Detection Adapter** (`llm_intent_detection_adapter.py`)
- Uses generic `LLMGateway` with hardcoded prompts
- Has manual intent-to-handler mapping
- Doesn't integrate with Agent Squad's `IntentClassifier`
- Doesn't detect compound/sequential intents
- Not used in guest chat (keyword adapter is default)

✅ **Agent Squad IntentClassifier** (`intent_classifier.py`)
- Already LLM-based using `LLMClientGateway`
- Has sophisticated intent classification
- Maps intents to agents automatically
- **Not currently used for guest chat intent detection**

✅ **Agno Agent Router** (`agent_router.py`)
- Has intelligent routing logic
- Can orchestrate multiple agents
- **Not integrated with intent detection**

### Problem

**Guest chat uses keyword-based detection** which:
- ❌ Misses compound intents ("what's the price of btc, and what swaps you can make?")
- ❌ Requires manual pattern maintenance
- ❌ Doesn't understand context
- ❌ Limited language support

## Proposed Solution

### Architecture: Unified LLM Intent Detection

```
User Query
  ↓
Agent Squad IntentClassifier (LLM)
  ├─ Single Intent → Route to Handler
  ├─ Multiple Intents → SupervisorCoordinator
  └─ Complex/Ambiguous → Agno Router
  ↓
Agent Execution
```

### Implementation Plan

#### 1. **Enhanced LLM Adapter with Agent Squad Integration**

**File**: `src/app/infrastructure/adapters/chat/agent_squad_intent_adapter.py` (NEW)

**Purpose**: Bridge between chat intent detection and Agent Squad's IntentClassifier

```python
class AgentSquadIntentAdapter(IntentDetectionPort):
    """
    LLM-based intent detection using Agent Squad's IntentClassifier.
    
    Advantages:
    - Uses Agent Squad's sophisticated classification
    - Automatic agent mapping
    - Context-aware (conversation history)
    - Detects compound/sequential intents
    - No manual patterns required
    """
    
    def __init__(
        self,
        intent_classifier: IntentClassifier,  # From Agent Squad
        supervisor_coordinator: SupervisorCoordinator | None = None,
        agno_router: AgentRouter | None = None,
    ):
        self._intent_classifier = intent_classifier
        self._supervisor = supervisor_coordinator
        self._agno_router = agno_router
    
    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Detect intent using Agent Squad's IntentClassifier.
        
        Flow:
        1. Check for compound intents (multiple queries)
        2. If compound → Return COMPLEX_WORKFLOW intent
        3. If single → Use IntentClassifier
        4. If ambiguous → Use Agno for reasoning (optional)
        """
        # Build conversation context
        context = self._build_agent_squad_context(request)
        
        # Check for compound intents first
        is_compound = await self._detect_compound_intent(
            request.message, context
        )
        
        if is_compound:
            return IntentDetectionResult(
                intent=ChatIntent.COMPLEX_WORKFLOW,
                confidence=0.95,
                entities={},
                reasoning="Detected multiple intents in query",
                handler="agent_orchestrator",
            )
        
        # Single intent → Use IntentClassifier
        classification = await self._intent_classifier.classify(
            message=MessageContent(request.message),
            conversation_context=context,
        )
        
        # Map Agent Squad intent to ChatIntent
        chat_intent = self._map_to_chat_intent(classification.intent)
        
        # Extract entities
        entities = await self._extract_entities_llm(
            request.message, chat_intent, context
        )
        
        return IntentDetectionResult(
            intent=chat_intent,
            confidence=classification.confidence,
            entities=entities,
            reasoning=classification.reasoning,
            suggested_agent=classification.agent_type.value,
        )
    
    async def _detect_compound_intent(
        self,
        message: str,
        context: ConversationContext,
    ) -> bool:
        """
        Detect if query contains multiple intents using LLM.
        
        Examples:
        - "what's the price of btc, and what swaps you can make?"
        - "analyze risk and optimize portfolio"
        """
        prompt = f"""
        Analyze this query and determine if it contains MULTIPLE distinct intents.
        
        Query: {message}
        
        Respond with JSON:
        {{
            "is_compound": true/false,
            "intents": ["intent1", "intent2", ...],
            "reasoning": "explanation"
        }}
        
        Examples:
        - "what's the price of btc, and what swaps you can make?"
          → {{"is_compound": true, "intents": ["price_query", "swap_query"]}}
        - "swap ETH to USDC"
          → {{"is_compound": false, "intents": ["swap"]}}
        """
        
        # Use IntentClassifier's LLM client
        response = await self._intent_classifier._llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini",
        )
        
        result = json.loads(response)
        return result.get("is_compound", False)
```

#### 2. **Update Guest Chat to Use Agent Squad Intent Detection**

**File**: `src/app/setup/ioc/guest.py`

**Changes**:
- Replace `KeywordIntentDetectionAdapter` with `AgentSquadIntentAdapter`
- Inject `IntentClassifier` from Agent Squad
- Remove manual pattern detection code

```python
@provide(scope=Scope.REQUEST)
def provide_guest_intent_detector(
    self,
    intent_classifier: IntentClassifier,  # From Agent Squad
    supervisor_coordinator: SupervisorCoordinator | None = None,
) -> IntentDetectorService:
    """
    Provide LLM-based intent detector for guest users.
    
    Uses Agent Squad's IntentClassifier for:
    - Generic intent detection (no manual patterns)
    - Context-aware classification
    - Compound intent detection
    - Automatic agent mapping
    """
    from app.infrastructure.adapters.chat.agent_squad_intent_adapter import (
        AgentSquadIntentAdapter,
    )
    
    adapter = AgentSquadIntentAdapter(
        intent_classifier=intent_classifier,
        supervisor_coordinator=supervisor_coordinator,
    )
    
    return IntentDetectorService(intent_port=adapter)
```

#### 3. **Remove Manual Pattern Detection**

**File**: `src/app/application/guest/commands/send_guest_message.py`

**Remove**:
- `_needs_agent_squad()` method (LLM will detect compound intents)
- `_detect_sequential_intents()` method
- `_classify_part_intent()` method
- Manual pattern matching in `_needs_agent_squad()`

**Simplify**:
```python
# Before (manual patterns)
if self._needs_agent_squad(content, language):
    return await self._handle_with_agent_squad(...)

# After (LLM-based)
intent_result = await self._intent_detector.detect_intent(
    message=content,
    conversation_history=context,
)

if intent_result.intent == ChatIntent.COMPLEX_WORKFLOW:
    # LLM detected compound intent
    return await self._handle_with_agent_squad(...)
```

#### 4. **Agno Integration for Complex Reasoning** (Optional)

**File**: `src/app/infrastructure/adapters/chat/agno_intent_adapter.py` (NEW)

**Purpose**: Use Agno for ambiguous/complex queries requiring deep reasoning

```python
class AgnoIntentAdapter(IntentDetectionPort):
    """
    Intent detection using Agno agent router for complex reasoning.
    
    Use cases:
    - Ambiguous queries requiring tool access
    - Multi-step intent planning
    - Context-heavy queries
    """
    
    def __init__(self, agno_router: AgentRouter):
        self._agno_router = agno_router
    
    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Use Agno to reason about intent with tool access.
        """
        # Use Agno to analyze query
        agno_response = await self._agno_router.route(
            message=request.message,
            context=request.user_context,
            task="intent_classification",
        )
        
        # Parse Agno response
        intent = self._parse_agno_intent(agno_response)
        
        return IntentDetectionResult(
            intent=intent,
            confidence=0.9,
            entities={},
            reasoning=agno_response.reasoning,
        )
```

### Benefits

✅ **Generic**: No hardcoded patterns, works for any intent
✅ **Context-Aware**: Understands conversation history
✅ **Compound Intent Detection**: Automatically detects multi-intent queries
✅ **Agent Integration**: Uses Agent Squad's existing infrastructure
✅ **Language-Agnostic**: Works in any language (via LLM)
✅ **Maintainable**: Single source of truth (LLM prompts in IntentClassifier)
✅ **Extensible**: New intents don't require code changes

### Migration Strategy

#### Phase 1: Create Agent Squad Adapter (2-3 hours)
- [ ] Create `AgentSquadIntentAdapter`
- [ ] Integrate with `IntentClassifier`
- [ ] Add compound intent detection
- [ ] Test alongside keyword adapter

#### Phase 2: Update Guest Chat (1-2 hours)
- [ ] Update DI to use `AgentSquadIntentAdapter`
- [ ] Remove manual pattern detection methods
- [ ] Simplify `send_guest_message.py`
- [ ] Test with various queries

#### Phase 3: Testing & Validation (2-3 hours)
- [ ] Test compound intent detection
- [ ] Measure accuracy vs keyword adapter
- [ ] Optimize LLM prompts
- [ ] Add caching if needed

#### Phase 4: Agno Integration (Optional, 2-3 hours)
- [ ] Create Agno intent adapter
- [ ] Integrate for complex queries
- [ ] Test reasoning capabilities

### Example: Compound Intent Detection

**Query**: "what's the price of btc, and what swaps you can make?"

**LLM Analysis** (via Agent Squad IntentClassifier):
```json
{
  "is_compound": true,
  "intents": [
    {
      "intent": "price_query",
      "entity": "BTC",
      "confidence": 0.95
    },
    {
      "intent": "swap_query",
      "entity": null,
      "confidence": 0.92
    }
  ],
  "reasoning": "Query contains two distinct intents: price inquiry and swap inquiry"
}
```

**Action**: 
- Return `ChatIntent.COMPLEX_WORKFLOW`
- Route to `SupervisorCoordinator`
- Create workflow:
  - Task 1: HUNTER_AI → Get BTC price
  - Task 2: CHAT → List available swaps
- Aggregate results

### Cost & Performance

**LLM Costs**:
- `gpt-4o-mini`: ~$0.15/1M input, $0.60/1M output
- Average query: ~100 tokens input, ~50 tokens output
- **Cost per query: ~$0.00003** (negligible)

**Latency**:
- LLM classification: ~200-500ms
- Acceptable for user experience

**Optimization**:
- Cache intent classifications for similar queries
- Use cheaper models for simple queries
- Batch processing for multiple queries

### Files to Create/Modify

**New Files**:
- `src/app/infrastructure/adapters/chat/agent_squad_intent_adapter.py`
- `src/app/infrastructure/adapters/chat/agno_intent_adapter.py` (optional)

**Modified Files**:
- `src/app/setup/ioc/guest.py` (use Agent Squad adapter)
- `src/app/application/guest/commands/send_guest_message.py` (remove manual patterns)
- `src/app/domain/services/agent_squad/intent_classifier.py` (enhance prompts for compound intents)

### Success Metrics

- ✅ **Accuracy**: >90% intent detection accuracy
- ✅ **Compound Intent Detection**: >85% accuracy for multi-intent queries
- ✅ **Cost**: <$0.0001 per query
- ✅ **Latency**: <500ms for intent classification
- ✅ **Language Support**: Works in en, es, pt, zh without changes

---

**Next Steps**: Should I implement the Agent Squad intent adapter and integrate it into guest chat?
