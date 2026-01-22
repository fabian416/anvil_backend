"""
User Integration Test Configuration and Fixtures.

Provides:
- Dynamic JWT token management (no hardcoded tokens)
- Async HTTP client fixtures
- Conversation management fixtures
- CSV report generation utilities

Token Priority:
1. Environment variable: JWT_TEST_TOKEN
2. Login via API endpoint
3. Create session directly in database
"""

import asyncio
import csv
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# ============================================================
# Configuration
# ============================================================

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8080")
TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "ops@anvilcrypto.com")
TEST_USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "")
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "user"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Data Classes
# ============================================================

@dataclass
class TestResult:
    """Structured test result for CSV output."""
    
    test_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    category: str = ""
    subcategory: str = ""
    is_multi_step: str = "NO"
    step_number: int = 1
    total_steps: int = 1
    input: str = ""
    output: str = ""
    expected_agent: str = ""
    actual_agents: str = ""
    sources: str = ""
    handler: str = ""
    response_time_ms: int = 0
    has_execute_data: str = "NO"
    execute_action_type: str = ""
    user_type: str = "authenticated"
    language: str = "en"
    status: str = "PENDING"
    error_message: str = ""
    conversation_id: str = ""
    # LLM Validation fields
    llm_verdict: str = ""  # PASS/FAIL/WARNING/SKIP
    llm_confidence: float = 0.0
    llm_reasoning: str = ""
    llm_accuracy_score: Optional[float] = None
    llm_relevance_score: Optional[float] = None
    llm_safety_score: Optional[float] = None
    llm_coherence_score: Optional[float] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for CSV writing."""
        return asdict(self)


@dataclass
class TokenInfo:
    """JWT token with metadata."""
    
    token: str
    expires_at: datetime
    user_email: str
    user_id: Optional[int] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 min buffer)."""
        return datetime.now(UTC) >= (self.expires_at - timedelta(minutes=5))
    
    @property
    def authorization_header(self) -> str:
        """Get Authorization header value."""
        return f"Bearer {self.token}"


# ============================================================
# Token Management
# ============================================================

class TokenManager:
    """
    Manages JWT tokens for authenticated user tests.
    
    Token retrieval priority:
    1. Cached valid token
    2. Environment variable JWT_TEST_TOKEN
    3. Login via API
    4. Create session in database
    """
    
    _cached_token: Optional[TokenInfo] = None
    
    @classmethod
    async def get_token(cls, client: Optional[AsyncClient] = None) -> TokenInfo:
        """
        Get a valid JWT token for testing.
        
        Args:
            client: Optional HTTP client for API calls
            
        Returns:
            TokenInfo with valid token
            
        Raises:
            RuntimeError: If unable to obtain a valid token
        """
        # Check cache first
        if cls._cached_token and not cls._cached_token.is_expired:
            return cls._cached_token
        
        # Try environment variable
        env_token = os.environ.get("JWT_TEST_TOKEN")
        if env_token:
            # Decode to get expiration (basic JWT parsing)
            token_info = cls._parse_jwt(env_token)
            if token_info and not token_info.is_expired:
                cls._cached_token = token_info
                return token_info
        
        # Try login via API
        if client and TEST_USER_PASSWORD:
            token_info = await cls._login_via_api(client)
            if token_info:
                cls._cached_token = token_info
                return token_info
        
        # Try database session creation
        token_info = await cls._create_database_session()
        if token_info:
            cls._cached_token = token_info
            return token_info
        
        raise RuntimeError(
            "Unable to obtain JWT token. Set JWT_TEST_TOKEN env var or provide TEST_USER_PASSWORD"
        )
    
    @classmethod
    def _parse_jwt(cls, token: str) -> Optional[TokenInfo]:
        """Parse JWT to extract expiration and user info."""
        import base64
        
        try:
            # Split JWT into parts
            parts = token.split(".")
            if len(parts) != 3:
                return None
            
            # Decode payload (add padding if needed)
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            
            # Extract expiration
            exp = data.get("exp")
            if not exp:
                return None
            
            expires_at = datetime.fromtimestamp(exp, tz=UTC)
            
            return TokenInfo(
                token=token,
                expires_at=expires_at,
                user_email=data.get("email", TEST_USER_EMAIL),
                user_id=data.get("user_id"),
            )
        except Exception:
            return None
    
    @classmethod
    async def _login_via_api(cls, client: AsyncClient) -> Optional[TokenInfo]:
        """Login via API endpoint to get token."""
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/account/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD,
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token")
                expires_at_str = data.get("expires_at")
                
                if token:
                    expires_at = (
                        datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                        if expires_at_str
                        else datetime.now(UTC) + timedelta(hours=1)
                    )
                    
                    return TokenInfo(
                        token=token,
                        expires_at=expires_at,
                        user_email=TEST_USER_EMAIL,
                        user_id=data.get("user_id"),
                    )
        except Exception:
            pass
        
        return None
    
    @classmethod
    async def _create_database_session(cls) -> Optional[TokenInfo]:
        """Create session directly in database."""
        try:
            from app.setup.config.settings import load_settings
            from app.infrastructure.persistence_sqla.mappings.user import map_users_table
            from app.infrastructure.persistence_sqla.mappings.session import map_sessions_table
            from app.infrastructure.persistence_sqla.registry import mapping_registry
            from app.infrastructure.auth.session.id_generator_str import StrAuthSessionIdGenerator
            from app.infrastructure.auth.session.timer_utc import UtcAuthSessionTimer, AuthSessionTtlMin, AuthSessionRefreshThreshold
            from app.presentation.http.auth.access_token_processor_jwt import JwtAccessTokenProcessor
            from app.setup.config.security import SecuritySettings
            
            settings = load_settings()
            security_settings = settings.security
            
            # Map tables
            map_users_table()
            map_sessions_table()
            
            # Create engine
            engine = create_async_engine(settings.postgres.dsn, echo=False)
            async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session_maker() as session:
                users_table = mapping_registry.metadata.tables.get("users")
                sessions_table = mapping_registry.metadata.tables.get("sessions")
                
                if not users_table or not sessions_table:
                    await engine.dispose()
                    return None
                
                # Find user
                stmt = select(users_table.c.id).where(users_table.c.email == TEST_USER_EMAIL)
                result = await session.execute(stmt)
                user_row = result.first()
                
                if not user_row:
                    await engine.dispose()
                    return None
                
                user_id = user_row.id
                
                # Check for existing valid session
                stmt = (
                    select(sessions_table.c.access_token, sessions_table.c.expires_at)
                    .where(sessions_table.c.user_id == user_id)
                    .where(sessions_table.c.is_active == True)
                    .where(sessions_table.c.expires_at > text("CURRENT_TIMESTAMP"))
                    .order_by(sessions_table.c.expires_at.desc())
                    .limit(1)
                )
                result = await session.execute(stmt)
                token_row = result.first()
                
                if token_row:
                    await engine.dispose()
                    return TokenInfo(
                        token=token_row.access_token,
                        expires_at=token_row.expires_at.replace(tzinfo=UTC) if token_row.expires_at.tzinfo is None else token_row.expires_at,
                        user_email=TEST_USER_EMAIL,
                        user_id=user_id,
                    )
                
                # Create new session
                jwt_processor = JwtAccessTokenProcessor(security_settings)
                session_timer = UtcAuthSessionTimer(
                    auth_session_ttl_min=AuthSessionTtlMin(security_settings.auth.session_ttl_min),
                    auth_session_refresh_threshold=AuthSessionRefreshThreshold(security_settings.auth.session_refresh_threshold),
                )
                
                session_id = StrAuthSessionIdGenerator()()
                expiration = session_timer.auth_session_expiration
                
                # Create JWT
                access_token = jwt_processor.encode_auth_session_id(session_id, expiration)
                
                # Insert session
                refresh_token = str(uuid4())
                insert_stmt = sessions_table.insert().values(
                    id=session_id,
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expiration,
                    is_active=True,
                    created_at=datetime.now(UTC),
                )
                await session.execute(insert_stmt)
                await session.commit()
                
                await engine.dispose()
                
                return TokenInfo(
                    token=access_token,
                    expires_at=expiration,
                    user_email=TEST_USER_EMAIL,
                    user_id=user_id,
                )
                
        except Exception as e:
            print(f"Database session creation failed: {e}")
            return None
    
    @classmethod
    def clear_cache(cls):
        """Clear cached token."""
        cls._cached_token = None


# ============================================================
# CSV Reporter
# ============================================================

class CSVReporter:
    """
    Generates CSV reports from test results.
    
    Output files:
    - {category}_{timestamp}.csv: Detailed test results
    - summary_{timestamp}.json: Aggregated summary
    """
    
    CSV_FIELDS = [
        "test_id", "timestamp", "category", "subcategory", "is_multi_step",
        "step_number", "total_steps", "input", "output", "expected_agent",
        "actual_agents", "sources", "handler", "response_time_ms",
        "has_execute_data", "execute_action_type", "user_type", "language",
        "status", "error_message", "conversation_id",
        # LLM Validation fields
        "llm_verdict", "llm_confidence", "llm_reasoning",
        "llm_accuracy_score", "llm_relevance_score", "llm_safety_score", "llm_coherence_score"
    ]
    
    def __init__(self, category: str, output_dir: Path = OUTPUT_DIR):
        """
        Initialize CSV reporter.
        
        Args:
            category: Test category name (e.g., "workflows", "agents")
            output_dir: Directory for output files
        """
        self.category = category
        self.output_dir = output_dir
        self.results: list[TestResult] = []
        self.start_time = datetime.now(UTC)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def add_result(self, result: TestResult):
        """Add a test result."""
        self.results.append(result)
    
    def get_csv_path(self) -> Path:
        """Get path for CSV output file."""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{self.category}_{timestamp}.csv"
    
    def get_summary_path(self) -> Path:
        """Get path for summary JSON file."""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"summary_{self.category}_{timestamp}.json"
    
    def write_csv(self) -> Path:
        """Write results to CSV file."""
        csv_path = self.get_csv_path()
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
            writer.writeheader()
            
            for result in self.results:
                row = result.to_dict()
                # Truncate long fields
                row["output"] = row["output"][:500] if row["output"] else ""
                row["sources"] = row["sources"][:200] if row["sources"] else ""
                writer.writerow(row)
        
        return csv_path
    
    def write_summary(self) -> Path:
        """Write summary JSON file."""
        summary_path = self.get_summary_path()
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        partial = sum(1 for r in self.results if r.status == "PARTIAL")
        failed = sum(1 for r in self.results if r.status in ("FAIL", "ERROR"))
        
        # Group by category
        by_category: dict[str, dict[str, int]] = {}
        for r in self.results:
            cat = r.subcategory or r.category
            if cat not in by_category:
                by_category[cat] = {"total": 0, "pass": 0, "partial": 0, "fail": 0}
            by_category[cat]["total"] += 1
            if r.status == "PASS":
                by_category[cat]["pass"] += 1
            elif r.status == "PARTIAL":
                by_category[cat]["partial"] += 1
            else:
                by_category[cat]["fail"] += 1
        
        # Group by agent
        by_agent: dict[str, dict[str, int]] = {}
        for r in self.results:
            for agent in (r.actual_agents or "").split(","):
                agent = agent.strip()
                if not agent:
                    continue
                if agent not in by_agent:
                    by_agent[agent] = {"total": 0, "pass": 0, "partial": 0, "fail": 0}
                by_agent[agent]["total"] += 1
                if r.status == "PASS":
                    by_agent[agent]["pass"] += 1
                elif r.status == "PARTIAL":
                    by_agent[agent]["partial"] += 1
                else:
                    by_agent[agent]["fail"] += 1
        
        # Calculate average response time
        response_times = [r.response_time_ms for r in self.results if r.response_time_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Find slowest tests
        slowest = sorted(self.results, key=lambda r: r.response_time_ms, reverse=True)[:10]
        
        summary = {
            "run_timestamp": self.start_time.isoformat(),
            "category": self.category,
            "total_tests": total,
            "passed": passed,
            "partial": partial,
            "failed": failed,
            "pass_rate": f"{passed/total*100:.1f}%" if total else "N/A",
            "by_category": by_category,
            "by_agent": by_agent,
            "avg_response_time_ms": int(avg_response_time),
            "slowest_tests": [
                {"test_id": r.test_id, "response_time_ms": r.response_time_ms, "status": r.status}
                for r in slowest
            ],
        }
        
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        
        return summary_path
    
    def print_summary(self):
        """Print summary to console."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        partial = sum(1 for r in self.results if r.status == "PARTIAL")
        failed = sum(1 for r in self.results if r.status in ("FAIL", "ERROR"))
        
        print(f"\n{'='*60}")
        print(f"Test Results: {self.category}")
        print(f"{'='*60}")
        print(f"Total:   {total}")
        print(f"PASS:    {passed} ({passed/total*100:.1f}%)" if total else "N/A")
        print(f"PARTIAL: {partial} ({partial/total*100:.1f}%)" if total else "N/A")
        print(f"FAIL:    {failed} ({failed/total*100:.1f}%)" if total else "N/A")
        print(f"{'='*60}")


# ============================================================
# Pytest Fixtures
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def token_manager() -> TokenManager:
    """Provide token manager instance."""
    return TokenManager()


@pytest_asyncio.fixture(scope="session")
async def auth_token(token_manager: TokenManager) -> TokenInfo:
    """
    Get a valid authentication token.
    
    This fixture provides a JWT token for authenticated API calls.
    Token is cached for the test session.
    """
    return await token_manager.get_token()


@pytest_asyncio.fixture
async def client():
    """
    Create async HTTP test client.
    
    Uses ASGI transport for in-process testing when available,
    otherwise connects to BASE_URL.
    """
    try:
        from app.run import make_app
        app = make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            yield ac
    except ImportError:
        # Fallback to external HTTP client
        async with AsyncClient(base_url=BASE_URL) as ac:
            yield ac


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, auth_token: TokenInfo):
    """
    Provide HTTP client with authentication headers pre-configured.
    """
    client.headers["Authorization"] = auth_token.authorization_header
    yield client


@pytest_asyncio.fixture
async def conversation_id(authenticated_client: AsyncClient) -> str:
    """
    Create a new conversation for testing.
    
    Returns the conversation ID.
    """
    response = await authenticated_client.post(
        "/api/v1/conversations",
        json={"title": f"Test Session {datetime.now(UTC).isoformat()}"},
    )
    
    if response.status_code not in (200, 201):
        # Try legacy endpoint
        response = await authenticated_client.post(
            "/api/v1/user/chat/conversations",
            json={"title": f"Test Session {datetime.now(UTC).isoformat()}", "language": "en"},
        )
    
    assert response.status_code in (200, 201), f"Failed to create conversation: {response.text}"
    
    data = response.json()
    return data.get("id") or data.get("conversation_id")


@pytest.fixture
def csv_reporter(request) -> CSVReporter:
    """
    Provide CSV reporter for test output.
    
    Category is derived from test module name.
    """
    # Get category from test module name
    module_name = request.module.__name__.split(".")[-1]
    category = module_name.replace("test_", "")
    
    reporter = CSVReporter(category=category)
    yield reporter
    
    # Write reports after tests complete
    if reporter.results:
        csv_path = reporter.write_csv()
        summary_path = reporter.write_summary()
        reporter.print_summary()
        print(f"CSV output: {csv_path}")
        print(f"Summary: {summary_path}")


# ============================================================
# Helper Functions
# ============================================================

async def send_message(
    client: AsyncClient,
    conversation_id: str,
    content: str,
    language: str = "en",
    timeout: float = 60.0,
    use_legacy_endpoint: bool = False,
) -> tuple[dict[str, Any], int]:
    """
    Send a message to a conversation and return response data.
    
    Args:
        client: Authenticated HTTP client
        conversation_id: Conversation ID
        content: Message content
        language: Language code
        timeout: Request timeout in seconds
        use_legacy_endpoint: If True, use legacy /api/v1/user/chat/... endpoint
        
    Returns:
        Tuple of (response_data, response_time_ms)
    """
    start_time = time.time()
    
    # Try new endpoint first, fall back to legacy if needed
    if use_legacy_endpoint:
        url = f"/api/v1/user/chat/conversations/{conversation_id}/messages"
    else:
        url = f"/api/v1/conversations/{conversation_id}/messages"
    
    response = await client.post(
        url,
        json={"content": content, "language": language},
        timeout=timeout,
    )
    
    # If new endpoint fails with 404, try legacy
    if response.status_code == 404 and not use_legacy_endpoint:
        response = await client.post(
            f"/api/v1/user/chat/conversations/{conversation_id}/messages",
            json={"content": content, "language": language},
            timeout=timeout,
        )
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    if response.status_code not in (200, 201):
        return {
            "error": True,
            "status_code": response.status_code,
            "message": response.text[:500],
        }, elapsed_ms
    
    data = response.json()
    data["error"] = False
    return data, elapsed_ms


async def create_conversation(
    client: AsyncClient,
    title: str = "",
    language: str = "en",
    use_legacy_endpoint: bool = False,
) -> str:
    """
    Create a new conversation.
    
    Args:
        client: Authenticated HTTP client
        title: Conversation title
        language: Language code
        use_legacy_endpoint: If True, use legacy /api/v1/user/chat/... endpoint
        
    Returns:
        Conversation ID
    """
    if not title:
        title = f"Test Session {datetime.now(UTC).isoformat()}"
    
    if use_legacy_endpoint:
        url = "/api/v1/user/chat/conversations"
        payload = {"title": title, "language": language}
    else:
        url = "/api/v1/conversations"
        payload = {"title": title}
    
    response = await client.post(url, json=payload)
    
    # Fall back to legacy if new endpoint fails
    if response.status_code == 404 and not use_legacy_endpoint:
        response = await client.post(
            "/api/v1/user/chat/conversations",
            json={"title": title, "language": language},
        )
    
    assert response.status_code in (200, 201), f"Failed to create conversation: {response.text}"
    
    data = response.json()
    return data.get("id") or data.get("conversation_id")


def parse_response(data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse API response into standardized format.
    
    Args:
        data: Raw API response data
        
    Returns:
        Standardized response dict
    """
    if data.get("error"):
        return {
            "content": data.get("message", ""),
            "agents_used": "",
            "sources": "",
            "handler": "error",
            "execute_data": None,
            "user_type": "",
            "error": True,
            "error_message": data.get("message", ""),
        }
    
    routing = data.get("routing", {})
    enrichment = data.get("enrichment", {})
    agent_message = data.get("agent_message", {})
    
    return {
        "content": agent_message.get("content", ""),
        "agents_used": ",".join(
            routing.get("agents_used", []) or
            enrichment.get("agents_used", [])
        ),
        "sources": json.dumps(agent_message.get("sources", []))[:200] if agent_message.get("sources") else "",
        "handler": routing.get("handler", ""),
        "execute_data": data.get("execute"),
        "user_type": routing.get("user_type", ""),
        "error": False,
        "error_message": enrichment.get("metadata", {}).get("error", ""),
    }


def create_test_result(
    test_id: str,
    test_case: dict[str, Any],
    response_data: dict[str, Any],
    response_time_ms: int,
    conversation_id: str = "",
    llm_validation: Optional[Any] = None,
) -> TestResult:
    """
    Create a TestResult from test case and response data.
    
    Args:
        test_id: Unique test identifier
        test_case: Test case definition
        response_data: Parsed response data
        response_time_ms: Response time in milliseconds
        conversation_id: Conversation ID
        llm_validation: Optional LLM validation result
        
    Returns:
        TestResult instance
    """
    parsed = parse_response(response_data) if not response_data.get("error") else response_data
    
    # Determine status
    expected_agent = test_case.get("expected_agent", "")
    actual_agents = parsed.get("agents_used", "")
    has_execute = bool(parsed.get("execute_data"))
    
    if parsed.get("error"):
        status = "FAIL"
    elif expected_agent and expected_agent in actual_agents:
        status = "PASS" if has_execute or not test_case.get("requires_execute") else "PARTIAL"
    elif actual_agents:
        status = "PARTIAL"
    else:
        status = "FAIL"
    
    # Extract LLM validation fields
    llm_verdict = ""
    llm_confidence = 0.0
    llm_reasoning = ""
    llm_accuracy_score = None
    llm_relevance_score = None
    llm_safety_score = None
    llm_coherence_score = None
    
    if llm_validation:
        llm_verdict = llm_validation.verdict.value if hasattr(llm_validation.verdict, 'value') else str(llm_validation.verdict)
        llm_confidence = llm_validation.confidence
        llm_reasoning = llm_validation.reasoning[:500] if llm_validation.reasoning else ""
        
        if llm_validation.scoring:
            llm_accuracy_score = llm_validation.scoring.accuracy_score
            llm_relevance_score = llm_validation.scoring.relevance_score
            llm_safety_score = llm_validation.scoring.safety_score
            llm_coherence_score = llm_validation.scoring.coherence_score
    
    return TestResult(
        test_id=test_id,
        category=test_case.get("category", ""),
        subcategory=test_case.get("subcategory", ""),
        is_multi_step="YES" if test_case.get("is_multi_step") else "NO",
        step_number=test_case.get("step_number", 1),
        total_steps=test_case.get("total_steps", 1),
        input=test_case.get("input", ""),
        output=parsed.get("content", "")[:500],
        expected_agent=expected_agent,
        actual_agents=actual_agents,
        sources=parsed.get("sources", ""),
        handler=parsed.get("handler", ""),
        response_time_ms=response_time_ms,
        has_execute_data="YES" if has_execute else "NO",
        execute_action_type=parsed.get("execute_data", {}).get("action_type", "") if has_execute else "",
        user_type=parsed.get("user_type", "authenticated"),
        language=test_case.get("language", "en"),
        status=status,
        error_message=parsed.get("error_message", ""),
        conversation_id=conversation_id,
        llm_verdict=llm_verdict,
        llm_confidence=llm_confidence,
        llm_reasoning=llm_reasoning,
        llm_accuracy_score=llm_accuracy_score,
        llm_relevance_score=llm_relevance_score,
        llm_safety_score=llm_safety_score,
        llm_coherence_score=llm_coherence_score,
    )


async def validate_with_llm(
    llm_validator: Any,
    test_name: str,
    user_input: str,
    agent_output: str,
    expected_behavior: str,
    additional_context: Optional[dict[str, Any]] = None,
) -> Optional[Any]:
    """
    Validate response using LLM if enabled.
    
    Args:
        llm_validator: LLM validator fixture
        test_name: Name of the test
        user_input: User input
        agent_output: Agent output
        expected_behavior: Expected behavior description
        additional_context: Optional additional context
        
    Returns:
        ValidationResult or None if validation is disabled
    """
    if not llm_validator or not llm_validator.enabled:
        return None
    
    try:
        return await llm_validator.validate_single_response(
            test_name=test_name,
            user_input=user_input,
            agent_output=agent_output,
            expected_behavior=expected_behavior,
            additional_context=additional_context,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"LLM validation failed: {e}")
        return None
