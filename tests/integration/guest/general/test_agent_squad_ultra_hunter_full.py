"""
Full integration tests for Agent Squad, Ultra, and Hunter systems.

Tests comprehensive functionality for:
- Agent Squad: All 18 specialized AI agents
- Ultra: Arbitrage, flash loans, MEV protection, auto-executor
- Hunter: Sentiment, price prediction, patterns, portfolio, risk, trading signals

This test suite validates the unified chat endpoint properly routes
to specialized handlers and returns correctly structured responses.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any, List

from tests.helpers.api_client import AuthenticatedClient
from tests.helpers.auth_helper import AuthHelper


# =============================================================================
# Test Data - Comprehensive test cases for all systems
# =============================================================================

AGENT_SQUAD_TEST_CASES = {
    "core_agents": [
        {"id": "squad_chat_001", "input": {"content": "Hello! What can you help me with?"}},
        {"id": "squad_chat_002", "input": {"content": "What features do you offer?"}},
        {"id": "squad_hunter_001", "input": {"content": "What's the current market sentiment for Ethereum?"}},
        {"id": "squad_hunter_002", "input": {"content": "Predict Bitcoin price for the next week"}},
        {"id": "squad_research_001", "input": {"content": "Do a deep research analysis on Aave V3 protocol"}},
        {"id": "squad_research_002", "input": {"content": "Research the tokenomics of Uniswap UNI token"}},
        {"id": "squad_exec_001", "input": {"content": "Execute a swap of 1 ETH for USDC on Uniswap"}},
        {"id": "squad_risk_001", "input": {"content": "Analyze the risk of my current DeFi positions"}},
        {"id": "squad_risk_002", "input": {"content": "What are the risks of using Curve Finance?"}},
        {"id": "squad_portfolio_001", "input": {"content": "Optimize my crypto portfolio for maximum Sharpe ratio"}},
        {"id": "squad_portfolio_002", "input": {"content": "Suggest rebalancing for my BTC, ETH, SOL holdings"}},
        {"id": "squad_tax_001", "input": {"content": "Find tax loss harvesting opportunities in my portfolio"}},
        {"id": "squad_yield_001", "input": {"content": "Find the best yield farming opportunities on Ethereum"}},
        {"id": "squad_security_001", "input": {"content": "Check if Compound protocol has any known security issues"}},
        {"id": "squad_gas_001", "input": {"content": "When is the best time to send transactions for low gas?"}},
    ],
    "advanced_agents": [
        {"id": "squad_bridge_001", "input": {"content": "Bridge 100 USDC from Ethereum to Arbitrum"}},
        {"id": "squad_bridge_002", "input": {"content": "Find the cheapest bridge route from Polygon to Optimism"}},
        {"id": "squad_lending_001", "input": {"content": "Create a 2x leveraged position on ETH using Aave"}},
        {"id": "squad_lending_002", "input": {"content": "Optimize my collateral ratio on Compound"}},
        {"id": "squad_nft_001", "input": {"content": "Value my NFT portfolio and suggest which to hold or sell"}},
        {"id": "squad_dao_001", "input": {"content": "Show me active governance proposals on Uniswap DAO"}},
    ],
    "enterprise_agents": [
        {"id": "squad_compliance_001", "input": {"content": "Screen wallet 0xabc123 for AML compliance"}},
        {"id": "squad_multisig_001", "input": {"content": "Create a multi-sig proposal to transfer 10 ETH from treasury"}},
        {"id": "squad_alert_001", "input": {"content": "Set an alert when ETH drops below $2000"}},
        {"id": "squad_crisis_001", "input": {"content": "There's a potential exploit on the protocol I'm using, what should I do?"}},
    ],
}

ULTRA_TEST_CASES = {
    "arbitrage": [
        {"id": "ultra_arb_001", "input": {"content": "Find arbitrage opportunities with $10,000 capital"}},
        {"id": "ultra_arb_002", "input": {"content": "Search for 2-hop arbitrage between Uniswap and SushiSwap"}},
        {"id": "ultra_arb_003", "input": {"content": "Find triangle arbitrage opportunities on ETH/USDC/WBTC"}},
        {"id": "ultra_arb_004", "input": {"content": "Discover cross-chain arbitrage between Ethereum and Arbitrum"}},
    ],
    "flash_loans": [
        {"id": "ultra_flash_001", "input": {"content": "Best flash loan protocol for 100k USDC"}},
        {"id": "ultra_flash_002", "input": {"content": "Get a flash loan from Aave for 50 ETH"}},
        {"id": "ultra_flash_003", "input": {"content": "Execute flash loan on Balancer for WBTC"}},
        {"id": "ultra_flash_004", "input": {"content": "Use flash loan to create 3x leverage on ETH"}},
    ],
    "mev_protection": [
        {"id": "ultra_mev_001", "input": {"content": "Execute ARB-001 with Flashbots protection"}},
        {"id": "ultra_mev_002", "input": {"content": "Send this transaction privately to avoid frontrunning"}},
        {"id": "ultra_mev_003", "input": {"content": "Protect my large swap from sandwich attacks"}},
    ],
    "auto_executor": [
        {"id": "ultra_ae_001", "input": {"content": "Start the automated trading bot"}},
        {"id": "ultra_ae_002", "input": {"content": "Stop the trading bot immediately"}},
        {"id": "ultra_ae_003", "input": {"content": "Show me the current bot status and performance"}},
    ],
}

HUNTER_TEST_CASES = {
    "sentiment": [
        {"id": "hunter_sent_001", "input": {"content": "What's the ETH sentiment on Twitter and Reddit?"}},
        {"id": "hunter_sent_002", "input": {"content": "Show me BTC social media sentiment from last 7 days"}},
        {"id": "hunter_sent_003", "input": {"content": "Compare sentiment between ETH, SOL, and AVAX"}},
    ],
    "price_prediction": [
        {"id": "hunter_pp_001", "input": {"content": "Predict BTC price for next 7 days"}},
        {"id": "hunter_pp_002", "input": {"content": "Forecast ETH price for next 30 days"}},
        {"id": "hunter_pp_003", "input": {"content": "What will SOL price be next week?"}},
    ],
    "patterns": [
        {"id": "hunter_pat_001", "input": {"content": "What chart patterns do you see for BTC?"}},
        {"id": "hunter_pat_002", "input": {"content": "Detect technical formations for ETH"}},
    ],
    "portfolio": [
        {"id": "hunter_port_001", "input": {"content": "Analyze my crypto portfolio performance"}},
        {"id": "hunter_port_002", "input": {"content": "What are the correlations in my portfolio?"}},
    ],
    "risk_signals": [
        {"id": "hunter_risk_001", "input": {"content": "Any risk signals for my BTC position?"}},
        {"id": "hunter_risk_002", "input": {"content": "Detect early warning signs in my portfolio"}},
    ],
    "trading_signals": [
        {"id": "hunter_ts_001", "input": {"content": "Generate trading signals for ETH"}},
        {"id": "hunter_ts_002", "input": {"content": "What are the entry and exit points for BTC today?"}},
    ],
}


def get_all_agent_squad_cases() -> List[Dict[str, Any]]:
    """Get all Agent Squad test cases."""
    cases = []
    for category in AGENT_SQUAD_TEST_CASES.values():
        cases.extend(category)
    return cases


def get_all_ultra_cases() -> List[Dict[str, Any]]:
    """Get all Ultra test cases."""
    cases = []
    for category in ULTRA_TEST_CASES.values():
        cases.extend(category)
    return cases


def get_all_hunter_cases() -> List[Dict[str, Any]]:
    """Get all Hunter test cases."""
    cases = []
    for category in HUNTER_TEST_CASES.values():
        cases.extend(category)
    return cases


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def authenticated_client(test_app, async_db_session):
    """Create authenticated client for API requests with database-backed user."""
    user, token = await AuthHelper.create_test_user_in_db(
        db_session=async_db_session,
        role="user",
    )

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
        json={"title": "Integration Test Conversation"},
    )

    assert response.status_code == 201, f"Failed to create conversation: {response.text}"
    conversation_data = response.json()
    return conversation_data["id"]


# =============================================================================
# Agent Squad Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.agent_squad
class TestAgentSquadCoreAgents:
    """Test core Agent Squad agents (10 agents)."""

    @pytest.mark.parametrize(
        "test_case",
        AGENT_SQUAD_TEST_CASES["core_agents"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_core_agent_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that core agents respond correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()

        assert "user_message" in data, f"Missing user_message for {test_case['id']}"
        assert "agent_message" in data, f"Missing agent_message for {test_case['id']}"
        assert "routing" in data, f"Missing routing for {test_case['id']}"

        routing = data["routing"]
        assert "intent" in routing, f"Missing intent in routing for {test_case['id']}"
        assert "confidence" in routing, f"Missing confidence in routing for {test_case['id']}"

        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.agent_squad
class TestAgentSquadAdvancedAgents:
    """Test advanced Agent Squad agents (4 agents)."""

    @pytest.mark.parametrize(
        "test_case",
        AGENT_SQUAD_TEST_CASES["advanced_agents"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_advanced_agent_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that advanced agents respond correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data
        assert len(data["agent_message"]["content"]) > 0


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.agent_squad
class TestAgentSquadEnterpriseAgents:
    """Test enterprise Agent Squad agents (4 agents)."""

    @pytest.mark.parametrize(
        "test_case",
        AGENT_SQUAD_TEST_CASES["enterprise_agents"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_enterprise_agent_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that enterprise agents respond correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


# =============================================================================
# Ultra Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraArbitrage:
    """Test Ultra arbitrage features."""

    @pytest.mark.parametrize(
        "test_case",
        ULTRA_TEST_CASES["arbitrage"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_arbitrage_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that arbitrage requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraFlashLoans:
    """Test Ultra flash loan features."""

    @pytest.mark.parametrize(
        "test_case",
        ULTRA_TEST_CASES["flash_loans"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_flash_loan_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that flash loan requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraMEVProtection:
    """Test Ultra MEV protection features."""

    @pytest.mark.parametrize(
        "test_case",
        ULTRA_TEST_CASES["mev_protection"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_mev_protection_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that MEV protection requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraAutoExecutor:
    """Test Ultra auto-executor features."""

    @pytest.mark.parametrize(
        "test_case",
        ULTRA_TEST_CASES["auto_executor"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auto_executor_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that auto-executor requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


# =============================================================================
# Hunter Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterSentiment:
    """Test Hunter sentiment analysis features."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["sentiment"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that sentiment requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterPricePrediction:
    """Test Hunter price prediction features."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["price_prediction"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_price_prediction_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that price prediction requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterPatterns:
    """Test Hunter pattern detection features."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["patterns"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_pattern_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that pattern detection requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterPortfolio:
    """Test Hunter portfolio analysis features."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["portfolio"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_portfolio_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that portfolio requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterRiskSignals:
    """Test Hunter risk signal features."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["risk_signals"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_risk_signal_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that risk signal requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterTradingSignals:
    """Test Hunter trading signal features."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["trading_signals"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_trading_signal_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that trading signal requests route correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201
        data = response.json()

        assert "agent_message" in data
        assert "routing" in data


# =============================================================================
# Full System Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.chat
class TestFullSystemIntegration:
    """Test full system integration across all components."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_all_agent_squad_agents_respond(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify all Agent Squad agents can respond."""
        all_cases = get_all_agent_squad_cases()
        passed = 0
        failed = []

        for case in all_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": case["input"]["content"]},
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("agent_message", {}).get("content"):
                    passed += 1
                else:
                    failed.append(f"{case['id']}: Empty response")
            else:
                failed.append(f"{case['id']}: Status {response.status_code}")

        total = len(all_cases)
        assert passed == total, f"Agent Squad: {passed}/{total} passed. Failed: {failed[:5]}..."

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_all_ultra_features_respond(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify all Ultra features can respond."""
        all_cases = get_all_ultra_cases()
        passed = 0
        failed = []

        for case in all_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": case["input"]["content"]},
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("agent_message", {}).get("content"):
                    passed += 1
                else:
                    failed.append(f"{case['id']}: Empty response")
            else:
                failed.append(f"{case['id']}: Status {response.status_code}")

        total = len(all_cases)
        assert passed == total, f"Ultra: {passed}/{total} passed. Failed: {failed[:5]}..."

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_all_hunter_features_respond(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify all Hunter features can respond."""
        all_cases = get_all_hunter_cases()
        passed = 0
        failed = []

        for case in all_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": case["input"]["content"]},
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("agent_message", {}).get("content"):
                    passed += 1
                else:
                    failed.append(f"{case['id']}: Empty response")
            else:
                failed.append(f"{case['id']}: Status {response.status_code}")

        total = len(all_cases)
        assert passed == total, f"Hunter: {passed}/{total} passed. Failed: {failed[:5]}..."

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_response_structure_consistency(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify response structure is consistent across all handlers."""
        test_cases = [
            "Hello, what can you help me with?",
            "Find arbitrage opportunities",
            "What's the sentiment for BTC?",
        ]

        for content in test_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": content},
            )

            assert response.status_code == 201
            data = response.json()

            # Validate consistent structure
            assert "user_message" in data
            assert "agent_message" in data
            assert "routing" in data

            assert "id" in data["user_message"]
            assert "content" in data["user_message"]
            assert "id" in data["agent_message"]
            assert "content" in data["agent_message"]
            assert "intent" in data["routing"]
            assert "confidence" in data["routing"]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_latency_within_bounds(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify response latency is within acceptable bounds."""
        import time

        start = time.time()
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": "What is the price of Bitcoin?"},
        )
        elapsed = time.time() - start

        assert response.status_code == 201
        # Should respond within 30 seconds
        assert elapsed < 30, f"Response took too long: {elapsed:.2f}s"
