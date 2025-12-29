# LLM Gateway Consolidation - Implementation Plan

**Initiative**: Consolidate dual LLM abstractions into single interface
**Timeline**: 3-4 days
**Risk Level**: Medium
**Dependencies**: None

---

## Phase 1: Analysis & Design (Day 1 - Morning)

### 1.1 Inventory Current Usage

**Task**: Map all consumers of each gateway type

```bash
# Find all LLMGateway consumers
grep -r "LLMGateway" src/app --include="*.py" | grep -v "LLMClientGateway" > llm_gateway_usage.txt

# Find all LLMClientGateway consumers
grep -r "LLMClientGateway" src/app --include="*.py" > llm_client_gateway_usage.txt
```

**Expected Consumers**:

**LLMGateway** (to migrate):
- `ChatLLMProvider` (regular chat)
- Various handler classes
- Admin LLM controllers
- ~10-15 files estimated

**LLMClientGateway** (target interface):
- `IntentDetectorService`
- Agent squad services
- ~5-8 files

**Deliverable**: Usage matrix spreadsheet

---

### 1.2 Interface Comparison

**Current Interfaces**:

```python
# LLMClientGateway (TARGET)
class LLMClientGateway(ABC):
    @abstractmethod
    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Simple string response."""
        ...

    @abstractmethod
    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """Intent classification (can be removed if unused)."""
        ...

# LLMGateway (TO DEPRECATE)
class LLMGateway(ABC):
    @abstractmethod
    async def generate_response(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        ...

    @abstractmethod
    async def generate_response_with_metadata(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        ...
```

**Unified Interface Design**:

```python
# src/app/domain/ports/ai/llm_gateway.py (UPDATED)
from abc import ABC, abstractmethod
from typing import Optional

class LLMGateway(ABC):
    """
    Unified LLM gateway for all AI interactions.

    Consolidates previous LLMGateway and LLMClientGateway interfaces.
    """

    @abstractmethod
    async def generate(
        self,
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

    @abstractmethod
    async def generate_with_metadata(
        self,
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

**Migration Strategy**: Adapter pattern during transition

```python
# src/app/infrastructure/adapters/ai/llm_gateway_adapter.py (TEMPORARY)
class LLMGatewayAdapter(LLMGateway):
    """
    Temporary adapter to migrate LLMClientGateway consumers.

    DELETE after migration complete.
    """

    def __init__(self, new_gateway: LLMGateway):
        self._gateway = new_gateway

    async def generate(self, model: str, messages: list[dict], **kwargs) -> str:
        # Delegate to new interface
        return await self._gateway.generate(model, messages, **kwargs)

    # Legacy methods (deprecated)
    async def classify_intent(self, prompt: str, model: str) -> dict:
        """DEPRECATED: Use IntentDetectionService instead."""
        warnings.warn("classify_intent deprecated, use IntentDetectionService")
        # Fallback implementation or raise NotImplementedError
        ...
```

**Deliverable**: Updated interface definition + migration adapter

---

## Phase 2: Implementation (Day 1 Afternoon - Day 2)

### 2.1 Update LLMGateway Interface

**File**: `src/app/domain/ports/ai/llm_gateway.py`

**Changes**:
1. Rename `generate_response` → `generate`
2. Rename `generate_response_with_metadata` → `generate_with_metadata`
3. Add `tools` parameter (optional)
4. Update type hints to modern Python syntax
5. Add comprehensive docstrings

**Validation**:
```bash
# Check no breaking changes to method signatures consumers expect
mypy src/app/domain/ports/ai/llm_gateway.py
```

---

### 2.2 Update Infrastructure Implementations

**Files to Update**:

**Primary**:
- `src/app/infrastructure/adapters/ai/llm_gateway_impl.py`
  - Rename methods
  - Update parameter names
  - Keep logic identical

**LLM Provider Adapters**:
- `src/app/infrastructure/adapters/ai/llm_client_vertex_ai.py`
- `src/app/infrastructure/adapters/ai/llm_client_deepinfra.py`
- `src/app/infrastructure/adapters/ai/llm_client_openai.py`

**Changes Per File**:
```python
# BEFORE
async def generate_response(self, model_name: str, messages: List[Dict], ...) -> str:
    ...

# AFTER
async def generate(self, model: str, messages: list[dict], ...) -> str:
    ...
```

**Testing Strategy**:
- Update unit tests for each adapter
- Verify mock implementations match interface
- Run adapter-specific integration tests

---

### 2.3 Migrate Application Layer Consumers

**Migration Pattern**:

```python
# BEFORE
response = await self._llm_gateway.generate_response(
    model_name="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
)

# AFTER
response = await self._llm_gateway.generate(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
)
```

**Files to Migrate** (estimated 10-15 files):
- `src/app/application/chat/services/*.py`
- `src/app/application/*/commands/*.py`
- `src/app/presentation/http/controllers/admin/llm/*.py`

**Batch Migration Script**:
```bash
# Automated refactoring (review before committing)
find src/app -name "*.py" -exec sed -i 's/generate_response(/generate(/g' {} \;
find src/app -name "*.py" -exec sed -i 's/model_name=/model=/g' {} \;
```

**Manual Review Required**:
- Verify parameter order
- Check for `generate_response_with_metadata` calls
- Update to `generate_with_metadata`

---

## Phase 3: Testing & Validation (Day 3)

### 3.1 Update Test Mocks

**File**: `src/app/setup/ioc/testing.py`

**Changes**:

```python
class MockLLMGateway(LLMGateway):
    """Unified mock for both regular chat and agent squad."""

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[list[dict]] = None,
    ) -> str:
        """Mock generate with intent classification logic."""
        # Extract user message
        message_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                message_content = msg.get("content", "")
                break

        # Use existing keyword classification logic
        return self._classify_intent(message_content)

    async def generate_with_metadata(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[list[dict]] = None,
    ) -> tuple[str, dict]:
        """Mock with metadata."""
        response = await self.generate(model, messages, temperature, max_tokens, tools)
        metadata = {
            "tokens_used": 100,
            "model": model,
            "latency_ms": 50,
            "finish_reason": "stop",
        }
        return response, metadata
```

**Delete Deprecated Mocks**:
- `MockLLMClientGateway` (merged into above)
- Any other gateway-specific mocks

---

### 3.2 Update Test Providers

**File**: `src/app/setup/ioc/testing.py`

**Changes**:

```python
class TestMockProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_mock_llm_gateway(self) -> LLMGateway:
        """
        Provide unified mock LLM gateway.

        Overrides both old LLMGateway and LLMClientGateway providers.
        """
        return MockLLMGateway()
```

**Delete**:
- `provide_mock_llm_client_gateway()` (no longer needed)

---

### 3.3 Run Full Test Suite

**Validation Steps**:

```bash
# 1. Run all tests
./env/bin/python -m pytest tests/ -v

# 2. Expected results
# - All 31 previously passing tests: PASS
# - 6 previously failing tests: Should now PASS (or fail with different error)

# 3. Specific validation
./env/bin/python -m pytest tests/integration/chat/test_unified_chat_with_test_data.py -v

# 4. Check for regressions
./env/bin/python -m pytest tests/unit/ -v
```

**Success Criteria**:
- ✅ All 31 existing tests pass
- ✅ No new test failures introduced
- ✅ Squad tests improve (if DI issue was type mismatch)
- ✅ Type checking passes (`mypy src/`)

---

## Phase 4: Cleanup & Documentation (Day 4)

### 4.1 Remove Deprecated Code

**Files to Delete**:
- `src/app/domain/ports/agent_squad/llm_client_gateway.py` (if separate file)
- Any `LLMGatewayAdapter` temporary files
- Old mock implementations

**Files to Update**:
- Remove `LLMClientGateway` imports
- Update to `LLMGateway` everywhere

**Validation**:
```bash
# Ensure no references remain
grep -r "LLMClientGateway" src/app
# Should return 0 results
```

---

### 4.2 Update Documentation

**Files to Create/Update**:

**1. Architecture Decision Record**:
```markdown
# docs/architecture/adr/004-unified-llm-gateway.md

# ADR 004: Unified LLM Gateway Interface

## Status
Accepted

## Context
System had two separate LLM gateway abstractions:
- `LLMGateway` (general chat)
- `LLMClientGateway` (agent squad)

This caused:
- Test infrastructure complexity
- DI provider confusion
- Duplicate mock implementations

## Decision
Consolidate into single `LLMGateway` interface with:
- `generate()` for simple text responses
- `generate_with_metadata()` for usage tracking
- Support for tool calling (function calling)

## Consequences

### Positive
- Single test mock implementation
- Clearer DI provider precedence
- Easier to maintain and extend

### Negative
- Migration effort (3-4 days)
- Temporary breaking changes during transition

### Mitigation
- Adapter pattern during migration
- Comprehensive test coverage
- Gradual rollout (feature flag if needed)
```

**2. Update Developer Guide**:
```markdown
# docs/development/llm-integration.md

# LLM Integration Guide

## Using the LLM Gateway

All LLM interactions go through the unified `LLMGateway` interface.

### Basic Usage

```python
from app.domain.ports.ai.llm_gateway import LLMGateway

class MyService:
    def __init__(self, llm_gateway: LLMGateway):
        self._llm = llm_gateway

    async def generate_response(self, user_message: str) -> str:
        response = await self._llm.generate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response
```

### With Metadata

```python
response, metadata = await self._llm.generate_with_metadata(
    model="gpt-4o-mini",
    messages=[...],
)

print(f"Used {metadata['tokens_used']} tokens")
print(f"Latency: {metadata['latency_ms']}ms")
```

### Testing

```python
# tests/conftest.py provides MockLLMGateway automatically
# No need to mock in individual tests

async def test_my_service(test_app):
    # LLM calls are automatically mocked with deterministic responses
    response = await my_service.generate_response("Hello")
    assert "mock" in response.lower()
```
```

---

## Risk Mitigation

### Potential Issues & Solutions

| Risk | Impact | Mitigation | Rollback Plan |
|------|--------|------------|---------------|
| **Breaking production** | High | Comprehensive test suite, gradual rollout | Git revert, deploy previous version |
| **Type checking failures** | Medium | Run `mypy` before commit | Fix type hints incrementally |
| **Test failures** | Medium | Fix before merging | Keep old mocks during transition |
| **Performance regression** | Low | Same underlying implementation | Monitor latency metrics |

### Validation Checkpoints

**Before Merging**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Type checking passes (`mypy`)
- [ ] No deprecated imports remain
- [ ] Documentation updated

**After Deploying to Staging**:
- [ ] Smoke tests pass
- [ ] LLM latency within baseline ±5%
- [ ] No error spike in logs
- [ ] Manual testing of chat features

---

## Success Metrics

**Primary**:
- ✅ Single `LLMGateway` interface
- ✅ All tests passing (31/31 minimum, ideally 37/37)
- ✅ Zero production incidents

**Secondary**:
- ✅ Test execution time unchanged
- ✅ Code coverage maintained or improved
- ✅ Developer documentation complete

---

## Timeline

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **Day 1 AM** | Analysis & Design | Interface design, usage inventory |
| **Day 1 PM** | Update interface + implementations | Updated domain port, adapters |
| **Day 2** | Migrate consumers | All application layer updated |
| **Day 3** | Testing & validation | All tests passing |
| **Day 4** | Cleanup & documentation | Deprecated code removed, docs complete |

**Total**: 3-4 days (depends on consumer count)

---

## Next Steps After Completion

This consolidation unblocks:
1. ✅ Intent Detection Port creation (Initiative 2)
2. ✅ Simplified test mocking
3. ✅ Clearer DI provider patterns

**Proceed to**: Initiative 2 - Create Intent Detection Domain Port
