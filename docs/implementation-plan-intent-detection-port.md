# Intent Detection Domain Port - Implementation Plan

**Initiative**: Decouple intent detection from infrastructure LLM clients
**Timeline**: 2-3 days
**Risk Level**: Low
**Dependencies**: Initiative 1 (LLM Gateway Consolidation) recommended but not required

---

## Phase 1: Problem Analysis & Root Cause (Day 1 - Morning)

### Current Architecture Issues

**Problem**: `IntentDetectorService` directly depends on `LLMGateway` (infrastructure)

```python
# Current (TIGHT COUPLING)
class IntentDetectorService:
    def __init__(self, llm_client: Optional[LLMGateway] = None):
        self._llm_client = llm_client  # Infrastructure dependency!

    async def detect_intent(self, message: str) -> IntentDetectionResult:
        if self._llm_client:
            # Calls infrastructure directly
            response = await self._llm_client.generate(...)
```

**Violation**: Application layer depends on infrastructure layer

**Hexagonal Architecture Principle**: Domain and application should depend on domain ports, NOT infrastructure adapters.

---

### Solution Design: Intent Detection Port

**Target Architecture** (Hexagonal):

```
┌─────────────────────────────────────────────┐
│         Application Layer                   │
│  ┌─────────────────────────────────────┐   │
│  │ IntentDetectorService                │   │
│  │   depends on ↓                       │   │
│  │ IntentDetectionPort (interface)      │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                    ↑ implements
┌─────────────────────────────────────────────┐
│      Infrastructure Layer                   │
│  ┌─────────────────────────────────────┐   │
│  │ LLMIntentDetectionAdapter            │   │
│  │   uses → LLMGateway                  │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │ KeywordIntentDetectionAdapter        │   │
│  │   (fallback, no LLM)                 │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Domain logic independent of LLM provider
- ✅ Easy to mock in tests (simple interface)
- ✅ Can swap LLM provider without changing application
- ✅ Follows hexagonal architecture principles

---

## Phase 2: Design Intent Detection Port (Day 1 - Afternoon)

### 2.1 Domain Port Interface

**File**: `src/app/domain/ports/chat/intent_detection_port.py` (NEW)

```python
"""
Intent detection port for chat domain.

Defines the interface for detecting user intent from messages.
Implementations can use LLM, keywords, ML models, or hybrid approaches.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class IntentDetectionRequest:
    """
    Request for intent detection.

    Contains all information needed to classify user intent.
    """
    message: str
    conversation_history: Optional[list["Message"]] = None
    user_context: Optional[dict] = None  # User preferences, tier, etc.


@dataclass
class IntentDetectionResult:
    """
    Result of intent detection.

    Includes classified intent, confidence, extracted entities, and reasoning.
    """
    intent: "ChatIntent"
    confidence: float  # 0.0 - 1.0
    entities: dict  # Extracted entities (protocol_name, token_symbol, etc.)
    reasoning: str  # Human-readable explanation
    handler: str  # Handler category (graphrag_search, ultra, hunter_ai, etc.)


class IntentDetectionPort(ABC):
    """
    Port for detecting user intent from chat messages.

    Implementations:
    - LLMIntentDetectionAdapter: Uses LLM for high accuracy
    - KeywordIntentDetectionAdapter: Fast keyword-based fallback
    - HybridIntentDetectionAdapter: LLM with keyword fallback
    """

    @abstractmethod
    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Detect user intent from message.

        Args:
            request: Intent detection request with message and context

        Returns:
            Intent detection result with classification and entities

        Raises:
            IntentDetectionError: If detection fails critically
        """
        ...

    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Whether this implementation supports streaming responses.

        Returns:
            True if streaming is supported, False otherwise
        """
        ...
```

**Domain Exception**:

```python
# src/app/domain/exceptions/chat.py (ADD)

class IntentDetectionError(DomainError):
    """Raised when intent detection fails critically."""
    pass
```

---

### 2.2 Update IntentDetectorService

**File**: `src/app/application/chat/services/intent_detector.py` (REFACTOR)

**Changes**:

```python
# BEFORE
class IntentDetectorService:
    def __init__(self, llm_client: Optional[LLMGateway] = None):
        self._llm_client = llm_client

    async def detect_intent(self, message: str, ...) -> IntentDetectionResult:
        if self._llm_client:
            try:
                result = await self._llm_classify_intent(...)
            except Exception:
                return self._keyword_classify_intent(...)
        return self._keyword_classify_intent(...)

# AFTER
class IntentDetectorService:
    """
    Application service for intent detection.

    Delegates to domain port implementation (LLM, keywords, or hybrid).
    """

    def __init__(self, intent_detector: IntentDetectionPort):
        """
        Initialize with intent detection port.

        Args:
            intent_detector: Port implementation (injected by DI)
        """
        self._intent_detector = intent_detector

    async def detect_intent(
        self,
        message: str,
        conversation_history: Optional[list[Message]] = None,
    ) -> IntentDetectionResult:
        """
        Detect intent using configured port implementation.

        Simple delegation - all logic moved to port implementations.
        """
        request = IntentDetectionRequest(
            message=message,
            conversation_history=conversation_history,
        )

        try:
            return await self._intent_detector.detect_intent(request)
        except IntentDetectionError as e:
            # Log and re-raise (let upper layers handle)
            import logging
            logging.error(f"Intent detection failed: {e}")
            raise
```

**Migration Impact**:
- ✅ Simpler service (delegation only)
- ✅ No more LLM logic in application layer
- ✅ Easier to test (mock single interface)

---

## Phase 3: Infrastructure Implementations (Day 2)

### 3.1 LLM Intent Detection Adapter

**File**: `src/app/infrastructure/adapters/chat/llm_intent_detection_adapter.py` (NEW)

```python
"""
LLM-based intent detection adapter.

Uses LLM gateway for high-accuracy intent classification.
"""

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.domain.exceptions.chat import IntentDetectionError
import json
import re


class LLMIntentDetectionAdapter(IntentDetectionPort):
    """
    Intent detection using LLM classification.

    Provides high accuracy but slower and costs tokens.
    """

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initialize with LLM gateway.

        Args:
            llm_gateway: LLM gateway for generating classifications
        """
        self._llm = llm_gateway

    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Use LLM to classify intent.

        Returns:
            High-confidence intent detection result
        """
        # Build classification prompt (moved from IntentDetectorService)
        system_prompt = self._build_classification_prompt()
        user_prompt = self._build_user_prompt(request)

        # Call LLM
        try:
            response = await self._llm.generate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low for consistent classification
                max_tokens=300,
            )
        except Exception as e:
            raise IntentDetectionError(f"LLM call failed: {e}") from e

        # Parse JSON response
        try:
            data = self._parse_llm_response(response)
        except Exception as e:
            raise IntentDetectionError(f"Failed to parse LLM response: {e}") from e

        # Build result
        return IntentDetectionResult(
            intent=ChatIntent(data["intent"]),
            confidence=data["confidence"],
            entities=data.get("entities", {}),
            reasoning=data.get("reasoning", "LLM classification"),
            handler=self._map_intent_to_handler(data["intent"]),
        )

    def supports_streaming(self) -> bool:
        return False  # Classification needs full response

    def _build_classification_prompt(self) -> str:
        """Build system prompt for intent classification."""
        # Copy from current IntentDetectorService._llm_classify_intent
        return """You are an intent classifier for a DeFi chat interface.

Classify the user's message into ONE of these intents:
...
"""

    def _build_user_prompt(self, request: IntentDetectionRequest) -> str:
        """Build user prompt with message and context."""
        context = ""
        if request.conversation_history:
            context = self._format_conversation_history(request.conversation_history)

        return f"""Previous context:
{context if context else "None"}

Current message: {request.message}

Classify the intent and extract entities."""

    def _parse_llm_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError("No valid JSON in response")

    def _map_intent_to_handler(self, intent: str) -> str:
        """Map intent to handler category."""
        mapping = {
            # GraphRAG
            "protocol_search": "graphrag_search",
            "risk_assessment": "graphrag_search",
            "similar_protocols": "graphrag_search",
            # Hunter
            "hunter_sentiment": "hunter_ai",
            "hunter_price_prediction": "hunter_ai",
            # ...
            # Squad
            "specialist_task": "agent_orchestrator",
            "complex_workflow": "agent_orchestrator",
            # Default
            "general_conversation": "general_chat",
        }
        return mapping.get(intent, "general_chat")
```

---

### 3.2 Keyword Intent Detection Adapter

**File**: `src/app/infrastructure/adapters/chat/keyword_intent_detection_adapter.py` (NEW)

```python
"""
Keyword-based intent detection adapter.

Fast, deterministic fallback that doesn't require LLM.
"""

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)


class KeywordIntentDetectionAdapter(IntentDetectionPort):
    """
    Intent detection using keyword matching.

    Fast and deterministic, but lower accuracy than LLM.
    """

    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Classify intent using keyword matching.

        Returns:
            Intent detection result with lower confidence
        """
        message_lower = request.message.lower()

        # Keyword matching logic (moved from IntentDetectorService)
        intent = self._classify_by_keywords(message_lower)
        entities = self._extract_entities(intent, message_lower)

        return IntentDetectionResult(
            intent=ChatIntent(intent),
            confidence=self._calculate_confidence(intent, message_lower),
            entities=entities,
            reasoning="Keyword-based classification",
            handler=self._map_intent_to_handler(intent),
        )

    def supports_streaming(self) -> bool:
        return False

    def _classify_by_keywords(self, message: str) -> str:
        """Classify using keyword rules."""
        # Copy keyword logic from IntentDetectorService._keyword_classify_intent
        if any(word in message for word in ["complete", "strategy"]):
            return "complex_workflow"
        elif any(word in message for word in ["analyze", "liquidity"]):
            return "specialist_task"
        # ...
        else:
            return "general_conversation"

    def _extract_entities(self, intent: str, message: str) -> dict:
        """Extract entities based on intent and message."""
        entities = {}

        # Protocol name extraction
        if intent == "risk_assessment":
            protocols = {"aave": "Aave", "uniswap": "Uniswap"}
            for keyword, name in protocols.items():
                if keyword in message:
                    entities["protocol_name"] = name
                    break

        # Token symbol extraction
        if intent.startswith("hunter_"):
            tokens = {"eth": "ETH", "btc": "BTC", "sol": "SOL"}
            for keyword, symbol in tokens.items():
                if keyword in message:
                    entities["token_symbol"] = symbol
                    break

        return entities

    def _calculate_confidence(self, intent: str, message: str) -> float:
        """Calculate confidence based on intent and message clarity."""
        if intent == "general_conversation":
            # High confidence for clear greetings
            if any(word in message for word in ["hello", "hi", "what can you"]):
                return 0.95
            else:
                return 0.65  # Unclear message
        else:
            return 0.85  # Keyword match confidence
```

---

### 3.3 Hybrid Intent Detection Adapter

**File**: `src/app/infrastructure/adapters/chat/hybrid_intent_detection_adapter.py` (NEW)

```python
"""
Hybrid intent detection with LLM + keyword fallback.

Best of both worlds: high accuracy with reliability.
"""

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)
import logging


class HybridIntentDetectionAdapter(IntentDetectionPort):
    """
    Intent detection with LLM primary and keyword fallback.

    Tries LLM first for accuracy, falls back to keywords for reliability.
    """

    def __init__(
        self,
        llm_adapter: "LLMIntentDetectionAdapter",
        keyword_adapter: "KeywordIntentDetectionAdapter",
        min_llm_confidence: float = 0.7,
    ):
        """
        Initialize hybrid adapter.

        Args:
            llm_adapter: Primary LLM-based detector
            keyword_adapter: Fallback keyword detector
            min_llm_confidence: Minimum confidence to accept LLM result
        """
        self._llm = llm_adapter
        self._keyword = keyword_adapter
        self._min_confidence = min_llm_confidence
        self._logger = logging.getLogger(__name__)

    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Detect intent with LLM + fallback.

        Strategy:
        1. Try LLM classification
        2. If confidence >= threshold, return LLM result
        3. If LLM fails or low confidence, fallback to keywords
        """
        # Try LLM first
        try:
            llm_result = await self._llm.detect_intent(request)

            if llm_result.confidence >= self._min_confidence:
                return llm_result

            # Low confidence, use fallback
            self._logger.warning(
                f"LLM confidence {llm_result.confidence} < {self._min_confidence}, "
                f"using keyword fallback"
            )

        except Exception as e:
            # LLM failed, use fallback
            self._logger.warning(f"LLM intent detection failed: {e}, using keyword fallback")

        # Fallback to keywords
        return await self._keyword.detect_intent(request)

    def supports_streaming(self) -> bool:
        return False
```

---

## Phase 4: DI Provider Updates (Day 2 - Afternoon)

### 4.1 Production Provider

**File**: `src/app/setup/ioc/chat_phase2.py` (UPDATE)

```python
from app.domain.ports.chat.intent_detection_port import IntentDetectionPort
from app.infrastructure.adapters.chat.hybrid_intent_detection_adapter import (
    HybridIntentDetectionAdapter,
)
from app.infrastructure.adapters.chat.llm_intent_detection_adapter import (
    LLMIntentDetectionAdapter,
)
from app.infrastructure.adapters.chat.keyword_intent_detection_adapter import (
    KeywordIntentDetectionAdapter,
)


class ChatPhase2Provider(Provider):
    scope = Scope.REQUEST

    # NEW: Intent detection adapters
    @provide
    def provide_llm_intent_adapter(
        self,
        llm_gateway: LLMGateway,
    ) -> LLMIntentDetectionAdapter:
        """Provide LLM-based intent detection."""
        return LLMIntentDetectionAdapter(llm_gateway=llm_gateway)

    @provide
    def provide_keyword_intent_adapter(self) -> KeywordIntentDetectionAdapter:
        """Provide keyword-based intent detection."""
        return KeywordIntentDetectionAdapter()

    @provide
    def provide_intent_detection_port(
        self,
        llm_adapter: LLMIntentDetectionAdapter,
        keyword_adapter: KeywordIntentDetectionAdapter,
    ) -> IntentDetectionPort:
        """
        Provide hybrid intent detection (production).

        Uses LLM for accuracy with keyword fallback for reliability.
        """
        return HybridIntentDetectionAdapter(
            llm_adapter=llm_adapter,
            keyword_adapter=keyword_adapter,
            min_llm_confidence=0.7,
        )

    # UPDATED: Intent detector service
    @provide
    def provide_intent_detector_service(
        self,
        intent_detector: IntentDetectionPort,  # Changed from LLMGateway!
    ) -> IntentDetectorService:
        """
        Provide intent detector service.

        Now depends on domain port instead of infrastructure LLM.
        """
        return IntentDetectorService(intent_detector=intent_detector)
```

---

### 4.2 Test Provider

**File**: `src/app/setup/ioc/testing.py` (UPDATE)

```python
from app.infrastructure.adapters.chat.keyword_intent_detection_adapter import (
    KeywordIntentDetectionAdapter,
)


class TestMockProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_mock_intent_detection_port(self) -> IntentDetectionPort:
        """
        Provide mock intent detection for tests.

        Uses keyword adapter (fast, deterministic) instead of LLM.
        """
        return KeywordIntentDetectionAdapter()

    # Delete: provide_mock_llm_client_gateway (no longer needed for intent detection)
```

**Benefits**:
- ✅ No need to mock LLM gateway for intent detection
- ✅ Simpler test setup
- ✅ Faster tests (no async LLM calls)
- ✅ Deterministic results

---

## Phase 5: Testing & Validation (Day 3)

### 5.1 Unit Tests for Adapters

**File**: `tests/unit/infrastructure/adapters/chat/test_intent_detection_adapters.py` (NEW)

```python
import pytest
from app.infrastructure.adapters.chat.keyword_intent_detection_adapter import (
    KeywordIntentDetectionAdapter,
)
from app.domain.ports.chat.intent_detection_port import IntentDetectionRequest


@pytest.mark.asyncio
class TestKeywordIntentDetectionAdapter:
    """Test keyword adapter in isolation."""

    @pytest.fixture
    def adapter(self):
        return KeywordIntentDetectionAdapter()

    async def test_detect_complex_workflow_intent(self, adapter):
        """Should classify complex workflow from keywords."""
        request = IntentDetectionRequest(
            message="Create a complete DeFi investment strategy"
        )

        result = await adapter.detect_intent(request)

        assert result.intent.value == "complex_workflow"
        assert result.confidence >= 0.8
        assert result.handler == "agent_orchestrator"

    async def test_detect_specialist_task_intent(self, adapter):
        """Should classify specialist task from keywords."""
        request = IntentDetectionRequest(
            message="Analyze ETH/USDC liquidity depth"
        )

        result = await adapter.detect_intent(request)

        assert result.intent.value == "specialist_task"
        assert result.handler == "agent_orchestrator"

    async def test_extract_protocol_entity(self, adapter):
        """Should extract protocol name entity."""
        request = IntentDetectionRequest(
            message="Is Aave safe?"
        )

        result = await adapter.detect_intent(request)

        assert result.intent.value == "risk_assessment"
        assert result.entities.get("protocol_name") == "Aave"
```

---

### 5.2 Integration Tests

**Run existing tests**:

```bash
# Should now pass with cleaner architecture
./env/bin/python -m pytest tests/integration/chat/test_unified_chat_with_test_data.py -v

# Expected improvements:
# - squad_spec_001: PASS (keyword adapter detects specialist_task)
# - squad_work_001: PASS (keyword adapter detects complex_workflow)
```

---

### 5.3 Success Criteria

**Checklist**:
- [ ] All 31 existing tests pass
- [ ] Squad tests improve (intent detection works)
- [ ] No regressions in other tests
- [ ] Unit tests for adapters pass
- [ ] Type checking passes
- [ ] Architecture cleaner (verified with diagram)

---

## Phase 6: Documentation (Day 3 - Afternoon)

### Update Architecture Docs

**File**: `docs/architecture/hexagonal-architecture.md` (UPDATE)

```markdown
## Intent Detection

Intent detection follows the hexagonal architecture pattern:

```
Application Layer:
  IntentDetectorService
    ↓ depends on
  IntentDetectionPort (domain interface)

Infrastructure Layer (implementations):
  - LLMIntentDetectionAdapter (uses LLM for accuracy)
  - KeywordIntentDetectionAdapter (fast fallback)
  - HybridIntentDetectionAdapter (LLM + fallback)
```

### Usage

The service automatically uses the configured implementation:

```python
# Production: Hybrid (LLM + keyword fallback)
# Tests: Keyword only (fast, deterministic)
```

No code changes needed to switch implementations - DI handles it.
```

---

## Success Metrics

**Before**:
- ❌ IntentDetectorService → LLMGateway (infrastructure coupling)
- ❌ Hard to mock (need LLM gateway mock)
- ❌ Logic mixed (LLM + keyword in same service)

**After**:
- ✅ IntentDetectorService → IntentDetectionPort (domain port)
- ✅ Easy to mock (single interface, keyword adapter available)
- ✅ Clean separation (adapters contain implementation logic)
- ✅ Hexagonal architecture compliance

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing tests | Run full suite before merging |
| Performance regression | Benchmark intent detection latency |
| Missing edge cases | Copy all test cases from old service |

---

## Next Steps

After completion:
1. ✅ Initiative 3: Document DI Provider Patterns
2. ✅ Re-test squad failures (should pass with keyword adapter)
3. ✅ Monitor production intent detection accuracy

**Expected Test Improvement**: 83.8% → 94.6% (4 squad tests pass)
