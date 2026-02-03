# Context-Aware Agents Test Specification

> **Spec Version:** 2.0  
> **Status:** Active  
> **Created:** 2026-01-24  
> **Updated:** 2026-01-24  
> **Authors:** @qa-automation-engineer @test-automation-expert  
> **Related:** [requirements.md](./requirements.md)

---

## Executive Summary

This specification defines a comprehensive **Test Strategy** for:
1. **Existing E2E Test Suite** - All authenticated user tests in `tests/integration/user/`
2. **Context-Aware Agent Tests** - New tests for the context-aware system

All tests require **JWT access tokens** via the `TokenManager` class in `conftest.py`.

---

## 1. Existing Test Infrastructure Analysis

### 1.1 Token Management (conftest.py)

All authenticated tests use `TokenManager` which provides tokens via:
1. **Environment variable**: `JWT_TEST_TOKEN`
2. **API Login**: `/api/v1/account/login`
3. **Database session creation**: Direct DB insertion

```python
# Token retrieval priority
token_info = await TokenManager.get_token(client)
client.headers["Authorization"] = token_info.authorization_header
```

**Key Fixtures:**
- `auth_token` - Provides `TokenInfo` with valid JWT
- `authenticated_client` - HTTP client with auth headers
- `conversation_id` - Creates conversation for testing
- `csv_reporter` - Generates CSV test reports

### 1.2 Current Test Directory Structure

```
tests/integration/user/                    # 43 test files
├── conftest.py                            # Shared fixtures & TokenManager
├── test_runner.py                         # Comprehensive test runner
│
├── agents/                                # Agent-specific tests
│   ├── test_all_agents_comprehensive.py   # 27 agents, 100+ test cases
│   ├── test_agent_squad_advanced.py       # Advanced agent tests
│   ├── test_hunter_ai.py                  # Hunter AI tests
│   ├── test_hunter_advanced.py            # Advanced Hunter tests
│   ├── test_defi_yield.py                 # DeFi Yield agent
│   ├── test_portfolio.py                  # Portfolio agent
│   └── test_execution_agent.py            # Execution agent
│
├── workflows/                             # Workflow tests
│   ├── test_swap_workflow.py              # Swap tests + LLM validation
│   ├── test_buy_workflow.py               # Buy workflow
│   ├── test_lending_workflow.py           # Lending workflow
│   ├── test_transfer_workflow.py          # Transfer workflow
│   ├── test_money_market_workflow.py      # Money market workflow
│   ├── test_cross_chain_workflow.py       # Cross-chain operations
│   ├── test_protocol_specific.py          # Protocol-specific tests
│   └── test_cancellation_flows.py         # Workflow cancellation
│
├── multi_step/                            # Multi-step conversation tests
│   ├── test_confirmation_flows.py         # Confirmation flows
│   ├── test_modification_flows.py         # Workflow modifications
│   └── test_cancellation_flows.py         # Cancellation flows
│
├── multilingual/                          # Multi-language tests
│   ├── test_spanish.py                    # Spanish (es)
│   ├── test_portuguese.py                 # Portuguese (pt)
│   ├── test_chinese.py                    # Chinese (zh)
│   └── test_mixed_language.py             # Mixed language
│
├── authenticated/                         # Auth flow tests
│   ├── test_authenticated_chat_comprehensive.py
│   ├── test_authenticated_chat_integration.py
│   ├── test_conversation_lifecycle.py
│   └── test_archive_conversation.py
│
├── edge_cases/                            # Edge case tests
│   ├── test_complex_inputs.py
│   ├── test_error_handling.py
│   └── test_user_errors.py
│
├── errors/
│   └── test_user_error_handling.py
│
└── [standalone test files]
    ├── test_user_shortcuts_examples.py
    ├── test_user_hunter_advanced.py
    ├── test_user_ultra_advanced.py
    ├── test_user_agent_squad_advanced.py
    └── test_profile_management.py
```

---

## 2. E2E Test Inventory (Existing)

### 2.1 Agent Tests (test_all_agents_comprehensive.py)

**Total: 100+ test cases across 27 agents**

#### Core Agents (12)
| Agent | Test IDs | Test Count | Coverage |
|-------|----------|------------|----------|
| `chat` | chat_001-004 | 4 | Greetings, creative |
| `knowledge` | knowledge_001-004 | 4 | DeFi education |
| `hunter_ai` | hunter_001-010 | 10 | Price, sentiment, news |
| `risk_analyzer` | risk_001-002 | 2 | Protocol risk |
| `defi_yield` | yield_001-003 | 3 | Yield opportunities |
| `gas_optimizer` | gas_001-003 | 3 | Gas optimization |
| `portfolio` | portfolio_001-003 | 3 | Portfolio queries |
| `wallet` | wallet_001-003 | 3 | Wallet queries |
| `transaction_history` | history_001-003 | 3 | Transaction history |
| `research` | research_001-003 | 3 | Protocol research |

#### Workflow Agents (5)
| Agent | Test IDs | Test Count | Multi-step |
|-------|----------|------------|------------|
| `swap_workflow` | swap_001-003 | 3 | YES |
| `lending_workflow` | lending_001-003 | 3 | YES |
| `buy_workflow` | buy_001-003 | 3 | YES |
| `transfer_workflow` | transfer_001-003 | 3 | YES |
| `money_market_workflow` | mm_001-005 | 5 | NO |

#### Complex Queries (Multi-Agent)
| Test ID | Expected Agents | Scenario |
|---------|-----------------|----------|
| complex_001 | hunter_ai, risk_analyzer | Arbitrage opportunities |
| complex_002 | portfolio, hunter_ai | Rebalancing advice |
| complex_003 | defi_yield, risk_analyzer | Low-risk yield |
| complex_004-010 | hunter_ai, various | Advanced analysis |

### 2.2 Workflow Tests (Individual Files)

#### test_swap_workflow.py
```python
SWAP_TESTS = [
    # Basic Swaps (5 tests)
    "swap_basic_001": "swap 1 ETH to USDC"
    "swap_basic_002": "exchange 100 USDC for ETH"
    "swap_basic_003": "convert 0.5 ETH to DAI"
    "swap_basic_004": "swap 500 USDC to WBTC"
    "swap_basic_005": "trade 1000 USDT for USDC"
    
    # Swap Quotes (3 tests)
    "swap_quote_001": "get quote for 1 ETH to USDC"
    "swap_quote_002": "how much USDC for 1 ETH"
    "swap_quote_003": "best rate ETH to USDC"
    
    # Cross-Chain (3 tests)
    "swap_cross_001": "swap ETH from Ethereum to Base"
    "swap_cross_002": "bridge USDC from Arbitrum to Ethereum"
    "swap_cross_003": "transfer ETH to polygon"
    
    # Edge Cases (2 tests)
    "swap_edge_001": "swap ETH"
    "swap_edge_002": "swap"
]
```

#### test_buy_workflow.py
- Basic buy flows (buy_001-004)
- Buy with fiat (buy_fiat_001-003)
- Multi-step buy confirmation

#### test_lending_workflow.py
- Deposit flows (lend_001-004)
- Protocol-specific (Aave, Morpho, Compound)
- Withdrawal flows

#### test_transfer_workflow.py
- Basic transfers (transfer_001-004)
- Address validation
- Amount validation

#### test_money_market_workflow.py
- Rate comparisons (mm_001-006)
- Protocol selection
- Best rate recommendations

### 2.3 Multi-Step Tests (test_confirmation_flows.py)

```python
CONFIRMATION_FLOWS = [
    {
        "test_id": "confirm_swap_001",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
    },
    {
        "test_id": "confirm_lend_001",
        "steps": [
            {"input": "deposit 1000 USDC", "expect_agent": "lending_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
    },
    {
        "test_id": "confirm_transfer_001",
        "steps": [
            {"input": "send 100 USDC to 0x...", "expect_agent": "transfer_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
    },
    {
        "test_id": "confirm_buy_001",
        "steps": [
            {"input": "buy $100 of ETH", "expect_agent": "buy_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
    },
]
```

### 2.4 Multilingual Tests

| Language | Test File | Test Count | Sample Query |
|----------|-----------|------------|--------------|
| Spanish (es) | test_spanish.py | 5+ | "precio de bitcoin" |
| Portuguese (pt) | test_portuguese.py | 5+ | "preço do bitcoin" |
| Chinese (zh) | test_chinese.py | 3+ | "比特币价格" |
| Mixed | test_mixed_language.py | Various | Mixed inputs |

### 2.5 Edge Case Tests

#### test_complex_inputs.py
- Very long inputs (1000+ chars)
- Special characters
- Unicode inputs
- Malformed queries

#### test_error_handling.py
- Invalid conversation IDs
- Expired tokens
- Rate limiting
- Server errors

---

## 3. New Context-Aware Test Structure

### 3.1 Directory Addition

```
tests/
├── unit/
│   └── context_aware/                     # NEW: Unit tests
│       ├── __init__.py
│       ├── test_portfolio_state.py
│       ├── test_activity_level.py
│       ├── test_user_type.py
│       ├── test_user_context_entity.py
│       ├── test_response_template.py
│       └── test_analytics_entities.py
│
└── integration/
    └── user/
        └── context_aware/                 # NEW: Integration tests
            ├── __init__.py
            ├── test_user_context_service.py
            ├── test_response_templates.py
            ├── test_analytics_repository.py
            ├── test_context_routing.py
            ├── test_workflow_blocking.py
            └── test_admin_analytics_api.py
```

### 3.2 Context-Aware E2E Test Cases

#### Portfolio State Tests
| Test ID | Portfolio State | Input | Expected Behavior |
|---------|-----------------|-------|-------------------|
| ctx_empty_001 | EMPTY | "swap 1 ETH" | Blocked + buy suggestion |
| ctx_empty_002 | EMPTY | "my portfolio" | Empty message + buy CTA |
| ctx_empty_003 | EMPTY | "buy $100 ETH" | Allowed |
| ctx_starter_001 | STARTER | "swap 50 USDC" | Gas warning |
| ctx_active_001 | ACTIVE | "swap 1 ETH" | Allowed |
| ctx_whale_001 | WHALE | "swap 10 ETH" | No warnings |

#### Activity Level Tests
| Test ID | Activity Level | Expected Response Style |
|---------|----------------|------------------------|
| ctx_new_001 | NEW | Onboarding flow |
| ctx_active_001 | ACTIVE | Concise responses |
| ctx_inactive_001 | INACTIVE | Reengagement prompt |
| ctx_reactivated_001 | REACTIVATED | Welcome back message |

#### User Type Tests
| Test ID | User Type | Input | Expected Agent Priority |
|---------|-----------|-------|------------------------|
| ctx_trader_001 | TRADER | "swap" | swap_workflow priority |
| ctx_yield_001 | YIELD_FARMER | "best rates" | defi_yield priority |
| ctx_casual_001 | CASUAL | "help" | Educational response |

### 3.3 Admin Analytics API Tests

```python
ADMIN_ANALYTICS_ENDPOINTS = [
    # Distribution Endpoints
    {"method": "GET", "path": "/admin/analytics/users/distribution", "auth": "admin"},
    {"method": "GET", "path": "/admin/analytics/users/summary", "auth": "admin"},
    
    # Snapshot Endpoints
    {"method": "GET", "path": "/admin/analytics/snapshots/latest", "auth": "admin"},
    {"method": "GET", "path": "/admin/analytics/snapshots/history", "auth": "admin"},
    {"method": "GET", "path": "/admin/analytics/snapshots/date/{date}", "auth": "admin"},
    
    # Trend Endpoints
    {"method": "GET", "path": "/admin/analytics/trends/week-over-week", "auth": "admin"},
    {"method": "GET", "path": "/admin/analytics/trends/month-over-month", "auth": "admin"},
    {"method": "GET", "path": "/admin/analytics/trends/custom", "auth": "admin"},
    
    # Totals Endpoint
    {"method": "GET", "path": "/admin/analytics/totals", "auth": "admin"},
]
```

---

## 4. Test Fixtures for Context-Aware Tests

### 4.1 User Context Fixtures

Add to `tests/integration/user/conftest.py`:

```python
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, UTC

from app.domain.chat.entities.user_context_aware import UserContextAware


# ============================================================
# User Context Fixtures
# ============================================================

@pytest.fixture
def empty_user_context() -> UserContextAware:
    """User with empty portfolio ($0)."""
    return UserContextAware(
        id=uuid4(),
        chat_user_id=uuid4(),
        portfolio_state="empty",
        activity_level="new",
        user_type="new_user",
        total_balance_usd=Decimal("0"),
        wallet_total_usd=Decimal("0"),
    )


@pytest.fixture
def starter_user_context() -> UserContextAware:
    """User with starter portfolio ($50)."""
    return UserContextAware(
        id=uuid4(),
        chat_user_id=uuid4(),
        portfolio_state="starter",
        activity_level="active",
        user_type="casual",
        total_balance_usd=Decimal("50.00"),
        wallet_total_usd=Decimal("50.00"),
    )


@pytest.fixture
def active_user_context() -> UserContextAware:
    """User with active portfolio ($5000)."""
    return UserContextAware(
        id=uuid4(),
        chat_user_id=uuid4(),
        portfolio_state="active",
        activity_level="very_active",
        user_type="trader",
        total_balance_usd=Decimal("5000.00"),
        wallet_total_usd=Decimal("5000.00"),
        swap_count=50,
    )


@pytest.fixture
def whale_user_context() -> UserContextAware:
    """User with whale portfolio ($50000+)."""
    return UserContextAware(
        id=uuid4(),
        chat_user_id=uuid4(),
        portfolio_state="whale",
        activity_level="very_active",
        user_type="power_user",
        total_balance_usd=Decimal("50000.00"),
        wallet_total_usd=Decimal("50000.00"),
        swap_count=100,
        lending_count=50,
    )


@pytest.fixture
def inactive_user_context() -> UserContextAware:
    """Inactive user (no sessions in 30d)."""
    return UserContextAware(
        id=uuid4(),
        chat_user_id=uuid4(),
        portfolio_state="active",
        activity_level="inactive",
        user_type="casual",
        total_balance_usd=Decimal("1000.00"),
        chat_sessions_30d=0,
    )


# ============================================================
# Response Template Service Fixture
# ============================================================

@pytest.fixture
def response_template_service():
    """Provide ResponseTemplateService instance."""
    from app.application.chat.services.response_template_service import ResponseTemplateService
    return ResponseTemplateService()
```

### 4.2 Admin Token Fixture

```python
@pytest.fixture(scope="module")
def admin_token(token_manager: TokenManager) -> TokenInfo:
    """
    Get an admin authentication token.
    
    Requires admin user credentials in environment.
    """
    import os
    admin_email = os.environ.get("ADMIN_TEST_EMAIL", "admin@anvilcrypto.com")
    admin_password = os.environ.get("ADMIN_TEST_PASSWORD")
    
    if not admin_password:
        pytest.skip("Admin credentials not configured")
    
    # Override test user for admin
    original_email = os.environ.get("TEST_USER_EMAIL")
    os.environ["TEST_USER_EMAIL"] = admin_email
    os.environ["TEST_USER_PASSWORD"] = admin_password
    
    try:
        TokenManager.clear_cache()
        return asyncio.get_event_loop().run_until_complete(token_manager.get_token())
    finally:
        if original_email:
            os.environ["TEST_USER_EMAIL"] = original_email
```

---

## 5. Test Execution

### 5.1 Run All Existing E2E Tests

```bash
# All user integration tests
JWT_TEST_TOKEN=<token> pytest tests/integration/user/ -v

# Specific category
JWT_TEST_TOKEN=<token> pytest tests/integration/user/workflows/ -v
JWT_TEST_TOKEN=<token> pytest tests/integration/user/agents/ -v
JWT_TEST_TOKEN=<token> pytest tests/integration/user/multi_step/ -v

# With CSV output
JWT_TEST_TOKEN=<token> pytest tests/integration/user/test_runner.py -v
```

### 5.2 Run Context-Aware Tests

```bash
# Unit tests (no token required)
pytest tests/unit/context_aware/ -v

# Integration tests (requires token)
JWT_TEST_TOKEN=<token> pytest tests/integration/user/context_aware/ -v

# Admin analytics tests (requires admin token)
ADMIN_TEST_EMAIL=admin@example.com ADMIN_TEST_PASSWORD=xxx \
pytest tests/integration/user/context_aware/test_admin_analytics_api.py -v
```

### 5.3 Full Test Suite

```bash
# Complete test run with reports
make code.test

# Or manually with coverage
JWT_TEST_TOKEN=<token> pytest tests/ -v --cov=src/app --cov-report=html
```

---

## 6. CSV Output Format

All tests generate CSV reports in `tests/output/user/`:

| Field | Description |
|-------|-------------|
| `test_id` | Unique test identifier |
| `timestamp` | ISO timestamp |
| `category` | Test category (workflow, agent, etc.) |
| `subcategory` | Sub-category (swap, buy, etc.) |
| `is_multi_step` | YES/NO |
| `step_number` | Step number for multi-step |
| `total_steps` | Total steps in flow |
| `input` | User input |
| `output` | Agent response (truncated) |
| `expected_agent` | Expected agent name |
| `actual_agents` | Actual agents used |
| `sources` | Data sources used |
| `handler` | Handler name |
| `response_time_ms` | Response time |
| `has_execute_data` | YES/NO |
| `execute_action_type` | Action type if execute |
| `user_type` | authenticated/guest |
| `language` | Language code |
| `status` | PASS/PARTIAL/FAIL |
| `error_message` | Error if any |
| `conversation_id` | Conversation UUID |
| `llm_verdict` | LLM validation result |
| `llm_confidence` | LLM confidence score |
| `llm_reasoning` | LLM reasoning |

---

## 7. Implementation Plan

### Phase 1: Unit Tests (2 days)
- [ ] `test_portfolio_state.py` - Classification tests
- [ ] `test_activity_level.py` - Activity calculation
- [ ] `test_user_type.py` - User type inference
- [ ] `test_user_context_entity.py` - Entity methods
- [ ] `test_response_template.py` - Template rendering

### Phase 2: Integration Tests (3 days)
- [ ] `test_user_context_service.py` - Service tests
- [ ] `test_response_templates.py` - Template service
- [ ] `test_analytics_repository.py` - Repository tests
- [ ] `test_admin_analytics_api.py` - API endpoints

### Phase 3: Context Routing Tests (2 days)
- [ ] `test_context_routing.py` - Routing logic
- [ ] `test_workflow_blocking.py` - Blocking rules

### Phase 4: E2E Integration (1 day)
- [ ] Update `conftest.py` with new fixtures
- [ ] Add context-aware test cases to existing test files
- [ ] Verify CSV output includes context data

---

## 8. Coverage Targets

| Component | Current | Target |
|-----------|---------|--------|
| Existing E2E Tests | 100% | 100% |
| `PortfolioState` | 0% | 100% |
| `ActivityLevel` | 0% | 100% |
| `UserType` | 0% | 100% |
| `UserContextAware` | 0% | 90% |
| `ResponseTemplateService` | 0% | 90% |
| `AnalyticsRepository` | 0% | 80% |
| Admin Analytics API | 0% | 75% |

---

## References

- [Context-Aware Requirements](./requirements.md)
- [Test Runner](../../../tests/integration/user/test_runner.py)
- [Conftest](../../../tests/integration/user/conftest.py)
- [QA Automation Engineer](/.claude/agents/automation/qa-automation-engineer.md)
- [Test Automation Expert](/.claude/agents/testing/test-automation-expert.md)
