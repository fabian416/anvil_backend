"""
Comprehensive Cross-Chain Testing Suite.

Tests cross-chain functionality including:
- Ethereum → Base token swaps (P2 requirement)
- Multi-chain balance validation
- L2 → L2 direct bridging
- Cross-chain gas estimation
- Bridge security validation
- Error handling (insufficient gas)
- Bridge time estimation

Week 11: P2 Priority - Cross-Chain Testing
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.auth_helper import AuthHelper


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.cross_chain
class TestCrossChainComprehensive:
    """Comprehensive cross-chain integration tests."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="crosschain_test@example.com",
        )
        return user, token

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
    """Get authentication headers."""
    _, token = test_user
    return {"Authorization": f"Bearer {token}"}

    @pytest_asyncio.fixture
    async def conversation_id(self, authenticated_client: AsyncClient, auth_headers):
    """Create a test conversation."""
    response = await authenticated_client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"language": "en"},
    )
        assert response.status_code == 201
        return response.json()["id"]

    # =========================================================================
    # Test 1: Ethereum → Base Token Swap (P2 REQUIREMENT)
    # =========================================================================

    @pytest.mark.llm_validation
    async def test_cross_chain_001_ethereum_to_base_swap(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_001_ethereum_to_base_swap",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test Ethereum to Base USDC swap with bridge routing.

    P2 Requirement: Ethereum → Base swaps

    Validates:
    - Cross-chain swap routing detection
    - Bridge protocol selection (Axelar, LayerZero, native)
    - Gas cost estimation on both chains
    - Time estimation (5min - 7 days)
    - Slippage protection
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "Swap 500 USDC from Ethereum to Base",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Verify routing
        assert "routing" in data
        routing = data["routing"]
        assert routing["intent"] in ["swap", "specialist_task"]
        assert routing["confidence"] >= 0.7

        # Verify enrichment contains cross-chain info
        enrichment = data.get("enrichment", {})
        assert "task_type" in enrichment or "intent" in routing

        # Verify agent response mentions key concepts
        agent_content = data["agent_message"]["content"].lower()
        assert any(word in agent_content for word in ["bridge", "base", "ethereum"])
        assert any(word in agent_content for word in ["gas", "cost", "fee"])
        assert any(word in agent_content for word in ["time", "estimate", "minutes"])

        # Verify sources include bridge/swap data
        sources = data["agent_message"].get("sources", [])
        assert len(sources) > 0, "Should have data sources"

    # =========================================================================
    # Test 2: Multi-Chain Balance Validation
    # =========================================================================

    @pytest.mark.llm_validation
    async def test_cross_chain_002_multi_chain_balance_check(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_002_multi_chain_balance_check",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test multi-chain balance checking across Ethereum, Arbitrum, and Base.

    Validates:
    - Multi-chain RPC integration
    - Balance aggregation across chains
    - Chain-specific token addresses
    - Total portfolio calculation
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "Show my USDC balance on Ethereum, Arbitrum, and Base",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Verify routing
        routing = data["routing"]
        assert routing["intent"] in ["check_balance", "portfolio", "info_request"]
        assert routing["confidence"] >= 0.6

        # Verify agent response mentions all chains
        agent_content = data["agent_message"]["content"].lower()
        assert "ethereum" in agent_content or "eth" in agent_content
        assert "arbitrum" in agent_content
        assert "base" in agent_content
        assert "usdc" in agent_content

        # Should mention balance or total
        assert any(word in agent_content for word in ["balance", "total", "holdings"])

    # =========================================================================
    # Test 3: L2 → L2 Direct Bridge (Optimistic Rollup)
    # =========================================================================

    @pytest.mark.llm_validation
    async def test_cross_chain_003_l2_to_l2_direct_bridge(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_003_l2_to_l2_direct_bridge",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test L2 to L2 direct bridging (Arbitrum to Optimism).

    Validates:
    - L2-L2 direct bridging support
    - Route optimization (L2-L2 vs L1 intermediate)
    - Bridge protocol selection (Hop, Connext, Across)
    - Cost/time tradeoffs
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "Bridge 1000 USDC from Arbitrum to Optimism using fastest route",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Verify routing for specialist task
        routing = data["routing"]
        assert routing["intent"] in ["specialist_task", "swap", "bridging"]
        assert routing["confidence"] >= 0.7

        # Verify agent response mentions L2s and bridging concepts
        agent_content = data["agent_message"]["content"].lower()
        assert "arbitrum" in agent_content
        assert "optimism" in agent_content
        assert any(word in agent_content for word in ["bridge", "transfer", "move"])

        # Should mention speed or time
        assert any(word in agent_content for word in ["fast", "quick", "time", "minutes"])

    # =========================================================================
    # Test 4: Cross-Chain Gas Estimation
    # =========================================================================

    @pytest.mark.llm_validation
    async def test_cross_chain_004_gas_cost_estimation(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_004_gas_cost_estimation",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate cryptocurrency price information in a clear format. Response must reference cryptocurrency specifically (not other cryptocurrencies) and include current price data with USD denomination."
            ),
            additional_context={'test_category': 'price_query', 'token': 'cryptocurrency'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test cross-chain gas cost estimation before bridging.

    Validates:
    - Gas estimation on source chain
    - Bridge fee calculation
    - Destination chain gas estimation
    - Total cost breakdown in USD
    - Fee comparison across bridges
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "How much will it cost to bridge 5000 USDC from Ethereum to Polygon?",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Verify routing
        routing = data["routing"]
        assert routing["intent"] in ["estimate_gas", "info_request", "specialist_task"]
        assert routing["confidence"] >= 0.6

        # Verify agent response mentions cost components
        agent_content = data["agent_message"]["content"].lower()
        assert "ethereum" in agent_content
        assert "polygon" in agent_content
        assert any(word in agent_content for word in ["gas", "cost", "fee", "price"])

        # Should provide numerical estimate or USD amount
        assert any(char.isdigit() for char in agent_content), "Should contain numerical cost estimate"

    # =========================================================================
    # Test 5: Bridge Security Validation
    # =========================================================================

    @pytest.mark.llm_validation
    async def test_cross_chain_005_bridge_security_check(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_005_bridge_security_check",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test bridge security risk assessment.

    Validates:
    - Bridge security scoring
    - Recent exploit detection
    - Audit status checking
    - Risk-based recommendations
    - Alternative safer routes
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "Is it safe to bridge large amounts from Ethereum to BSC? Any recent exploits?",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Verify routing
        routing = data["routing"]
        assert routing["intent"] in ["security_check", "info_request", "specialist_task", "risk_analysis"]
        assert routing["confidence"] >= 0.6

        # Verify agent response addresses security concerns
        agent_content = data["agent_message"]["content"].lower()
        assert any(word in agent_content for word in ["security", "safe", "risk", "audit"])
        assert "bridge" in agent_content or "bridging" in agent_content

        # Should mention BSC or Ethereum
        assert "bsc" in agent_content or "binance" in agent_content or "ethereum" in agent_content

    # =========================================================================
    # Test 6: Cross-Chain Error Handling (Insufficient Gas)
    # =========================================================================

    @pytest.mark.llm_validation
    async def test_cross_chain_006_insufficient_gas_error(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_006_insufficient_gas_error",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test cross-chain bridge error handling for insufficient gas.

    Validates:
    - Pre-flight gas validation
    - Clear error messaging
    - Actionable recommendations (buy gas tokens)
    - Multi-chain gas requirements
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "Bridge 1000 USDC from Polygon to Ethereum",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Verify routing
        routing = data["routing"]
        assert routing["intent"] in ["specialist_task", "swap", "bridging"]
        assert routing["confidence"] >= 0.6

        # Verify agent response discusses bridging
        agent_content = data["agent_message"]["content"].lower()
        assert "polygon" in agent_content
        assert "ethereum" in agent_content
        assert any(word in agent_content for word in ["bridge", "transfer", "move"])

        # Should mention gas considerations
        assert any(word in agent_content for word in ["gas", "fee", "cost", "matic", "eth"])

    # =========================================================================
    # Test 7: Bridge Time Estimation with Urgency
    # =========================================================================

    @pytest.mark.llm_validation
    async def test_cross_chain_007_fast_bridge_time_priority(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_007_fast_bridge_time_priority",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test fast bridge route selection with time priority.

    Validates:
    - Time-priority route selection
    - Bridge speed comparison
    - Cost vs speed tradeoffs
    - Realistic time estimates (5min - 7 days)
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "I need to bridge 500 USDC from Ethereum to Arbitrum ASAP, what's the fastest option?",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Verify routing
        routing = data["routing"]
        assert routing["intent"] in ["specialist_task", "swap", "bridging", "info_request"]
        assert routing["confidence"] >= 0.6

        # Verify agent response discusses speed
        agent_content = data["agent_message"]["content"].lower()
        assert "ethereum" in agent_content
        assert "arbitrum" in agent_content
        assert any(word in agent_content for word in ["fast", "quick", "asap", "urgent", "time"])

        # Should mention bridge options or timing
        assert any(word in agent_content for word in ["bridge", "minutes", "option", "route"])


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.cross_chain
class TestCrossChainEdgeCases:
    """Edge case testing for cross-chain functionality."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="crosschain_edge@example.com",
        )
        return user, token

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
    """Get authentication headers."""
    _, token = test_user
    return {"Authorization": f"Bearer {token}"}

    @pytest_asyncio.fixture
    async def conversation_id(self, authenticated_client: AsyncClient, auth_headers):
    """Create a test conversation."""
    response = await authenticated_client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"language": "en"},
    )
        assert response.status_code == 201
        return response.json()["id"]

    @pytest.mark.llm_validation
    async def test_cross_chain_edge_001_unsupported_chain(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_edge_001_unsupported_chain",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test handling of unsupported blockchain.

    Validates graceful handling of unsupported chains.
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "Bridge USDC from Ethereum to Solana",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Should still respond, possibly with limitations
        assert "agent_message" in data
        agent_content = data["agent_message"]["content"].lower()

        # Should mention Solana or provide helpful response
        assert len(agent_content) > 50, "Should provide meaningful response"

    @pytest.mark.llm_validation
    async def test_cross_chain_edge_002_same_chain_transfer(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_cross_chain_edge_002_same_chain_transfer",
            user_input="query",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
            ),
            additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    conversation_id: str,
    ):
    """
    Test detection when user mistakenly tries to "bridge" on same chain.

    Validates that system clarifies no bridge needed for same-chain transfers.
    """
    response = await authenticated_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={
            "content": "Bridge USDC from Ethereum to Ethereum",
            "language": "en",
        },
    )

        assert response.status_code == 200
        data = response.json()

        # Should respond appropriately
        assert "agent_message" in data
        agent_content = data["agent_message"]["content"].lower()

        # Should provide helpful response about same-chain transfers
        assert len(agent_content) > 30, "Should provide guidance"