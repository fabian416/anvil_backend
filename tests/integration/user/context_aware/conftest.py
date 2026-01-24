"""
Context-Aware Integration Test Configuration and Fixtures.

Provides:
- User context fixtures for all portfolio states
- User context fixtures for all activity levels
- User context fixtures for all user types
- Response template service fixture
- Analytics repository fixtures
- CSV reporters for each context category
"""

import asyncio
import pytest
import pytest_asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, UTC, date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

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
    DB_DSN,
)

# ============================================================
# Output Directory Configuration
# ============================================================

CONTEXT_OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "output" / "user" / "context_aware"

# Ensure all output directories exist
for subdir in ["portfolio_state", "activity_level", "user_type", "templates", "analytics", "routing", "workflows"]:
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
        "portfolio_state", "activity_level", "user_type", "total_balance_usd",
        "template_used", "template_key",
        "workflow_blocked", "block_reason",
        "context_enhanced_prompt", "response_style",
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
# User Context Fixtures
# ============================================================

@pytest.fixture
def empty_user_context():
    """User with EMPTY portfolio ($0)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="empty",
            activity_level="new",
            user_type="new_user",
            total_balance_usd=Decimal("0"),
            wallet_total_usd=Decimal("0"),
            token_count=0,
            has_connected_wallet=False,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def starter_user_context():
    """User with STARTER portfolio ($50)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="starter",
            activity_level="active",
            user_type="casual",
            total_balance_usd=Decimal("50.00"),
            wallet_total_usd=Decimal("50.00"),
            token_count=2,
            has_connected_wallet=True,
            swap_count=1,
            buy_count=1,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def active_user_context():
    """User with ACTIVE portfolio ($5000)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="active",
            activity_level="very_active",
            user_type="trader",
            total_balance_usd=Decimal("5000.00"),
            wallet_total_usd=Decimal("5000.00"),
            token_count=10,
            has_connected_wallet=True,
            swap_count=50,
            buy_count=10,
            lending_count=5,
            chat_sessions_30d=20,
            messages_sent_30d=100,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def whale_user_context():
    """User with WHALE portfolio ($50000+)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="whale",
            activity_level="very_active",
            user_type="power_user",
            total_balance_usd=Decimal("50000.00"),
            wallet_total_usd=Decimal("50000.00"),
            token_count=25,
            has_connected_wallet=True,
            swap_count=200,
            buy_count=50,
            lending_count=30,
            money_market_count=20,
            chat_sessions_30d=50,
            messages_sent_30d=500,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


# ============================================================
# Activity Level Fixtures
# ============================================================

@pytest.fixture
def new_user_context():
    """NEW user (< 7 days registered)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="empty",
            activity_level="new",
            user_type="new_user",
            total_balance_usd=Decimal("0"),
            first_active_at=datetime.now(UTC) - timedelta(days=2),
            chat_sessions_30d=3,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def very_active_user_context():
    """VERY_ACTIVE user (5+ sessions/week)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="active",
            activity_level="very_active",
            user_type="trader",
            total_balance_usd=Decimal("5000.00"),
            first_active_at=datetime.now(UTC) - timedelta(days=60),
            last_active_at=datetime.now(UTC),
            chat_sessions_30d=25,
            messages_sent_30d=200,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def inactive_user_context():
    """INACTIVE user (no sessions in 30d)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="active",
            activity_level="inactive",
            user_type="casual",
            total_balance_usd=Decimal("1000.00"),
            first_active_at=datetime.now(UTC) - timedelta(days=90),
            last_active_at=datetime.now(UTC) - timedelta(days=45),
            chat_sessions_30d=0,
            messages_sent_30d=0,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def reactivated_user_context():
    """REACTIVATED user (returned after inactivity)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="active",
            activity_level="reactivated",
            user_type="casual",
            total_balance_usd=Decimal("2000.00"),
            first_active_at=datetime.now(UTC) - timedelta(days=120),
            last_active_at=datetime.now(UTC),
            chat_sessions_30d=2,
            messages_sent_30d=5,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


# ============================================================
# User Type Fixtures
# ============================================================

@pytest.fixture
def casual_user_context():
    """CASUAL user (some interactions, few executions)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="starter",
            activity_level="weekly_active",
            user_type="casual",
            total_balance_usd=Decimal("200.00"),
            swap_count=3,
            buy_count=2,
            total_executions=5,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def trader_user_context():
    """TRADER user (many swaps)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="active",
            activity_level="very_active",
            user_type="trader",
            total_balance_usd=Decimal("10000.00"),
            swap_count=100,
            buy_count=20,
            lending_count=5,
            total_executions=125,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def yield_farmer_user_context():
    """YIELD_FARMER user (many lending/money market)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="active",
            activity_level="active",
            user_type="yield_farmer",
            total_balance_usd=Decimal("15000.00"),
            swap_count=10,
            buy_count=5,
            lending_count=50,
            money_market_count=30,
            total_executions=95,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


@pytest.fixture
def power_user_context():
    """POWER_USER (high activity across all)."""
    try:
        from app.domain.chat.entities.user_context_aware import UserContextAware
        return UserContextAware(
            id=uuid4(),
            chat_user_id=uuid4(),
            portfolio_state="whale",
            activity_level="very_active",
            user_type="power_user",
            total_balance_usd=Decimal("100000.00"),
            swap_count=200,
            buy_count=50,
            lending_count=80,
            money_market_count=40,
            transfer_count=30,
            total_executions=400,
        )
    except ImportError:
        pytest.skip("UserContextAware entity not available")


# ============================================================
# Service Fixtures
# ============================================================

@pytest.fixture
def response_template_service():
    """Provide ResponseTemplateService instance."""
    try:
        from app.application.chat.services.response_template_service import ResponseTemplateService
        return ResponseTemplateService()
    except ImportError:
        pytest.skip("ResponseTemplateService not available")


@pytest_asyncio.fixture
async def analytics_repository(db_session):
    """Provide AnalyticsRepository instance."""
    try:
        from app.infrastructure.adapters.analytics_repository_sqla import AnalyticsRepositorySqla
        return AnalyticsRepositorySqla(db_session)
    except ImportError:
        pytest.skip("AnalyticsRepositorySqla not available")


# ============================================================
# Analytics Sample Data Fixtures
# ============================================================

@pytest_asyncio.fixture
async def sample_analytics_snapshots(analytics_repository):
    """Create sample analytics snapshots for testing."""
    try:
        from app.domain.chat.entities.analytics_snapshot import (
            AnalyticsSnapshot,
            PortfolioDistribution,
            ActivityDistribution,
            UserTypeDistribution,
            ExecutionMetrics,
        )
        
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
                    very_active=30,
                    active=60,
                    weekly_active=40,
                    monthly_active=20,
                    inactive=30 - i,
                    reactivated=5,
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
                    transfer=30 + i * 3,
                    cashout=10 + i,
                    money_market=10 + i * 2,
                ),
                total_users=190 + i * 8,
                total_balance_usd=Decimal("500000.00") + Decimal(str(i * 10000)),
            )
            await analytics_repository.save(snapshot)
            snapshots.append(snapshot)
        
        return snapshots
    except ImportError:
        pytest.skip("Analytics entities not available")


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
    user_context: Any = None,
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
        user_context: UserContextAware instance
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
        result.portfolio_state = getattr(user_context, "portfolio_state", "")
        result.activity_level = getattr(user_context, "activity_level", "")
        result.user_type = getattr(user_context, "user_type", "")
        result.total_balance_usd = str(getattr(user_context, "total_balance_usd", ""))
    
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
