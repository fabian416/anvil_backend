"""
Portfolio Agent Tests for Authenticated Users.

Tests portfolio queries, holdings, and balance checks.
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


PORTFOLIO_TESTS = [
    {
        "test_id": "portfolio_001",
        "input": "my portfolio",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
    },
    {
        "test_id": "portfolio_002",
        "input": "show my holdings",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
    },
    {
        "test_id": "portfolio_003",
        "input": "portfolio breakdown",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
    },
    {
        "test_id": "portfolio_004",
        "input": "what's in my portfolio",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
    },
    {
        "test_id": "portfolio_005",
        "input": "portfolio value",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
    },
    {
        "test_id": "portfolio_006",
        "input": "how much is my portfolio worth",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
    },
]


WALLET_TESTS = [
    {
        "test_id": "wallet_001",
        "input": "my wallets",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
    },
    {
        "test_id": "wallet_002",
        "input": "show my wallet balance",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
    },
    {
        "test_id": "wallet_003",
        "input": "what tokens do I have",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
    },
    {
        "test_id": "wallet_004",
        "input": "check my balance",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
    },
    {
        "test_id": "wallet_005",
        "input": "my USDC balance",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
    },
    {
        "test_id": "wallet_006",
        "input": "how much ETH do I have",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
    },
]


TRANSACTION_TESTS = [
    {
        "test_id": "tx_001",
        "input": "transaction history",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "transactions",
    },
    {
        "test_id": "tx_002",
        "input": "recent activity",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "transactions",
    },
    {
        "test_id": "tx_003",
        "input": "show my transactions",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "transactions",
    },
    {
        "test_id": "tx_004",
        "input": "past trades",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "transactions",
    },
    {
        "test_id": "tx_005",
        "input": "my swap history",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "transactions",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestPortfolio:
    """Tests for Portfolio agent."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", PORTFOLIO_TESTS, ids=lambda t: t["test_id"])
    async def test_portfolio(self, test_case: dict):
        """Test portfolio queries."""
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
        
        assert not response_data.get("error"), f"Request failed: {response_data}"
        
        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        
        # Portfolio responses should mention holdings or wallet
        assert any(
            word in content
            for word in ["portfolio", "holdings", "wallet", "balance", "asset", "token"]
        ), f"Portfolio response should mention holdings: {content[:200]}"


@pytest.mark.asyncio
@pytest.mark.integration
class TestWallet:
    """Tests for Wallet agent."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", WALLET_TESTS, ids=lambda t: t["test_id"])
    async def test_wallet(self, test_case: dict):
        """Test wallet queries."""
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
        
        assert not response_data.get("error"), f"Request failed: {response_data}"


@pytest.mark.asyncio
@pytest.mark.integration
class TestTransactionHistory:
    """Tests for Transaction History agent."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", TRANSACTION_TESTS, ids=lambda t: t["test_id"])
    async def test_transactions(self, test_case: dict):
        """Test transaction history queries."""
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
        
        assert not response_data.get("error"), f"Request failed: {response_data}"
