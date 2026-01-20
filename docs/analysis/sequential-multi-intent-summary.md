# Sequential Multi-Intent Queries - Executive Summary

## Problem Statement

**Current Issue**: Users naturally combine informational queries with transactional actions in a single message (e.g., "I want to know about BTC and make a swap"), but the system only handles one intent per message, losing the informational part.

## Root Cause

The current architecture assumes **one message = one intent**, but users think in **conversational flows** where information gathering precedes action.

## Current Flow (Broken)
```
"I want to know about BTC and make a swap"
  ↓
Intent Detection → Picks SWAP (ignores informational)
  ↓
Handler → Executes only swap
  ↓
Response → Only swap quote (BTC info lost)
```

## Desired Flow (Fixed)
```
"I want to know about BTC and make a swap"
  ↓
Sequential Intent Detection → [INFORMATIONAL_QUERY(BTC), SWAP]
  ↓
Sequential Orchestrator
  ├─ Execute informational → BTC explanation
  ├─ Pass context (BTC entity)
  └─ Execute swap → Swap quote for BTC
  ↓
Multi-Part Response
  ├─ Part 1: "About Bitcoin (BTC)..."
  └─ Part 2: "Swap Quote for BTC..."
```

## Solution Architecture

### Key Components

1. **SequentialIntentDetector**
   - Detects multiple intents in compound queries
   - Recognizes patterns: "X and Y", "X, then Y", "X and also Y"
   - Extracts intent for each part

2. **SequentialIntentOrchestrator**
   - Executes intents in detected order
   - Maintains context between executions
   - Passes entities from first intent to second

3. **MultiPartResponseFormatter**
   - Structures responses as conversation flow
   - Adds visual separators
   - Maintains clear section headers

## Implementation Priority

### Phase 1: Quick Win (2-3 days)
- Add sequential intent detection patterns
- Parse compound queries into parts
- Detect intent for each part

### Phase 2: Core Feature (5-7 days)
- Create sequential orchestrator
- Implement context preservation
- Structure multi-part responses

### Phase 3: Enhancement (3-4 days)
- Improve context passing
- Handle entity extraction/reuse
- Add error recovery

## Benefits

✅ **Better UX**: Natural conversational flow
✅ **Context Preservation**: Information flows to actions
✅ **User Satisfaction**: Handles real-world query patterns
✅ **Competitive Advantage**: More intelligent than single-intent systems

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Intent detection accuracy | Start with simple patterns, refine based on usage |
| Performance overhead | Sequential execution is acceptable (< 5s target) |
| Response complexity | Clear formatting and visual separators |
| Context management | Careful state handling, fallback to single-intent |

## Next Steps

1. Review this analysis
2. Approve architecture approach
3. Start Phase 1 implementation
4. Test with real user queries
5. Iterate based on feedback

---

*For detailed analysis, see: `sequential-multi-intent-queries-architecture.md`*
