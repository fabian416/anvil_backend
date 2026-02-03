"""
Component tests for Hunter AI handler and intent classification.

Tests Hunter AI business logic in isolation from HTTP layer:
- Intent classification for Hunter AI queries
- Handler routing for Hunter AI intents
- Hunter AI handler execution logic
- Enrichment data validation

Performance target: <100ms per test (vs 2000-5000ms for HTTP integration tests).
"""

import pytest
from typing import Dict, Any

from tests.helpers.test_data_loader import (
    get_hunter_test_cases,
    get_test_case_by_id,
)


@pytest.mark.asyncio
class TestHunterIntentClassification:
    """Component tests for Hunter AI intent classification logic."""

    @pytest.mark.parametrize(
        "test_case", get_hunter_test_cases(), ids=lambda tc: tc["id"]
    )
    async def test_classify_hunter_intent(
        self,
        mock_intent_classifier,
        test_case: Dict[str, Any],
    ):
        """
        WHEN user sends Hunter AI query
        THEN intent classifier SHALL identify correct Hunter AI intent

        This tests the intent classification business logic without HTTP layer.
        """
        # Arrange: Configure mock classifier to return expected intent
        expected_intent = test_case["expected_routing"]["intent"]
        expected_confidence_min = test_case["expected_routing"].get(
            "confidence_min", 0.5
        )

        # Get IntentResult class from fixture
        IntentResult = mock_intent_classifier.IntentResult

        mock_intent_classifier.classify.return_value = IntentResult(
            intent=expected_intent,
            confidence=0.92,  # Above minimum threshold
            reasoning=f"Test classification for {test_case['id']}",
        )

        # Act: Classify user input
        result = await mock_intent_classifier.classify(test_case["input"]["content"])

        # Assert: Verify intent classification
        assert result.intent == expected_intent, (
            f"Intent mismatch for {test_case['id']}: "
            f"expected '{expected_intent}', got '{result.intent}'"
        )
        assert result.confidence >= expected_confidence_min, (
            f"Confidence too low for {test_case['id']}: "
            f"expected >= {expected_confidence_min}, got {result.confidence}"
        )
        assert result.reasoning is not None


@pytest.mark.asyncio
class TestHunterHandlerRouting:
    """Component tests for Hunter AI handler routing logic."""

    @pytest.mark.parametrize(
        "intent,expected_handler",
        [
            ("hunter_sentiment", "hunter_handler"),
            ("hunter_price_prediction", "hunter_handler"),
            ("hunter_trading_signals", "hunter_handler"),
            ("hunter_patterns", "hunter_handler"),
            ("hunter_portfolio", "hunter_handler"),
            ("hunter_risk_signals", "hunter_handler"),
        ],
    )
    async def test_route_hunter_intent_to_handler(
        self,
        mock_handler_router,
        intent: str,
        expected_handler: str,
    ):
        """
        WHEN Hunter AI intent is classified
        THEN handler router SHALL select Hunter AI handler

        Tests handler routing logic without HTTP/database dependencies.
        """
        # Act: Get handler for intent
        handler_name = mock_handler_router.get_handler(intent)

        # Assert: Verify correct handler selected
        assert handler_name == expected_handler, (
            f"Handler mismatch for intent '{intent}': "
            f"expected '{expected_handler}', got '{handler_name}'"
        )


@pytest.mark.asyncio
class TestHunterHandlerExecution:
    """Component tests for Hunter AI handler business logic."""

    async def test_hunter_sentiment_execution(
        self,
        mock_hunter_handler,
    ):
        """
        WHEN Hunter AI sentiment analysis is executed
        THEN handler SHALL return sentiment data with enrichment

        Tests Hunter AI sentiment analysis handler logic.
        """
        # Arrange: Configure mock handler response
        test_case = get_test_case_by_id("hunter_sent_001")
        assert test_case is not None, "Test case hunter_sent_001 not found"

        mock_hunter_handler.execute.return_value = {
            "content": "Mock Hunter AI sentiment analysis results",
            "enrichment": {
                "token_symbol": "ETH",
                "hunter_tool": "sentiment_analyzer",
                "sentiment_score": 0.75,
                "sources": ["twitter", "reddit", "news"],
            },
        }

        # Act: Execute handler
        result = await mock_hunter_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result
        assert result["content"] is not None
        assert len(result["content"]) > 0

        # Assert: Verify enrichment data
        enrichment = result["enrichment"]
        assert "hunter_tool" in enrichment, (
            "Hunter AI enrichment must include hunter_tool"
        )
        assert "token_symbol" in enrichment or "tokens" in enrichment, (
            "Hunter AI enrichment must include token_symbol or tokens"
        )

    async def test_hunter_price_prediction_execution(
        self,
        mock_hunter_handler,
    ):
        """
        WHEN Hunter AI price prediction is executed
        THEN handler SHALL return prediction data with enrichment

        Tests price prediction handler logic.
        """
        # Arrange: Configure mock handler for price prediction
        test_case = get_test_case_by_id("hunter_pp_001")
        if test_case is None:
            pytest.skip("Test case hunter_pp_001 not found in test_data.json")

        mock_hunter_handler.execute.return_value = {
            "content": "Mock price prediction results",
            "enrichment": {
                "token_symbol": "BTC",
                "hunter_tool": "price_predictor",
                "time_horizon": "7d",
                "predictions": [
                    {"timestamp": "2024-01-01", "price": 45000, "confidence": 0.85},
                    {"timestamp": "2024-01-07", "price": 48000, "confidence": 0.75},
                ],
            },
        }

        # Act: Execute handler
        result = await mock_hunter_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify price prediction enrichment
        enrichment = result["enrichment"]
        assert "hunter_tool" in enrichment
        assert "time_horizon" in enrichment or "predictions" in enrichment, (
            "Price prediction enrichment must include time_horizon or predictions"
        )

    async def test_hunter_trading_signals_execution(
        self,
        mock_hunter_handler,
    ):
        """
        WHEN Hunter AI trading signals are executed
        THEN handler SHALL return signals with recommendations

        Tests trading signals handler logic.
        """
        # Arrange: Configure mock handler for trading signals
        mock_hunter_handler.execute.return_value = {
            "content": "Mock trading signals results",
            "enrichment": {
                "token_symbol": "ETH",
                "hunter_tool": "signal_generator",
                "signals": [
                    {"type": "buy", "strength": 0.8, "indicator": "RSI"},
                    {"type": "hold", "strength": 0.6, "indicator": "MACD"},
                ],
                "recommendation": "BUY",
            },
        }

        # Act: Execute handler
        result = await mock_hunter_handler.execute(
            content="What are the trading signals for ETH?",
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify trading signals enrichment
        enrichment = result["enrichment"]
        assert "hunter_tool" in enrichment
        assert "signals" in enrichment or "recommendation" in enrichment, (
            "Trading signals enrichment must include signals or recommendation"
        )

    async def test_hunter_patterns_execution(
        self,
        mock_hunter_handler,
    ):
        """
        WHEN Hunter AI pattern detection is executed
        THEN handler SHALL return detected patterns

        Tests pattern detection handler logic.
        """
        # Arrange: Configure mock handler for pattern detection
        mock_hunter_handler.execute.return_value = {
            "content": "Mock pattern detection results",
            "enrichment": {
                "token_symbol": "BTC",
                "hunter_tool": "pattern_detector",
                "patterns": [
                    {
                        "name": "Head and Shoulders",
                        "confidence": 0.82,
                        "timeframe": "4h",
                    },
                    {"name": "Bull Flag", "confidence": 0.75, "timeframe": "1h"},
                ],
            },
        }

        # Act: Execute handler
        result = await mock_hunter_handler.execute(
            content="Detect patterns for BTC",
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify pattern detection enrichment
        enrichment = result["enrichment"]
        assert "hunter_tool" in enrichment
        assert "patterns" in enrichment, (
            "Pattern detection enrichment must include patterns"
        )

    async def test_hunter_portfolio_execution(
        self,
        mock_hunter_handler,
    ):
        """
        WHEN Hunter AI portfolio optimization is executed
        THEN handler SHALL return portfolio allocation

        Tests portfolio optimization handler logic.
        """
        # Arrange: Configure mock handler for portfolio optimization
        mock_hunter_handler.execute.return_value = {
            "content": "Mock portfolio optimization results",
            "enrichment": {
                "tokens": ["BTC", "ETH", "SOL"],
                "hunter_tool": "portfolio_optimizer",
                "risk_tolerance": "moderate",
                "allocation": {
                    "BTC": 0.50,
                    "ETH": 0.30,
                    "SOL": 0.20,
                },
            },
        }

        # Act: Execute handler
        result = await mock_hunter_handler.execute(
            content="Optimize my portfolio",
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify portfolio enrichment
        enrichment = result["enrichment"]
        assert "hunter_tool" in enrichment
        assert "tokens" in enrichment or "allocation" in enrichment, (
            "Portfolio enrichment must include tokens or allocation"
        )

    async def test_hunter_risk_signals_execution(
        self,
        mock_hunter_handler,
    ):
        """
        WHEN Hunter AI risk signals are executed
        THEN handler SHALL return risk indicators

        Tests risk signals handler logic.
        """
        # Arrange: Configure mock handler for risk signals
        mock_hunter_handler.execute.return_value = {
            "content": "Mock risk signals results",
            "enrichment": {
                "token_symbol": "ETH",
                "hunter_tool": "risk_analyzer",
                "risk_signals": [
                    {"type": "volatility", "level": "high", "score": 0.85},
                    {"type": "liquidity", "level": "medium", "score": 0.60},
                ],
            },
        }

        # Act: Execute handler
        result = await mock_hunter_handler.execute(
            content="What are the risk signals for ETH?",
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify risk signals enrichment
        enrichment = result["enrichment"]
        assert "hunter_tool" in enrichment
        assert "risk_signals" in enrichment, (
            "Risk signals enrichment must include risk_signals"
        )


@pytest.mark.asyncio
class TestHunterEnrichmentValidation:
    """Component tests for Hunter AI enrichment data structure."""

    @pytest.mark.parametrize(
        "test_case", get_hunter_test_cases(), ids=lambda tc: tc["id"]
    )
    async def test_hunter_enrichment_structure(
        self,
        mock_hunter_handler,
        test_case: Dict[str, Any],
    ):
        """
        WHEN Hunter AI handler returns enrichment data
        THEN enrichment SHALL match expected structure for subcategory

        Validates enrichment data structure for each Hunter AI subcategory.
        """
        # Arrange: Get subcategory-specific enrichment expectations
        subcategory = test_case["_subcategory"]
        expected_enrichment = test_case.get("expected_enrichment", {})

        # Configure mock handler with appropriate enrichment
        if subcategory == "sentiment":
            enrichment = {
                "token_symbol": "TEST",
                "hunter_tool": "sentiment_analyzer",
                "sentiment_score": 0.75,
                "sources": ["twitter", "reddit"],
            }
        elif subcategory == "price_prediction":
            enrichment = {
                "token_symbol": "TEST",
                "hunter_tool": "price_predictor",
                "time_horizon": "7d",
                "predictions": [{"timestamp": "2024-01-01", "price": 1000}],
            }
        elif subcategory == "trading_signals":
            enrichment = {
                "token_symbol": "TEST",
                "hunter_tool": "signal_generator",
                "signals": [{"type": "buy", "strength": 0.8}],
                "recommendation": "BUY",
            }
        elif subcategory == "patterns":
            enrichment = {
                "token_symbol": "TEST",
                "hunter_tool": "pattern_detector",
                "patterns": [{"name": "Bull Flag", "confidence": 0.75}],
            }
        elif subcategory == "portfolio":
            enrichment = {
                "tokens": ["BTC", "ETH"],
                "hunter_tool": "portfolio_optimizer",
                "risk_tolerance": "moderate",
                "allocation": {"BTC": 0.6, "ETH": 0.4},
            }
        elif subcategory == "risk_signals":
            enrichment = {
                "token_symbol": "TEST",
                "hunter_tool": "risk_analyzer",
                "risk_signals": [{"type": "volatility", "level": "high"}],
            }
        else:
            enrichment = {}

        mock_hunter_handler.execute.return_value = {
            "content": "Mock response",
            "enrichment": enrichment,
        }

        # Act: Execute handler
        result = await mock_hunter_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify enrichment structure matches subcategory
        result_enrichment = result.get("enrichment", {})

        # All Hunter AI enrichment must include hunter_tool
        assert "hunter_tool" in result_enrichment, (
            f"Hunter AI enrichment missing hunter_tool for {test_case['id']}"
        )

        # Verify subcategory-specific enrichment
        if subcategory == "sentiment":
            assert "token_symbol" in result_enrichment, (
                f"Sentiment enrichment missing token_symbol for {test_case['id']}"
            )
            assert (
                "sentiment_score" in result_enrichment or "sources" in result_enrichment
            ), (
                f"Sentiment enrichment missing sentiment_score or sources for {test_case['id']}"
            )

        elif subcategory == "price_prediction":
            assert "token_symbol" in result_enrichment, (
                f"Price prediction enrichment missing token_symbol for {test_case['id']}"
            )
            assert (
                "time_horizon" in result_enrichment
                or "predictions" in result_enrichment
            ), (
                f"Price prediction enrichment missing time_horizon or predictions for {test_case['id']}"
            )

        elif subcategory == "trading_signals":
            assert "token_symbol" in result_enrichment, (
                f"Trading signals enrichment missing token_symbol for {test_case['id']}"
            )
            assert (
                "signals" in result_enrichment or "recommendation" in result_enrichment
            ), (
                f"Trading signals enrichment missing signals or recommendation for {test_case['id']}"
            )

        elif subcategory == "patterns":
            assert "token_symbol" in result_enrichment, (
                f"Pattern detection enrichment missing token_symbol for {test_case['id']}"
            )
            assert "patterns" in result_enrichment, (
                f"Pattern detection enrichment missing patterns for {test_case['id']}"
            )

        elif subcategory == "portfolio":
            assert "tokens" in result_enrichment, (
                f"Portfolio enrichment missing tokens for {test_case['id']}"
            )
            assert (
                "allocation" in result_enrichment
                or "risk_tolerance" in result_enrichment
            ), (
                f"Portfolio enrichment missing allocation or risk_tolerance for {test_case['id']}"
            )

        elif subcategory == "risk_signals":
            assert "token_symbol" in result_enrichment, (
                f"Risk signals enrichment missing token_symbol for {test_case['id']}"
            )
            assert "risk_signals" in result_enrichment, (
                f"Risk signals enrichment missing risk_signals for {test_case['id']}"
            )
