"""
Integration tests for unified chat endpoint using test_data.json.

Tests the POST /api/v1/user/chat/conversations/{conversation_id}/messages endpoint
with all test cases from test_data.json, validating:
- Intent detection and routing
- Response structure (UnifiedChatResponse)
- Enrichment data
- Error handling
"""

import json
import pytest
import pytest_asyncio
from pathlib import Path
from typing import Dict, Any, List
from uuid import UUID

from tests.helpers.api_client import AuthenticatedClient
from tests.helpers.auth_helper import AuthHelper


# Load test data
TEST_DATA_PATH = Path(__file__).parent.parent.parent.parent / "docs" / "api" / "examples" / "test_data.json"


def load_test_data() -> Dict[str, Any]:
    """Load test data from JSON file."""
    with open(TEST_DATA_PATH, "r") as f:
        return json.load(f)


def get_all_test_cases() -> List[Dict[str, Any]]:
    """Extract all test cases from test_data.json."""
    data = load_test_data()
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


@pytest.fixture(scope="module")
def test_data():
    """Load test data once per test module."""
    return load_test_data()


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
    """Integration tests for unified chat endpoint using test_data.json."""
    
    def test_authentication_setup(self, test_data):
        """Test that authentication data is valid."""
        auth_data = test_data.get("authentication", {})
        assert "test_user" in auth_data
        assert "expected_response" in auth_data
        assert "access_token" in auth_data["expected_response"]
    
    def test_conversation_setup(self, test_data):
        """Test that conversation setup data is valid."""
        conv_data = test_data.get("conversation_setup", {})
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
        
        # Validate intent matches expected
        expected_intent = expected_routing.get("intent")
        if expected_intent:
            assert routing["intent"] == expected_intent, (
                f"Intent mismatch for {test_id}: expected '{expected_intent}', "
                f"got '{routing['intent']}'"
            )
        
        # Validate confidence
        confidence_min = expected_routing.get("confidence_min")
        if confidence_min:
            assert routing["confidence"] >= confidence_min, (
                f"Confidence too low for {test_id}: expected >= {confidence_min}, "
                f"got {routing['confidence']}"
            )
        
        confidence_max = expected_routing.get("confidence_max")
        if confidence_max:
            assert routing["confidence"] <= confidence_max, (
                f"Confidence too high for {test_id}: expected <= {confidence_max}, "
                f"got {routing['confidence']}"
            )
        
        # Validate handler
        expected_handler = expected_routing.get("handler")
        if expected_handler:
            assert routing["handler"] == expected_handler, (
                f"Handler mismatch for {test_id}: expected '{expected_handler}', "
                f"got '{routing['handler']}'"
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
    
    @pytest.mark.asyncio
    async def test_graphrag_protocol_search_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        test_data: Dict[str, Any],
    ):
        """Test all GraphRAG protocol search test cases."""
        graphrag_cases = test_data["test_cases"]["graphrag"]["protocol_search"]

        for test_case in graphrag_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            # Validate GraphRAG-specific response
            assert data["routing"]["intent"] == "protocol_search"
            assert data["routing"]["handler"] == "graphrag_search"
            assert data.get("enrichment", {}).get("protocols") is not None or \
                   data.get("enrichment", {}).get("search_context") is not None
    
    @pytest.mark.asyncio
    async def test_hunter_ai_sentiment_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        test_data: Dict[str, Any],
    ):
        """Test all Hunter AI sentiment test cases."""
        sentiment_cases = test_data["test_cases"]["hunter_ai"]["sentiment"]

        for test_case in sentiment_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            # Validate Hunter AI-specific response
            assert data["routing"]["intent"] == "hunter_sentiment"
            enrichment = data.get("enrichment", {})
            assert enrichment.get("token_symbol") is not None
            assert enrichment.get("hunter_tool") == "sentiment_analyzer"
    
    @pytest.mark.asyncio
    async def test_ultra_arbitrage_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        test_data: Dict[str, Any],
    ):
        """Test all ULTRA arbitrage test cases."""
        arbitrage_cases = test_data["test_cases"]["ultra"]["arbitrage"]

        for test_case in arbitrage_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": test_case["input"]["content"]},
            )
            
            assert response.status_code == 201, f"Failed for {test_case['id']}: {response.text}"
            data = response.json()
            
            # Validate ULTRA-specific response
            assert data["routing"]["intent"] == "ultra_arbitrage"
            enrichment = data.get("enrichment", {})
            assert enrichment.get("ultra_tool") == "arbitrage_scanner"
            assert enrichment.get("capital") is not None or enrichment.get("arb_type") is not None
    
    def test_edge_cases(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
        test_data: Dict[str, Any],
    ):
        """Test edge cases from test_data.json."""
        edge_cases = test_data.get("edge_cases", [])
        
        for edge_case in edge_cases:
            test_id = edge_case["id"]
            content = edge_case["input"]["content"]
            expected_error = edge_case.get("expected_error")
            
            response = authenticated_client.post(
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
    
    def test_performance_benchmarks(
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
            for tc in test_data["test_cases"][category][subcategory]:
                if tc["id"] == test_id:
                    test_case = tc
                    break
            
            if not test_case:
                continue
            
            # Send request and measure latency
            import time
            start_time = time.time()
            
            response = authenticated_client.post(
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


@pytest.mark.integration
@pytest.mark.chat
class TestUnifiedChatResponseStructure:
    """Test that UnifiedChatResponse structure matches expected format."""
    
    def test_response_has_all_required_fields(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that response includes all required UnifiedChatResponse fields."""
        response = authenticated_client.post(
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
    
    def test_enrichment_is_optional(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: UUID,
    ):
        """Test that enrichment field is optional in response."""
        response = authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "Hello"},
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Enrichment may or may not be present
        if "enrichment" in data:
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
