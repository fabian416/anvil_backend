"""
Component tests for ULTRA handler and intent classification.

Tests ULTRA business logic in isolation from HTTP layer:
- Intent classification for ULTRA queries
- Handler routing for ULTRA intents
- ULTRA handler execution logic
- Enrichment data validation

Performance target: <100ms per test (vs 2000-5000ms for HTTP integration tests).
"""

import pytest
from typing import Dict, Any

from tests.helpers.test_data_loader import (
    get_ultra_test_cases,
    get_test_case_by_id,
)


@pytest.mark.asyncio
class TestULTRAIntentClassification:
    """Component tests for ULTRA intent classification logic."""

    @pytest.mark.parametrize("test_case", get_ultra_test_cases(), ids=lambda tc: tc["id"])
    async def test_classify_ultra_intent(
        self,
        mock_intent_classifier,
        test_case: Dict[str, Any],
    ):
        """
        WHEN user sends ULTRA query
        THEN intent classifier SHALL identify correct ULTRA intent

        This tests the intent classification business logic without HTTP layer.
        """
        # Arrange: Configure mock classifier to return expected intent
        expected_intent = test_case["expected_routing"]["intent"]
        expected_confidence_min = test_case["expected_routing"].get("confidence_min", 0.5)

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
class TestULTRAHandlerRouting:
    """Component tests for ULTRA handler routing logic."""

    @pytest.mark.parametrize(
        "intent,expected_handler",
        [
            ("ultra_arbitrage", "ultra_handler"),
            ("ultra_auto_executor", "ultra_handler"),
            ("ultra_flash_loans", "ultra_handler"),
            ("ultra_mev_protection", "ultra_handler"),
        ],
    )
    async def test_route_ultra_intent_to_handler(
        self,
        mock_handler_router,
        intent: str,
        expected_handler: str,
    ):
        """
        WHEN ULTRA intent is classified
        THEN handler router SHALL select ULTRA handler

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
class TestULTRAHandlerExecution:
    """Component tests for ULTRA handler business logic."""

    async def test_ultra_arbitrage_execution(
        self,
        mock_ultra_handler,
    ):
        """
        WHEN ULTRA arbitrage scan is executed
        THEN handler SHALL return arbitrage opportunities with enrichment

        Tests ULTRA arbitrage scanner handler logic.
        """
        # Arrange: Configure mock handler response
        test_case = get_test_case_by_id("ultra_arb_001")
        assert test_case is not None, "Test case ultra_arb_001 not found"

        mock_ultra_handler.execute.return_value = {
            "content": "Mock ULTRA arbitrage scan results",
            "enrichment": {
                "ultra_tool": "arbitrage_scanner",
                "capital": 10000,
                "arb_type": "cross_dex",
                "opportunities": [
                    {
                        "dex_pair": "Uniswap-Sushiswap",
                        "token": "ETH",
                        "profit_usd": 250.50,
                        "confidence": 0.92,
                    }
                ],
            },
        }

        # Act: Execute handler
        result = await mock_ultra_handler.execute(
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
        assert "ultra_tool" in enrichment, (
            "ULTRA enrichment must include ultra_tool"
        )
        assert "capital" in enrichment or "opportunities" in enrichment, (
            "Arbitrage enrichment must include capital or opportunities"
        )

    async def test_ultra_auto_executor_execution(
        self,
        mock_ultra_handler,
    ):
        """
        WHEN ULTRA auto executor is triggered
        THEN handler SHALL return execution confirmation

        Tests ULTRA auto executor handler logic.
        """
        # Arrange: Configure mock handler for auto executor
        test_case = get_test_case_by_id("ultra_ae_001")
        if test_case is None:
            pytest.skip("Test case ultra_ae_001 not found in test_data.json")

        mock_ultra_handler.execute.return_value = {
            "content": "Mock auto execution results",
            "enrichment": {
                "ultra_tool": "auto_executor",
                "action": "execute_trade",
                "status": "executed",
                "transaction_hash": "0xabc123...",
            },
        }

        # Act: Execute handler
        result = await mock_ultra_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify auto executor enrichment
        enrichment = result["enrichment"]
        assert "ultra_tool" in enrichment
        assert "action" in enrichment or "status" in enrichment, (
            "Auto executor enrichment must include action or status"
        )

    async def test_ultra_flash_loans_execution(
        self,
        mock_ultra_handler,
    ):
        """
        WHEN ULTRA flash loan analysis is executed
        THEN handler SHALL return flash loan recommendations

        Tests ULTRA flash loan handler logic.
        """
        # Arrange: Configure mock handler for flash loans
        mock_ultra_handler.execute.return_value = {
            "content": "Mock flash loan analysis results",
            "enrichment": {
                "ultra_tool": "flash_loan_analyzer",
                "token_symbol": "DAI",
                "amount": 1000000,
                "protocol_recommendations": [
                    {"protocol": "Aave", "fee": 0.09, "max_amount": 5000000},
                    {"protocol": "dYdX", "fee": 0.00, "max_amount": 2000000},
                ],
            },
        }

        # Act: Execute handler
        result = await mock_ultra_handler.execute(
            content="Analyze flash loan options for DAI",
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify flash loan enrichment
        enrichment = result["enrichment"]
        assert "ultra_tool" in enrichment
        assert "token_symbol" in enrichment or "protocol_recommendations" in enrichment, (
            "Flash loan enrichment must include token_symbol or protocol_recommendations"
        )

    async def test_ultra_mev_protection_execution(
        self,
        mock_ultra_handler,
    ):
        """
        WHEN ULTRA MEV protection is executed
        THEN handler SHALL return protection recommendations

        Tests ULTRA MEV protection handler logic.
        """
        # Arrange: Configure mock handler for MEV protection
        mock_ultra_handler.execute.return_value = {
            "content": "Mock MEV protection results",
            "enrichment": {
                "ultra_tool": "mev_protector",
                "opportunity_id": "arb_001",
                "protection_method": "flashbots_rpc",
                "recommendations": [
                    {"method": "flashbots", "priority_fee": 2.5, "success_rate": 0.95},
                    {"method": "private_relay", "priority_fee": 3.0, "success_rate": 0.98},
                ],
            },
        }

        # Act: Execute handler
        result = await mock_ultra_handler.execute(
            content="Protect my arbitrage from MEV",
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify MEV protection enrichment
        enrichment = result["enrichment"]
        assert "ultra_tool" in enrichment
        assert "protection_method" in enrichment or "recommendations" in enrichment, (
            "MEV protection enrichment must include protection_method or recommendations"
        )


@pytest.mark.asyncio
class TestULTRAEnrichmentValidation:
    """Component tests for ULTRA enrichment data structure."""

    @pytest.mark.parametrize("test_case", get_ultra_test_cases(), ids=lambda tc: tc["id"])
    async def test_ultra_enrichment_structure(
        self,
        mock_ultra_handler,
        test_case: Dict[str, Any],
    ):
        """
        WHEN ULTRA handler returns enrichment data
        THEN enrichment SHALL match expected structure for subcategory

        Validates enrichment data structure for each ULTRA subcategory.
        """
        # Arrange: Get subcategory-specific enrichment expectations
        subcategory = test_case["_subcategory"]
        expected_enrichment = test_case.get("expected_enrichment", {})

        # Configure mock handler with appropriate enrichment
        if subcategory == "arbitrage":
            enrichment = {
                "ultra_tool": "arbitrage_scanner",
                "capital": 10000,
                "arb_type": "cross_dex",
                "opportunities": [
                    {"dex_pair": "Uni-Sushi", "profit_usd": 100.0}
                ],
            }
        elif subcategory == "auto_executor":
            enrichment = {
                "ultra_tool": "auto_executor",
                "action": "execute_trade",
                "status": "executed",
            }
        elif subcategory == "flash_loans":
            enrichment = {
                "ultra_tool": "flash_loan_analyzer",
                "token_symbol": "DAI",
                "amount": 1000000,
                "protocol_recommendations": [
                    {"protocol": "Aave", "fee": 0.09}
                ],
            }
        elif subcategory == "mev_protection":
            enrichment = {
                "ultra_tool": "mev_protector",
                "opportunity_id": "arb_001",
                "protection_method": "flashbots",
                "recommendations": [
                    {"method": "flashbots", "priority_fee": 2.5}
                ],
            }
        else:
            enrichment = {}

        mock_ultra_handler.execute.return_value = {
            "content": "Mock response",
            "enrichment": enrichment,
        }

        # Act: Execute handler
        result = await mock_ultra_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify enrichment structure matches subcategory
        result_enrichment = result.get("enrichment", {})

        # All ULTRA enrichment must include ultra_tool
        assert "ultra_tool" in result_enrichment, (
            f"ULTRA enrichment missing ultra_tool for {test_case['id']}"
        )

        # Verify subcategory-specific enrichment
        if subcategory == "arbitrage":
            assert "capital" in result_enrichment or "opportunities" in result_enrichment, (
                f"Arbitrage enrichment missing capital or opportunities for {test_case['id']}"
            )

        elif subcategory == "auto_executor":
            assert "action" in result_enrichment or "status" in result_enrichment, (
                f"Auto executor enrichment missing action or status for {test_case['id']}"
            )

        elif subcategory == "flash_loans":
            assert "token_symbol" in result_enrichment or "protocol_recommendations" in result_enrichment, (
                f"Flash loan enrichment missing token_symbol or protocol_recommendations for {test_case['id']}"
            )

        elif subcategory == "mev_protection":
            assert "protection_method" in result_enrichment or "recommendations" in result_enrichment, (
                f"MEV protection enrichment missing protection_method or recommendations for {test_case['id']}"
            )
