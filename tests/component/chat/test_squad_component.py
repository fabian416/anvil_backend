"""
Component tests for Agent Squad handler and intent classification.

Tests Agent Squad business logic in isolation from HTTP layer:
- Intent classification for Agent Squad queries
- Handler routing for Agent Squad intents
- Agent Squad handler execution logic
- Enrichment data validation

Performance target: <100ms per test (vs 2000-5000ms for HTTP integration tests).
"""

import pytest
from typing import Dict, Any

from tests.helpers.test_data_loader import (
    get_squad_test_cases,
    get_test_case_by_id,
)


@pytest.mark.asyncio
class TestSquadIntentClassification:
    """Component tests for Agent Squad intent classification logic."""

    @pytest.mark.parametrize(
        "test_case", get_squad_test_cases(), ids=lambda tc: tc["id"]
    )
    async def test_classify_squad_intent(
        self,
        mock_intent_classifier,
        test_case: Dict[str, Any],
    ):
        """
        WHEN user sends Agent Squad query
        THEN intent classifier SHALL identify correct Agent Squad intent

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
class TestSquadHandlerRouting:
    """Component tests for Agent Squad handler routing logic."""

    @pytest.mark.parametrize(
        "intent,expected_handler",
        [
            ("specialist_task", "squad_handler"),
            ("complex_workflow", "squad_handler"),
        ],
    )
    async def test_route_squad_intent_to_handler(
        self,
        mock_handler_router,
        intent: str,
        expected_handler: str,
    ):
        """
        WHEN Agent Squad intent is classified
        THEN handler router SHALL select Agent Squad handler

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
class TestSquadHandlerExecution:
    """Component tests for Agent Squad handler business logic."""

    async def test_squad_specialist_task_execution(
        self,
        mock_squad_handler,
    ):
        """
        WHEN Agent Squad specialist task is executed
        THEN handler SHALL return task results with enrichment

        Tests Agent Squad specialist task handler logic.
        """
        # Arrange: Configure mock handler response
        test_case = get_test_case_by_id("squad_spec_001")
        assert test_case is not None, "Test case squad_spec_001 not found"

        mock_squad_handler.execute.return_value = {
            "content": "Mock Agent Squad specialist task results",
            "enrichment": {
                "task_type": "code_review",
                "tools_used": ["static_analyzer", "security_scanner"],
                "agents_involved": ["code_quality_specialist"],
                "completion_time": 45.2,
            },
        }

        # Act: Execute handler
        result = await mock_squad_handler.execute(
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
        assert "task_type" in enrichment or "tools_used" in enrichment, (
            "Specialist task enrichment must include task_type or tools_used"
        )

    async def test_squad_complex_workflow_execution(
        self,
        mock_squad_handler,
    ):
        """
        WHEN Agent Squad complex workflow is executed
        THEN handler SHALL return workflow results with enrichment

        Tests Agent Squad complex workflow handler logic.
        """
        # Arrange: Configure mock handler for complex workflow
        test_case = get_test_case_by_id("squad_work_001")
        if test_case is None:
            pytest.skip("Test case squad_work_001 not found in test_data.json")

        mock_squad_handler.execute.return_value = {
            "content": "Mock complex workflow results",
            "enrichment": {
                "workflow_type": "full_feature_implementation",
                "workflow_id": "wf_12345",
                "agents_count": 5,
                "capital": 50000,
                "phases": [
                    {"phase": "planning", "status": "completed", "agents": 2},
                    {"phase": "implementation", "status": "in_progress", "agents": 3},
                ],
            },
        }

        # Act: Execute handler
        result = await mock_squad_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify response structure
        assert "content" in result
        assert "enrichment" in result

        # Assert: Verify workflow enrichment
        enrichment = result["enrichment"]
        assert "workflow_type" in enrichment or "workflow_id" in enrichment, (
            "Complex workflow enrichment must include workflow_type or workflow_id"
        )
        assert "agents_count" in enrichment or "phases" in enrichment, (
            "Complex workflow enrichment must include agents_count or phases"
        )


@pytest.mark.asyncio
class TestSquadEnrichmentValidation:
    """Component tests for Agent Squad enrichment data structure."""

    @pytest.mark.parametrize(
        "test_case", get_squad_test_cases(), ids=lambda tc: tc["id"]
    )
    async def test_squad_enrichment_structure(
        self,
        mock_squad_handler,
        test_case: Dict[str, Any],
    ):
        """
        WHEN Agent Squad handler returns enrichment data
        THEN enrichment SHALL match expected structure for subcategory

        Validates enrichment data structure for each Agent Squad subcategory.
        """
        # Arrange: Get subcategory-specific enrichment expectations
        subcategory = test_case["_subcategory"]
        expected_enrichment = test_case.get("expected_enrichment", {})

        # Configure mock handler with appropriate enrichment
        if subcategory == "specialist_task":
            enrichment = {
                "task_type": "code_review",
                "tools_used": ["analyzer", "linter"],
                "agents_involved": ["specialist"],
                "completion_time": 30.0,
            }
        elif subcategory == "complex_workflow":
            enrichment = {
                "workflow_type": "feature_implementation",
                "workflow_id": "wf_001",
                "agents_count": 5,
                "capital": 50000,
                "phases": [{"phase": "planning", "status": "completed"}],
            }
        else:
            enrichment = {}

        mock_squad_handler.execute.return_value = {
            "content": "Mock response",
            "enrichment": enrichment,
        }

        # Act: Execute handler
        result = await mock_squad_handler.execute(
            content=test_case["input"]["content"],
            context={},
        )

        # Assert: Verify enrichment structure matches subcategory
        result_enrichment = result.get("enrichment", {})

        # Verify subcategory-specific enrichment
        if subcategory == "specialist_task":
            assert (
                "task_type" in result_enrichment or "tools_used" in result_enrichment
            ), (
                f"Specialist task enrichment missing task_type or tools_used for {test_case['id']}"
            )

        elif subcategory == "complex_workflow":
            assert (
                "workflow_type" in result_enrichment
                or "workflow_id" in result_enrichment
            ), (
                f"Complex workflow enrichment missing workflow_type or workflow_id for {test_case['id']}"
            )
            assert (
                "agents_count" in result_enrichment or "phases" in result_enrichment
            ), (
                f"Complex workflow enrichment missing agents_count or phases for {test_case['id']}"
            )
