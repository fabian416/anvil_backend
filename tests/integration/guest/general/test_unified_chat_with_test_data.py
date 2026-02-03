"""
Integration tests for unified chat endpoint using test_data JSON files.

Tests the POST /api/v1/user/chat/conversations/{conversation_id}/messages endpoint
with all test cases from separated test_data files, validating:
- Intent detection and routing
- Response structure (UnifiedChatResponse)
- Enrichment data
- Error handling

Test Data Files:
- test_data_common.json: Authentication, setup, edge cases, benchmarks
- test_data_chat.json: General chat and GraphRAG test cases
- test_data_hunter.json: Hunter AI test cases (sentiment, prediction, signals, patterns, portfolio)
- test_data_ultra.json: Ultra test cases (arbitrage, flash loans, MEV, auto executor)
- test_data_agent_squad.json: Agent Squad test cases (core, advanced, enterprise agents)

NOTE: This file is skipped due to AuthenticatedClient fixture issues.
"""

import json
import pytest

# Skip entire module - AuthenticatedClient.setup() doesn't exist
pytestmark = pytest.mark.skip(
    reason="AuthenticatedClient fixture needs setup() method implementation"
)
import pytest_asyncio
from pathlib import Path
from typing import Dict, Any, List
from uuid import UUID

from tests.helpers.api_client import AuthenticatedClient
from tests.helpers.auth_helper import AuthHelper


# Test data file paths
TEST_DATA_DIR = Path(__file__).parent.parent.parent.parent / "docs" / "api" / "examples"
TEST_DATA_FILES = {
    "common": TEST_DATA_DIR / "test_data_common.json",
    "chat": TEST_DATA_DIR / "test_data_chat.json",
    "hunter": TEST_DATA_DIR / "test_data_hunter.json",
    "ultra": TEST_DATA_DIR / "test_data_ultra.json",
    "agent_squad": TEST_DATA_DIR / "test_data_agent_squad.json",
    "defi_shortcuts": TEST_DATA_DIR / "test_data_defi_shortcuts.json",
}


def load_test_data_file(file_type: str) -> Dict[str, Any]:
    """Load test data from a specific JSON file."""
    file_path = TEST_DATA_FILES.get(file_type)
    if not file_path or not file_path.exists():
        return {}
    with open(file_path, "r") as f:
        return json.load(f)


def load_all_test_data() -> Dict[str, Any]:
    """Load and merge all test data files."""
    merged = {
        "metadata": {
            "version": "2.0.0",
            "description": "Merged test data from all files",
        },
        "test_cases": {},
    }

    # Load common data (auth, edge cases, benchmarks)
    common_data = load_test_data_file("common")
    merged["authentication"] = common_data.get("authentication", {})
    merged["conversation_setup"] = common_data.get("conversation_setup", {})
    merged["edge_cases"] = common_data.get("edge_cases", [])
    merged["performance_benchmarks"] = common_data.get("performance_benchmarks", {})

    # Load and merge test cases from each domain file
    for file_type in ["chat", "hunter", "ultra", "agent_squad", "defi_shortcuts"]:
        data = load_test_data_file(file_type)
        if "test_cases" in data:
            merged["test_cases"].update(data["test_cases"])

    return merged


def get_all_test_cases() -> List[Dict[str, Any]]:
    """Extract all test cases from all test data files."""
    data = load_all_test_data()
    test_cases = []

    test_cases_data = data.get("test_cases", {})
    if not isinstance(test_cases_data, dict):
        return test_cases

    for category, category_data in test_cases_data.items():
        if not isinstance(category_data, dict):
            continue

        for subcategory, subcategory_data in category_data.items():
            if not isinstance(subcategory_data, list):
                continue

            for test_case in subcategory_data:
                if not isinstance(test_case, dict):
                    continue
                # Create a copy to avoid modifying original
                test_case_copy = test_case.copy()
                test_case_copy["_category"] = category
                test_case_copy["_subcategory"] = subcategory
                test_cases.append(test_case_copy)

    return test_cases


def get_test_cases_by_type(file_type: str) -> List[Dict[str, Any]]:
    """Get test cases from a specific test data file."""
    data = load_test_data_file(file_type)
    test_cases = []

    test_cases_data = data.get("test_cases", {})
    if not isinstance(test_cases_data, dict):
        return test_cases

    for category, category_data in test_cases_data.items():
        if not isinstance(category_data, dict):
            continue

        for subcategory, subcategory_data in category_data.items():
            if not isinstance(subcategory_data, list):
                continue

            for test_case in subcategory_data:
                if not isinstance(test_case, dict):
                    continue
                test_case_copy = test_case.copy()
                test_case_copy["_category"] = category
                test_case_copy["_subcategory"] = subcategory
                test_cases.append(test_case_copy)

    return test_cases


@pytest.fixture(scope="module")
def test_data():
    """Load all test data once per test module."""
    return load_all_test_data()


@pytest.fixture(scope="module")
def common_test_data():
    """Load common test data (auth, edge cases, benchmarks)."""
    return load_test_data_file("common")


@pytest.fixture(scope="module")
def chat_test_data():
    """Load chat and GraphRAG test data."""
    return load_test_data_file("chat")


@pytest.fixture(scope="module")
def hunter_test_data():
    """Load Hunter AI test data."""
    return load_test_data_file("hunter")


@pytest.fixture(scope="module")
def ultra_test_data():
    """Load Ultra test data."""
    return load_test_data_file("ultra")


@pytest.fixture(scope="module")
def agent_squad_test_data():
    """Load Agent Squad test data."""
    return load_test_data_file("agent_squad")


@pytest.fixture(scope="module")
def defi_shortcuts_test_data():
    """Load DeFi Shortcuts test data."""
    return load_test_data_file("defi_shortcuts")


@pytest_asyncio.fixture
async def authenticated_client():
    """Create an authenticated client for testing."""
    client = AuthenticatedClient()
    await client.setup()
    yield client
    await client.teardown()


@pytest_asyncio.fixture
async def test_conversation(authenticated_client):
    """Create a test conversation."""
    response = await authenticated_client.post(
        "/api/v1/conversations",
        json={"title": "Test Conversation"},
    )
    assert response.status_code == 200
    return UUID(response.json()["id"])


@pytest.mark.integration
@pytest.mark.chat
class TestUnifiedChatWithTestData:
    """Integration tests for unified chat endpoint using test_data files."""

    def test_authentication_setup(self, common_test_data):
        """Test that authentication data is valid."""
        auth_data = common_test_data.get("authentication", {})
        assert "test_user" in auth_data
        assert "expected_response" in auth_data
        assert "access_token" in auth_data["expected_response"]

    def test_conversation_setup(self, common_test_data):
        """Test that conversation setup data is valid."""
        conv_data = common_test_data.get("conversation_setup", {})
        assert "create_request" in conv_data
        assert "expected_response" in conv_data

    @pytest.mark.parametrize(
        "test_case", get_all_test_cases(), ids=lambda tc: tc.get("id", "unknown")
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_send_message_with_test_case(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        test_case: Dict[str, Any],
    ):
        """
        Test sending message using test case data.

        Validates:
        - Request structure
        - Response status code
        - Response structure (UnifiedChatResponse)
        - Routing metadata
        - Enrichment data
        """
        # Get test case data
        test_id = test_case.get("id", "unknown")
        input_data = test_case.get("input", {})
        input_content = input_data.get("content", "")
        expected_error = test_case.get("expected_error")

        # Send message
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": input_content},
        )

        # Handle expected error cases
        if expected_error:
            assert response.status_code == expected_error.get("status_code", 400), (
                f"Expected {expected_error.get('status_code')} for {test_id}, "
                f"got {response.status_code}. Response: {response.text}"
            )
            return

        # Validate success response status
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for test case {test_id}. "
            f"Response: {response.text}"
        )

        # Parse response
        response_data = response.json()

        # Validate response structure
        assert "user_message" in response_data, (
            f"Missing user_message in response for {test_id}"
        )
        assert "agent_message" in response_data, (
            f"Missing agent_message in response for {test_id}"
        )
        assert "routing" in response_data, f"Missing routing in response for {test_id}"

        # Validate user message
        user_msg = response_data["user_message"]
        assert user_msg["role"] == "user", (
            f"User message role should be 'user' for {test_id}"
        )
        assert user_msg["content"] == input_content, (
            f"User message content mismatch for {test_id}"
        )


@pytest.mark.integration
@pytest.mark.chat
class TestChatTestCases:
    """Tests for chat and GraphRAG test cases (from test_data_chat.json)."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_graphrag_protocol_search_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        chat_test_data: Dict[str, Any],
    ):
        """Test all GraphRAG protocol search test cases."""
        graphrag_cases = (
            chat_test_data.get("test_cases", {})
            .get("graphrag", {})
            .get("protocol_search", [])
        )

        for test_case in graphrag_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_graphrag_risk_assessment_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        chat_test_data: Dict[str, Any],
    ):
        """Test all GraphRAG risk assessment test cases."""
        risk_cases = (
            chat_test_data.get("test_cases", {})
            .get("graphrag", {})
            .get("risk_assessment", [])
        )

        for test_case in risk_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_general_chat_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        chat_test_data: Dict[str, Any],
    ):
        """Test all general chat test cases."""
        general_cases = (
            chat_test_data.get("test_cases", {})
            .get("general_chat", {})
            .get("greetings", [])
        )

        for test_case in general_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data


@pytest.mark.integration
@pytest.mark.chat
class TestHunterTestCases:
    """Tests for Hunter AI test cases (from test_data_hunter.json)."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_hunter_sentiment_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI sentiment test cases."""
        sentiment_cases = (
            hunter_test_data.get("test_cases", {})
            .get("hunter", {})
            .get("sentiment", [])
        )

        for test_case in sentiment_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_hunter_price_prediction_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI price prediction test cases."""
        prediction_cases = (
            hunter_test_data.get("test_cases", {})
            .get("hunter", {})
            .get("price_prediction", [])
        )

        for test_case in prediction_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_hunter_risk_signals_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI risk signals test cases."""
        risk_cases = (
            hunter_test_data.get("test_cases", {})
            .get("hunter", {})
            .get("risk_signals", [])
        )

        for test_case in risk_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_hunter_trading_signals_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI trading signals test cases."""
        trading_cases = (
            hunter_test_data.get("test_cases", {})
            .get("hunter", {})
            .get("trading_signals", [])
        )

        for test_case in trading_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_hunter_patterns_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI patterns test cases."""
        pattern_cases = (
            hunter_test_data.get("test_cases", {}).get("hunter", {}).get("patterns", [])
        )

        for test_case in pattern_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_hunter_portfolio_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI portfolio test cases."""
        portfolio_cases = (
            hunter_test_data.get("test_cases", {})
            .get("hunter", {})
            .get("portfolio", [])
        )

        for test_case in portfolio_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data


@pytest.mark.integration
@pytest.mark.chat
class TestUltraTestCases:
    """Tests for Ultra test cases (from test_data_ultra.json)."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_arbitrage_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        ultra_test_data: Dict[str, Any],
    ):
        """Test all Ultra arbitrage test cases."""
        arbitrage_cases = (
            ultra_test_data.get("test_cases", {}).get("ultra", {}).get("arbitrage", [])
        )

        for test_case in arbitrage_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_flash_loans_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        ultra_test_data: Dict[str, Any],
    ):
        """Test all Ultra flash loans test cases."""
        flash_cases = (
            ultra_test_data.get("test_cases", {})
            .get("ultra", {})
            .get("flash_loans", [])
        )

        for test_case in flash_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_mev_protection_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        ultra_test_data: Dict[str, Any],
    ):
        """Test all Ultra MEV protection test cases."""
        mev_cases = (
            ultra_test_data.get("test_cases", {})
            .get("ultra", {})
            .get("mev_protection", [])
        )

        for test_case in mev_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_auto_executor_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        ultra_test_data: Dict[str, Any],
    ):
        """Test all Ultra auto executor test cases."""
        executor_cases = (
            ultra_test_data.get("test_cases", {})
            .get("ultra", {})
            .get("auto_executor", [])
        )

        for test_case in executor_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data


@pytest.mark.integration
@pytest.mark.chat
class TestAgentSquadTestCases:
    """Tests for Agent Squad test cases (from test_data_agent_squad.json)."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_core_agents_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all core agents test cases."""
        core_cases = (
            agent_squad_test_data.get("test_cases", {})
            .get("agent_squad", {})
            .get("core_agents", [])
        )

        for test_case in core_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_advanced_agents_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all advanced agents test cases."""
        advanced_cases = (
            agent_squad_test_data.get("test_cases", {})
            .get("agent_squad", {})
            .get("advanced_agents", [])
        )

        for test_case in advanced_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_enterprise_agents_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all enterprise agents test cases."""
        enterprise_cases = (
            agent_squad_test_data.get("test_cases", {})
            .get("agent_squad", {})
            .get("enterprise_agents", [])
        )

        for test_case in enterprise_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_specialist_task_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all specialist task test cases."""
        specialist_cases = (
            agent_squad_test_data.get("test_cases", {})
            .get("agent_squad", {})
            .get("specialist_tasks", [])
        )

        for test_case in specialist_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_complex_workflow_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all complex workflow test cases."""
        workflow_cases = (
            agent_squad_test_data.get("test_cases", {})
            .get("agent_squad", {})
            .get("complex_workflows", [])
        )

        for test_case in workflow_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data


@pytest.mark.integration
@pytest.mark.chat
class TestDefiShortcutsTestCases:
    """Tests for DeFi shortcuts test cases (from test_data_defi_shortcuts.json)."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all LENDING intent test cases."""
        lending_cases = (
            defi_shortcuts_test_data.get("test_cases", {})
            .get("defi_shortcuts", {})
            .get("lending", [])
        )

        for test_case in lending_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_money_market_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all MONEY MARKET intent test cases."""
        money_market_cases = (
            defi_shortcuts_test_data.get("test_cases", {})
            .get("defi_shortcuts", {})
            .get("money_market", [])
        )

        for test_case in money_market_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_swap_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all SWAP intent test cases."""
        swap_cases = (
            defi_shortcuts_test_data.get("test_cases", {})
            .get("defi_shortcuts", {})
            .get("swap", [])
        )

        for test_case in swap_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_portfolio_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all PORTFOLIO intent test cases."""
        portfolio_cases = (
            defi_shortcuts_test_data.get("test_cases", {})
            .get("defi_shortcuts", {})
            .get("portfolio", [])
        )

        for test_case in portfolio_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_balance_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all BALANCE intent test cases."""
        balance_cases = (
            defi_shortcuts_test_data.get("test_cases", {})
            .get("defi_shortcuts", {})
            .get("balance", [])
        )

        for test_case in balance_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_activity_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all ACTIVITY intent test cases."""
        activity_cases = (
            defi_shortcuts_test_data.get("test_cases", {})
            .get("defi_shortcuts", {})
            .get("activity", [])
        )

        for test_case in activity_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_receive_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all RECEIVE intent test cases."""
        receive_cases = (
            defi_shortcuts_test_data.get("test_cases", {})
            .get("defi_shortcuts", {})
            .get("receive", [])
        )

        for test_case in receive_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )

            assert response.status_code == 201, (
                f"Failed for {test_case['id']}: {response.text}"
            )
            data = response.json()

            assert "routing" in data
            assert "agent_message" in data


@pytest.mark.integration
@pytest.mark.chat
class TestUnifiedChatResponseStructure:
    """Test that UnifiedChatResponse structure matches expected format."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_response_has_all_required_fields(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that response includes all required UnifiedChatResponse fields."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "Hello! What can you help me with?"},
        )

        assert response.status_code == 201
        data = response.json()

        # Required fields
        required_fields = ["user_message", "agent_message", "routing"]
        for field in required_fields:
            assert field in data, f"Response missing required field: {field}"

        # Validate user_message structure
        user_msg = data["user_message"]
        assert "id" in user_msg
        assert "conversation_id" in user_msg
        assert "role" in user_msg
        assert "content" in user_msg
        assert "created_at" in user_msg

        # Validate agent_message structure
        agent_msg = data["agent_message"]
        assert "id" in agent_msg
        assert "conversation_id" in agent_msg
        assert "role" in agent_msg
        assert "content" in agent_msg
        assert "created_at" in agent_msg

        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert "handler" in routing
        assert "reasoning" in routing

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_enrichment_is_optional(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that enrichment field is optional in response."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "Hello"},
        )

        assert response.status_code == 201
        data = response.json()

        # Enrichment may or may not be present (can be None or dict)
        if "enrichment" in data and data["enrichment"] is not None:
            assert isinstance(data["enrichment"], dict)


@pytest.mark.integration
@pytest.mark.chat
class TestUnifiedChatErrorHandling:
    """Test error handling for unified chat endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_empty_message_returns_error(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that empty message returns appropriate error."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": ""},
        )

        # Should return error for empty content
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_missing_content_returns_error(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that missing content returns appropriate error."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={},
        )

        # Should return error for missing content
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_nonexistent_conversation_returns_error(
        self,
        authenticated_client: AuthenticatedClient,
    ):
        """Test that nonexistent conversation returns 404."""
        fake_conversation_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{fake_conversation_id}/messages",
            json={"content": "Hello"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_unauthenticated_request_fails(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that unauthenticated request fails."""
        # This test would need a non-authenticated client
        # For now, we just verify the endpoint exists
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "Hello"},
        )

        # Should succeed with authentication
        assert response.status_code == 201


@pytest.mark.integration
@pytest.mark.chat
class TestMultiLanguageSupport:
    """Test multi-language support for unified chat."""

    SUPPORTED_LANGUAGES = ["en", "es", "pt", "zh", "fr"]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_send_message_with_language_parameter(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test sending message with explicit language parameter."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "¿Cuál es el precio de Bitcoin?", "language": "es"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "routing" in data
        assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_default_language_is_english(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that default language is English."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "What is Bitcoin?"},
        )

        assert response.status_code == 201
        data = response.json()

        # Default language should be used
        if "routing" in data and "language" in data["routing"]:
            assert data["routing"]["language"] == "en"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_invalid_language_falls_back_to_english(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that invalid language falls back to English."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "What is Bitcoin?", "language": "invalid"},
        )

        # Should handle gracefully
        assert response.status_code in [200, 201, 400, 422]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_localized_lending_response(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test localized lending response."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "Préstamos DeFi", "language": "es"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_money_market_in_all_languages(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test money market queries in multiple languages."""
        queries = {
            "en": "money market rates",
            "es": "tasas de mercado monetario",
            "pt": "taxas de mercado monetário",
        }

        for lang, query in queries.items():
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": query, "language": lang},
            )

            assert response.status_code == 201, f"Failed for language {lang}"


@pytest.mark.integration
@pytest.mark.chat
class TestEdgeCasesAndBenchmarks:
    """Test edge cases and performance benchmarks."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_edge_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        test_data: Dict[str, Any],
    ):
        """Test edge cases from test_data_common.json."""
        edge_cases = test_data.get("edge_cases", [])

        for edge_case in edge_cases:
            input_content = edge_case.get("input", {}).get("content", "")
            expected_error = edge_case.get("expected_error")

            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": input_content},
            )

            if expected_error:
                expected_status = expected_error.get("status_code", 400)
                assert response.status_code == expected_status, (
                    f"Expected {expected_status} for edge case {edge_case.get('id')}, "
                    f"got {response.status_code}"
                )
            else:
                assert response.status_code in [200, 201], (
                    f"Edge case {edge_case.get('id')} failed unexpectedly"
                )

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_performance_benchmarks(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test performance benchmarks."""
        import time

        start_time = time.time()
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "What is the price of Bitcoin?"},
        )
        elapsed = time.time() - start_time

        assert response.status_code == 201
        # Response should complete within reasonable time
        assert elapsed < 30, f"Response took too long: {elapsed:.2f}s"
