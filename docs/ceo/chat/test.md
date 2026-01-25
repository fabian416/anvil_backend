# Chat System Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Chat System has comprehensive test coverage across multiple test types:
- **Unit Tests**: 15+ files testing individual services and components
- **Component Tests**: 9+ files testing integrated components
- **Integration Tests**: 30+ files testing full system flows
- **E2E Tests**: 1+ files testing complete user journeys
- **Security Tests**: 2+ files testing security aspects

**Total Test Files**: 55+ (126 files when including all chat-related tests)

---

## 1. Unit Tests

### 1.1 Application Layer Tests

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/unit/application/chat/test_intent_detector_v2_multi_intent.py` | Multi-intent detection | IntentDetectorV2 |
| `tests/unit/application/chat/test_intent_orchestrator.py` | Intent orchestration | IntentOrchestrator |
| `tests/unit/application/chat/test_multi_intent_integration_service.py` | Multi-intent integration | MultiIntentIntegrationService |
| `tests/unit/application/chat/test_multi_intent_response_formatter.py` | Response formatting | MultiIntentResponseFormatter |
| `tests/unit/application/chat/services/test_flow_cancellation_detector.py` | Flow cancellation | FlowCancellationDetector |
| `tests/unit/application/test_guest_money_market_handler.py` | Guest money market | MoneyMarketHandler (guest) |

### 1.2 Domain Layer Tests

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/unit/domain/entities/test_conversation.py` | Conversation entity | Conversation model |
| `tests/unit/domain/entities/test_message.py` | Message entity | Message model |
| `tests/unit/domain/entities/chat/test_performance_metrics.py` | Performance metrics | PerformanceMetrics |
| `tests/unit/domain/value_objects/test_message_role.py` | Message roles | MessageRole enum |
| `tests/unit/domain/value_objects/chat/test_multi_intent_result.py` | Multi-intent result | MultiIntentResult |

### 1.3 Presentation Layer Tests

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/unit/presentation/chat/test_chat_controllers.py` | Chat controllers | Controller structure |
| `tests/unit/presentation/controllers/test_chat_controllers.py` | Controller validation | Request/response |

### 1.4 Infrastructure Layer Tests

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/unit/infrastructure/adapters/chat/test_redis_intent_cache_adapter.py` | Intent caching | RedisIntentCacheAdapter |

---

## 2. Component Tests

**Directory**: `tests/component/chat/`

| Test File | Purpose | Components Tested |
|-----------|---------|-------------------|
| `test_chat_component.py` | Core chat flow | ConversationService, MessageHandling |
| `test_conversation_lifecycle.py` | Conversation CRUD | Create, Update, Archive, Delete |
| `test_message_handling.py` | Message processing | Intent detection, routing |
| `test_hunter_component.py` | Hunter AI integration | HunterAIAgent, price checks |
| `test_ultra_component.py` | ULTRA research | ULTRAAgent, research queries |
| `test_squad_component.py` | Agent Squad | SupervisorCoordinator |
| `test_graphrag_component.py` | GraphRAG integration | Knowledge graph queries |

### Component Test Factories

**File**: `tests/component/factories/chat_factories.py`

Provides factory functions for creating test data:
- `create_test_conversation()`
- `create_test_message()`
- `create_test_user()`

---

## 3. Integration Tests

### 3.1 User Chat Integration

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/integration/user/authenticated/test_authenticated_chat_integration.py` | Basic auth flow | Authentication, routing |
| `tests/integration/user/authenticated/test_authenticated_chat_comprehensive.py` | Full auth scenarios | All authenticated features |
| `tests/integration/user/workflows/test_swap_workflow_hyperliquid.py` | Swap workflow | Hyperliquid integration |

### 3.2 Guest Chat Integration

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/integration/guest/test_guest_chat_knowledge_research.py` | Knowledge queries | Research, education |
| `tests/integration/guest/test_guest_chat_historial_real.py` | Historical data | Price history |
| `tests/integration/guest/test_guest_chat_hunter_real.py` | Hunter AI (real) | Live price data |
| `tests/integration/guest/test_guest_chat_ultra_real.py` | ULTRA (real) | Live research |
| `tests/integration/guest/test_guest_chat_agent_squad_real.py` | Agent Squad | Full squad integration |
| `tests/integration/guest/test_guest_chat_shortcuts.py` | Shortcuts | Quick commands |
| `tests/integration/guest/test_guest_chat_and_shortcuts_real.py` | Combined | Shortcuts + chat |

### 3.3 Guest General Integration

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/integration/guest/general/test_hunter_chat_integration.py` | Hunter chat | Price queries |
| `tests/integration/guest/general/test_historical_chat_advanced.py` | Historical advanced | Complex queries |
| `tests/integration/guest/general/test_historical_chat_data_integrity.py` | Data integrity | Response validation |
| `tests/integration/guest/general/test_historical_chat_advanced_scenarios.py` | Edge scenarios | Error handling |
| `tests/integration/guest/general/test_historical_chat_edge_cases.py` | Edge cases | Boundary conditions |
| `tests/integration/guest/general/test_unified_chat_with_test_data.py` | Unified chat | Test data scenarios |
| `tests/integration/guest/general/test_unified_chat_critical_paths.py` | Critical paths | Core flows |
| `tests/integration/guest/general/test_ultra_chat_integration.py` | ULTRA integration | Research queries |
| `tests/integration/guest/general/test_user_chat_messages.py` | Message handling | Message CRUD |
| `tests/integration/guest/general/test_guest_chat_parity.py` | Parity testing | Guest vs auth |
| `tests/integration/guest/general/test_guest_chat_comprehensive.py` | Comprehensive | All guest features |

### 3.4 WebSocket Integration

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/integration/websocket/test_websocket_chat.py` | WebSocket | Real-time messaging |

### 3.5 Workflow Integration

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/integration/workflows/test_chat_workflow.py` | Multi-step workflows | Swap, lending, etc. |

### 3.6 Database Integration

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/integration/database/test_conversation_repository_integration.py` | Repository | CRUD operations |

### 3.7 AI Adapter Integration

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/integration/infrastructure/adapters/ai/test_anthropic_chat_adapter.py` | Anthropic | Claude integration |
| `tests/integration/infrastructure/adapters/ai/test_openai_chat_adapter.py` | OpenAI | GPT integration |

---

## 4. E2E Tests

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/e2e/endpoints/test_chat_endpoints_e2e.py` | Complete user journey | Full API flow |

---

## 5. Security Tests

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `tests/security/test_authenticated_chat_security.py` | Auth security | Token validation, access control |
| `tests/security/auth/test_auth_security.py` | Auth flows | Session management |

---

## 6. Missing Tests (Gaps Analysis)

### 6.1 Critical Missing Tests

| Area | Missing Test | Priority | Description |
|------|-------------|----------|-------------|
| **SwapHandlerV2** | Unit tests | HIGH | Test Hyperliquid routing logic |
| **MoneyMarketHandler** | Integration tests | HIGH | Test deposit/withdraw flows |
| **AdminAnalyticsService** | Unit tests | MEDIUM | Test metrics aggregation |
| **RateLimitService** | Integration tests | HIGH | Test rate limiting enforcement |
| **ConversationMemory** | Unit tests | MEDIUM | Test context building |
| **UserContextService** | Integration tests | MEDIUM | Test context-aware routing |

### 6.2 Missing Unit Tests

```python
# Recommended new test files:

# 1. tests/unit/application/chat/handlers/test_swap_handler_v2.py
class TestSwapHandlerV2:
    def test_hyperliquid_routing_meme_tokens()
    def test_error_message_for_unsupported_tokens()
    def test_multi_turn_swap_flow()
    def test_execute_data_generation()

# 2. tests/unit/application/chat/handlers/test_money_market_handler.py
class TestMoneyMarketHandler:
    def test_morpho_deposit_flow()
    def test_aave_deposit_flow()
    def test_apy_comparison()

# 3. tests/unit/application/chat/services/test_admin_analytics_service.py
class TestAdminAnalyticsService:
    def test_dashboard_summary()
    def test_agent_performance_metrics()
    def test_cost_tracking()
    def test_error_monitoring()

# 4. tests/unit/application/chat/services/test_rate_limit_service.py
class TestRateLimitService:
    def test_hourly_limit_enforcement()
    def test_daily_limit_enforcement()
    def test_limit_reset()
    def test_different_user_tiers()

# 5. tests/unit/application/chat/services/test_conversation_memory.py
class TestConversationMemory:
    def test_context_building()
    def test_pending_action_detection()
    def test_workflow_state_tracking()
```

### 6.3 Missing Integration Tests

```python
# Recommended new test files:

# 1. tests/integration/chat/test_rate_limiting_integration.py
class TestRateLimitingIntegration:
    def test_guest_rate_limit_enforcement()
    def test_authenticated_rate_limit_by_tier()
    def test_rate_limit_headers_in_response()

# 2. tests/integration/chat/test_admin_dashboard_integration.py
class TestAdminDashboardIntegration:
    def test_dashboard_endpoint_access()
    def test_agent_performance_endpoint()
    def test_cost_tracking_endpoint()
    def test_export_functionality()

# 3. tests/integration/chat/test_workflow_continuation.py
class TestWorkflowContinuation:
    def test_swap_confirmation_flow()
    def test_swap_cancellation_flow()
    def test_swap_modification_flow()
    def test_lending_multi_step_flow()

# 4. tests/integration/celery/test_chat_celery_tasks.py
class TestChatCeleryTasks:
    def test_archive_guest_conversations()
    def test_update_agent_stats()
    def test_user_context_update()
```

### 6.4 Missing E2E Tests

```python
# 1. tests/e2e/chat/test_guest_to_authenticated_journey.py
class TestGuestToAuthenticatedJourney:
    def test_guest_swap_prompts_registration()
    def test_guest_can_view_prices()
    def test_authenticated_can_execute_swap()

# 2. tests/e2e/chat/test_full_swap_journey.py
class TestFullSwapJourney:
    def test_swap_from_request_to_execution()
    def test_swap_with_modification()
    def test_swap_cancellation()
```

---

## 7. Test Commands

### Run All Chat Tests

```bash
# All chat-related tests
pytest tests/ -k "chat" -v

# Component tests only
pytest tests/component/chat/ -v

# Integration tests only
pytest tests/integration/ -k "chat" -v

# Unit tests only
pytest tests/unit/ -k "chat" -v
```

### Run Specific Test Categories

```bash
# Guest tests
pytest tests/integration/guest/ -v

# Authenticated user tests
pytest tests/integration/user/authenticated/ -v

# Workflow tests
pytest tests/integration/workflows/ -v

# Security tests
pytest tests/security/ -k "chat" -v
```

### Run with Coverage

```bash
# Coverage for chat module
pytest tests/ -k "chat" --cov=src/app/application/chat --cov-report=html

# Coverage report location
open htmlcov/index.html
```

---

## 8. Test Coverage Goals

| Layer | Current | Target | Gap |
|-------|---------|--------|-----|
| Domain | ~85% | 90% | 5% |
| Application | ~70% | 80% | 10% |
| Infrastructure | ~60% | 70% | 10% |
| Presentation | ~65% | 75% | 10% |

---

## 9. Test Data Management

### Test Fixtures

**Location**: `tests/fixtures/`

| File | Purpose |
|------|---------|
| `domain_factories.py` | Domain entity factories |
| `mock_services.py` | Mock service implementations |

### Component Fixtures

**Location**: `tests/component/`

| File | Purpose |
|------|---------|
| `conftest.py` | Shared component fixtures |
| `mocks/gateways.py` | Mock gateway implementations |
| `mocks/repositories.py` | Mock repository implementations |

---

## 10. Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to `main`/`master`
- Pull requests

**Workflow**: `.github/workflows/test.yml`

```yaml
- name: Run Chat Tests
  run: |
    pytest tests/ -k "chat" -v --tb=short
```

---

## References

- **Test Directory**: `tests/`
- **Pytest Config**: `pyproject.toml`
- **Coverage Config**: `.coveragerc`
- **CI Workflow**: `.github/workflows/`
