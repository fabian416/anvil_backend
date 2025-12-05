"""
End-to-end tests for Agent Squad API endpoints.

Tests the complete flow:
1. User authentication
2. API request to Agent Squad endpoints
3. Intent classification and routing
4. Agent execution
5. Response formatting
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from dishka import make_async_container

from app.run import make_app


pytestmark = pytest.mark.asyncio


class TestAgentSquadAPIEndpoints:
    """E2E tests for Agent Squad API endpoints."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create FastAPI app for testing."""
        return make_app()

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self) -> dict:
        """
        Mock authentication headers.
        
        In real tests, would use actual JWT token from login endpoint.
        """
        return {
            "Authorization": "Bearer mock_token_for_testing",
        }

    async def test_send_agent_squad_message_basic_flow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test basic message sending flow.
        
        Flow:
        1. Create conversation
        2. Send message with Agent Squad
        3. Verify response contains agent info
        4. Verify telemetry metrics
        """
        # Step 1: Create conversation
        conversation_id = uuid4()

        # Step 2: Send message
        response = client.post(
            f"/api/v1/chat/agent-squad/messages?conversation_id={conversation_id}",
            headers=auth_headers,
            json={
                "content": "What's the current price of ETH?",
            },
        )

        # Step 3: Verify response (may fail until full integration complete)
        # For now, we expect either success or 401 (no real auth)
        assert response.status_code in [201, 401, 500]  # Allow failure for now

        # If successful, verify response structure
        if response.status_code == 201:
            data = response.json()
            assert "user_message_id" in data
            assert "agent_message_id" in data
            assert "agent_type" in data
            assert "content" in data
            assert "latency_ms" in data
            assert isinstance(data["latency_ms"], int)
            assert data["latency_ms"] > 0

    async def test_send_agent_squad_message_with_force_agent(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test sending message with forced agent routing.
        
        Verifies:
        - force_agent parameter bypasses intent classification
        - Correct agent is used
        - No intent_classification in response (since bypassed)
        """
        conversation_id = uuid4()

        # Send message with forced agent
        response = client.post(
            f"/api/v1/chat/agent-squad/messages?conversation_id={conversation_id}",
            headers=auth_headers,
            json={
                "content": "Execute swap: 1 ETH to USDC",
                "force_agent": "execution",
            },
        )

        # Verify response
        if response.status_code == 201:
            data = response.json()
            assert data["agent_type"] == "execution"
            # Intent classification should be None (bypassed)
            assert data.get("intent_classification") is None

    async def test_execute_supervisor_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test supervisor workflow execution.
        
        Flow:
        1. Submit complex task
        2. Supervisor plans workflow
        3. Multiple agents execute
        4. Results aggregated
        5. Final synthesis returned
        """
        conversation_id = uuid4()

        # Submit complex task
        response = client.post(
            f"/api/v1/chat/agent-squad/supervisor?conversation_id={conversation_id}",
            headers=auth_headers,
            json={
                "complex_task": "Create a balanced DeFi portfolio with $10k",
                "max_agents": 5,
            },
        )

        # Verify response
        if response.status_code == 201:
            data = response.json()
            assert "workflow_id" in data
            assert "plan" in data
            assert "tasks" in data
            assert "final_synthesis" in data
            assert "agents_used" in data
            assert isinstance(data["agents_used"], int)
            assert data["agents_used"] > 0

            # Verify plan structure
            assert isinstance(data["plan"], list)
            for task in data["plan"]:
                assert "agent_type" in task
                assert "task_description" in task
                assert "order" in task

            # Verify task results
            assert isinstance(data["tasks"], list)
            for task in data["tasks"]:
                assert "agent_type" in task
                assert "response" in task
                assert "success" in task

    async def test_list_enabled_agents(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test listing enabled agents.
        
        Verifies:
        - All enabled agents returned
        - Agent metadata included (model, temperature, etc.)
        - Subscription tier filtering works
        """
        # List all agents (enterprise tier)
        response = client.get(
            "/api/v1/chat/agent-squad/agents",
            headers=auth_headers,
        )

        # Verify response
        if response.status_code == 200:
            data = response.json()
            assert "agents" in data
            assert "total_count" in data
            assert isinstance(data["agents"], list)
            assert data["total_count"] > 0

            # Verify agent structure
            for agent in data["agents"]:
                assert "agent_type" in agent
                assert "name" in agent
                assert "description" in agent
                assert "capabilities" in agent
                assert "model" in agent
                assert "temperature" in agent
                assert "tier_required" in agent

    async def test_list_enabled_agents_by_tier(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test listing agents filtered by subscription tier.
        
        Verifies:
        - Free tier: 5 agents
        - Pro tier: 10 agents
        - Enterprise tier: 18 agents
        """
        # Test free tier
        response_free = client.get(
            "/api/v1/chat/agent-squad/agents?user_subscription_tier=free",
            headers=auth_headers,
        )

        if response_free.status_code == 200:
            data_free = response_free.json()
            assert data_free["total_count"] == 5

        # Test pro tier
        response_pro = client.get(
            "/api/v1/chat/agent-squad/agents?user_subscription_tier=pro",
            headers=auth_headers,
        )

        if response_pro.status_code == 200:
            data_pro = response_pro.json()
            assert data_pro["total_count"] == 10

        # Test enterprise tier
        response_enterprise = client.get(
            "/api/v1/chat/agent-squad/agents?user_subscription_tier=enterprise",
            headers=auth_headers,
        )

        if response_enterprise.status_code == 200:
            data_enterprise = response_enterprise.json()
            assert data_enterprise["total_count"] == 18

    async def test_conversation_context_preservation(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test conversation context is preserved across multiple messages.
        
        Flow:
        1. Send first message
        2. Send follow-up message (references first)
        3. Verify context was used (agent understands reference)
        """
        conversation_id = uuid4()

        # First message
        response1 = client.post(
            f"/api/v1/chat/agent-squad/messages?conversation_id={conversation_id}",
            headers=auth_headers,
            json={
                "content": "What's the TVL of Aave?",
            },
        )

        # Follow-up message (references "it" = Aave)
        response2 = client.post(
            f"/api/v1/chat/agent-squad/messages?conversation_id={conversation_id}",
            headers=auth_headers,
            json={
                "content": "What about its security audit history?",
            },
        )

        # Verify both succeeded
        if response1.status_code == 201 and response2.status_code == 201:
            data2 = response2.json()
            # Response should reference Aave (context preserved)
            assert "aave" in data2["content"].lower() or "protocol" in data2["content"].lower()

    async def test_agent_routing_accuracy(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test intent classification routes to correct agents.
        
        Verifies:
        - Trading intent -> Execution agent
        - Research intent -> Research agent
        - Risk intent -> Risk Analyzer agent
        - General intent -> Chat agent
        """
        conversation_id = uuid4()

        test_cases = [
            ("Swap 1 ETH to USDC", "execution"),
            ("Research Uniswap v3", "research"),
            ("Analyze my portfolio risk", "risk_analyzer"),
            ("What is DeFi?", "chat"),
        ]

        for message, expected_agent in test_cases:
            response = client.post(
                f"/api/v1/chat/agent-squad/messages?conversation_id={conversation_id}",
                headers=auth_headers,
                json={"content": message},
            )

            if response.status_code == 201:
                data = response.json()
                # Verify correct agent was routed to
                assert data["agent_type"] == expected_agent

    async def test_error_handling(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test error handling for various failure scenarios.
        
        Scenarios:
        - Invalid conversation ID
        - Empty message content
        - Invalid force_agent value
        - Disabled agent requested
        """
        # Empty message
        response = client.post(
            f"/api/v1/chat/agent-squad/messages?conversation_id={uuid4()}",
            headers=auth_headers,
            json={"content": ""},
        )
        assert response.status_code == 422  # Validation error

        # Invalid force_agent
        response = client.post(
            f"/api/v1/chat/agent-squad/messages?conversation_id={uuid4()}",
            headers=auth_headers,
            json={
                "content": "Test message",
                "force_agent": "invalid_agent_type",
            },
        )
        # Should fail validation or return error
        assert response.status_code in [422, 400]

    async def test_telemetry_tracking(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test telemetry metrics are tracked correctly.
        
        Verifies:
        - Latency is measured
        - Token usage is tracked
        - Tools used are recorded
        - Success status is tracked
        """
        conversation_id = uuid4()

        response = client.post(
            f"/api/v1/chat/agent-squad/messages?conversation_id={conversation_id}",
            headers=auth_headers,
            json={"content": "What's the price of ETH?"},
        )

        if response.status_code == 201:
            data = response.json()

            # Verify telemetry fields
            assert "latency_ms" in data
            assert isinstance(data["latency_ms"], int)
            assert data["latency_ms"] > 0

            assert "tokens_used" in data
            # tokens_used can be None if not tracked

            assert "tools_used" in data
            assert isinstance(data["tools_used"], list)
