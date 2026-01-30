"""
Wallet Agent Tests for Authenticated Users.

Tests wallet queries, balances, and token lookups.
Uses LLM (Vertex AI) validation for semantic output verification.

Migrated from: tests/integration/user/agents/test_portfolio.py (wallet section)
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ...conftest import (
    CSVReporter,
    TestResult,
    send_message,
    parse_response,
    create_test_result,
    validate_with_llm,
)


WALLET_TESTS = [
    # Primary Wallet Patterns (from shortcuts.md)
    {
        "test_id": "wallet_address_001",
        "input": "my wallet",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_address",
    },
    {
        "test_id": "wallet_address_002",
        "input": "my wallets",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_address",
    },
    {
        "test_id": "wallet_address_003",
        "input": "wallet address",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_address",
    },
    {
        "test_id": "wallet_address_004",
        "input": "show my wallet",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_address",
    },
    {
        "test_id": "wallet_address_005",
        "input": "connected wallets",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_address",
    },
    {
        "test_id": "wallet_address_006",
        "input": "wallet info",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_address",
    },
    
    # Multi-Language: Spanish
    {
        "test_id": "wallet_es_001",
        "input": "mi cartera",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_spanish",
    },
    {
        "test_id": "wallet_es_002",
        "input": "dirección de cartera",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_spanish",
    },
    
    # Multi-Language: Portuguese
    {
        "test_id": "wallet_pt_001",
        "input": "minha carteira",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_portuguese",
    },
    
    # Multi-Language: Chinese
    {
        "test_id": "wallet_zh_001",
        "input": "我的钱包",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet_chinese",
    },
    
    # Wallet vs Portfolio Distinction (should NOT go to wallet)
    {
        "test_id": "wallet_distinction_001",
        "input": "my balance",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "wallet_distinction",
    },
    {
        "test_id": "wallet_distinction_002",
        "input": "my portfolio",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "wallet_distinction",
    },
    {
        "test_id": "wallet_distinction_003",
        "input": "my holdings",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "wallet_distinction",
    },
]


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
