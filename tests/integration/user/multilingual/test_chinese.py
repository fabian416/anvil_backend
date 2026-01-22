"""
Chinese Language Tests for Authenticated Users.

Tests all workflows with Chinese input.
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


CHINESE_TESTS = [
    # Swap
    {
        "test_id": "zh_swap_001",
        "input": "我想交换 1 ETH 到 USDC",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "chinese_swap",
        "language": "zh",
    },
    {
        "test_id": "zh_swap_002",
        "input": "兑换 100 USDC 为 ETH",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "chinese_swap",
        "language": "zh",
    },
    {
        "test_id": "zh_swap_003",
        "input": "换币 ETH 到 USDC",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "chinese_swap",
        "language": "zh",
    },
    
    # Lending
    {
        "test_id": "zh_lend_001",
        "input": "存款 1000 USDC",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "chinese_lending",
        "language": "zh",
    },
    {
        "test_id": "zh_lend_002",
        "input": "存入 ETH 赚取收益",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "chinese_lending",
        "language": "zh",
    },
    
    # Money Market
    {
        "test_id": "zh_mm_001",
        "input": "比较 USDC 利率",
        "expected_agent": "money_market_workflow",
        "category": "multilingual",
        "subcategory": "chinese_money_market",
        "language": "zh",
    },
    {
        "test_id": "zh_mm_002",
        "input": "最好的 ETH 存款利率",
        "expected_agent": "money_market_workflow",
        "category": "multilingual",
        "subcategory": "chinese_money_market",
        "language": "zh",
    },
    
    # Buy
    {
        "test_id": "zh_buy_001",
        "input": "购买 100 美元的 ETH",
        "expected_agent": "buy_workflow",
        "category": "multilingual",
        "subcategory": "chinese_buy",
        "language": "zh",
    },
    {
        "test_id": "zh_buy_002",
        "input": "买比特币",
        "expected_agent": "buy_workflow",
        "category": "multilingual",
        "subcategory": "chinese_buy",
        "language": "zh",
    },
    
    # Price
    {
        "test_id": "zh_price_001",
        "input": "比特币价格",
        "expected_agent": "hunter_ai",
        "category": "multilingual",
        "subcategory": "chinese_price",
        "language": "zh",
    },
    {
        "test_id": "zh_price_002",
        "input": "ETH 多少钱",
        "expected_agent": "hunter_ai",
        "category": "multilingual",
        "subcategory": "chinese_price",
        "language": "zh",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestChinese:
    """Tests for Chinese language support."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", CHINESE_TESTS, ids=lambda t: t["test_id"])
    async def test_chinese(self, test_case: dict):
        """Test Chinese language routing."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
            language=test_case.get("language", "zh"),
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
