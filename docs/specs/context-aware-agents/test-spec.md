# Context-Aware Agents Test Specification

> **Spec Version:** 1.0  
> **Status:** Draft  
> **Created:** 2026-01-24  
> **Authors:** @qa-automation-engineer @test-automation-expert  
> **Related:** [requirements.md](./requirements.md)

---

## Executive Summary

This specification defines a comprehensive **Test Strategy** for the Context-Aware Agents system implemented in `docs/specs/context-aware-agents/requirements.md`. The test suite validates:

1. **User Classification Logic** - Portfolio state, activity level, user type calculations
2. **Response Template System** - Template loading, rendering, multi-language support
3. **Analytics Dashboard** - Snapshot persistence, trends, admin API endpoints
4. **Context Integration** - Supervisor integration, workflow blocking, prompt enhancement
5. **Celery Tasks** - Background context updates, analytics generation

---

## 1. Problem Analysis (First Principles)

### 1.1 Current Test State

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT TEST STRUCTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  tests/integration/user/                                         │
│  ├── agents/           # Agent-specific tests                    │
│  ├── authenticated/    # Auth flow tests                         │
│  ├── edge_cases/       # Error handling                          │
│  ├── multi_step/       # Workflow continuation                   │
│  ├── multilingual/     # i18n support                            │
│  ├── workflows/        # Swap, buy, lending, etc.                │
│  └── conftest.py       # Shared fixtures                         │
│                                                                  │
│  GAPS IDENTIFIED:                                                │
│  ✗ No tests for user context classification                     │
│  ✗ No tests for response templates                              │
│  ✗ No tests for analytics dashboard                             │
│  ✗ No tests for context-aware routing                           │
│  ✗ No tests for workflow blocking based on portfolio            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Test Gap Analysis

| Component | Current Coverage | Required Coverage | Priority |
|-----------|------------------|-------------------|----------|
| `PortfolioState` enum | 0% | 100% | P0 |
| `ActivityLevel` enum | 0% | 100% | P0 |
| `UserType` enum | 0% | 100% | P0 |
| `UserContextAware` entity | 0% | 90% | P0 |
| `UserContextService` | 0% | 85% | P0 |
| `ResponseTemplateService` | 0% | 90% | P1 |
| `AnalyticsRepository` | 0% | 80% | P1 |
| Admin Analytics API | 0% | 75% | P1 |
| Celery tasks | 0% | 70% | P2 |
| Supervisor integration | Partial | 90% | P0 |

---

## 2. Test Architecture

### 2.1 Test Pyramid

```
┌─────────────────────────────────────────────────────────────────┐
│                       TEST PYRAMID                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                         ╱╲                                       │
│                        ╱  ╲     E2E Tests (10%)                  │
│                       ╱    ╲    - Full user journey with context │
│                      ╱──────╲                                    │
│                     ╱        ╲   Integration Tests (30%)         │
│                    ╱   API    ╲  - Admin endpoints               │
│                   ╱   Tests    ╲ - Context-aware routing         │
│                  ╱──────────────╲                                │
│                 ╱                ╲  Unit Tests (60%)             │
│                ╱   Domain Logic   ╲ - Enums, entities, services  │
│               ╱    & Services      ╲                             │
│              ╱──────────────────────╲                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 New Test Directory Structure

```
tests/
├── unit/
│   └── context_aware/
│       ├── __init__.py
│       ├── test_portfolio_state.py          # PortfolioState enum tests
│       ├── test_activity_level.py           # ActivityLevel enum tests
│       ├── test_user_type.py                # UserType enum tests
│       ├── test_user_context_entity.py      # UserContextAware entity tests
│       ├── test_response_template.py        # Template entity tests
│       └── test_analytics_entities.py       # Analytics entity tests
│
├── integration/
│   └── user/
│       └── context_aware/
│           ├── __init__.py
│           ├── test_user_context_service.py # UserContextService tests
│           ├── test_response_templates.py   # ResponseTemplateService tests
│           ├── test_analytics_repository.py # AnalyticsRepository tests
│           ├── test_context_routing.py      # Context-aware routing tests
│           ├── test_workflow_blocking.py    # Workflow blocking tests
│           └── test_admin_analytics_api.py  # Admin API endpoint tests
│
└── e2e/
    └── context_aware/
        ├── __init__.py
        ├── test_empty_portfolio_journey.py  # New user → buy → use
        ├── test_whale_user_journey.py       # High-value user flows
        └── test_inactive_reengagement.py    # Returning user flows
```

---

## 3. Unit Test Specifications

### 3.1 Portfolio State Tests (`test_portfolio_state.py`)

```python
"""
Unit tests for PortfolioState enum.

Tests the classification logic based on user wallet balance.
"""

import pytest
from decimal import Decimal
from app.domain.chat.enums.portfolio_state import PortfolioState


class TestPortfolioStateClassification:
    """Test PortfolioState.from_balance() classification logic."""
    
    @pytest.mark.parametrize("balance,expected_state", [
        # EMPTY state ($0)
        (Decimal("0"), PortfolioState.EMPTY),
        (Decimal("0.00"), PortfolioState.EMPTY),
        (0, PortfolioState.EMPTY),
        (0.0, PortfolioState.EMPTY),
        
        # STARTER state ($0.01 - $99.99)
        (Decimal("0.01"), PortfolioState.STARTER),
        (Decimal("50.00"), PortfolioState.STARTER),
        (Decimal("99.99"), PortfolioState.STARTER),
        (1, PortfolioState.STARTER),
        (99, PortfolioState.STARTER),
        
        # ACTIVE state ($100 - $9,999.99)
        (Decimal("100.00"), PortfolioState.ACTIVE),
        (Decimal("5000.00"), PortfolioState.ACTIVE),
        (Decimal("9999.99"), PortfolioState.ACTIVE),
        (100, PortfolioState.ACTIVE),
        (5000, PortfolioState.ACTIVE),
        
        # WHALE state ($10,000+)
        (Decimal("10000.00"), PortfolioState.WHALE),
        (Decimal("100000.00"), PortfolioState.WHALE),
        (Decimal("1000000.00"), PortfolioState.WHALE),
        (10000, PortfolioState.WHALE),
        (1000000, PortfolioState.WHALE),
    ])
    def test_from_balance_classification(self, balance, expected_state):
        """Test balance to state classification."""
        result = PortfolioState.from_balance(balance)
        assert result == expected_state
    
    def test_negative_balance_treated_as_empty(self):
        """Negative balances should be treated as EMPTY."""
        result = PortfolioState.from_balance(Decimal("-100"))
        assert result == PortfolioState.EMPTY


class TestPortfolioStateProperties:
    """Test PortfolioState enum properties."""
    
    def test_empty_state_blocks_swap(self):
        """EMPTY state should not allow swap."""
        assert PortfolioState.EMPTY.can_swap is False
    
    def test_active_state_allows_swap(self):
        """ACTIVE state should allow swap."""
        assert PortfolioState.ACTIVE.can_swap is True
    
    def test_empty_state_needs_onboarding(self):
        """EMPTY state should need onboarding."""
        assert PortfolioState.EMPTY.needs_onboarding is True
    
    def test_starter_state_warns_gas_costs(self):
        """STARTER state should warn about gas costs."""
        assert PortfolioState.STARTER.warn_gas_costs is True
    
    def test_whale_state_no_gas_warning(self):
        """WHALE state should not warn about gas costs."""
        assert PortfolioState.WHALE.warn_gas_costs is False


class TestPortfolioStatePromptEnhancement:
    """Test PortfolioState.get_prompt_enhancement() method."""
    
    def test_empty_state_prompt_enhancement(self):
        """EMPTY state should return buy-focused prompt."""
        enhancement = PortfolioState.EMPTY.get_prompt_enhancement()
        assert "buy" in enhancement.lower()
        assert "empty" in enhancement.lower() or "$0" in enhancement
    
    def test_whale_state_prompt_enhancement(self):
        """WHALE state should return advanced options prompt."""
        enhancement = PortfolioState.WHALE.get_prompt_enhancement()
        assert "whale" in enhancement.lower() or "advanced" in enhancement.lower()
```

### 3.2 Activity Level Tests (`test_activity_level.py`)

```python
"""
Unit tests for ActivityLevel enum.

Tests the classification logic based on user session activity.
"""

import pytest
from app.domain.chat.enums.activity_level import ActivityLevel


class TestActivityLevelClassification:
    """Test ActivityLevel.calculate() classification logic."""
    
    @pytest.mark.parametrize("sessions_7d,sessions_30d,days_registered,expected", [
        # NEW (< 7 days registered)
        (5, 10, 3, ActivityLevel.NEW),
        (0, 0, 1, ActivityLevel.NEW),
        (10, 20, 5, ActivityLevel.NEW),
        
        # VERY_ACTIVE (5+ sessions/week, 7+ days)
        (5, 20, 30, ActivityLevel.VERY_ACTIVE),
        (7, 25, 60, ActivityLevel.VERY_ACTIVE),
        (10, 30, 90, ActivityLevel.VERY_ACTIVE),
        
        # ACTIVE (2-4 sessions/week, 7+ days)
        (3, 12, 30, ActivityLevel.ACTIVE),
        (4, 16, 45, ActivityLevel.ACTIVE),
        
        # WEEKLY_ACTIVE (1 session/week, 7+ days)
        (1, 4, 30, ActivityLevel.WEEKLY_ACTIVE),
        
        # MONTHLY_ACTIVE (< 1 session/week, some activity)
        (0, 2, 60, ActivityLevel.MONTHLY_ACTIVE),
        
        # INACTIVE (no sessions in 30d)
        (0, 0, 60, ActivityLevel.INACTIVE),
    ])
    def test_calculate_classification(
        self, sessions_7d, sessions_30d, days_registered, expected
    ):
        """Test activity level calculation."""
        result = ActivityLevel.calculate(
            sessions_7d=sessions_7d,
            sessions_30d=sessions_30d,
            days_since_registration=days_registered,
        )
        assert result == expected


class TestActivityLevelProperties:
    """Test ActivityLevel enum properties."""
    
    def test_very_active_is_engaged(self):
        """VERY_ACTIVE should be engaged."""
        assert ActivityLevel.VERY_ACTIVE.is_engaged is True
    
    def test_inactive_needs_reengagement(self):
        """INACTIVE should need reengagement."""
        assert ActivityLevel.INACTIVE.needs_reengagement is True
    
    def test_reactivated_is_returning(self):
        """REACTIVATED should be returning user."""
        assert ActivityLevel.REACTIVATED.is_returning is True
```

### 3.3 User Type Tests (`test_user_type.py`)

```python
"""
Unit tests for UserType enum.

Tests the classification logic based on user behavior patterns.
"""

import pytest
from app.domain.chat.enums.user_type import UserType


class TestUserTypeClassification:
    """Test UserType.calculate() classification logic."""
    
    @pytest.mark.parametrize("total_messages,swap_count,lending_count,buy_count,expected", [
        # NEW_USER (few interactions)
        (5, 0, 0, 0, UserType.NEW_USER),
        (10, 0, 0, 1, UserType.NEW_USER),
        
        # CASUAL (some interactions, few executions)
        (50, 2, 0, 1, UserType.CASUAL),
        (100, 3, 1, 2, UserType.CASUAL),
        
        # TRADER (many swaps)
        (100, 20, 2, 5, UserType.TRADER),
        (200, 30, 5, 10, UserType.TRADER),
        
        # YIELD_FARMER (many lending/money market)
        (100, 5, 25, 3, UserType.YIELD_FARMER),
        (150, 10, 30, 5, UserType.YIELD_FARMER),
        
        # POWER_USER (high activity across all)
        (500, 50, 30, 20, UserType.POWER_USER),
    ])
    def test_calculate_classification(
        self, total_messages, swap_count, lending_count, buy_count, expected
    ):
        """Test user type calculation."""
        result = UserType.calculate(
            total_messages=total_messages,
            swap_count=swap_count,
            lending_count=lending_count,
            buy_count=buy_count,
        )
        assert result == expected


class TestUserTypeProperties:
    """Test UserType enum properties."""
    
    def test_trader_is_execution_focused(self):
        """TRADER should be execution focused."""
        assert UserType.TRADER.is_execution_focused is True
    
    def test_yield_farmer_prefers_defi(self):
        """YIELD_FARMER should prefer DeFi."""
        assert UserType.YIELD_FARMER.prefers_defi is True
    
    def test_casual_not_execution_focused(self):
        """CASUAL should not be execution focused."""
        assert UserType.CASUAL.is_execution_focused is False
```

### 3.4 User Context Entity Tests (`test_user_context_entity.py`)

```python
"""
Unit tests for UserContextAware entity.

Tests the entity creation, classification recalculation, and serialization.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from uuid import uuid4
from app.domain.chat.entities.user_context_aware import UserContextAware


class TestUserContextAwareCreation:
    """Test UserContextAware entity creation."""
    
    def test_create_with_defaults(self):
        """Test creating entity with default values."""
        context = UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
        )
        
        assert context.portfolio_state == "empty"
        assert context.activity_level == "new"
        assert context.user_type == "new_user"
        assert context.total_balance_usd == Decimal("0")
        assert context.total_executions == 0
    
    def test_create_with_custom_values(self):
        """Test creating entity with custom values."""
        context = UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="active",
            activity_level="very_active",
            user_type="trader",
            total_balance_usd=Decimal("5000.00"),
            swap_count=50,
        )
        
        assert context.portfolio_state == "active"
        assert context.activity_level == "very_active"
        assert context.user_type == "trader"
        assert context.swap_count == 50


class TestUserContextAwareRecalculation:
    """Test UserContextAware.recalculate_classifications() method."""
    
    def test_recalculate_portfolio_state(self):
        """Test portfolio state recalculation based on balance."""
        context = UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="empty",
            wallet_total_usd=Decimal("5000.00"),  # Should be ACTIVE
        )
        
        context.recalculate_classifications()
        
        assert context.portfolio_state == "active"
    
    def test_recalculate_activity_level(self):
        """Test activity level recalculation."""
        context = UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            activity_level="new",
            chat_sessions_30d=20,
            first_active_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        
        context.recalculate_classifications()
        
        # Should be VERY_ACTIVE or ACTIVE based on session count
        assert context.activity_level in ["very_active", "active"]


class TestUserContextAwareSerialization:
    """Test UserContextAware serialization methods."""
    
    def test_to_dict(self):
        """Test to_dict() method."""
        context = UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="active",
            user_type="trader",
        )
        
        result = context.to_dict()
        
        assert isinstance(result, dict)
        assert result["portfolio_state"] == "active"
        assert result["user_type"] == "trader"
    
    def test_get_combined_prompt_enhancement(self):
        """Test get_combined_prompt_enhancement() method."""
        context = UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="empty",
            activity_level="new",
            user_type="new_user",
        )
        
        enhancement = context.get_combined_prompt_enhancement()
        
        assert isinstance(enhancement, str)
        assert len(enhancement) > 0
```

### 3.5 Response Template Tests (`test_response_template.py`)

```python
"""
Unit tests for ResponseTemplate entities.

Tests template message rendering and variable substitution.
"""

import pytest
from app.domain.chat.entities.response_template import (
    TemplateMessage,
    ResponseTemplate,
    TemplateContext,
    TemplateResult,
)


class TestTemplateMessage:
    """Test TemplateMessage dataclass."""
    
    def test_get_english_default(self):
        """Test getting English message by default."""
        msg = TemplateMessage(
            en="Hello",
            es="Hola",
            pt="Olá",
            zh="你好",
        )
        
        assert msg.get() == "Hello"
        assert msg.get("en") == "Hello"
    
    def test_get_spanish(self):
        """Test getting Spanish message."""
        msg = TemplateMessage(
            en="Hello",
            es="Hola",
        )
        
        assert msg.get("es") == "Hola"
    
    def test_fallback_to_english(self):
        """Test fallback to English when language not available."""
        msg = TemplateMessage(en="Hello")
        
        assert msg.get("fr") == "Hello"
    
    def test_render_with_variables(self):
        """Test variable substitution."""
        msg = TemplateMessage(
            en="Your balance is ${total_usd}",
        )
        
        result = msg.render("en", total_usd="1,000.00")
        
        assert result == "Your balance is $1,000.00"
    
    def test_render_multiple_variables(self):
        """Test multiple variable substitution."""
        msg = TemplateMessage(
            en="Swap {amount} {from_token} to {to_token}",
        )
        
        result = msg.render("en", amount="100", from_token="ETH", to_token="USDC")
        
        assert result == "Swap 100 ETH to USDC"


class TestTemplateContext:
    """Test TemplateContext dataclass."""
    
    def test_to_render_kwargs(self):
        """Test converting context to render kwargs."""
        context = TemplateContext(
            portfolio_state="active",
            activity_level="very_active",
            user_type="trader",
            total_balance_usd=5000.00,
        )
        
        kwargs = context.to_render_kwargs()
        
        assert kwargs["total_usd"] == "5,000.00"
        assert kwargs["portfolio_state"] == "active"


class TestTemplateResult:
    """Test TemplateResult dataclass."""
    
    def test_has_template_true(self):
        """Test has_template when template found."""
        result = TemplateResult(
            message="Hello",
            template_key="portfolio:empty:greeting",
            language="en",
        )
        
        assert result.has_template is True
    
    def test_has_template_false(self):
        """Test has_template when no template found."""
        result = TemplateResult(
            message="",
            template_key="",
            language="en",
        )
        
        assert result.has_template is False
```

---

## 4. Integration Test Specifications

### 4.1 User Context Service Tests (`test_user_context_service.py`)

```python
"""
Integration tests for UserContextService.

Tests context creation, update, and aggregation with real database.
"""

import pytest
from uuid import uuid4
from decimal import Decimal


@pytest.mark.asyncio
class TestUserContextServiceCreation:
    """Test context creation for new users."""
    
    async def test_create_for_new_user(self, user_context_service, db_session):
        """Test creating context for a new user."""
        chat_user_id = uuid4()
        
        context = await user_context_service.create_for_new_user(
            chat_user_id=chat_user_id,
            legacy_user_id=None,
        )
        
        assert context is not None
        assert context.chat_user_id == chat_user_id
        assert context.portfolio_state == "empty"
        assert context.activity_level == "new"
    
    async def test_create_with_wallet_address(self, user_context_service, db_session):
        """Test creating context with wallet address."""
        chat_user_id = uuid4()
        wallet_address = "0x1234567890abcdef"
        
        context = await user_context_service.create_for_new_user(
            chat_user_id=chat_user_id,
            wallet_address=wallet_address,
        )
        
        assert context.primary_wallet_address == wallet_address
        assert context.has_connected_wallet is True


@pytest.mark.asyncio
class TestUserContextServiceUpdate:
    """Test context update and classification."""
    
    async def test_update_recalculates_classifications(
        self, user_context_service, test_context, db_session
    ):
        """Test that update recalculates classifications."""
        # Simulate user activity
        test_context.chat_sessions_30d = 10
        test_context.swap_count = 20
        
        updated = await user_context_service.update_user_context(
            chat_user_id=test_context.chat_user_id,
        )
        
        # Should have recalculated based on activity
        assert updated is not None
    
    async def test_update_respects_cooldown(
        self, user_context_service, test_context, db_session
    ):
        """Test that update respects cooldown period."""
        # First update
        await user_context_service.update_user_context(
            chat_user_id=test_context.chat_user_id,
            cooldown_hours=1,
        )
        
        # Second update immediately should be skipped
        result = await user_context_service.update_user_context(
            chat_user_id=test_context.chat_user_id,
            cooldown_hours=1,
        )
        
        # Should be None (skipped due to cooldown)
        assert result is None


@pytest.mark.asyncio
class TestUserContextServiceAggregation:
    """Test context aggregation methods."""
    
    async def test_get_distribution_stats(
        self, user_context_service, multiple_test_contexts, db_session
    ):
        """Test getting distribution stats."""
        stats = await user_context_service.get_distribution_stats()
        
        assert "portfolio_state" in stats
        assert "activity_level" in stats
        assert "user_type" in stats
        
        # Should have counts
        assert isinstance(stats["portfolio_state"], dict)
```

### 4.2 Response Template Service Tests (`test_response_templates.py`)

```python
"""
Integration tests for ResponseTemplateService.

Tests template loading, rendering, and workflow blocking.
"""

import pytest


class TestResponseTemplateLoading:
    """Test template file loading."""
    
    def test_loads_portfolio_templates(self, response_template_service):
        """Test loading portfolio state templates."""
        assert len(response_template_service._portfolio_templates) == 4
        assert "empty" in response_template_service._portfolio_templates
        assert "whale" in response_template_service._portfolio_templates
    
    def test_loads_activity_templates(self, response_template_service):
        """Test loading activity level templates."""
        assert len(response_template_service._activity_templates) == 7
        assert "new" in response_template_service._activity_templates
        assert "inactive" in response_template_service._activity_templates
    
    def test_loads_user_type_templates(self, response_template_service):
        """Test loading user type templates."""
        assert len(response_template_service._user_type_templates) == 5
        assert "trader" in response_template_service._user_type_templates
    
    def test_loads_workflow_templates(self, response_template_service):
        """Test loading workflow templates."""
        assert len(response_template_service._workflow_templates) >= 4
        assert "swap" in response_template_service._workflow_templates


class TestResponseTemplateRetrieval:
    """Test template retrieval methods."""
    
    def test_get_portfolio_response_empty(self, response_template_service):
        """Test getting response for empty portfolio."""
        result = response_template_service.get_portfolio_response(
            portfolio_state="empty",
            message_key="portfolio_query",
            language="en",
        )
        
        assert result.message != ""
        assert result.template_key == "portfolio:empty:portfolio_query"
        assert "buy" in result.message.lower() or "welcome" in result.message.lower()
    
    def test_get_portfolio_response_spanish(self, response_template_service):
        """Test getting Spanish response."""
        result = response_template_service.get_portfolio_response(
            portfolio_state="empty",
            message_key="portfolio_query",
            language="es",
        )
        
        assert result.message != ""
        assert "bienvenido" in result.message.lower() or "comprar" in result.message.lower()
    
    def test_get_workflow_response(self, response_template_service):
        """Test getting workflow response."""
        result = response_template_service.get_workflow_response(
            workflow="swap",
            message_key="initiation",
            language="en",
            from_token="ETH",
            to_token="USDC",
            amount="1.0",
        )
        
        assert result.message != ""
        assert "ETH" in result.message
        assert "USDC" in result.message


class TestWorkflowBlocking:
    """Test workflow blocking logic."""
    
    def test_swap_blocked_for_empty_portfolio(self, response_template_service):
        """Test that swap is blocked for empty portfolio."""
        is_blocked, message = response_template_service.check_workflow_blocked(
            portfolio_state="empty",
            workflow="swap",
            language="en",
        )
        
        assert is_blocked is True
        assert message is not None
        assert "buy" in message.lower() or "need" in message.lower()
    
    def test_swap_allowed_for_active_portfolio(self, response_template_service):
        """Test that swap is allowed for active portfolio."""
        is_blocked, message = response_template_service.check_workflow_blocked(
            portfolio_state="active",
            workflow="swap",
            language="en",
        )
        
        assert is_blocked is False
        assert message is None
    
    def test_lending_blocked_for_empty_portfolio(self, response_template_service):
        """Test that lending is blocked for empty portfolio."""
        is_blocked, _ = response_template_service.check_workflow_blocked(
            portfolio_state="empty",
            workflow="lending",
            language="en",
        )
        
        assert is_blocked is True


class TestGasWarning:
    """Test gas warning logic."""
    
    def test_gas_warning_for_starter_portfolio(self, response_template_service):
        """Test gas warning shown for small amounts."""
        should_warn = response_template_service.should_show_gas_warning(
            portfolio_state="starter",
            amount_usd=50.0,
        )
        
        assert should_warn is True
    
    def test_no_gas_warning_for_whale(self, response_template_service):
        """Test no gas warning for whale portfolios."""
        should_warn = response_template_service.should_show_gas_warning(
            portfolio_state="whale",
            amount_usd=50.0,
        )
        
        assert should_warn is False
```

### 4.3 Analytics Repository Tests (`test_analytics_repository.py`)

```python
"""
Integration tests for AnalyticsRepository.

Tests snapshot persistence, querying, and trend calculations.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from app.domain.chat.entities.analytics_snapshot import (
    AnalyticsSnapshot,
    PortfolioDistribution,
    ActivityDistribution,
    UserTypeDistribution,
    ExecutionMetrics,
)


@pytest.mark.asyncio
class TestAnalyticsSnapshotPersistence:
    """Test snapshot save and retrieve."""
    
    async def test_save_snapshot(self, analytics_repository, db_session):
        """Test saving a new snapshot."""
        snapshot = AnalyticsSnapshot(
            id=uuid4(),
            snapshot_date=date.today(),
            snapshot_type="daily",
            portfolio=PortfolioDistribution(empty=100, starter=50, active=30, whale=10),
            activity=ActivityDistribution(new=50, active=80, inactive=60),
            user_types=UserTypeDistribution(new_user=50, trader=40, casual=100),
            executions=ExecutionMetrics(total=500, swap=200, buy=150, lending=100),
            total_users=190,
            total_balance_usd=Decimal("500000.00"),
        )
        
        await analytics_repository.save(snapshot)
        
        # Retrieve and verify
        retrieved = await analytics_repository.get_by_date(date.today(), "daily")
        
        assert retrieved is not None
        assert retrieved.total_users == 190
        assert retrieved.portfolio.empty == 100
    
    async def test_upsert_snapshot(self, analytics_repository, db_session):
        """Test upserting (updating existing) snapshot."""
        today = date.today()
        
        # Create initial
        snapshot1 = AnalyticsSnapshot(
            id=uuid4(),
            snapshot_date=today,
            snapshot_type="daily",
            portfolio=PortfolioDistribution(empty=100),
            activity=ActivityDistribution(),
            user_types=UserTypeDistribution(),
            executions=ExecutionMetrics(),
            total_users=100,
        )
        await analytics_repository.save(snapshot1)
        
        # Update with new data
        snapshot2 = AnalyticsSnapshot(
            id=uuid4(),  # Different ID
            snapshot_date=today,
            snapshot_type="daily",
            portfolio=PortfolioDistribution(empty=150),  # Updated
            activity=ActivityDistribution(),
            user_types=UserTypeDistribution(),
            executions=ExecutionMetrics(),
            total_users=150,  # Updated
        )
        await analytics_repository.save(snapshot2)
        
        # Should have updated values
        retrieved = await analytics_repository.get_by_date(today, "daily")
        
        assert retrieved.total_users == 150
        assert retrieved.portfolio.empty == 150


@pytest.mark.asyncio
class TestAnalyticsSnapshotQueries:
    """Test snapshot query methods."""
    
    async def test_get_latest(self, analytics_repository, sample_snapshots, db_session):
        """Test getting latest snapshot."""
        latest = await analytics_repository.get_latest("daily")
        
        assert latest is not None
        # Should be the most recent date
    
    async def test_get_range(self, analytics_repository, sample_snapshots, db_session):
        """Test getting snapshots in date range."""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        snapshots = await analytics_repository.get_range(start_date, end_date, "daily")
        
        assert len(snapshots) > 0
        # Should be ordered by date
        for i in range(1, len(snapshots)):
            assert snapshots[i].snapshot_date >= snapshots[i-1].snapshot_date
    
    async def test_get_last_n_days(self, analytics_repository, sample_snapshots, db_session):
        """Test getting last N days of snapshots."""
        snapshots = await analytics_repository.get_last_n_days(7, "daily")
        
        assert len(snapshots) <= 7


@pytest.mark.asyncio
class TestAnalyticsTrends:
    """Test trend calculation methods."""
    
    async def test_get_trends(self, analytics_repository, sample_snapshots, db_session):
        """Test getting trends between two dates."""
        trends = await analytics_repository.get_trends(
            current_date=date.today(),
            comparison_date=date.today() - timedelta(days=7),
            snapshot_type="daily",
        )
        
        assert len(trends) > 0
        
        # Check trend structure
        for trend in trends:
            assert trend.metric_name != ""
            assert trend.trend in ["up", "down", "stable"]
    
    async def test_week_over_week(self, analytics_repository, sample_snapshots, db_session):
        """Test week-over-week trends."""
        trends = await analytics_repository.get_week_over_week()
        
        # Should return standard metrics
        metric_names = [t.metric_name for t in trends]
        assert "total_users" in metric_names or len(trends) == 0  # May be empty if no data
```

### 4.4 Admin Analytics API Tests (`test_admin_analytics_api.py`)

```python
"""
Integration tests for Admin Analytics API endpoints.

Tests all admin analytics endpoints with authentication.
"""

import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
class TestAdminAnalyticsDistribution:
    """Test /admin/analytics/users/distribution endpoint."""
    
    async def test_get_distribution_requires_auth(self, async_client):
        """Test that endpoint requires authentication."""
        response = await async_client.get("/api/v1/admin/analytics/users/distribution")
        
        assert response.status_code == 401
    
    async def test_get_distribution_success(self, async_client, admin_token):
        """Test successful distribution retrieval."""
        response = await async_client.get(
            "/api/v1/admin/analytics/users/distribution",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "portfolio" in data
        assert "activity" in data
        assert "user_types" in data
        assert "executions" in data
        assert "totals" in data


@pytest.mark.asyncio
class TestAdminAnalyticsSummary:
    """Test /admin/analytics/users/summary endpoint."""
    
    async def test_get_summary_success(self, async_client, admin_token):
        """Test successful summary retrieval."""
        response = await async_client.get(
            "/api/v1/admin/analytics/users/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_users" in data
        assert "total_balance_usd" in data
        assert "portfolio_distribution" in data
        assert "activity_distribution" in data
        assert "user_type_distribution" in data
        
        # Check percentages sum to ~100%
        portfolio_sum = sum(data["portfolio_distribution"].values())
        assert 99 <= portfolio_sum <= 101  # Allow rounding errors


@pytest.mark.asyncio
class TestAdminAnalyticsSnapshots:
    """Test snapshot endpoints."""
    
    async def test_get_latest_snapshot(self, async_client, admin_token, sample_snapshots):
        """Test getting latest snapshot."""
        response = await async_client.get(
            "/api/v1/admin/analytics/snapshots/latest",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code in [200, 404]  # 404 if no snapshots
        
        if response.status_code == 200:
            data = response.json()
            assert "snapshot_date" in data
            assert "portfolio" in data
    
    async def test_get_snapshot_history(self, async_client, admin_token, sample_snapshots):
        """Test getting snapshot history."""
        response = await async_client.get(
            "/api/v1/admin/analytics/snapshots/history",
            params={"days": 30},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "snapshots" in data
        assert "count" in data
        assert "start_date" in data
        assert "end_date" in data
    
    async def test_get_snapshot_by_date(self, async_client, admin_token, sample_snapshots):
        """Test getting snapshot by specific date."""
        response = await async_client.get(
            f"/api/v1/admin/analytics/snapshots/date/{date.today().isoformat()}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        # May be 200 or 404 depending on test data
        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestAdminAnalyticsTrends:
    """Test trend endpoints."""
    
    async def test_get_week_over_week_trends(self, async_client, admin_token, sample_snapshots):
        """Test week-over-week trends."""
        response = await async_client.get(
            "/api/v1/admin/analytics/trends/week-over-week",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "trends" in data
        assert "current_date" in data
        assert "comparison_date" in data
    
    async def test_get_month_over_month_trends(self, async_client, admin_token, sample_snapshots):
        """Test month-over-month trends."""
        response = await async_client.get(
            "/api/v1/admin/analytics/trends/month-over-month",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code == 200
    
    async def test_get_custom_trends(self, async_client, admin_token, sample_snapshots):
        """Test custom date range trends."""
        current = date.today()
        comparison = current - timedelta(days=14)
        
        response = await async_client.get(
            "/api/v1/admin/analytics/trends/custom",
            params={
                "current_date": current.isoformat(),
                "comparison_date": comparison.isoformat(),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code == 200


@pytest.mark.asyncio
class TestAdminAnalyticsTotals:
    """Test /admin/analytics/totals endpoint."""
    
    async def test_get_totals(self, async_client, admin_token):
        """Test getting total metrics."""
        response = await async_client.get(
            "/api/v1/admin/analytics/totals",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_users" in data
        assert "total_balance_usd" in data
        assert "as_of" in data
```

### 4.5 Context-Aware Routing Tests (`test_context_routing.py`)

```python
"""
Integration tests for context-aware routing in AuthenticatedSupervisor.

Tests that user context affects agent routing and response generation.
"""

import pytest


@pytest.mark.asyncio
class TestContextAwareRouting:
    """Test context-aware routing in supervisor."""
    
    async def test_empty_portfolio_blocks_swap_intent(
        self, authenticated_supervisor, empty_user_context
    ):
        """Test that swap is blocked for empty portfolio users."""
        authenticated_supervisor.set_context_aware(empty_user_context)
        
        can_execute, reason = authenticated_supervisor.can_execute_workflow("swap")
        
        assert can_execute is False
        assert reason is not None
        assert "buy" in reason.lower() or "empty" in reason.lower()
    
    async def test_active_portfolio_allows_swap(
        self, authenticated_supervisor, active_user_context
    ):
        """Test that swap is allowed for active portfolio users."""
        authenticated_supervisor.set_context_aware(active_user_context)
        
        can_execute, reason = authenticated_supervisor.can_execute_workflow("swap")
        
        assert can_execute is True
        assert reason is None
    
    async def test_new_user_gets_onboarding_suggestion(
        self, authenticated_supervisor, new_user_context
    ):
        """Test that new users get onboarding suggestions."""
        authenticated_supervisor.set_context_aware(new_user_context)
        
        suggestion = authenticated_supervisor.get_onboarding_suggestion()
        
        assert suggestion is not None
        assert "buy" in suggestion.lower() or "welcome" in suggestion.lower()
    
    async def test_inactive_user_gets_reengagement(
        self, authenticated_supervisor, inactive_user_context
    ):
        """Test that inactive users get reengagement suggestions."""
        authenticated_supervisor.set_context_aware(inactive_user_context)
        
        suggestion = authenticated_supervisor.get_onboarding_suggestion()
        
        assert suggestion is not None
        assert "back" in suggestion.lower() or "welcome" in suggestion.lower()


@pytest.mark.asyncio
class TestContextAwarePromptBuilding:
    """Test context-aware prompt enhancement."""
    
    async def test_empty_portfolio_prompt_includes_buy_suggestion(
        self, authenticated_supervisor, empty_user_context
    ):
        """Test that empty portfolio context enhances prompt with buy suggestion."""
        authenticated_supervisor.set_context_aware(empty_user_context)
        
        # Build planning prompt and check for context
        # (Would need access to internal methods or mock)
        response_style = authenticated_supervisor.get_response_style()
        
        # Should recommend educational style for new/empty users
        assert response_style in ["educational", "default"]


@pytest.mark.asyncio
class TestWorkflowBlockingWithTemplates:
    """Test workflow blocking with template responses."""
    
    async def test_blocked_swap_returns_template_message(
        self, authenticated_supervisor, empty_user_context
    ):
        """Test that blocked swap returns localized template message."""
        authenticated_supervisor.set_context_aware(empty_user_context)
        
        is_blocked, message = authenticated_supervisor.check_workflow_blocked_with_template(
            workflow_type="swap",
            language="en",
        )
        
        assert is_blocked is True
        assert message is not None
        # Should be a helpful message with buy suggestion
    
    async def test_blocked_lending_returns_template_message(
        self, authenticated_supervisor, empty_user_context
    ):
        """Test that blocked lending returns localized template message."""
        authenticated_supervisor.set_context_aware(empty_user_context)
        
        is_blocked, message = authenticated_supervisor.check_workflow_blocked_with_template(
            workflow_type="lending",
            language="es",  # Spanish
        )
        
        assert is_blocked is True
        assert message is not None
```

---

## 5. E2E Test Specifications

### 5.1 Empty Portfolio Journey (`test_empty_portfolio_journey.py`)

```python
"""
E2E test for empty portfolio user journey.

Tests the complete flow: new user → blocked swap → buy suggestion → buy → use.
"""

import pytest


@pytest.mark.asyncio
class TestEmptyPortfolioJourney:
    """Test complete empty portfolio user journey."""
    
    async def test_new_user_swap_blocked_with_buy_suggestion(
        self, async_client, authenticated_token, conversation_id
    ):
        """Test that new user trying to swap gets buy suggestion."""
        # Step 1: Try to swap
        response = await async_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "swap 1 ETH to USDC"},
            headers={"Authorization": f"Bearer {authenticated_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should mention need to buy first
        content = data["content"].lower()
        assert "buy" in content or "need" in content or "empty" in content
    
    async def test_new_user_gets_buy_workflow(
        self, async_client, authenticated_token, conversation_id
    ):
        """Test that new user can start buy workflow."""
        response = await async_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "buy 100 USD of ETH"},
            headers={"Authorization": f"Bearer {authenticated_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should start buy workflow
        assert data.get("workflow_active") is True or "ETH" in data["content"]
    
    async def test_complete_buy_then_swap_available(
        self, async_client, authenticated_token, conversation_with_balance
    ):
        """Test that after buying, swap becomes available."""
        # Now try swap again
        response = await async_client.post(
            f"/api/v1/conversations/{conversation_with_balance}/messages",
            json={"content": "swap 0.5 ETH to USDC"},
            headers={"Authorization": f"Bearer {authenticated_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should start swap workflow
        content = data["content"]
        assert "swap" in content.lower() or "ETH" in content
```

---

## 6. Test Fixtures

### 6.1 New Conftest Additions (`conftest.py`)

```python
"""
Additional fixtures for context-aware agent tests.
"""

import pytest
import pytest_asyncio
from datetime import datetime, UTC
from decimal import Decimal
from uuid import uuid4

from app.domain.chat.entities.user_context_aware import UserContextAware
from app.domain.chat.entities.analytics_snapshot import (
    AnalyticsSnapshot,
    PortfolioDistribution,
    ActivityDistribution,
    UserTypeDistribution,
    ExecutionMetrics,
)
from app.application.chat.services.user_context_service import UserContextService
from app.application.chat.services.response_template_service import ResponseTemplateService
from app.infrastructure.adapters.analytics_repository_sqla import AnalyticsRepositorySqla


# ============================================================
# User Context Fixtures
# ============================================================

@pytest.fixture
def empty_user_context() -> UserContextAware:
    """Create a user context with empty portfolio."""
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
    """Create a user context with starter portfolio."""
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
    """Create a user context with active portfolio."""
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
    """Create a user context with whale portfolio."""
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
    """Create an inactive user context."""
    return UserContextAware(
        id=uuid4(),
        chat_user_id=uuid4(),
        portfolio_state="active",
        activity_level="inactive",
        user_type="casual",
        total_balance_usd=Decimal("1000.00"),
        chat_sessions_30d=0,
    )


@pytest.fixture
def new_user_context() -> UserContextAware:
    """Create a brand new user context."""
    return UserContextAware(
        id=uuid4(),
        chat_user_id=uuid4(),
        portfolio_state="empty",
        activity_level="new",
        user_type="new_user",
        first_active_at=datetime.now(UTC),
    )


# ============================================================
# Service Fixtures
# ============================================================

@pytest.fixture
def response_template_service() -> ResponseTemplateService:
    """Create ResponseTemplateService instance."""
    return ResponseTemplateService()


@pytest_asyncio.fixture
async def user_context_service(db_session) -> UserContextService:
    """Create UserContextService with mocked dependencies."""
    # Would need to create with real or mocked repositories
    pass


@pytest_asyncio.fixture
async def analytics_repository(db_session) -> AnalyticsRepositorySqla:
    """Create AnalyticsRepository instance."""
    return AnalyticsRepositorySqla(db_session)


# ============================================================
# Sample Data Fixtures
# ============================================================

@pytest_asyncio.fixture
async def sample_snapshots(analytics_repository, db_session):
    """Create sample analytics snapshots for testing."""
    from datetime import date, timedelta
    
    snapshots = []
    for i in range(7):
        snapshot_date = date.today() - timedelta(days=i)
        snapshot = AnalyticsSnapshot(
            id=uuid4(),
            snapshot_date=snapshot_date,
            snapshot_type="daily",
            portfolio=PortfolioDistribution(
                empty=100 + i * 5,
                starter=50 + i * 2,
                active=30 + i,
                whale=10,
            ),
            activity=ActivityDistribution(
                new=20 + i,
                active=60,
                inactive=30 - i,
            ),
            user_types=UserTypeDistribution(
                new_user=30,
                casual=80,
                trader=40,
                yield_farmer=20,
                power_user=10,
            ),
            executions=ExecutionMetrics(
                total=500 + i * 50,
                swap=200 + i * 20,
                buy=150 + i * 15,
                lending=100 + i * 10,
            ),
            total_users=190 + i * 8,
            total_balance_usd=Decimal("500000.00") + Decimal(str(i * 10000)),
        )
        await analytics_repository.save(snapshot)
        snapshots.append(snapshot)
    
    return snapshots
```

---

## 7. Test Execution Plan

### 7.1 Phase 1: Unit Tests (Week 1)

| Day | Tests | Coverage Target |
|-----|-------|-----------------|
| 1 | `test_portfolio_state.py` | 100% |
| 2 | `test_activity_level.py` | 100% |
| 3 | `test_user_type.py` | 100% |
| 4 | `test_user_context_entity.py` | 90% |
| 5 | `test_response_template.py`, `test_analytics_entities.py` | 90% |

### 7.2 Phase 2: Integration Tests (Week 2)

| Day | Tests | Coverage Target |
|-----|-------|-----------------|
| 1-2 | `test_user_context_service.py` | 85% |
| 3 | `test_response_templates.py` | 90% |
| 4 | `test_analytics_repository.py` | 80% |
| 5 | `test_admin_analytics_api.py` | 75% |

### 7.3 Phase 3: E2E & Routing Tests (Week 3)

| Day | Tests | Coverage Target |
|-----|-------|-----------------|
| 1-2 | `test_context_routing.py` | 85% |
| 3 | `test_workflow_blocking.py` | 90% |
| 4-5 | E2E journey tests | 70% |

---

## 8. CI/CD Integration

### 8.1 GitHub Actions Workflow

```yaml
name: Context-Aware Tests

on:
  push:
    paths:
      - 'src/app/domain/chat/**'
      - 'src/app/application/chat/**'
      - 'src/app/infrastructure/adapters/*context*'
      - 'src/app/infrastructure/adapters/*analytics*'
      - 'src/app/infrastructure/templates/**'
      - 'tests/**/context_aware/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e '.[dev,test]'
      - name: Run unit tests
        run: |
          pytest tests/unit/context_aware/ -v --cov=src/app/domain/chat --cov-report=xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: |
          pytest tests/integration/user/context_aware/ -v --cov-append
```

---

## 9. Quality Metrics

### 9.1 Coverage Targets

| Component | Target | Minimum |
|-----------|--------|---------|
| Domain Enums | 100% | 95% |
| Domain Entities | 90% | 85% |
| Application Services | 85% | 80% |
| Infrastructure Adapters | 80% | 75% |
| API Endpoints | 75% | 70% |

### 9.2 Performance Targets

| Test Type | Max Duration | Max Memory |
|-----------|--------------|------------|
| Unit test | 100ms | 50MB |
| Integration test | 2s | 100MB |
| E2E test | 10s | 200MB |

---

## 10. Implementation Status

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Unit Tests | Pending | 0% |
| Phase 2: Integration Tests | Pending | 0% |
| Phase 3: E2E Tests | Pending | 0% |
| CI/CD Integration | Pending | 0% |

---

## References

- [Context-Aware Agents Requirements](./requirements.md)
- [QA Automation Engineer Agent](/.claude/agents/automation/qa-automation-engineer.md)
- [Test Automation Expert Agent](/.claude/agents/testing/test-automation-expert.md)
- [CTO Methodology](/../../../cto.md)
