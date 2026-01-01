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
"""

import json
import pytest
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
    """Load DeFi shortcuts test data (LENDING, MONEY_MARKET, SWAP, etc.)."""
    return load_test_data_file("defi_shortcuts")


@pytest.fixture(scope="module")
def all_test_cases():
    """Get all test cases once per test module."""
    return get_all_test_cases()


@pytest_asyncio.fixture
async def authenticated_client(test_app, async_db_session):
    """Create authenticated client for API requests with database-backed user."""
    from tests.helpers.auth_helper import AuthHelper
    import asyncio

    # Create user in database
    user, token = await AuthHelper.create_test_user_in_db(
        db_session=async_db_session,
        role="user",
    )

    # Create authenticated client with real token
    client = AuthenticatedClient()
    client.set_app(test_app)
    client._access_token = token
    client._current_user = user
    client._update_headers()

    return client


@pytest_asyncio.fixture
async def test_conversation(authenticated_client):
    """Create a test conversation for message testing."""
    response = await authenticated_client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Test Conversation"},
    )

    assert response.status_code == 201, f"Failed to create conversation: {response.text}"
    conversation_data = response.json()
    return conversation_data["id"]


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
    
    @pytest.mark.parametrize("test_case", get_all_test_cases(), ids=lambda tc: tc["id"])
    @pytest.mark.asyncio
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
        test_id = test_case["id"]
        input_content = test_case["input"]["content"]
        expected_routing = test_case.get("expected_routing", {})
        expected_enrichment = test_case.get("expected_enrichment", {})
        expected_output = test_case.get("expected_output")
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
            # Error case validated, skip further checks
            return

        # Validate success response status
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for test case {test_id}. "
            f"Response: {response.text}"
        )

        # Parse response
        response_data = response.json()
        
        # Validate response structure
        assert "user_message" in response_data, f"Missing user_message in response for {test_id}"
        assert "agent_message" in response_data, f"Missing agent_message in response for {test_id}"
        assert "routing" in response_data, f"Missing routing in response for {test_id}"
        
        # Validate user message
        user_msg = response_data["user_message"]
        assert user_msg["role"] == "user", f"User message role should be 'user' for {test_id}"
        assert user_msg["content"] == input_content, f"User message content mismatch for {test_id}"
        assert "id" in user_msg, f"User message missing id for {test_id}"
        assert "conversation_id" in user_msg, f"User message missing conversation_id for {test_id}"
        
        # Validate agent message
        agent_msg = response_data["agent_message"]
        assert agent_msg["role"] == "assistant", f"Agent message role should be 'assistant' for {test_id}"
        assert "content" in agent_msg, f"Agent message missing content for {test_id}"
        assert len(agent_msg["content"]) > 0, f"Agent message content is empty for {test_id}"
        assert "id" in agent_msg, f"Agent message missing id for {test_id}"
        
        # Validate routing metadata
        routing = response_data["routing"]
        assert "intent" in routing, f"Routing missing intent for {test_id}"
        assert "confidence" in routing, f"Routing missing confidence for {test_id}"
        assert "handler" in routing, f"Routing missing handler for {test_id}"
        assert "reasoning" in routing, f"Routing missing reasoning for {test_id}"
        
        # Validate confidence is reasonable (minimum 0.5 for any valid response)
        assert routing["confidence"] >= 0.5, (
            f"Confidence too low for {test_id}: got {routing['confidence']}"
        )
        
        # Validate confidence max if specified (for fallback tests)
        confidence_max = expected_routing.get("confidence_max")
        if confidence_max:
            assert routing["confidence"] <= confidence_max, (
                f"Confidence too high for {test_id}: expected <= {confidence_max}, "
                f"got {routing['confidence']}"
            )
        
        # Validate enrichment data (if present)
        enrichment = response_data.get("enrichment")
        if enrichment:
            # Validate category-specific enrichment
            category = test_case.get("_category")
            subcategory = test_case.get("_subcategory")
            
            if category == "graphrag":
                if subcategory == "protocol_search":
                    assert "protocols" in enrichment or "search_context" in enrichment, (
                        f"GraphRAG protocol search missing enrichment for {test_id}"
                    )
                elif subcategory == "risk_assessment":
                    assert "risk_analysis" in enrichment or "protocol_name" in enrichment, (
                        f"GraphRAG risk assessment missing enrichment for {test_id}"
                    )
                elif subcategory == "similar_protocols":
                    assert "similar_protocols" in enrichment or "base_protocol" in enrichment, (
                        f"GraphRAG similar protocols missing enrichment for {test_id}"
                    )
            
            elif category == "hunter_ai":
                if "token_symbol" in expected_enrichment:
                    assert enrichment.get("token_symbol") == expected_enrichment["token_symbol"], (
                        f"Token symbol mismatch for {test_id}"
                    )
                if "hunter_tool" in expected_enrichment:
                    assert enrichment.get("hunter_tool") == expected_enrichment["hunter_tool"], (
                        f"Hunter tool mismatch for {test_id}"
                    )
            
            elif category == "ultra":
                if "ultra_tool" in expected_enrichment:
                    assert enrichment.get("ultra_tool") == expected_enrichment["ultra_tool"], (
                        f"ULTRA tool mismatch for {test_id}"
                    )
                if "capital" in expected_enrichment:
                    assert enrichment.get("capital") == expected_enrichment["capital"], (
                        f"Capital mismatch for {test_id}"
                    )
            
            elif category == "agent_squad":
                if "task_type" in expected_enrichment:
                    assert enrichment.get("task_type") == expected_enrichment["task_type"], (
                        f"Task type mismatch for {test_id}"
                    )
                if "workflow_type" in expected_enrichment:
                    assert enrichment.get("workflow_type") == expected_enrichment["workflow_type"], (
                        f"Workflow type mismatch for {test_id}"
                    )
        
        # Validate latency is reasonable
        if "total_latency_ms" in routing:
            assert routing["total_latency_ms"] > 0, f"Latency should be positive for {test_id}"
            assert routing["total_latency_ms"] < 30000, f"Latency too high for {test_id}"


@pytest.mark.integration
@pytest.mark.chat
class TestChatTestCases:
    """Tests for chat and GraphRAG test cases (from test_data_chat.json)."""
    
    @pytest.mark.asyncio
    async def test_graphrag_protocol_search_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        chat_test_data: Dict[str, Any],
    ):
        """Test all GraphRAG protocol search test cases."""
        graphrag_cases = chat_test_data["test_cases"]["graphrag"]["protocol_search"]

        for test_case in graphrag_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            # Validate response structure and non-empty content
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_graphrag_risk_assessment_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        chat_test_data: Dict[str, Any],
    ):
        """Test all GraphRAG risk assessment test cases."""
        risk_cases = chat_test_data["test_cases"]["graphrag"]["risk_assessment"]

        for test_case in risk_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_general_chat_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        chat_test_data: Dict[str, Any],
    ):
        """Test all general chat test cases."""
        chat_cases = chat_test_data["test_cases"]["chat"]["general_conversation"]

        for test_case in chat_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterTestCases:
    """Tests for Hunter AI test cases (from test_data_hunter.json)."""
    
    @pytest.mark.asyncio
    async def test_hunter_sentiment_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI sentiment test cases."""
        sentiment_cases = hunter_test_data["test_cases"]["hunter_ai"]["sentiment"]

        for test_case in sentiment_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_hunter_price_prediction_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI price prediction test cases."""
        prediction_cases = hunter_test_data["test_cases"]["hunter_ai"]["price_prediction"]

        for test_case in prediction_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_hunter_risk_signals_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI risk signals test cases."""
        risk_cases = hunter_test_data["test_cases"]["hunter_ai"]["risk_signals"]

        for test_case in risk_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_hunter_trading_signals_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI trading signals test cases."""
        trading_cases = hunter_test_data["test_cases"]["hunter_ai"]["trading_signals"]

        for test_case in trading_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_hunter_patterns_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI pattern detection test cases."""
        pattern_cases = hunter_test_data["test_cases"]["hunter_ai"]["patterns"]

        for test_case in pattern_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_hunter_portfolio_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        hunter_test_data: Dict[str, Any],
    ):
        """Test all Hunter AI portfolio optimization test cases."""
        portfolio_cases = hunter_test_data["test_cases"]["hunter_ai"]["portfolio"]

        for test_case in portfolio_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraTestCases:
    """Tests for Ultra test cases (from test_data_ultra.json)."""
    
    @pytest.mark.asyncio
    async def test_ultra_arbitrage_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        ultra_test_data: Dict[str, Any],
    ):
        """Test all ULTRA arbitrage test cases."""
        arbitrage_cases = ultra_test_data["test_cases"]["ultra"]["arbitrage"]

        for test_case in arbitrage_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_ultra_flash_loans_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        ultra_test_data: Dict[str, Any],
    ):
        """Test all ULTRA flash loans test cases."""
        flash_loan_cases = ultra_test_data["test_cases"]["ultra"]["flash_loans"]

        for test_case in flash_loan_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_ultra_mev_protection_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        ultra_test_data: Dict[str, Any],
    ):
        """Test all ULTRA MEV protection test cases."""
        mev_cases = ultra_test_data["test_cases"]["ultra"]["mev_protection"]

        for test_case in mev_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_ultra_auto_executor_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        ultra_test_data: Dict[str, Any],
    ):
        """Test all ULTRA auto executor test cases."""
        executor_cases = ultra_test_data["test_cases"]["ultra"]["auto_executor"]

        for test_case in executor_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.agent_squad
class TestAgentSquadTestCases:
    """Tests for Agent Squad test cases (from test_data_agent_squad.json)."""
    
    @pytest.mark.asyncio
    async def test_core_agents_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all Agent Squad core agent test cases."""
        core_cases = agent_squad_test_data["test_cases"]["agent_squad"]["core_agents"]

        for test_case in core_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_advanced_agents_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all Agent Squad advanced agent test cases."""
        advanced_cases = agent_squad_test_data["test_cases"]["agent_squad"]["advanced_agents"]

        for test_case in advanced_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_enterprise_agents_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all Agent Squad enterprise agent test cases."""
        enterprise_cases = agent_squad_test_data["test_cases"]["agent_squad"]["enterprise_agents"]

        for test_case in enterprise_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_specialist_task_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all Agent Squad specialist task test cases."""
        specialist_cases = agent_squad_test_data["test_cases"]["agent_squad"]["specialist_task"]

        for test_case in specialist_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_complex_workflow_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        agent_squad_test_data: Dict[str, Any],
    ):
        """Test all Agent Squad complex workflow test cases."""
        workflow_cases = agent_squad_test_data["test_cases"]["agent_squad"]["complex_workflow"]

        for test_case in workflow_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.defi_shortcuts
class TestDefiShortcutsTestCases:
    """Tests for DeFi shortcut intents (from test_data_defi_shortcuts.json)."""
    
    @pytest.mark.asyncio
    async def test_lending_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all LENDING intent test cases (Morpho vaults)."""
        lending_cases = defi_shortcuts_test_data["test_cases"]["defi_shortcuts"]["lending"]

        for test_case in lending_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_money_market_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all MONEY_MARKET intent test cases (Aave + Compound)."""
        money_market_cases = defi_shortcuts_test_data["test_cases"]["defi_shortcuts"]["money_market"]

        for test_case in money_market_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_swap_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all SWAP intent test cases (1inch + LiFi + Hyperliquid)."""
        swap_cases = defi_shortcuts_test_data["test_cases"]["defi_shortcuts"]["swap"]

        for test_case in swap_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_portfolio_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all PORTFOLIO intent test cases."""
        portfolio_cases = defi_shortcuts_test_data["test_cases"]["defi_shortcuts"]["portfolio"]

        for test_case in portfolio_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_balance_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all BALANCE intent test cases."""
        balance_cases = defi_shortcuts_test_data["test_cases"]["defi_shortcuts"]["balance"]

        for test_case in balance_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_activity_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all ACTIVITY intent test cases."""
        activity_cases = defi_shortcuts_test_data["test_cases"]["defi_shortcuts"]["activity"]

        for test_case in activity_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_receive_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        defi_shortcuts_test_data: Dict[str, Any],
    ):
        """Test all RECEIVE intent test cases."""
        receive_cases = defi_shortcuts_test_data["test_cases"]["defi_shortcuts"]["receive"]

        for test_case in receive_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            assert "routing" in data
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0
            assert data["routing"]["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
class TestUnifiedChatResponseStructure:
    """Test that UnifiedChatResponse structure matches expected format."""
    
    @pytest.mark.asyncio
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
    async def test_empty_message_returns_error(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that empty message returns validation error."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": ""},
        )

        assert response.status_code == 422, "Empty message should return 422"
    
    @pytest.mark.asyncio
    async def test_missing_content_returns_error(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that missing content field returns error."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={},
        )

        assert response.status_code == 422, "Missing content should return 422"
    
    @pytest.mark.asyncio
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

        assert response.status_code == 404, "Nonexistent conversation should return 404"
    
    @pytest.mark.asyncio
    async def test_unauthenticated_request_fails(
        self,
        test_app,
        test_conversation: UUID,
    ):
        """Test that unauthenticated request returns 401."""
        from httpx import AsyncClient, ASGITransport

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": "Hello"},
            )

            assert response.status_code == 401, "Unauthenticated request should return 401"


@pytest.mark.integration
@pytest.mark.chat
class TestEdgeCasesAndBenchmarks:
    """Test edge cases and performance benchmarks."""
    
    @pytest.mark.asyncio
    async def test_edge_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        common_test_data: Dict[str, Any],
    ):
        """Test edge cases from test_data_common.json."""
        edge_cases = common_test_data.get("edge_cases", [])

        for edge_case in edge_cases:
            test_id = edge_case["id"]
            content = edge_case["input"]["content"]
            expected_error = edge_case.get("expected_error")

            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": content},
            )
            
            if expected_error:
                # Should return error
                assert response.status_code == expected_error["status_code"], (
                    f"Expected {expected_error['status_code']} for {test_id}, "
                    f"got {response.status_code}"
                )
            else:
                # Should succeed but with routing validation
                assert response.status_code in [201, 400, 422], (
                    f"Unexpected status {response.status_code} for {test_id}"
                )
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        test_data: Dict[str, Any],
    ):
        """Test that responses meet performance benchmarks."""
        benchmarks = test_data.get("performance_benchmarks", {})
        latency_targets = benchmarks.get("latency_targets", {})

        # Test a sample from each category
        sample_cases = [
            ("graphrag", "protocol_search", "graphrag_ps_001"),
            ("hunter_ai", "sentiment", "hunter_sent_001"),
            ("ultra", "arbitrage", "ultra_arb_001"),
            ("chat", "general_conversation", "chat_gen_001"),
        ]

        for category, subcategory, test_id in sample_cases:
            # Find test case
            test_case = None
            category_data = test_data.get("test_cases", {}).get(category, {})
            subcategory_data = category_data.get(subcategory, [])
            
            for tc in subcategory_data:
                if tc["id"] == test_id:
                    test_case = tc
                    break

            if not test_case:
                continue

            # Send request and measure latency
            import time
            start_time = time.time()

            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            assert response.status_code == 201, f"Request failed for {test_id}"
            data = response.json()
            
            # Get latency target for handler
            handler = data["routing"]["handler"]
            handler_targets = latency_targets.get(handler, latency_targets.get("general_chat", {}))
            p95_target = handler_targets.get("p95", 5000)  # Default 5s
            
            # Validate latency (allow some margin for test environment)
            assert elapsed_ms < p95_target * 1.5, (
                f"Latency {elapsed_ms:.0f}ms exceeds p95 target {p95_target}ms "
                f"for {test_id} (handler: {handler})"
            )
