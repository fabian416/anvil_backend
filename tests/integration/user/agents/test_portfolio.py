"""
Portfolio Agent Tests for Authenticated Users.

Tests portfolio queries, holdings, and balance checks.
Uses LLM (Vertex AI) validation for semantic output verification.
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
    validate_with_llm,
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
@pytest.mark.llm_validation
class TestPortfolio:
    """Tests for Portfolio agent with LLM validation."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter, llm_validator):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator
    
    @pytest.mark.parametrize("test_case", PORTFOLIO_TESTS, ids=lambda t: t["test_id"])
    async def test_portfolio(self, test_case: dict):
        """Test portfolio queries with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )
        
        # LLM Validation
        llm_validation = None
        if not response_data.get("error"):
            parsed = parse_response(response_data)
            llm_validation = await validate_with_llm(
                llm_validator=self.llm_validator,
                test_name=test_case["test_id"],
                user_input=test_case["input"],
                agent_output=parsed.get("content", ""),
                expected_behavior="Response should provide portfolio information including holdings, balances, or asset breakdown.",
                additional_context={
                    "test_category": "portfolio",
                    "user_type": "authenticated",
                }
            )
        
        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
            llm_validation=llm_validation,
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
@pytest.mark.llm_validation
class TestWallet:
    """Tests for Wallet agent with LLM validation."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter, llm_validator):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator
    
    @pytest.mark.parametrize("test_case", WALLET_TESTS, ids=lambda t: t["test_id"])
    async def test_wallet(self, test_case: dict):
        """Test wallet queries with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )
        
        # LLM Validation
        llm_validation = None
        if not response_data.get("error"):
            parsed = parse_response(response_data)
            llm_validation = await validate_with_llm(
                llm_validator=self.llm_validator,
                test_name=test_case["test_id"],
                user_input=test_case["input"],
                agent_output=parsed.get("content", ""),
                expected_behavior="Response should provide wallet information including balances, tokens, or connected addresses.",
                additional_context={
                    "test_category": "wallet",
                    "user_type": "authenticated",
                }
            )
        
        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
            llm_validation=llm_validation,
        )
        
        self.reporter.add_result(result)
        
        assert not response_data.get("error"), f"Request failed: {response_data}"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestTransactionHistory:
    """Tests for Transaction History agent with LLM validation."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter, llm_validator):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator
    
    @pytest.mark.parametrize("test_case", TRANSACTION_TESTS, ids=lambda t: t["test_id"])
    async def test_transactions(self, test_case: dict):
        """Test transaction history queries with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )
        
        # LLM Validation
        llm_validation = None
        if not response_data.get("error"):
            parsed = parse_response(response_data)
            llm_validation = await validate_with_llm(
                llm_validator=self.llm_validator,
                test_name=test_case["test_id"],
                user_input=test_case["input"],
                agent_output=parsed.get("content", ""),
                expected_behavior="Response should provide transaction history or recent activity information.",
                additional_context={
                    "test_category": "transaction_history",
                    "user_type": "authenticated",
                }
            )
        
        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
            llm_validation=llm_validation,
        )
        
        self.reporter.add_result(result)
        
        assert not response_data.get("error"), f"Request failed: {response_data}"
