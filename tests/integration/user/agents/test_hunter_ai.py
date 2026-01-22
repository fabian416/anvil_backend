"""
Hunter AI Agent Tests for Authenticated Users.

Tests price queries, sentiment analysis, trading signals, and news.
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


HUNTER_AI_TESTS = [
    # Price Queries
    {
        "test_id": "hunter_price_001",
        "input": "what is the price of ETH",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_price",
    },
    {
        "test_id": "hunter_price_002",
        "input": "BTC price",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_price",
    },
    {
        "test_id": "hunter_price_003",
        "input": "how much is ethereum",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_price",
    },
    {
        "test_id": "hunter_price_004",
        "input": "current price of SOL",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_price",
    },
    {
        "test_id": "hunter_price_005",
        "input": "ETH and BTC prices",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_price",
    },
    
    # Price Predictions
    {
        "test_id": "hunter_prediction_001",
        "input": "BTC price prediction",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_prediction",
    },
    {
        "test_id": "hunter_prediction_002",
        "input": "will ETH go up",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_prediction",
    },
    {
        "test_id": "hunter_prediction_003",
        "input": "ethereum forecast",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_prediction",
    },
    
    # Sentiment Analysis
    {
        "test_id": "hunter_sentiment_001",
        "input": "ethereum sentiment",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_sentiment",
    },
    {
        "test_id": "hunter_sentiment_002",
        "input": "what do people think about BTC",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_sentiment",
    },
    {
        "test_id": "hunter_sentiment_003",
        "input": "bitcoin social sentiment",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_sentiment",
    },
    
    # Trading Signals
    {
        "test_id": "hunter_signals_001",
        "input": "BTC trading signals",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_signals",
    },
    {
        "test_id": "hunter_signals_002",
        "input": "ETH buy or sell signal",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_signals",
    },
    
    # News
    {
        "test_id": "hunter_news_001",
        "input": "crypto market news",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_news",
    },
    {
        "test_id": "hunter_news_002",
        "input": "latest bitcoin news",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_news",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestHunterAI:
    """Tests for Hunter AI agent with LLM validation."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter, llm_validator):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator
    
    @pytest.mark.parametrize("test_case", HUNTER_AI_TESTS, ids=lambda t: t["test_id"])
    async def test_hunter_ai(self, test_case: dict):
        """Test Hunter AI routing and response quality with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )
        
        # LLM Validation
        llm_validation = None
        if not response_data.get("error"):
            parsed = parse_response(response_data)
            expected_behavior = self._get_expected_behavior(test_case)
            
            llm_validation = await validate_with_llm(
                llm_validator=self.llm_validator,
                test_name=test_case["test_id"],
                user_input=test_case["input"],
                agent_output=parsed.get("content", ""),
                expected_behavior=expected_behavior,
                additional_context={
                    "test_category": "hunter_ai",
                    "subcategory": test_case.get("subcategory", ""),
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
        
        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"
        
        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        
        # Verify response contains relevant data
        if "price" in test_case["subcategory"]:
            assert any(
                indicator in content
                for indicator in ["$", "price", "usd", "current"]
            ), f"Price query should contain price data: {content[:200]}"
        
        elif "sentiment" in test_case["subcategory"]:
            assert any(
                indicator in content
                for indicator in ["sentiment", "bullish", "bearish", "neutral", "social"]
            ), f"Sentiment query should contain sentiment data: {content[:200]}"
        
        elif "signal" in test_case["subcategory"]:
            assert any(
                indicator in content
                for indicator in ["signal", "buy", "sell", "hold", "trading"]
            ), f"Signal query should contain trading signals: {content[:200]}"
    
    def _get_expected_behavior(self, test_case: dict) -> str:
        """Get expected behavior description for LLM validation."""
        subcategory = test_case.get("subcategory", "")
        
        behaviors = {
            "hunter_price": "Response should provide current price data with USD value, formatted clearly. Should mention the token name and current market price.",
            "hunter_prediction": "Response should provide price prediction or forecast with reasoning. Should include timeframe and confidence level if available.",
            "hunter_sentiment": "Response should provide sentiment analysis with classification (bullish/bearish/neutral), score, and source breakdown.",
            "hunter_signals": "Response should provide trading signals with entry/exit points, stop loss, and confidence levels.",
            "hunter_news": "Response should provide relevant crypto news with sources and recency indicators.",
        }
        
        return behaviors.get(subcategory, "Response should be relevant and informative about crypto markets.")
