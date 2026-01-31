"""
Example integration test with AI validation.

Demonstrates how to use LLMTestValidator and LogAnalyzer in integration tests.

Environment Variables Required:
    ENABLE_LLM_VALIDATION=true  # Enable LLM validation
    ENABLE_LOG_ANALYSIS=true    # Enable log analysis
    DEEPINFRA_API_KEY=xxx       # DeepInfra API key

Usage:
    # Run without AI validation (fast)
    pytest tests/integration/chat/test_ai_validation_example.py

    # Run with AI validation (slower, requires API key)
    ENABLE_LLM_VALIDATION=true ENABLE_LOG_ANALYSIS=true DEEPINFRA_API_KEY=xxx \
        pytest tests/integration/chat/test_ai_validation_example.py -v
"""

import asyncio
from datetime import datetime

import pytest
from httpx import AsyncClient
from starlette import status

from tests.helpers.llm_test_validator import LLMTestValidator, ValidationVerdict
from tests.helpers.log_analyzer import LogAnalyzer
from tests.helpers.enhanced_csv_writer import (
    EnhancedCSVWriter,
    EnhancedTestResult,
)


@pytest.fixture
def llm_validator():
    """LLM test validator fixture."""
    return LLMTestValidator()


@pytest.fixture
def log_analyzer():
    """Log analyzer fixture."""
    return LogAnalyzer()


@pytest.fixture
def csv_writer(tmp_path):
    """CSV writer fixture."""
    output_file = tmp_path / "test_results.csv"
    return EnhancedCSVWriter(str(output_file))


class TestAIValidationExample:
    """Example tests demonstrating AI validation integration."""

    async def test_guest_chat_with_ai_validation(
        self,
        client: AsyncClient,
        llm_validator: LLMTestValidator,
        log_analyzer: LogAnalyzer,
        csv_writer: EnhancedCSVWriter,
    ):
        """
        Example: Test guest chat with full AI validation.

        This test demonstrates:
        1. Making an API call
        2. Standard assertions (unchanged)
        3. Optional LLM semantic validation
        4. Optional log analysis on failure
        5. Writing results with AI analysis to CSV
        """
        # Step 1: Make API call (standard test flow)
        user_input = "What is Bitcoin?"
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": user_input, "language": "en"},
        )

        # Step 2: Standard assertions (unchanged)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "agent_message" in data
        agent_output = data["agent_message"]["content"]
        assert len(agent_output) > 0

        # Step 3: Optional LLM semantic validation
        validation_result = None
    async def test_multistep_chat_with_ai_validation(
        self,
        client: AsyncClient,
        llm_validator: LLMTestValidator,
        csv_writer: EnhancedCSVWriter,
    ):
        """
        Example: Test multi-step chat with AI validation.

        Demonstrates validating conversation flow across multiple steps.
        """
        # Step 1: Initial request
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I want to swap tokens", "language": "en"},
        )
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conv_id = data1["conversation_id"]
        output1 = data1["agent_message"]["content"]

        # Step 2: Follow-up request
        response2 = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "ETH to USDC", "language": "en"},
        )
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        output2 = data2["agent_message"]["content"]

        # Step 3: Final request
        response3 = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1 ETH", "language": "en"},
        )
        assert response3.status_code == status.HTTP_200_OK
        data3 = response3.json()
        output3 = data3["agent_message"]["content"]

        # Multi-step AI validation
    async def test_security_injection_with_ai_validation(
        self,
        client: AsyncClient,
        llm_validator: LLMTestValidator,
        csv_writer: EnhancedCSVWriter,
    ):
        """
        Example: Test XSS injection protection with AI validation.

        AI validation helps verify not just that XSS is blocked,
        but that the response is semantically appropriate.
        """
        # Test XSS injection
        xss_input = "Show me Bitcoin <script>alert('XSS')</script> price"
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": xss_input, "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        agent_output = data["agent_message"]["content"]

        # Standard security assertion
        assert "<script>" not in agent_output.lower()
        assert "alert(" not in agent_output.lower()

        # AI validation - verify semantic appropriateness