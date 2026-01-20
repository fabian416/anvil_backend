# LLM-Based Generic Intent Detection Proposal

## Problem Statement

Current intent detection uses **manual rule-based patterns** (`KeywordIntentDetectionAdapter`) with:
- ❌ Hardcoded keyword lists (1000+ lines of patterns)
- ❌ Brittle pattern matching (misses variations)
- ❌ No context understanding
- ❌ Can't handle compound/sequential intents
- ❌ Requires constant maintenance for new intents
- ❌ Limited language support

**Example Failure:**
- Query: "what's the price of btc, and what swaps you can make?"
- Current: Detects only "swap" intent, misses "price" query
- Result: Returns swap info but not BTC price

## Solution: LLM-Based Generic Intent Detection

### Architecture Overview

```
User Query
  ↓
LLM Intent Classifier (Agent Squad)
  ├─ Single Intent → Route to Handler
  ├─ Multiple Intents → SupervisorCoordinator
  └─ Complex Query → Agno Agent Router
  ↓
Agent Execution
```

### Proposed Implementation

#### 1. **LLM Intent Detection Adapter** (New)

**File**: `src/app/infrastructure/adapters/chat/llm_intent_detection_adapter.py`

**Purpose**: Replace keyword-based detection with LLM-based classification

**Features**:
- Uses Agent Squad's `IntentClassifier` (already LLM-based)
- No hardcoded patterns
- Understands context and variations
- Detects compound/sequential intents
- Multi-language support (via LLM)

**Implementation**:
```python
class LLMIntentDetectionAdapter(IntentDetectionPort):
    """
    LLM-based intent detection using Agent Squad IntentClassifier.
    
    Advantages:
    - Generic: No hardcoded patterns
    - Context-aware: Understands conversation history
    - Multi-intent: Detects compound queries
    - Language-agnostic: Works in any language
    - Extensible: New intents don't require code changes
    """
    
    def __init__(
        self,
        intent_classifier: IntentClassifier,  # From Agent Squad
        agno_router: AgentRouter | None = None,  # Optional Agno integration
    ):
        self._intent_classifier = intent_classifier
        self._agno_router = agno_router
    
    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Detect intent using LLM classification.
        
        Flow:
        1. Check for compound/sequential intents
        2. If single intent → Use IntentClassifier
        3. If multiple intents → Use SupervisorCoordinator
        4. If complex → Use Agno for reasoning
        """
        # Build conversation context
        context = self._build_context(request)
        
        # Check for compound intents (multiple queries in one message)
        compound_intents = await self._detect_compound_intents(
            request.message, context
        )
        
        if len(compound_intents) > 1:
            # Multiple intents detected → Use SupervisorCoordinator
            return await self._handle_compound_intents(
                compound_intents, request, context
            )
        
        # Single intent → Use IntentClassifier
        classification = await self._intent_classifier.classify(
            message=MessageContent(request.message),
            conversation_context=context,
        )
        
        # Map Agent Squad intent to ChatIntent
        chat_intent = self._map_to_chat_intent(classification.intent)
        
        # Extract entities using LLM (if needed)
        entities = await self._extract_entities_llm(
            request.message, chat_intent, context
        )
        
        return IntentDetectionResult(
            intent=chat_intent,
            confidence=classification.confidence,
            entities=entities,
            reasoning=classification.reasoning,
            suggested_agent=classification.agent_type.value if hasattr(classification, 'agent_type') else None,
        )
    
    async def _detect_compound_intents(
        self,
        message: str,
        context: ConversationContext,
    ) -> list[str]:
        """
        Detect if query contains multiple intents.
        
        Uses LLM to identify compound queries like:
        - "what's the price of btc, and what swaps you can make?"
        - "analyze risk and optimize portfolio"
        """
        prompt = f"""
        Analyze this user query and identify ALL intents present.
        
        Query: {message}
        
        Respond with JSON array of intents:
        ["intent1", "intent2", ...]
        
        Examples:
        - "what's the price of btc, and what swaps you can make?" 
          → ["price_query", "swap_query"]
        - "analyze risk and optimize portfolio"
          → ["risk_analysis", "portfolio_optimization"]
        """
        
        # Use LLM to detect compound intents
        response = await self._intent_classifier._llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini",
        )
        
        # Parse response
        intents = self._parse_intent_list(response)
        return intents
```

#### 2. **Agno Integration for Complex Reasoning** (Optional Enhancement)

**Purpose**: Use Agno for sophisticated intent reasoning when needed

**Use Cases**:
- Ambiguous queries requiring deep reasoning
- Multi-step intent planning
- Context-heavy queries

**Implementation**:
```python
async def _handle_complex_intent_with_agno(
    self,
    message: str,
    context: ConversationContext,
) -> IntentDetectionResult:
    """
    Use Agno agent router for complex intent reasoning.
    
    Agno provides:
    - Advanced reasoning capabilities
    - Tool access for data validation
    - Multi-step planning
    """
    if not self._agno_router:
        # Fallback to standard LLM classification
        return await self._standard_classification(message, context)
    
    # Use Agno to reason about intent
    agno_response = await self._agno_router.route(
        message=message,
        context=context,
        task="intent_classification",
    )
    
    # Parse Agno response to extract intent
    intent = self._parse_agno_intent(agno_response)
    
    return IntentDetectionResult(
        intent=intent,
        confidence=0.9,  # High confidence for Agno reasoning
        entities={},
        reasoning=agno_response.reasoning,
    )
```

#### 3. **Hybrid Adapter** (Fallback Strategy)

**File**: `src/app/infrastructure/adapters/chat/hybrid_intent_detection_adapter.py`

**Purpose**: Combine LLM with keyword fallback for reliability

**Strategy**:
1. Try LLM classification first
2. If LLM fails/unavailable → Fallback to keyword matching
3. If confidence low → Use keyword validation

```python
class HybridIntentDetectionAdapter(IntentDetectionPort):
    """
    Hybrid intent detection: LLM primary, keyword fallback.
    
    Provides:
    - Best accuracy (LLM)
    - Reliability (keyword fallback)
    - Cost optimization (keyword for simple queries)
    """
    
    def __init__(
        self,
        llm_adapter: LLMIntentDetectionAdapter,
        keyword_adapter: KeywordIntentDetectionAdapter,
        llm_threshold: float = 0.85,  # Use LLM if confidence >= threshold
    ):
        self._llm_adapter = llm_adapter
        self._keyword_adapter = keyword_adapter
        self._llm_threshold = llm_threshold
    
    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        # Try LLM first
        try:
            llm_result = await self._llm_adapter.detect_intent(request)
            
            # If high confidence, use LLM result
            if llm_result.confidence >= self._llm_threshold:
                return llm_result
            
            # Low confidence → Validate with keyword
            keyword_result = await self._keyword_adapter.detect_intent(request)
            
            # If both agree, use LLM (more nuanced)
            if llm_result.intent == keyword_result.intent:
                return llm_result
            
            # Disagreement → Use keyword (more reliable for simple queries)
            return keyword_result
            
        except Exception:
            # LLM failed → Fallback to keyword
            return await self._keyword_adapter.detect_intent(request)
```

### Integration Points

#### 1. **Guest Chat Integration**

**File**: `src/app/application/guest/commands/send_guest_message.py`

**Changes**:
- Replace `KeywordIntentDetectionAdapter` with `LLMIntentDetectionAdapter`
- Remove manual pattern detection (`_needs_agent_squad`, `_detect_sequential_intents`)
- Let LLM handle all intent detection

```python
# Before (manual patterns)
if self._needs_agent_squad(content, language):
    # Manual pattern matching...

# After (LLM-based)
intent_result = await self._intent_detector.detect_intent(content)
if intent_result.intent == ChatIntent.COMPLEX_WORKFLOW:
    # LLM detected complex workflow
    return await self._handle_with_agent_squad(...)
```

#### 2. **Agent Squad Integration**

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

**Enhancements**:
- Already LLM-based ✅
- Add compound intent detection
- Add entity extraction via LLM
- Improve prompt engineering

#### 3. **Agno Integration** (Optional)

**File**: `src/app/infrastructure/adapters/chat/agno_intent_adapter.py`

**Purpose**: Use Agno for complex reasoning when standard LLM isn't sufficient

**When to Use**:
- Ambiguous queries
- Multi-step planning required
- Need tool access for validation

### Benefits

✅ **Generic**: No hardcoded patterns, works for any intent
✅ **Context-Aware**: Understands conversation history
✅ **Multi-Intent**: Detects compound/sequential queries automatically
✅ **Language-Agnostic**: Works in any language (via LLM)
✅ **Extensible**: New intents don't require code changes
✅ **Accurate**: LLM understands variations and nuances
✅ **Maintainable**: Single source of truth (LLM prompts)

### Migration Strategy

#### Phase 1: Add LLM Adapter (Non-Breaking)
1. Create `LLMIntentDetectionAdapter`
2. Integrate with Agent Squad's `IntentClassifier`
3. Test alongside keyword adapter
4. **No breaking changes** - keyword adapter still default

#### Phase 2: Hybrid Mode (Gradual Rollout)
1. Create `HybridIntentDetectionAdapter`
2. Use LLM for complex queries, keyword for simple
3. Monitor accuracy and costs
4. Gradually increase LLM usage

#### Phase 3: Full LLM (Production)
1. Make LLM adapter default
2. Keep keyword adapter as fallback
3. Remove manual pattern detection code
4. Optimize LLM prompts based on usage

#### Phase 4: Agno Integration (Advanced)
1. Add Agno for complex reasoning
2. Use for ambiguous queries
3. Leverage tool access for validation

### Cost Considerations

**LLM Costs** (per request):
- `gpt-4o-mini`: ~$0.15/1M input tokens, $0.60/1M output tokens
- Average query: ~100 tokens input, ~50 tokens output
- Cost per query: ~$0.00003 (very low)

**Optimization Strategies**:
1. **Caching**: Cache intent classifications for similar queries
2. **Batch Processing**: Process multiple queries together
3. **Model Selection**: Use cheaper models for simple queries
4. **Hybrid Approach**: Use keyword for high-confidence patterns

### Example: Compound Intent Detection

**Query**: "what's the price of btc, and what swaps you can make?"

**LLM Analysis**:
```json
{
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
  "is_compound": true,
  "recommended_approach": "supervisor_coordinator"
}
```

**Action**: Route to SupervisorCoordinator
- Task 1: HUNTER_AI agent → Get BTC price
- Task 2: CHAT agent → List available swaps
- Aggregate results

### Implementation Plan

#### Step 1: Create LLM Adapter (2-3 hours)
- [ ] Create `LLMIntentDetectionAdapter`
- [ ] Integrate with Agent Squad's `IntentClassifier`
- [ ] Add compound intent detection
- [ ] Add entity extraction

#### Step 2: Update Guest Chat (1-2 hours)
- [ ] Replace keyword adapter with LLM adapter
- [ ] Remove manual pattern detection
- [ ] Update DI configuration
- [ ] Test with various queries

#### Step 3: Add Hybrid Mode (1 hour)
- [ ] Create `HybridIntentDetectionAdapter`
- [ ] Implement fallback strategy
- [ ] Add configuration for LLM threshold

#### Step 4: Testing & Optimization (2-3 hours)
- [ ] Test with real queries
- [ ] Measure accuracy vs keyword adapter
- [ ] Optimize LLM prompts
- [ ] Add caching if needed

#### Step 5: Agno Integration (Optional, 2-3 hours)
- [ ] Create Agno intent adapter
- [ ] Integrate for complex queries
- [ ] Test reasoning capabilities

### Files to Create/Modify

**New Files**:
- `src/app/infrastructure/adapters/chat/llm_intent_detection_adapter.py`
- `src/app/infrastructure/adapters/chat/hybrid_intent_detection_adapter.py`
- `src/app/infrastructure/adapters/chat/agno_intent_adapter.py` (optional)

**Modified Files**:
- `src/app/application/guest/commands/send_guest_message.py` (remove manual patterns)
- `src/app/setup/ioc/guest.py` (update DI)
- `src/app/domain/services/agent_squad/intent_classifier.py` (enhance prompts)

### Success Metrics

- ✅ **Accuracy**: >90% intent detection accuracy
- ✅ **Compound Intent Detection**: >85% accuracy for multi-intent queries
- ✅ **Cost**: <$0.0001 per query
- ✅ **Latency**: <500ms for intent classification
- ✅ **Language Support**: Works in en, es, pt, zh without changes

---

**Next Steps**: Should I implement the LLM-based intent detection adapter?
