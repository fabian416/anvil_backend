"""
Context-Aware Integration Test Configuration and Fixtures.

Provides:
- HTTP client fixtures for API testing
- User context fixtures (mock data for test assertions)
- CSV reporters for each context category
- Helper functions for context-aware tests

NOTE: These tests use HTTP requests to the live API server.
They do NOT create a separate test database.
"""

import pytest
import pytest_asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import httpx

# Import parent conftest utilities
from ..conftest import (
    TokenManager,
    TokenInfo,
    CSVReporter,
    TestResult,
    send_message,
    create_conversation,
    parse_response,
    create_test_result,
    BASE_URL,
)

# ============================================================
# Output Directory Configuration
# ============================================================

CONTEXT_OUTPUT_DIR = (
    Path(__file__).parent.parent.parent.parent / "output" / "user" / "context_aware"
)

# Ensure all output directories exist
for subdir in [
    "portfolio_state",
    "activity_level",
    "user_type",
    "templates",
    "analytics",
    "routing",
    "workflows",
]:
    (CONTEXT_OUTPUT_DIR / subdir).mkdir(parents=True, exist_ok=True)


# ============================================================
# Context-Aware Test Result
# ============================================================


@dataclass
class ContextAwareTestResult(TestResult):
    """Extended test result with context-aware fields."""

    # Context fields
    portfolio_state: str = ""
    activity_level: str = ""
    user_type: str = ""
    total_balance_usd: str = ""

    # Template fields
    template_used: str = ""
    template_key: str = ""

    # Workflow blocking fields
    workflow_blocked: str = "NO"
    block_reason: str = ""

    # Context routing fields
    context_enhanced_prompt: str = "NO"
    response_style: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for CSV writing."""
        return asdict(self)


# ============================================================
# Context-Aware CSV Reporter
# ============================================================


class ContextAwareCSVReporter(CSVReporter):
    """CSV reporter with context-aware fields."""

    CSV_FIELDS = CSVReporter.CSV_FIELDS + [
        "portfolio_state",
        "activity_level",
        "user_type",
        "total_balance_usd",
        "template_used",
        "template_key",
        "workflow_blocked",
        "block_reason",
        "context_enhanced_prompt",
        "response_style",
    ]

    def __init__(self, category: str, subcategory: str = ""):
        """
        Initialize context-aware CSV reporter.

        Args:
            category: Test category (portfolio_state, activity_level, etc.)
            subcategory: Optional subcategory
        """
        self.subcategory = subcategory
        output_dir = CONTEXT_OUTPUT_DIR / category
        super().__init__(category=f"context_{category}", output_dir=output_dir)


# ============================================================
# Mock User Context Data Classes (for test assertions)
# ============================================================


@dataclass
class MockUserContext:
    """Mock user context for testing."""

    id: str = field(default_factory=lambda: str(uuid4()))
    chat_user_id: str = field(default_factory=lambda: str(uuid4()))
    portfolio_state: str = "empty"
    activity_level: str = "new"
    user_type: str = "new_user"
    total_balance_usd: Decimal = Decimal("0")
    wallet_total_usd: Decimal = Decimal("0")
    token_count: int = 0
    has_connected_wallet: bool = False
    swap_count: int = 0
    buy_count: int = 0
    lending_count: int = 0
    money_market_count: int = 0
    transfer_count: int = 0
    total_executions: int = 0
    chat_sessions_30d: int = 0
    messages_sent_30d: int = 0
    first_active_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_active_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ============================================================
# User Context Fixtures (Mock Data for Assertions)
# ============================================================


@pytest.fixture
def empty_user_context() -> MockUserContext:
    """User with EMPTY portfolio ($0)."""
    return MockUserContext(
        portfolio_state="empty",
        activity_level="new",
        user_type="new_user",
        total_balance_usd=Decimal("0"),
        has_connected_wallet=False,
    )


@pytest.fixture
def starter_user_context() -> MockUserContext:
    """User with STARTER portfolio ($50)."""
    return MockUserContext(
        portfolio_state="starter",
        activity_level="active",
        user_type="casual",
        total_balance_usd=Decimal("50.00"),
        has_connected_wallet=True,
        swap_count=1,
        buy_count=1,
    )


@pytest.fixture
def active_user_context() -> MockUserContext:
    """User with ACTIVE portfolio ($5000)."""
    return MockUserContext(
        portfolio_state="active",
        activity_level="very_active",
        user_type="trader",
        total_balance_usd=Decimal("5000.00"),
        has_connected_wallet=True,
        swap_count=50,
        buy_count=10,
        lending_count=5,
        chat_sessions_30d=20,
        messages_sent_30d=100,
    )


@pytest.fixture
def whale_user_context() -> MockUserContext:
    """User with WHALE portfolio ($50000+)."""
    return MockUserContext(
        portfolio_state="whale",
        activity_level="very_active",
        user_type="power_user",
        total_balance_usd=Decimal("50000.00"),
        has_connected_wallet=True,
        swap_count=200,
        buy_count=50,
        lending_count=30,
        money_market_count=20,
        chat_sessions_30d=50,
        messages_sent_30d=500,
    )


@pytest.fixture
def inactive_user_context() -> MockUserContext:
    """INACTIVE user (no sessions in 30d)."""
    return MockUserContext(
        portfolio_state="active",
        activity_level="inactive",
        user_type="casual",
        total_balance_usd=Decimal("1000.00"),
        first_active_at=datetime.now(UTC) - timedelta(days=90),
        last_active_at=datetime.now(UTC) - timedelta(days=45),
        chat_sessions_30d=0,
        messages_sent_30d=0,
    )


# ============================================================
# CSV Reporter Fixtures
# ============================================================


@pytest.fixture
def portfolio_state_reporter() -> ContextAwareCSVReporter:
    """CSV reporter for portfolio state tests."""
    reporter = ContextAwareCSVReporter(category="portfolio_state")
    yield reporter
    _finalize_reporter(reporter)


@pytest.fixture
def activity_level_reporter() -> ContextAwareCSVReporter:
    """CSV reporter for activity level tests."""
    reporter = ContextAwareCSVReporter(category="activity_level")
    yield reporter
    _finalize_reporter(reporter)


@pytest.fixture
def user_type_reporter() -> ContextAwareCSVReporter:
    """CSV reporter for user type tests."""
    reporter = ContextAwareCSVReporter(category="user_type")
    yield reporter
    _finalize_reporter(reporter)


@pytest.fixture
def templates_reporter() -> ContextAwareCSVReporter:
    """CSV reporter for template tests."""
    reporter = ContextAwareCSVReporter(category="templates")
    yield reporter
    _finalize_reporter(reporter)


@pytest.fixture
def analytics_reporter() -> ContextAwareCSVReporter:
    """CSV reporter for analytics tests."""
    reporter = ContextAwareCSVReporter(category="analytics")
    yield reporter
    _finalize_reporter(reporter)


@pytest.fixture
def routing_reporter() -> ContextAwareCSVReporter:
    """CSV reporter for routing tests."""
    reporter = ContextAwareCSVReporter(category="routing")
    yield reporter
    _finalize_reporter(reporter)


@pytest.fixture
def workflows_reporter() -> ContextAwareCSVReporter:
    """CSV reporter for workflow blocking tests."""
    reporter = ContextAwareCSVReporter(category="workflows")
    yield reporter
    _finalize_reporter(reporter)


def _finalize_reporter(reporter: ContextAwareCSVReporter):
    """Write reports if results exist."""
    if reporter.results:
        csv_path = reporter.write_csv()
        summary_path = reporter.write_summary()
        reporter.print_summary()
        print(f"CSV output: {csv_path}")
        print(f"Summary: {summary_path}")


# ============================================================
# Helper Functions
# ============================================================


def create_context_test_result(
    test_id: str,
    test_case: dict[str, Any],
    response_data: dict[str, Any],
    response_time_ms: int,
    user_context: MockUserContext = None,
    template_info: dict[str, Any] = None,
    workflow_info: dict[str, Any] = None,
    conversation_id: str = "",
) -> ContextAwareTestResult:
    """
    Create a ContextAwareTestResult from test case and response data.

    Args:
        test_id: Unique test identifier
        test_case: Test case definition
        response_data: Parsed response data
        response_time_ms: Response time in milliseconds
        user_context: MockUserContext instance
        template_info: Template usage info
        workflow_info: Workflow blocking info
        conversation_id: Conversation ID

    Returns:
        ContextAwareTestResult instance
    """
    # Get base result from parent
    base_result = create_test_result(
        test_id=test_id,
        test_case=test_case,
        response_data=response_data,
        response_time_ms=response_time_ms,
        conversation_id=conversation_id,
    )

    # Create context-aware result
    result = ContextAwareTestResult(
        **base_result.to_dict(),
    )

    # Add context fields
    if user_context:
        result.portfolio_state = user_context.portfolio_state
        result.activity_level = user_context.activity_level
        result.user_type = user_context.user_type
        result.total_balance_usd = str(user_context.total_balance_usd)

    # Add template fields
    if template_info:
        result.template_used = "YES" if template_info.get("used") else "NO"
        result.template_key = template_info.get("key", "")

    # Add workflow fields
    if workflow_info:
        result.workflow_blocked = "YES" if workflow_info.get("blocked") else "NO"
        result.block_reason = workflow_info.get("reason", "")

    # Add routing fields
    result.context_enhanced_prompt = test_case.get("context_enhanced", "NO")
    result.response_style = test_case.get("response_style", "")

    return result
