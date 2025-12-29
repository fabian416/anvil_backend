# LLM Gateway Consolidation - Phase 1 Analysis

**Date**: 2025-12-28
**Initiative**: 1 - LLM Gateway Consolidation
**Phase**: 1.1 - Inventory Current Usage (COMPLETE)

---

## Summary Statistics

- **LLMGateway references**: 23 lines across 6 files
- **LLMClientGateway references**: 47 lines across 10 files
- **Total migration scope**: ~16 files

---

## Interface Comparison

### LLMGateway (Current)

**Location**: `src/app/domain/ports/ai/llm_gateway.py`

**Methods**:
```python
async def generate_response(
    model_name: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None
) -> str

async def generate_response_with_metadata(
    model_name: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict, str, Any]]] = None
) -> Dict[str, Any]
```

**Characteristics**:
- ✅ Supports tools/function calling
- ✅ Has metadata variant
- ❌ Verbose method names
- ❌ Uses `model_name` (inconsistent)

### LLMClientGateway (Current)

**Location**: `src/app/domain/ports/agent_squad/llm_client_gateway.py`

**Methods**:
```python
async def classify_intent(prompt: str, model: str) -> dict
async def recommend_agents(prompt: str, model: str) -> dict
async def plan_workflow(prompt: str, max_agents: int) -> dict
async def chat(messages: list[dict], model: str, ...) -> dict
async def generate(model: str, messages: list[dict], ...) -> str
```

**Characteristics**:
- ✅ Clean `generate()` method name
- ✅ Modern type hints (`list[dict]` vs `List[Dict]`)
- ❌ Domain-specific methods mixed with generic methods
- ❌ No tools support in `generate()`

---

## Consumer Analysis

### LLMGateway Consumers (6 files)

| File | Type | Usage Pattern | Migration Effort |
|------|------|---------------|------------------|
| `domain/ports/ai/llm_gateway.py` | Port Definition | Interface declaration | **Update interface** |
| `infrastructure/adapters/ai/llm_gateway_impl.py` | Implementation | Implements port | **Update methods** |
| `infrastructure/adapters/ai/instrumented_llm_gateway.py` | Wrapper | Telemetry wrapper | **Update method calls** |
| `infrastructure/adapters/ai/agent_gateway_impl.py` | Adapter | Uses as dependency | **Update constructor** |
| `application/graph/entity_extraction.py` | Service | Calls `generate_response()` | **Rename method calls** |
| `application/chat/services/agent_orchestration_service.py` | Service | Calls `generate_response()` | **Rename method calls** |

**Total Effort**: ~4 hours

### LLMClientGateway Consumers (10 files)

| File | Type | Usage Pattern | Migration Effort |
|------|------|---------------|------------------|
| `domain/ports/agent_squad/llm_client_gateway.py` | Port Definition | Interface declaration | **DELETE after migration** |
| `infrastructure/adapters/agent_squad/llm_client_openai.py` | Implementation | OpenAI adapter | **DELETE or merge** |
| `infrastructure/adapters/agent_squad/llm_client_deepinfra.py` | Implementation | DeepInfra adapter | **DELETE or merge** |
| `infrastructure/adapters/agent_squad/llm_client_vertex_ai.py` | Implementation | Vertex AI adapter | **DELETE or merge** |
| `infrastructure/adapters/agent_squad/llm_client_with_fallback.py` | Wrapper | Fallback logic | **Update or DELETE** |
| `application/chat/services/intent_detector.py` | Service | Calls `generate()` | **Update to use new interface** |
| `setup/ioc/agent_squad_infrastructure.py` | DI Provider | Many providers (15+) | **Consolidate providers** |
| `setup/ioc/agent_squad_domain.py` | DI Provider | Domain services | **Update dependencies** |
| `setup/ioc/chat_phase2.py` | DI Provider | Chat services | **Update dependencies** |
| `setup/ioc/testing.py` | Mock | `MockLLMClientGateway` | **Merge into MockLLMGateway** |

**Total Effort**: ~8 hours

---

## Unified Interface Design

### Proposed: Single LLMGateway Interface

**Location**: `src/app/domain/ports/ai/llm_gateway.py` (UPDATE)

**Core Methods** (generic LLM operations):
```python
async def generate(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 1000,
    tools: Optional[list[dict]] = None,
) -> str:
    """
    Generate text completion.

    Args:
        model: Model identifier (e.g., "gpt-4o-mini", "claude-sonnet-4")
        messages: Conversation messages [{"role": "user", "content": "..."}]
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum response tokens
        tools: Optional tool definitions for function calling

    Returns:
        Generated text response
    """
    ...

async def generate_with_metadata(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 1000,
    tools: Optional[list[dict]] = None,
) -> tuple[str, dict]:
    """
    Generate with usage metadata.

    Returns:
        Tuple of (response_text, metadata)
        metadata = {
            "tokens_used": int,
            "model": str,
            "latency_ms": int,
            "finish_reason": str,
        }
    """
    ...
```

**Decision**: Domain-specific methods (`classify_intent`, `recommend_agents`, `plan_workflow`) should be **EXTRACTED** into separate domain ports:
- `IntentDetectionPort` (Initiative 2)
- `AgentRecommendationPort` (future)
- `WorkflowPlanningPort` (future)

---

## Migration Strategy

### Option A: Migrate to LLMGateway Interface ✅ **SELECTED**

**Rationale**:
- `LLMGateway` is already in domain layer (correct location)
- Has `generate_response_with_metadata()` for tracking
- Easier to extend with `tools` parameter

**Migration Path**:
1. Rename `generate_response` → `generate`
2. Rename `generate_response_with_metadata` → `generate_with_metadata`
3. Change `model_name` → `model`
4. Update return type for metadata method: `Dict[str, Any]` → `tuple[str, dict]`
5. Modernize type hints: `List[Dict]` → `list[dict]`

### Option B: Migrate to LLMClientGateway Interface ❌ **REJECTED**

**Why Rejected**:
- Domain-specific methods pollute generic interface
- Located in `agent_squad` subdomain (too specific)
- Would require more files to change

---

## Provider Consolidation Plan

### Current State (Fragmented)

**Infrastructure Providers**:
- `InfrastructureProvider.provide_llm_gateway()` → `LLMGateway`
- `AgentSquadInfrastructureProvider.provide_llm_client()` → `LLMClientGateway`

**Test Providers**:
- `TestMockProvider.provide_mock_llm_gateway()` → `LLMGateway`
- `TestMockProvider.provide_mock_llm_client_gateway()` → `LLMClientGateway`

### Target State (Unified)

**Infrastructure Provider**:
```python
class InfrastructureProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_llm_gateway(self, settings: AppSettings) -> LLMGateway:
        """Unified LLM gateway with fallback."""
        # Use existing LLMGatewayImpl or create new unified implementation
        return LLMGatewayImpl(settings)
```

**Test Provider**:
```python
class TestMockProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_llm_gateway(self) -> LLMGateway:
        """Unified mock LLM gateway for all tests."""
        return MockLLMGateway()
```

**DELETE**:
- `provide_mock_llm_client_gateway()`
- All `AgentSquadInfrastructureProvider.provide_*()` methods that create agent services

---

## Implementation Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking production | High | Low | Comprehensive test suite before merge |
| Type checking failures | Medium | High | Run `mypy` after each phase |
| Test failures | Medium | Medium | Fix incrementally, keep old mocks during transition |
| DI provider conflicts | Medium | Medium | Use adapter pattern during migration |
| Performance regression | Low | Low | Same underlying implementation |

---

## Success Criteria

**Phase 1 (Analysis) - COMPLETE**:
- ✅ Usage inventory complete (23 + 47 references)
- ✅ Interface comparison documented
- ✅ Unified interface designed
- ✅ Migration strategy defined

**Phase 2 (Implementation)**:
- [ ] Updated `LLMGateway` interface
- [ ] All infrastructure implementations updated
- [ ] All application consumers migrated
- [ ] Zero compilation errors
- [ ] `mypy` passes

**Phase 3 (Testing)**:
- [ ] Unified `MockLLMGateway` created
- [ ] All 31 passing tests still pass
- [ ] Remaining 6 tests fixed (if DI issue resolved)
- [ ] No new test failures

**Phase 4 (Cleanup)**:
- [ ] `LLMClientGateway` deleted
- [ ] Agent squad adapters consolidated
- [ ] Documentation updated
- [ ] Zero deprecated imports

---

## Next Steps

**Ready to proceed to Phase 1.2**: Interface Comparison & Unified Design

The analysis shows:
- ✅ Consolidation is feasible
- ✅ Migration scope is well-defined (~12 hours total)
- ✅ Risk is manageable with incremental approach
- ✅ Unified interface design is clear

**Recommendation**: Proceed with implementation starting Phase 2.1
