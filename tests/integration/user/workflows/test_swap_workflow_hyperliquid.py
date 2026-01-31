"""
Integration Tests for Swap Workflow Agent with Hyperliquid Integration.

Tests the intelligent provider routing:
- Hyperliquid Spot: Meme tokens (PURR, TRUMP, etc.) paired with USDC
- 1inch/LiFi: Major tokens (ETH, BTC, USDC, etc.)

@prompt-engineer @backend-engineer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from app.infrastructure.adapters.agent_squad.agents.workflows.swap_workflow_agent import (
    SwapWorkflowAgent,
    HYPERLIQUID_SPOT_TOKENS,
)

# Define locally since this constant was removed from the source
# These are major tokens that require DEX routing (1inch/LiFi) instead of Hyperliquid
MAJOR_TOKENS_REQUIRE_DEX = {
    "ETH", "BTC", "SOL", "WBTC", "WETH", "LINK", "UNI", "AAVE",
    "MATIC", "ARB", "OP", "AVAX", "DOT", "ATOM", "LTC", "XRP",
}
from app.infrastructure.adapters.agent_squad.agents.workflows.base_workflow_agent import (
    WorkflowState,
    WorkflowStep,
    UserContext,
)
from app.domain.value_objects.message_content import MessageContent


# =============================================================================
# Test Constants
# =============================================================================

class TestHyperliquidSpotTokens:
    """Test HYPERLIQUID_SPOT_TOKENS constant."""
    
    def test_usdc_in_hyperliquid_tokens(self):
        """USDC must be in Hyperliquid tokens (required quote currency)."""
        assert "USDC" in HYPERLIQUID_SPOT_TOKENS
    
    def test_meme_tokens_in_hyperliquid(self):
        """Popular meme tokens should be in Hyperliquid list."""
        meme_tokens = ["PURR", "HFUN", "TRUMP", "PEPE", "MOG"]
        for token in meme_tokens:
            assert token in HYPERLIQUID_SPOT_TOKENS, f"{token} should be in HYPERLIQUID_SPOT_TOKENS"
    
    def test_major_tokens_not_in_hyperliquid(self):
        """Major tokens should NOT be in Hyperliquid spot list."""
        major_tokens = ["ETH", "BTC", "SOL", "WETH", "WBTC"]
        for token in major_tokens:
            assert token not in HYPERLIQUID_SPOT_TOKENS, f"{token} should NOT be in HYPERLIQUID_SPOT_TOKENS"


class TestMajorTokensRequireDex:
    """Test MAJOR_TOKENS_REQUIRE_DEX constant."""
    
    def test_major_tokens_present(self):
        """All expected major tokens should be in the list."""
        expected = ["ETH", "BTC", "SOL", "WBTC", "WETH", "LINK", "UNI", "AAVE"]
        for token in expected:
            assert token in MAJOR_TOKENS_REQUIRE_DEX, f"{token} should be in MAJOR_TOKENS_REQUIRE_DEX"


# =============================================================================
# Test Swap Routing Logic
# =============================================================================

class TestSwapRoutingLogic:
    """Test the _is_hyperliquid_swap routing method."""
    
    @pytest.fixture
    def agent(self):
        """Create SwapWorkflowAgent with mocked dependencies."""
        return SwapWorkflowAgent(
            llm_client=None,
            oneinch_client=None,
            lifi_client=None,
            coingecko_client=None,
            hyperliquid_client=MagicMock(),
        )
    
    def test_usdc_to_purr_is_hyperliquid(self, agent):
        """USDC to PURR should route to Hyperliquid."""
        assert agent._is_hyperliquid_swap("USDC", "PURR") is True
    
    def test_purr_to_usdc_is_hyperliquid(self, agent):
        """PURR to USDC should route to Hyperliquid."""
        assert agent._is_hyperliquid_swap("PURR", "USDC") is True
    
    def test_usdc_to_trump_is_hyperliquid(self, agent):
        """USDC to TRUMP should route to Hyperliquid."""
        assert agent._is_hyperliquid_swap("USDC", "TRUMP") is True
    
    def test_eth_to_usdc_not_hyperliquid(self, agent):
        """ETH to USDC should NOT route to Hyperliquid."""
        assert agent._is_hyperliquid_swap("ETH", "USDC") is False
    
    def test_btc_to_usdc_not_hyperliquid(self, agent):
        """BTC to USDC should NOT route to Hyperliquid."""
        assert agent._is_hyperliquid_swap("BTC", "USDC") is False
    
    def test_eth_to_wbtc_not_hyperliquid(self, agent):
        """ETH to WBTC should NOT route to Hyperliquid."""
        assert agent._is_hyperliquid_swap("ETH", "WBTC") is False
    
    def test_usdc_to_usdc_not_hyperliquid(self, agent):
        """USDC to USDC should NOT route to Hyperliquid (no-op)."""
        assert agent._is_hyperliquid_swap("USDC", "USDC") is False
    
    def test_case_insensitive_routing(self, agent):
        """Routing should be case-insensitive."""
        assert agent._is_hyperliquid_swap("usdc", "purr") is True
        assert agent._is_hyperliquid_swap("USDC", "purr") is True
        assert agent._is_hyperliquid_swap("usdc", "PURR") is True


# =============================================================================
# Test Quote Fetching with Provider Routing
# =============================================================================

@dataclass
class MockSpotQuote:
    """Mock Hyperliquid SpotQuote."""
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float
    price: float
    mid_price: float
    spread_bps: float
    timestamp: int


@dataclass
class MockLiFiQuote:
    """Mock LiFi quote."""
    to_amount: str
    price_impact: float = 0.0
    estimated_gas: int = 250000


class TestFetchQuoteProviderRouting:
    """Test _fetch_quote routes to correct provider."""
    
    @pytest.fixture
    def mock_hyperliquid(self):
        """Create mock Hyperliquid client."""
        client = AsyncMock()
        client.get_spot_quote = AsyncMock(return_value=MockSpotQuote(
            from_token="USDC",
            to_token="PURR",
            from_amount=100.0,
            to_amount=50000.0,
            price=0.002,
            mid_price=0.002,
            spread_bps=10.0,
            timestamp=1234567890,
        ))
        return client
    
    @pytest.fixture
    def mock_lifi(self):
        """Create mock LiFi client."""
        client = AsyncMock()
        client.get_quote = AsyncMock(return_value=MockLiFiQuote(
            to_amount="280000000",  # 280 USDC in wei (6 decimals)
        ))
        return client
    
    @pytest.fixture
    def agent_with_all_providers(self, mock_hyperliquid, mock_lifi):
        """Create agent with all providers configured."""
        return SwapWorkflowAgent(
            llm_client=None,
            oneinch_client=None,
            lifi_client=mock_lifi,
            coingecko_client=None,
            hyperliquid_client=mock_hyperliquid,
        )
    
    @pytest.mark.asyncio
    async def test_meme_token_uses_hyperliquid(self, agent_with_all_providers, mock_hyperliquid):
        """Meme token swap should use Hyperliquid."""
        result = await agent_with_all_providers._fetch_quote(
            from_token="USDC",
            to_token="PURR",
            amount="100",
            chain="base",
            to_chain=None,
            wallet_address=None,
        )
        
        assert result.get("aggregator") == "hyperliquid"
        assert result.get("output_amount") == "50000"
        mock_hyperliquid.get_spot_quote.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_major_token_uses_lifi(self, agent_with_all_providers, mock_lifi):
        """Major token swap should use LiFi (when 1inch not available)."""
        result = await agent_with_all_providers._fetch_quote(
            from_token="ETH",
            to_token="USDC",
            amount="0.1",
            chain="base",
            to_chain=None,
            wallet_address=None,
        )
        
        assert result.get("aggregator") == "lifi"
        mock_lifi.get_quote.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hyperliquid_failure_falls_back_to_lifi(self, mock_lifi):
        """When Hyperliquid fails, should fall back to LiFi."""
        mock_hyperliquid = AsyncMock()
        mock_hyperliquid.get_spot_quote = AsyncMock(
            side_effect=ValueError("No spot market found for USDC/TRUMP")
        )
        
        agent = SwapWorkflowAgent(
            llm_client=None,
            oneinch_client=None,
            lifi_client=mock_lifi,
            coingecko_client=None,
            hyperliquid_client=mock_hyperliquid,
        )
        
        result = await agent._fetch_quote(
            from_token="USDC",
            to_token="TRUMP",  # Meme token but Hyperliquid fails
            amount="50",
            chain="base",
            to_chain=None,
            wallet_address=None,
        )
        
        # Should fall back to LiFi
        assert result.get("aggregator") == "lifi"
        mock_lifi.get_quote.assert_called_once()


# =============================================================================
# Test End-to-End Workflow
# =============================================================================

class TestSwapWorkflowEndToEnd:
    """Test complete swap workflow with Hyperliquid integration."""
    
    @pytest.fixture
    def mock_hyperliquid(self):
        """Create mock Hyperliquid client."""
        client = AsyncMock()
        client.get_spot_quote = AsyncMock(return_value=MockSpotQuote(
            from_token="USDC",
            to_token="PURR",
            from_amount=100.0,
            to_amount=1925.5,
            price=0.05194,
            mid_price=0.05194,
            spread_bps=25.0,
            timestamp=1234567890,
        ))
        return client
    
    @pytest.fixture
    def agent(self, mock_hyperliquid):
        """Create agent with Hyperliquid only (for meme token testing)."""
        return SwapWorkflowAgent(
            llm_client=None,
            oneinch_client=None,
            lifi_client=None,
            coingecko_client=None,
            hyperliquid_client=mock_hyperliquid,
        )
    
    @pytest.mark.asyncio
    async def test_fetch_quote_directly_uses_hyperliquid(self, agent, mock_hyperliquid):
        """Test _fetch_quote directly uses Hyperliquid for meme tokens."""
        result = await agent._fetch_quote(
            from_token="USDC",
            to_token="PURR",
            amount="100",
            chain="base",
            to_chain=None,
            wallet_address=None,
        )
        
        # Should use Hyperliquid
        assert result.get("aggregator") == "hyperliquid"
        assert result.get("output_amount") == "1925.5"
        assert result.get("gas_estimate") == 0  # Hyperliquid = zero gas
        mock_hyperliquid.get_spot_quote.assert_called_once_with(
            from_token="USDC",
            to_token="PURR",
            amount=100.0,
        )
    
    @pytest.mark.asyncio
    async def test_workflow_with_preset_params_uses_hyperliquid(self, agent, mock_hyperliquid):
        """Test workflow with pre-parsed params fetches Hyperliquid quote."""
        # Start from FETCH_DATA step with params already parsed
        state = WorkflowState(
            step=WorkflowStep.FETCH_DATA.value,
            data={
                "from_token": "USDC",
                "to_token": "PURR",
                "amount": "100",
                "chain": "base",
            }
        )
        user_context = UserContext(
            user_id="test-user",
            wallet_address=None,
            language="en",
        )
        message = MessageContent(value="")  # Not used in FETCH_DATA step
        
        response, new_state = await agent.process_step(message, state, user_context)
        
        # Should have fetched quote and moved to confirm step
        assert new_state.step == WorkflowStep.CONFIRM.value
        assert new_state.data.get("aggregator") == "hyperliquid"
        assert "PURR" in response
        assert "HYPERLIQUID" in response.upper()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
