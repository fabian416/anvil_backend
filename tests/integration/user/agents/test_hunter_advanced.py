"""
Hunter AI Advanced Tests for Authenticated Users.

Tests advanced Hunter AI features including cross-chain analysis,
sentiment aggregation, historical patterns, and market analysis.

Migrated from test_user_hunter_advanced.py to use new test infrastructure.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ..conftest import (
    CSVReporter,
    TestResult,
    send_message,
    parse_response,
    create_test_result,
)


HUNTER_ADVANCED_TESTS = [
    # Cross-Chain Analysis
    {
        "test_id": "hunter_cross_chain_001",
        "input": "Find arbitrage opportunities between Ethereum and Polygon for USDC",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_cross_chain",
    },
    
    # Sentiment Aggregation
    {
        "test_id": "hunter_sentiment_multi_001",
        "input": "What's the overall sentiment about Solana across news, Reddit, and Twitter?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_sentiment_multi",
    },
    
    # Historical Pattern Recognition
    {
        "test_id": "hunter_historical_001",
        "input": "Show me Bitcoin's price patterns during the last 3 bull markets",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_historical",
    },
    
    # Risk-Adjusted Recommendations
    {
        "test_id": "hunter_risk_adjusted_001",
        "input": "Suggest low-risk DeFi yield opportunities with 5%+ APY",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_risk_adjusted",
    },
    
    # Portfolio Rebalancing
    {
        "test_id": "hunter_portfolio_001",
        "input": "I have 70% ETH and 30% BTC. Should I rebalance?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_portfolio",
    },
    
    # Gas Optimization
    {
        "test_id": "hunter_gas_001",
        "input": "When is the best time to execute Ethereum transactions to save on gas?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_gas",
    },
    
    # Market Regime Detection
    {
        "test_id": "hunter_regime_001",
        "input": "Are we in a bull market or bear market right now?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_regime",
    },
    
    # Correlation Analysis
    {
        "test_id": "hunter_correlation_001",
        "input": "How correlated are BTC, ETH, and SOL price movements?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_correlation",
    },
    
    # Liquidity Depth
    {
        "test_id": "hunter_liquidity_001",
        "input": "What's the liquidity depth for AAVE/ETH on Uniswap?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_liquidity",
    },
    
    # Whale Activity
    {
        "test_id": "hunter_whale_001",
        "input": "Show me recent whale movements for Bitcoin",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_whale",
    },
    
    # DEX Volume Analysis
    {
        "test_id": "hunter_dex_001",
        "input": "Compare trading volumes across Uniswap, Sushiswap, and Curve",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_dex",
    },
    
    # Token Unlocks
    {
        "test_id": "hunter_unlocks_001",
        "input": "What major token unlocks are happening this month?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_unlocks",
    },
    
    # Protocol Comparison
    {
        "test_id": "hunter_protocol_001",
        "input": "Compare the tokenomics of Aave and Compound",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_protocol",
    },
    
    # Market Cap Analysis
    {
        "test_id": "hunter_mcap_001",
        "input": "Which DeFi protocols have the highest fully diluted valuation?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_mcap",
    },
    
    # Staking Yield
    {
        "test_id": "hunter_staking_001",
        "input": "What's the current staking yield for ETH across different validators?",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_staking",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestHunterAdvanced:
    """Tests for advanced Hunter AI features."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", HUNTER_ADVANCED_TESTS, ids=lambda t: t["test_id"])
    async def test_hunter_advanced(self, test_case: dict):
        """Test advanced Hunter AI features."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )
        
        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
        )
        
        self.reporter.add_result(result)
        
        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"
        
        parsed = parse_response(response_data)
        content = parsed.get("content", "")
        
        # Advanced queries should return substantial analysis
        assert len(content) > 50, f"Advanced query response too short: {content[:200]}"
        
        # Validate specific content based on subcategory
        subcategory = test_case["subcategory"]
        content_lower = content.lower()
        
        if "cross_chain" in subcategory:
            assert any(
                word in content_lower
                for word in ["arbitrage", "ethereum", "polygon", "usdc", "bridge", "opportunity"]
            ), f"Cross-chain response should mention relevant chains/tokens"
        
        elif "sentiment" in subcategory:
            assert any(
                word in content_lower
                for word in ["sentiment", "bullish", "bearish", "neutral", "social", "news"]
            ), f"Sentiment response should contain sentiment analysis"
        
        elif "historical" in subcategory:
            assert any(
                word in content_lower
                for word in ["bull", "bear", "market", "pattern", "history", "cycle", "2017", "2021"]
            ), f"Historical response should reference market cycles"
        
        elif "gas" in subcategory:
            assert any(
                word in content_lower
                for word in ["gas", "gwei", "time", "weekend", "peak", "cheap", "save"]
            ), f"Gas response should mention gas-related terms"
        
        elif "regime" in subcategory:
            assert any(
                word in content_lower
                for word in ["bull", "bear", "sideways", "market", "trend", "currently"]
            ), f"Regime response should identify market phase"
