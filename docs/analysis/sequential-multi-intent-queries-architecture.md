# Sequential Multi-Intent Queries Architecture - CTO Methodology Analysis

> **Problem**: Users want to ask compound queries like "I want to know about BTC and make a swap" that combine informational queries with transactional intents in a single message.

## Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 Assumption Questioning

**What is the actual requirement?**
- Users naturally combine informational queries with actions in conversational flow
- Example: "I want to know about BTC and make a swap" = [Informational Query] + [Transactional Intent]
- Users expect the system to:
  1. Answer the informational question first
  2. Then proceed with the transactional action
  3. Maintain context between both parts

**What unverified assumptions does the current approach make?**
- ❌ **Assumption**: Users only ask one thing at a time
  - **Reality**: Users naturally combine questions and actions
- ❌ **Assumption**: Intent detection should pick the "primary" intent
  - **Reality**: Multiple intents can coexist and should be handled sequentially
- ❌ **Assumption**: Informational queries are separate from transactional flows
  - **Reality**: Users often need information before taking action
- ❌ **Assumption**: Single response is sufficient
  - **Reality**: Compound queries need multi-part responses

**Which "obvious" constraints might be pseudo-constraints?**
- ⚠️ "One message = One intent" → Can be changed to "One message = Multiple intents"
- ⚠️ "Response must be atomic" → Can be structured as multi-part responses
- ⚠️ "Informational queries block transactions" → Can handle both sequentially
- ⚠️ "Guest users can't have complex flows" → Can support sequential multi-intent

### 1.2 Root Cause Identification

**Phenomena vs Essence:**
- **Phenomenon**: System only handles one intent per message
- **Essence**: Missing sequential multi-intent orchestration layer

**Causal Relationship Mapping:**
```
User Query: "I want to know about BTC and make a swap"
  ↓
Current Flow:
  1. Intent Detection → Picks ONE intent (likely SWAP, ignores informational)
  2. Handler Execution → Executes only SWAP
  3. Response → Only swap-related response
  ↓
Problem: Informational query is lost/ignored

Desired Flow:
  1. Intent Detection → Detects [INFORMATIONAL_QUERY, SWAP]
  2. Sequential Orchestration → 
     a. Execute informational query first
     b. Then execute swap with context
  3. Multi-Part Response → 
     a. Educational response about BTC
     b. Swap initiation/quote
```

**Mathematical/Algorithmic Foundation:**
- Current: `f(message) → single_intent → single_response`
- Needed: `f(message) → [intent₁, intent₂, ...] → [response₁, response₂, ...]`
- Orchestration: `orchestrate(intents) → execution_order → sequential_execution`

**System Invariants:**
- Guest users have rate limits (20/hour, 50/day)
- Guest users cannot execute transactions (but can get quotes)
- Responses must be helpful and contextual

**Design Degrees of Freedom:**
- ✅ Can detect multiple intents in one message
- ✅ Can orchestrate sequential execution
- ✅ Can structure multi-part responses
- ✅ Can maintain context between intents

**Hard vs Soft Constraints:**
- **Hard**: Guest users cannot execute transactions
- **Hard**: Rate limits must be enforced
- **Soft**: "One intent per message" → Can be changed
- **Soft**: "Atomic responses" → Can be structured

---

## Phase 2: Solution Generation & Trade-off Analysis

### 2.1 Solution Divergence

**Solution A: Sequential Intent Parser (Incremental)**
- Parse message into sequential parts using conjunctions ("and", "then", "also")
- Process each part independently in sequence
- Combine responses into structured multi-part response
- **Pros**: Simple, incremental, works with existing handlers
- **Cons**: May miss implicit connections, requires good parsing

**Solution B: Multi-Intent Detection + Sequential Orchestrator (Recommended)**
- Enhance existing multi-intent detection to recognize sequential patterns
- Create sequential orchestrator that executes intents in order
- Maintain context between executions
- Structure responses as conversation flow
- **Pros**: Comprehensive, handles complex cases, maintains context
- **Cons**: More complex, requires orchestration layer

**Solution C: LLM-Based Intent Decomposition (Disruptive)**
- Use LLM to decompose compound queries into sequential intents
- LLM determines execution order and dependencies
- Execute based on LLM's plan
- **Pros**: Handles any complexity, natural language understanding
- **Cons**: LLM costs, latency, less deterministic

**Solution D: No Change (Status Quo)**
- Keep current single-intent approach
- Users must split queries into separate messages
- **Pros**: No development cost
- **Cons**: Poor UX, user frustration, feels unnatural

### 2.2 Multi-dimensional Trade-off Matrix

| Solution | Technical Benefits | Implementation Cost | Risk Assessment | UX Impact | Maintainability |
|----------|-------------------|---------------------|-----------------|-----------|-----------------|
| **A: Sequential Parser** | ⭐⭐⭐ Simple, fast | ⭐⭐ Medium | ⭐⭐ Medium (parsing edge cases) | ⭐⭐⭐ Good | ⭐⭐⭐ Good |
| **B: Multi-Intent Orchestrator** | ⭐⭐⭐⭐⭐ Comprehensive | ⭐⭐⭐ Medium-High | ⭐⭐ Low-Medium | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Good |
| **C: LLM Decomposition** | ⭐⭐⭐⭐⭐ Handles any complexity | ⭐⭐⭐⭐ High | ⭐⭐⭐ Medium (costs, latency) | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐ Medium |
| **D: No Change** | ⭐ None | ⭐ None | ⭐⭐⭐ High (churn) | ⭐ Poor | ⭐⭐⭐ Good |

### 2.3 Constraint Priority Framework

**Performance Efficiency vs Code Maintainability:**
- Solution B balances both: efficient sequential execution, maintainable orchestration

**Development Speed vs Architecture Scalability:**
- Solution B: Start with sequential orchestrator (fast), enhance with LLM later (scalable)

**Feature Completeness vs Implementation Simplicity:**
- Solution B: Simple sequential execution first, complex dependencies later

**System Security vs Usage Convenience:**
- All solutions maintain security (no transaction execution for guests)
- Solution B enhances convenience without compromising security

---

## Phase 3: Risk Assessment & Validation Design

### 3.1 Cognitive Limitation Analysis

**This analysis may overlook factors such as:**
- User intent ambiguity (when is "and" sequential vs parallel?)
- Context preservation between sequential intents
- Response formatting for multi-part responses
- Error handling when one intent fails

**The solution assumes key premises like:**
- Sequential intents can be reliably detected
- Context can be maintained between executions
- Multi-part responses are acceptable UX
- Handlers can work with shared context

**Areas requiring further validation include:**
- Intent detection accuracy for compound queries
- Context preservation mechanisms
- Response formatting user acceptance
- Performance impact of sequential execution

### 3.2 Technical Debt Assessment

**Rapid Implementation Compromises:**
- If implementing Solution B quickly:
  - Start with simple sequential execution (no dependencies)
  - Add dependency resolution later
  - May create temporary inconsistencies

**Requirement Changes Impact:**
- If users want parallel execution for some intents:
  - Need to enhance orchestrator with parallel support
  - May need to restructure execution model

**Long-term Maintenance Costs:**
- Intent detection: Requires continuous refinement
- Orchestration logic: May become complex with many intent types
- Context management: Requires careful state handling

### 3.3 Validation & Testing Strategy

**Measurable Success/Failure Criteria:**
- ✅ "I want to know about BTC and make a swap" returns:
  1. Educational response about BTC
  2. Swap quote/initiation
- ✅ Response time < 5 seconds for compound queries
- ✅ Context is maintained between intents
- ✅ User satisfaction score > 4/5 for compound queries

**Validation Experiments:**
1. **Unit Tests**: Test sequential intent detection
2. **Integration Tests**: Test sequential execution flow
3. **User Tests**: A/B test single vs multi-intent responses
4. **Performance Tests**: Measure sequential execution overhead

**Error Detection & Rollback:**
- Monitor intent detection accuracy
- Fallback to single-intent if multi-intent fails
- Alert on high sequential execution times
- Track context preservation success rate

---

## Recommended Implementation Plan

### Phase 1: Sequential Intent Detection (Quick Win)
1. Enhance intent detector to recognize sequential patterns:
   - "I want to [X] and [Y]"
   - "[X], then [Y]"
   - "[X] and also [Y]"
2. Extract sequential intents from compound queries
3. Return ordered list of intents
4. **Timeline**: 2-3 days

### Phase 2: Sequential Orchestrator (Core Feature)
1. Create `SequentialIntentOrchestrator` class
2. Execute intents in detected order
3. Maintain context between executions:
   - Pass entities from first intent to second
   - Preserve conversation state
4. Structure multi-part responses
5. **Timeline**: 5-7 days

### Phase 3: Context Enhancement
1. Enhance context passing between intents
2. Support entity extraction and reuse
3. Handle implicit connections (e.g., "BTC" from informational → swap)
4. **Timeline**: 3-4 days

### Phase 4: Response Formatting
1. Create multi-part response formatter
2. Structure responses as conversation flow
3. Add visual separators between parts
4. **Timeline**: 2-3 days

---

## Architecture Design

### Current Architecture (Single Intent)
```
User Message
  ↓
Intent Detector → Single Intent
  ↓
Handler Service → Single Handler
  ↓
Response Generator → Single Response
```

### Proposed Architecture (Sequential Multi-Intent)
```
User Message
  ↓
Sequential Intent Detector → [Intent₁, Intent₂, ...]
  ↓
Sequential Orchestrator
  ├─ Execute Intent₁ → Response₁
  ├─ Pass Context → 
  ├─ Execute Intent₂ → Response₂
  └─ ...
  ↓
Multi-Part Response Formatter → Structured Response
```

### Key Components

**1. SequentialIntentDetector**
```python
class SequentialIntentDetector:
    def detect_sequential_intents(
        self, 
        message: str, 
        language: str
    ) -> List[IntentWithContext]:
        """
        Detect multiple sequential intents in a message.
        
        Examples:
        - "I want to know about BTC and make a swap"
          → [INFORMATIONAL_QUERY(BTC), SWAP]
        - "What is DeFi, then show me lending rates"
          → [INFORMATIONAL_QUERY(DeFi), LENDING]
        """
```

**2. SequentialIntentOrchestrator**
```python
class SequentialIntentOrchestrator:
    async def execute_sequential(
        self,
        intents: List[IntentWithContext],
        initial_context: UserContext
    ) -> List[IntentResult]:
        """
        Execute intents sequentially, maintaining context.
        
        Context flows:
        - Entities extracted in Intent₁ available to Intent₂
        - Conversation state preserved
        - User preferences maintained
        """
```

**3. MultiPartResponseFormatter**
```python
class MultiPartResponseFormatter:
    def format_sequential_response(
        self,
        results: List[IntentResult]
    ) -> StructuredResponse:
        """
        Format multiple intent results into structured response.
        
        Structure:
        {
            "parts": [
                {"type": "informational", "content": "..."},
                {"type": "transactional", "content": "..."}
            ],
            "flow": "sequential"
        }
        """
```

---

## Code Changes Required

### 1. Enhance Intent Detection
```python
# src/app/application/guest/commands/send_guest_message.py

def _detect_sequential_intents(
    self,
    content: str,
    language: str
) -> List[Tuple[ChatIntent, str, float]]:
    """
    Detect sequential intents in compound queries.
    
    Returns:
        List of (intent, extracted_content, confidence) tuples
    """
    # Patterns for sequential queries
    sequential_patterns = {
        "en": [
            r"(.+?)\s+(?:and|then|also)\s+(.+)",
            r"(.+?),\s+(?:and|then|also)\s+(.+)",
        ],
        "es": [
            r"(.+?)\s+(?:y|entonces|también)\s+(.+)",
            r"(.+?),\s+(?:y|entonces|también)\s+(.+)",
        ],
        # ... other languages
    }
    
    # Detect sequential structure
    # Extract parts
    # Detect intent for each part
    # Return ordered list
```

### 2. Create Sequential Orchestrator
```python
# src/app/application/guest/handlers/sequential_orchestrator.py

class SequentialIntentOrchestrator:
    async def execute_sequential(
        self,
        intents: List[IntentWithContext],
        handler_service: GuestHandlerService,
        context: UserContext
    ) -> List[IntentResult]:
        """
        Execute intents sequentially with context preservation.
        """
        results = []
        current_context = context
        
        for intent_info in intents:
            # Execute intent with current context
            result = await handler_service.handle_intent(
                intent=intent_info.intent,
                content=intent_info.content,
                language=intent_info.language,
                context=current_context,
            )
            
            # Update context with result
            current_context = self._update_context(
                current_context,
                result,
                intent_info
            )
            
            results.append(result)
        
        return results
```

### 3. Update Guest Message Handler
```python
# In send_guest_message.py execute() method

# Check for sequential intents BEFORE single intent detection
sequential_intents = self._detect_sequential_intents(content, language)

if len(sequential_intents) > 1:
    # Use sequential orchestrator
    orchestrator = SequentialIntentOrchestrator()
    results = await orchestrator.execute_sequential(
        sequential_intents,
        self._handler_service,
        context
    )
    
    # Format multi-part response
    formatter = MultiPartResponseFormatter()
    agent_content = formatter.format_sequential_response(results)
else:
    # Fall back to single intent flow
    # ... existing code ...
```

---

## UX/UI Considerations

### Response Structure
```json
{
  "content": "**About Bitcoin (BTC)**\n\nBitcoin is the first cryptocurrency...\n\n---\n\n**Swap Quote**\n\nI can help you swap BTC. Here's a quote...",
  "parts": [
    {
      "type": "informational",
      "title": "About Bitcoin",
      "content": "...",
      "sources": []
    },
    {
      "type": "transactional",
      "title": "Swap Quote",
      "content": "...",
      "action_required": true
    }
  ],
  "flow": "sequential"
}
```

### Visual Design
- Use visual separators between response parts
- Clear section headers
- Maintain conversation flow
- Show progression: "First, let me explain... Then, here's your swap quote..."

---

## Success Metrics

- **Intent Detection**: 90%+ accuracy for sequential intent detection
- **Context Preservation**: 95%+ success rate for context passing
- **Response Quality**: > 80% user satisfaction for compound queries
- **Performance**: < 5s response time for 2-intent queries
- **Adoption**: 30%+ of users use compound queries

---

## Migration Strategy

1. **Phase 1**: Feature flag for sequential multi-intent
2. **Phase 2**: A/B test with 10% of users
3. **Phase 3**: Monitor metrics and refine
4. **Phase 4**: Gradual rollout to 100%
5. **Phase 5**: Remove feature flag, make default

---

*Analysis completed using CTO Methodology Framework*
*Date: 2026-01-19*
*Focus: Sequential Multi-Intent Queries Architecture*
