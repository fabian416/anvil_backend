# LLM Orchestration System Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Good Coverage  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The LLM Orchestration System has comprehensive test coverage:
- **Unit Tests**: 15+ test files covering orchestration, ranking, agents
- **Component Tests**: Agent Squad intent classification
- **Integration Tests**: Agno agents, retry mechanisms
- **E2E Tests**: API endpoints

**Total Test Files**: 30+ files covering LLM functionality

---

## 1. Existing Unit Tests

### 1.1 LLM Orchestration Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/application/test_llm_dashboard_query.py` | Dashboard query | GetDashboardData |
| `tests/unit/presentation/admin/test_llm_management_controllers.py` | Admin controllers | Ranking, providers |
| `tests/unit/infrastructure/test_llm_gateway_tuple_handling.py` | Gateway handling | Response tuples |
| `tests/unit/infrastructure/test_llm_retry_handler.py` | Retry handler | Backoff, retries |
| `tests/unit/infrastructure/test_agent_gateway_normalization.py` | Gateway normalization | Response format |

---

### 1.2 Intent Classification Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/application/chat/test_intent_orchestrator.py` | Intent orchestrator | Routing decisions |
| `tests/unit/application/chat/test_multi_intent_integration_service.py` | Multi-intent | Complex routing |
| `tests/unit/application/chat/test_multi_intent_response_formatter.py` | Response formatting | Output format |

---

### 1.3 Agent Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/infrastructure/agents/test_lending_borrowing_agent_aave.py` | Aave agent | Lending operations |
| `tests/unit/infrastructure/gateways/test_gateway_implementations.py` | Gateways | LLM gateways |
| `tests/unit/infrastructure/adapters/test_repository_structure.py` | Repositories | Data access |

---

### 1.4 Service Layer Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/application/services/test_service_layer.py` | Service layer | LLM services |
| `tests/unit/application/interactors/test_command_query_interactors.py` | Interactors | Commands/queries |
| `tests/unit/setup/test_ioc_providers.py` | IoC providers | DI configuration |

---

## 2. Existing Component Tests

### 2.1 Agent Squad Component Tests
**Path**: `tests/component/agent_squad/`

| File | Tests | Coverage |
|------|-------|----------|
| `test_intent_classification.py` | Intent classification | Full classification flow |
| `conftest.py` | Fixtures | Test setup |

**Key Tests**:
```python
class TestIntentClassification:
    async def test_swap_intent_detection():
        """Test swap intent is correctly detected."""
        
    async def test_portfolio_intent_detection():
        """Test portfolio intent is correctly detected."""
        
    async def test_low_confidence_fallback():
        """Test fallback to chat agent on low confidence."""
```

---

### 2.2 Framework Validation
**Path**: `tests/component/test_framework_validation.py`

Tests for LLM framework integration.

---

## 3. Existing Integration Tests

### 3.1 Agno Agent Integration Tests
**Path**: `tests/integration/agno/`

| File | Tests | Coverage |
|------|-------|----------|
| `test_agent_retry.py` | Retry mechanisms | Agent retries |
| `test_agent_flags.py` | Feature flags | Agent enable/disable |
| `conftest.py` | Fixtures | Test setup |

**Key Tests**:
```python
class TestAgentRetry:
    async def test_retry_on_transient_error():
        """Test agent retries on transient errors."""
        
    async def test_no_retry_on_permanent_error():
        """Test no retry on permanent errors."""
        
    async def test_backoff_increases():
        """Test exponential backoff."""
```

---

### 3.2 Infrastructure Tests
**Path**: `tests/infrastructure/agno/`

| File | Tests | Coverage |
|------|-------|----------|
| `test_agents.py` | Agent implementations | All Agno agents |

---

## 4. Existing E2E Tests

### 4.1 API Endpoint Tests
**Path**: `tests/e2e/agent_squad/test_api_endpoints.py`

Tests full API workflow for Agent Squad.

**Key Tests**:
```python
class TestAgentSquadAPI:
    async def test_send_message_endpoint():
        """Test sending message to agent squad."""
        
    async def test_get_conversation_context():
        """Test retrieving conversation context."""
        
    async def test_workflow_execution():
        """Test multi-agent workflow execution."""
```

---

## 5. Missing Tests (Gaps Analysis)

### 5.1 Critical Missing Tests

| Area | Missing Test | Priority | Description |
|------|-------------|----------|-------------|
| **Orchestrator** | Unit tests | HIGH | Core orchestration logic |
| **Ranking Engine** | Unit tests | HIGH | Score calculation |
| **Circuit Breaker** | Unit tests | HIGH | State transitions |
| **Telemetry** | Integration tests | MEDIUM | Telemetry collection |
| **Admin Endpoints** | E2E tests | MEDIUM | Full admin workflow |

### 5.2 Missing Orchestrator Tests

```python
# tests/unit/domain/services/llm/test_orchestrator.py (MISSING)

class TestLLMOrchestrator:
    async def test_execute_selects_top_ranked_model():
        """Test orchestrator uses top-ranked model."""
        
    async def test_execute_skips_circuit_breaker_open():
        """Test orchestrator skips models with open circuit breakers."""
        
    async def test_execute_fallback_on_failure():
        """Test fallback to next model on failure."""
        
    async def test_execute_stream_yields_chunks():
        """Test streaming execution yields chunks."""
        
    async def test_no_available_models_error():
        """Test error when all models unavailable."""
        
    async def test_timeout_handling():
        """Test timeout handling and retry."""
```

### 5.3 Missing Ranking Engine Tests

```python
# tests/unit/domain/services/llm/test_ranking_engine.py (MISSING)

class TestRankingEngine:
    def test_calculate_ranking_score():
        """Test ranking score calculation."""
        
    def test_weight_profiles_by_agent_type():
        """Test different weights for different agents."""
        
    def test_latency_score_calculation():
        """Test latency score (lower is better)."""
        
    def test_cost_score_calculation():
        """Test cost score (lower is better)."""
        
    def test_recency_bonus():
        """Test recency bonus for recent usage."""
        
    def test_weights_sum_to_one():
        """Test weight validation."""
```

### 5.4 Missing Circuit Breaker Tests

```python
# tests/unit/domain/services/llm/test_circuit_breaker.py (MISSING)

class TestCircuitBreakerManager:
    def test_closed_state_allows_requests():
        """Test requests allowed when closed."""
        
    def test_open_after_failure_threshold():
        """Test opens after consecutive failures."""
        
    def test_half_open_after_timeout():
        """Test transitions to half-open after timeout."""
        
    def test_closes_after_success_in_half_open():
        """Test closes after success in half-open."""
        
    def test_record_success_resets_failures():
        """Test success resets failure count."""
```

### 5.5 Missing Admin Endpoint Tests

```python
# tests/e2e/admin/test_llm_admin_api.py (MISSING)

class TestLLMAdminAPI:
    async def test_get_dashboard_returns_data(self, client):
        """Test dashboard endpoint returns expected data."""
        
    async def test_get_rankings_for_agent(self, client):
        """Test rankings endpoint for specific agent."""
        
    async def test_recalculate_rankings(self, client):
        """Test manual ranking recalculation."""
        
    async def test_set_ranking_override(self, client):
        """Test setting ranking override."""
        
    async def test_remove_ranking_override(self, client):
        """Test removing ranking override."""
        
    async def test_register_new_model(self, client):
        """Test registering new model."""
        
    async def test_reset_circuit_breaker(self, client):
        """Test circuit breaker reset."""
```

### 5.6 Missing Provider Adapter Tests

```python
# tests/unit/infrastructure/llm/test_vertex_ai_adapter.py (MISSING)

class TestLLMClientVertexAI:
    async def test_classify_intent_returns_json():
        """Test intent classification returns valid JSON."""
        
    async def test_recommend_agents_returns_list():
        """Test agent recommendation returns list."""
        
    async def test_chat_completion():
        """Test chat completion."""
        
    async def test_model_resolution():
        """Test model name resolution."""
        
    async def test_fallback_model_selection():
        """Test fallback to default model."""

# tests/unit/infrastructure/llm/test_deepinfra_adapter.py (MISSING)

class TestLLMClientDeepInfra:
    async def test_generate_text():
        """Test text generation."""
        
    async def test_error_handling():
        """Test error handling."""
```

### 5.7 Missing Celery Task Tests

```python
# tests/integration/celery/test_llm_ranking_tasks.py (MISSING)

class TestLLMRankingTasks:
    def test_recalculate_all_rankings_task():
        """Test ranking recalculation task."""
        
    def test_recalculate_agent_rankings_task():
        """Test agent-specific recalculation."""
        
    def test_cache_llm_response_task():
        """Test response caching task."""
```

---

## 6. Test Commands

### Run All LLM Tests

```bash
# All LLM-related tests
pytest -k "llm or orchestrator or ranking or agent_squad or agno" -v

# Unit tests only
pytest tests/unit -k "llm or orchestrator" -v

# Integration tests
pytest tests/integration/agno/ -v

# E2E tests
pytest tests/e2e/agent_squad/ -v
```

### Run Specific Test Categories

```bash
# Intent classification tests
pytest tests/unit/application/chat/test_intent_orchestrator.py -v

# Agent tests
pytest tests/unit/infrastructure/agents/ -v

# Component tests
pytest tests/component/agent_squad/ -v
```

### Run with Coverage

```bash
pytest tests/ \
  -k "llm or orchestrator or agent_squad" \
  --cov=src/app/domain/services/llm \
  --cov=src/app/infrastructure/adapters/agent_squad \
  --cov=src/app/application/llm \
  --cov-report=html
```

---

## 7. Test Coverage Goals

| Layer | Current | Target | Gap |
|-------|---------|--------|-----|
| Orchestrator | ~20% | 80% | 60% |
| Ranking Engine | ~30% | 80% | 50% |
| Circuit Breaker | ~10% | 75% | 65% |
| Provider Adapters | ~25% | 70% | 45% |
| Admin Endpoints | ~15% | 70% | 55% |
| Agent Squad | ~40% | 75% | 35% |
| Celery Tasks | ~20% | 60% | 40% |

---

## 8. Test Fixtures

### 8.1 Mock LLM Provider
```python
@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    provider = AsyncMock(spec=LLMProviderPort)
    provider.complete.return_value = LLMResponse(
        content="Mock response",
        tokens_used=100,
        model="gemini-1.5-pro",
    )
    return provider
```

### 8.2 Mock Circuit Breaker
```python
@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker manager."""
    manager = MagicMock(spec=CircuitBreakerManager)
    manager.is_open.return_value = False
    return manager
```

### 8.3 Mock Ranking Engine
```python
@pytest.fixture
def mock_ranking_engine():
    """Mock ranking engine."""
    engine = MagicMock(spec=RankingEngine)
    engine.calculate_ranking_score.return_value = Decimal("0.85")
    return engine
```

### 8.4 Test Ranked Models
```python
@pytest.fixture
def test_ranked_models():
    """Test ranked models for orchestrator tests."""
    return [
        RankedModel(
            model_id=uuid4(),
            provider_name="vertex_ai",
            model_name="gemini-1.5-pro",
            display_name="Gemini 1.5 Pro",
            ranking_score=0.95,
            provider_adapter=AsyncMock(),
        ),
        RankedModel(
            model_id=uuid4(),
            provider_name="deepinfra",
            model_name="meta-llama/Meta-Llama-3.1-70B-Instruct",
            display_name="LLaMA 3.1 70B",
            ranking_score=0.85,
            provider_adapter=AsyncMock(),
        ),
    ]
```

---

## 9. Test Markers

```python
# pytest.ini or pyproject.toml markers
markers = [
    "llm: LLM orchestration tests",
    "orchestrator: Orchestrator tests",
    "ranking: Ranking engine tests",
    "agent_squad: Agent squad tests",
    "agno: Agno agent tests",
    "circuit_breaker: Circuit breaker tests",
    "celery: Celery task tests",
]
```

---

## References

- **Unit Tests**: `tests/unit/`
- **Integration Tests**: `tests/integration/agno/`
- **Component Tests**: `tests/component/agent_squad/`
- **E2E Tests**: `tests/e2e/agent_squad/`
- **Test Fixtures**: `tests/fixtures/`
