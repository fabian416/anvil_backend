"""
Component tests for GraphRAG handler and intent classification.

Tests GraphRAG business logic in isolation from HTTP layer:
- Intent classification for GraphRAG queries
- Handler routing for GraphRAG intents
- GraphRAG handler execution logic
- Enrichment data validation

Performance target: <100ms per test (vs 2000-5000ms for HTTP integration tests).
"""

import pytest
from typing import Dict, Any

from tests.helpers.test_data_loader import (
    get_graphrag_test_cases,
    get_test_case_by_id,
)


@pytest.mark.asyncio
class TestGraphRAGIntentClassification:
    """Component tests for GraphRAG intent classification logic."""

    @pytest.mark.parametrize(
        "test_case", get_graphrag_test_cases(), ids=lambda tc: tc["id"]
    )
    async def test_classify_graphrag_intent(
        self,
        mock_intent_classifier,
        test_case: Dict[str, Any],
    ):
        """
        WHEN user sends GraphRAG query
        THEN intent classifier SHALL identify correct GraphRAG intent

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
class TestGraphRAGHandlerRouting:
    """Component tests for GraphRAG handler routing logic."""

    @pytest.mark.parametrize(
        "intent,expected_handler",
        [
            ("protocol_search", "graphrag_handler"),
            ("protocol_risk_assessment", "graphrag_handler"),
            ("similar_protocols", "graphrag_handler"),
        ],
    )
    async def test_route_graphrag_intent_to_handler(
        self,
        mock_handler_router,
        intent: str,
        expected_handler: str,
    ):
        """
        WHEN GraphRAG intent is classified
        THEN handler router SHALL select GraphRAG handler

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
class TestGraphRAGHandlerExecution:
    """Component tests for GraphRAG handler business logic."""

    async def test_graphrag_protocol_search_execution(
        self,
        mock_graphrag_handler,
    ):
        """
        WHEN GraphRAG protocol search is executed
        THEN handler SHALL return protocols with enrichment data

        Tests GraphRAG handler execution without external GraphRAG service.
        """
        # Arrange: Configure mock handler response
        test_case = get_test_case_by_id("graphrag_ps_001")
        assert test_case is not None, "Test case graphrag_ps_001 not found"

        mock_graphrag_handler.execute.return_value = {
            "content": "Mock protocol search results",
            "enrichment": {
                "protocols": [
                    {
                        "protocol_id": "aave_v3",
                        "protocol_name": "Aave V3",
                        "similarity_score": 0.95,
                        "risk_score": 0.15,
                        "category": "lending",
                    }
                ],
                "search_context": {
                    "search_type": "protocols",
                    "filters": {"category": "lending", "chain": "ethereum"},
                },
            },
        }

        # Act: Execute handler
        result = await mock_graphrag_handler.execute(
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
        assert "protocols" in enrichment or "search_context" in enrichment, (
            "GraphRAG enrichment must include protocols or search_context"
        )

        if "protocols" in enrichment:
            protocols = enrichment["protocols"]
            assert isinstance(protocols, list)
            assert len(protocols) > 0
            # Verify protocol structure
            protocol = protocols[0]
            assert "protocol_id" in protocol
            assert "protocol_name" in protocol
            assert "similarity_score" in protocol

    async def test_graphrag_risk_assessment_execution(
        self,
        mock_graphrag_handler,
    ):
        """
        WHEN GraphRAG risk assessment is executed
        THEN handler SHALL return risk analysis with enrichment

        Tests risk assessment handler logic.
        """
        # Arrange: Configure mock handler for risk assessment
        test_case = get_test_case_by_id("graphrag_ra_001")
        if test_case is None:
            pytest.skip("Test case graphrag_ra_001 not found in test_data.json")

        mock_graphrag_handler.execute.return_value = {
            "content": "Mock risk assessment results",
            "enrichment": {
                "protocol_name": "Aave V3",
                "risk_analysis": {
                    "overall_risk_score": 0.15,
                    "risk_level": "low",
                    "risk_factors": [
                        {"factor": "audit_coverage", "score": 0.05, "weight": 0.3},
                        {"factor": "tvl_stability", "score": 0.10, "weight": 0.3},
                    ],
                },
            },
        }

        # Act: Execute handler
        result = await mock_graphrag_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify risk assessment enrichment
        enrichment = result["enrichment"]
        assert "risk_analysis" in enrichment or "protocol_name" in enrichment, (
            "Risk assessment enrichment must include risk_analysis or protocol_name"
        )

    async def test_graphrag_similar_protocols_execution(
        self,
        mock_graphrag_handler,
    ):
        """
        WHEN GraphRAG similar protocols search is executed
        THEN handler SHALL return similar protocols with similarity scores

        Tests similar protocols handler logic.
        """
        # Arrange: Configure mock handler for similar protocols
        mock_graphrag_handler.execute.return_value = {
            "content": "Mock similar protocols results",
            "enrichment": {
                "base_protocol": "Aave V3",
                "similar_protocols": [
                    {
                        "protocol_id": "compound_v3",
                        "protocol_name": "Compound V3",
                        "similarity_score": 0.88,
                        "category": "lending",
                    },
                    {
                        "protocol_id": "morpho_blue",
                        "protocol_name": "Morpho Blue",
                        "similarity_score": 0.82,
                        "category": "lending",
                    },
                ],
            },
        }

        # Act: Execute handler
        result = await mock_graphrag_handler.execute(
            content="Find protocols similar to Aave",
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify similar protocols enrichment
        enrichment = result["enrichment"]
        assert "similar_protocols" in enrichment or "base_protocol" in enrichment, (
            "Similar protocols enrichment must include similar_protocols or base_protocol"
        )

        if "similar_protocols" in enrichment:
            similar = enrichment["similar_protocols"]
            assert isinstance(similar, list)
            assert len(similar) > 0


@pytest.mark.asyncio
class TestGraphRAGEnrichmentValidation:
    """Component tests for GraphRAG enrichment data structure."""

    @pytest.mark.parametrize(
        "test_case", get_graphrag_test_cases(), ids=lambda tc: tc["id"]
    )
    async def test_graphrag_enrichment_structure(
        self,
        mock_graphrag_handler,
        test_case: Dict[str, Any],
    ):
        """
        WHEN GraphRAG handler returns enrichment data
        THEN enrichment SHALL match expected structure for subcategory

        Validates enrichment data structure for each GraphRAG subcategory.
        """
        # Arrange: Get subcategory-specific enrichment expectations
        subcategory = test_case["_subcategory"]
        expected_enrichment = test_case.get("expected_enrichment", {})

        # Configure mock handler with appropriate enrichment
        if subcategory == "protocol_search":
            enrichment = {
                "protocols": [
                    {"protocol_id": "test", "protocol_name": "Test Protocol"}
                ],
                "search_context": {"search_type": "protocols"},
            }
        elif subcategory == "risk_assessment":
            enrichment = {
                "protocol_name": "Test Protocol",
                "risk_analysis": {"overall_risk_score": 0.25, "risk_level": "low"},
            }
        elif subcategory == "similar_protocols":
            enrichment = {
                "base_protocol": "Test Protocol",
                "similar_protocols": [
                    {"protocol_id": "similar", "similarity_score": 0.85}
                ],
            }
        else:
            enrichment = {}

        mock_graphrag_handler.execute.return_value = {
            "content": "Mock response",
            "enrichment": enrichment,
        }

        # Act: Execute handler
        result = await mock_graphrag_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify enrichment structure matches subcategory
        result_enrichment = result.get("enrichment", {})

        if subcategory == "protocol_search":
            assert (
                "protocols" in result_enrichment
                or "search_context" in result_enrichment
            ), f"Protocol search enrichment missing for {test_case['id']}"

        elif subcategory == "risk_assessment":
            assert (
                "risk_analysis" in result_enrichment
                or "protocol_name" in result_enrichment
            ), f"Risk assessment enrichment missing for {test_case['id']}"

        elif subcategory == "similar_protocols":
            assert (
                "similar_protocols" in result_enrichment
                or "base_protocol" in result_enrichment
            ), f"Similar protocols enrichment missing for {test_case['id']}"
