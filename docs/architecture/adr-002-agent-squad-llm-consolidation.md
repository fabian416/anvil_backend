# ADR-002: Agent Squad LLM Consolidation

**Status**: Proposed  
**Date**: 2025-01-28  
**Decision Maker**: CTO  
**Context**: LLM Gateway Unification Initiative

## Context and Problem Statement

The codebase currently has **two separate LLM abstractions**:

1. **LLMGateway** (`app.domain.ports.ai.llm_gateway`)
   - Used by: Chat application, Intent Detection
   - Interface: `generate()`, `generate_with_metadata()`
   - Implementations: `LLMGatewayImpl`, `InstrumentedLLMGateway`, `MockLLMGateway`

2. **LLMClientGateway** (`app.domain.ports.agent_squad.llm_client_gateway`)
   - Used by: Agent Squad (18+ agents)
   - Interface: `classify_intent()`, `recommend_agents()`, `plan_workflow()`, `chat()`, `generate()`
   - Implementations: `LLMClientOpenAI`, `LLMClientVertexAI`, `LLMClientDeepInfra`, `LLMClientWithFallback`

This creates:
- Duplicate code paths for LLM interactions
- Inconsistent error handling and retry logic
- Separate test mocking infrastructure
- Maintenance overhead

## Decision Drivers

1. **Architecture Consistency**: Single LLM abstraction across the codebase
2. **Maintainability**: One place to update LLM provider logic
3. **Testability**: Unified mocking strategy
4. **Risk Tolerance**: Low tolerance for breaking production agents
5. **Time Constraints**: Incremental approach preferred

## Considered Options

### Option A: Full Migration (High Risk)
**Description**: Replace all `LLMClientGateway` usages with `LLMGateway`

**Pros:**
- Complete unification
- Cleanest architecture

**Cons:**
- Requires modifying 20+ files
- High risk of breaking agents
- 2-3 days of work
- Extensive testing needed

**Decision: REJECTED** - Too risky for immediate implementation

### Option B: Adapter Pattern (Selected)
**Description**: Create `LLMClientGatewayAdapter` that implements `LLMClientGateway` using `LLMGateway`

**Pros:**
- No changes to existing agents
- Gradual migration path
- Low risk
- Completed in 1-2 hours

**Cons:**
- Adds adapter indirection
- Two interfaces still exist (but single implementation)

**Decision: APPROVED** - Best balance of benefits and risk

### Option C: Interface Extension
**Description**: Add `LLMClientGateway` methods to `LLMGateway`

**Pros:**
- Single interface

**Cons:**
- Bloats the gateway interface
- Domain-specific methods in generic interface
- Violates interface segregation

**Decision: REJECTED** - Violates interface segregation principle

### Option D: Strategic Acceptance
**Description**: Document separation, accept as bounded contexts

**Pros:**
- Zero changes needed
- No risk

**Cons:**
- Doesn't address underlying issue
- Continued maintenance overhead

**Decision: FALLBACK** - Use if Option B causes issues

## Decision

**Selected Option: B - Adapter Pattern**

We will:
1. Create `LLMClientGatewayAdapter` that wraps `LLMGateway`
2. Register adapter as optional alternative to current implementation
3. Document migration path for future phases

## Implementation Status

### Phase 1: Adapter Creation ✅ COMPLETE
- Created `LLMClientGatewayAdapter` in `infrastructure/adapters/agent_squad/`
- Added to package exports
- Translates specialized calls to `generate()` calls

### Phase 2: AgentLLMGateway ✅ COMPLETE
- Created `AgentLLMGateway` adapter for agent-specific needs
- Wraps `LLMGateway` to provide `chat()` method returning dict format
- Registered in DI via `provide_agent_llm_gateway` method
- Enables gradual migration without changing agent code

### Phase 4: Production Activation (Future)
1. Feature flag to toggle between implementations
2. A/B testing in staging
3. Roll out to production
4. Deprecate direct LLM client implementations

## Architecture After Implementation

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────┬───────────────────────────────────────┤
│   Chat Services     │         Agent Squad                   │
│                     │                                       │
│ IntentDetectorSvc   │  ChatAgent  ResearchAgent  Portfolio  │
│        │            │      │           │            │       │
│        ▼            │      ▼           ▼            ▼       │
│ IntentDetectionPort │  LLMClientGateway (Port)              │
└─────────┬───────────┴───────────────────┬───────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐     ┌──────────────────────────┐       │
│  │   LLMGateway    │◄────│ LLMClientGatewayAdapter  │       │
│  │ Implementation  │     └──────────────────────────┘       │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          External LLM Providers                      │    │
│  │  Vertex AI  │  DeepInfra  │  OpenAI  │  Anthropic   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Consequences

### Positive
- Single LLM implementation in production
- Consistent error handling and retry logic
- Unified observability and instrumentation
- Simplified testing infrastructure

### Negative
- Adapter adds slight indirection (negligible performance impact)
- Two interfaces still exist in domain layer

### Risks
- Adapter response format differences (mitigated by JSON parsing fallback)
- Integration test failures (mitigated by comprehensive test coverage)

## References

- ADR-001: LLM Gateway Consolidation
- `src/app/infrastructure/adapters/agent_squad/llm_client_gateway_adapter.py`
- `docs/implementation-plan-llm-consolidation.md`
