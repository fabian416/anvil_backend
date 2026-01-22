"""
Protocol-Specific Workflow Tests for Authenticated Users.

Tests interactions with specific DeFi protocols.
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


AAVE_TESTS = [
    {
        "test_id": "aave_deposit_001",
        "input": "deposit 1000 USDC on Aave",
        "expected_agent": "lending_workflow",
        "category": "protocol",
        "subcategory": "aave_deposit",
    },
    {
        "test_id": "aave_rates_001",
        "input": "what's the current Aave supply rate for ETH",
        "expected_agent": "money_market_workflow",
        "category": "protocol",
        "subcategory": "aave_rates",
    },
    {
        "test_id": "aave_health_001",
        "input": "check my Aave health factor",
        "expected_agent": "portfolio",
        "category": "protocol",
        "subcategory": "aave_health",
    },
    {
        "test_id": "aave_borrow_001",
        "input": "can I borrow against my Aave deposits",
        "expected_agent": "lending_workflow",
        "category": "protocol",
        "subcategory": "aave_borrow",
    },
]


COMPOUND_TESTS = [
    {
        "test_id": "compound_deposit_001",
        "input": "supply USDC to Compound",
        "expected_agent": "lending_workflow",
        "category": "protocol",
        "subcategory": "compound_deposit",
    },
    {
        "test_id": "compound_rates_001",
        "input": "Compound V3 rates for USDC",
        "expected_agent": "money_market_workflow",
        "category": "protocol",
        "subcategory": "compound_rates",
    },
    {
        "test_id": "compound_compare_001",
        "input": "compare Compound to Aave for USDC lending",
        "expected_agent": "money_market_workflow",
        "category": "protocol",
        "subcategory": "compound_compare",
    },
]


MORPHO_TESTS = [
    {
        "test_id": "morpho_deposit_001",
        "input": "deposit USDC into Morpho vault",
        "expected_agent": "lending_workflow",
        "category": "protocol",
        "subcategory": "morpho_deposit",
    },
    {
        "test_id": "morpho_vaults_001",
        "input": "show me Morpho vaults for WETH",
        "expected_agent": "lending_workflow",
        "category": "protocol",
        "subcategory": "morpho_vaults",
    },
    {
        "test_id": "morpho_rates_001",
        "input": "Morpho yield rates",
        "expected_agent": "money_market_workflow",
        "category": "protocol",
        "subcategory": "morpho_rates",
    },
    {
        "test_id": "morpho_blue_001",
        "input": "what is Morpho Blue",
        "expected_agent": "research",
        "category": "protocol",
        "subcategory": "morpho_info",
    },
]


UNISWAP_TESTS = [
    {
        "test_id": "uniswap_swap_001",
        "input": "swap on Uniswap",
        "expected_agent": "swap_workflow",
        "category": "protocol",
        "subcategory": "uniswap_swap",
    },
    {
        "test_id": "uniswap_liquidity_001",
        "input": "provide liquidity on Uniswap V3",
        "expected_agent": "defi_yield",
        "category": "protocol",
        "subcategory": "uniswap_liquidity",
    },
    {
        "test_id": "uniswap_fees_001",
        "input": "Uniswap fee tiers explained",
        "expected_agent": "research",
        "category": "protocol",
        "subcategory": "uniswap_info",
    },
]


LIDO_TESTS = [
    {
        "test_id": "lido_stake_001",
        "input": "stake ETH with Lido",
        "expected_agent": "defi_yield",
        "category": "protocol",
        "subcategory": "lido_stake",
    },
    {
        "test_id": "lido_yield_001",
        "input": "what's the Lido staking APY",
        "expected_agent": "defi_yield",
        "category": "protocol",
        "subcategory": "lido_yield",
    },
    {
        "test_id": "lido_steth_001",
        "input": "how does stETH work",
        "expected_agent": "research",
        "category": "protocol",
        "subcategory": "lido_info",
    },
]


CURVE_TESTS = [
    {
        "test_id": "curve_swap_001",
        "input": "swap stablecoins on Curve",
        "expected_agent": "swap_workflow",
        "category": "protocol",
        "subcategory": "curve_swap",
    },
    {
        "test_id": "curve_pools_001",
        "input": "best Curve pools for USDC",
        "expected_agent": "defi_yield",
        "category": "protocol",
        "subcategory": "curve_pools",
    },
    {
        "test_id": "curve_gauge_001",
        "input": "explain Curve gauges",
        "expected_agent": "research",
        "category": "protocol",
        "subcategory": "curve_info",
    },
]


ALL_PROTOCOL_TESTS = (
    AAVE_TESTS + 
    COMPOUND_TESTS + 
    MORPHO_TESTS + 
    UNISWAP_TESTS + 
    LIDO_TESTS + 
    CURVE_TESTS
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestProtocolSpecific:
    """Tests for protocol-specific interactions."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", ALL_PROTOCOL_TESTS, ids=lambda t: t["test_id"])
    async def test_protocol_specific(self, test_case: dict):
        """Test protocol-specific workflow routing."""
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
        content = parsed.get("content", "").lower()
        
        # Verify protocol-specific response
        protocol = test_case["subcategory"].split("_")[0]
        
        assert any(
            indicator in content
            for indicator in [
                protocol, "deposit", "supply", "rate", "apy", "yield", 
                "vault", "pool", "swap", "stake", "liquidity"
            ]
        ), f"Protocol query should return relevant response: {content[:200]}"
