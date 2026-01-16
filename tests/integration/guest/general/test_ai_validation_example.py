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
        if llm_validator.enabled:
            validation_result = await llm_validator.validate_single_response(
                test_name="test_guest_chat_bitcoin_query",
                user_input=user_input,
                agent_output=agent_output,
                expected_behavior="Should provide accurate information about Bitcoin as a cryptocurrency",
                conversation_id=data.get("conversation_id"),
            )

            # Log validation result
            print(f"\n🤖 LLM Validation: {validation_result.verdict.value} (confidence: {validation_result.confidence:.2f})")
            print(f"   Reasoning: {validation_result.reasoning}")

            # Optional: Assert on validation result
            # assert validation_result.verdict == ValidationVerdict.PASS
            # assert validation_result.confidence >= 0.8

        # Step 4: Optional log analysis on failure
        error_analysis = None
        test_passed = response.status_code == status.HTTP_200_OK

        if not test_passed and log_analyzer.enabled:
            error_analysis = log_analyzer.analyze_error(
                test_name="test_guest_chat_bitcoin_query",
                error_message=f"HTTP {response.status_code}: {response.text[:100]}",
                timestamp=datetime.utcnow(),
            )

            print(f"\n🔍 Error Analysis:")
            print(f"   Root Cause: {error_analysis.root_cause}")
            print(f"   Suggested Fix: {error_analysis.suggested_fix}")

        # Step 5: Write results to CSV
        result = EnhancedTestResult(
            test_type="test_guest_chat_bitcoin_query",
            device="chrome",
            is_multi_step=False,
            inputs=[user_input],
            outputs=[agent_output],
            test_pass=test_passed,
            llm_verdict=validation_result.verdict.value if validation_result else None,
            llm_confidence=validation_result.confidence if validation_result else None,
            error_analysis="; ".join(validation_result.semantic_issues) if validation_result and validation_result.semantic_issues else None,
            root_cause=error_analysis.root_cause if error_analysis else None,
            suggested_fix=error_analysis.suggested_fix if error_analysis else None,
            timestamp=datetime.utcnow(),
        )
        csv_writer.write_single_result(result)

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
        if llm_validator.enabled:
            steps = [
                {
                    "user_input": "I want to swap tokens",
                    "agent_output": output1,
                    "expected_behavior": "Should ask for token pair details",
                },
                {
                    "user_input": "ETH to USDC",
                    "agent_output": output2,
                    "expected_behavior": "Should ask for amount",
                },
                {
                    "user_input": "1 ETH",
                    "agent_output": output3,
                    "expected_behavior": "Should provide swap details and confirmation",
                },
            ]

            flow_validation = await llm_validator.validate_multistep_flow(
                test_name="test_multistep_swap_flow",
                steps=steps,
                expected_flow_behavior="Should guide user through complete swap flow with context retention",
                conversation_id=conv_id,
            )

            print(f"\n🤖 Multi-Step Validation: {flow_validation.verdict.value}")
            print(f"   Confidence: {flow_validation.confidence:.2f}")
            print(f"   Context Consistency: {flow_validation.context_consistency_score:.2f}")
            print(f"   Reasoning: {flow_validation.reasoning}")

            # Check individual steps
            for i, step_val in enumerate(flow_validation.step_validations, 1):
                print(f"   Step {i}: {step_val.verdict.value} ({step_val.confidence:.2f})")

        # Write to CSV
        result = EnhancedTestResult(
            test_type="test_multistep_swap_flow",
            device="chrome",
            is_multi_step=True,
            inputs=["I want to swap tokens", "ETH to USDC", "1 ETH"],
            outputs=[output1, output2, output3],
            test_pass=True,
            timestamp=datetime.utcnow(),
        )

        if llm_validator.enabled and "flow_validation" in locals():
            result.llm_verdict = flow_validation.verdict.value
            result.llm_confidence = flow_validation.confidence

        csv_writer.write_single_result(result)

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
        if llm_validator.enabled:
            validation_result = await llm_validator.validate_single_response(
                test_name="test_xss_injection_protection",
                user_input=xss_input,
                agent_output=agent_output,
                expected_behavior=(
                    "Should provide Bitcoin price information while safely handling "
                    "the XSS attempt without executing or exposing the script tags"
                ),
                conversation_id=data.get("conversation_id"),
            )

            print(f"\n🤖 Security Validation: {validation_result.verdict.value}")
            print(f"   Confidence: {validation_result.confidence:.2f}")
            print(f"   Reasoning: {validation_result.reasoning}")

            # Verify AI confirms security handling
            assert validation_result.verdict in [ValidationVerdict.PASS, ValidationVerdict.WARNING]

        # Write to CSV
        result = EnhancedTestResult(
            test_type="security_xss_injection_protection",
            device="chrome",
            is_multi_step=False,
            inputs=[xss_input],
            outputs=[agent_output],
            test_pass=True,
            llm_verdict=validation_result.verdict.value if llm_validator.enabled and validation_result else None,
            llm_confidence=validation_result.confidence if llm_validator.enabled and validation_result else None,
            timestamp=datetime.utcnow(),
        )
        csv_writer.write_single_result(result)


# Standalone example function for documentation
async def example_usage():
    """
    Standalone example of using AI validation in tests.

    This can be run independently to demonstrate the API.
    """
    # Initialize components
    validator = LLMTestValidator()
    analyzer = LogAnalyzer()
    writer = EnhancedCSVWriter("tests/output/example_results.csv")

    # Simulate a test result
    test_passed = True
    user_input = "What is Ethereum?"
    agent_output = "Ethereum is a decentralized blockchain platform..."

    # Validate with AI (if enabled)
    validation_result = None
    if validator.enabled:
        validation_result = await validator.validate_single_response(
            test_name="example_test",
            user_input=user_input,
            agent_output=agent_output,
            expected_behavior="Should provide accurate Ethereum information",
        )
        print(f"Validation: {validation_result.verdict.value} ({validation_result.confidence:.2f})")

    # Analyze logs on failure (if enabled)
    error_analysis = None
    if not test_passed and analyzer.enabled:
        error_analysis = analyzer.analyze_error(
            test_name="example_test",
            error_message="Test failed",
            timestamp=datetime.utcnow(),
        )
        print(f"Root cause: {error_analysis.root_cause}")

    # Write to CSV
    result = EnhancedTestResult(
        test_type="example_test",
        device="chrome",
        is_multi_step=False,
        inputs=[user_input],
        outputs=[agent_output],
        test_pass=test_passed,
        llm_verdict=validation_result.verdict.value if validation_result else None,
        llm_confidence=validation_result.confidence if validation_result else None,
        root_cause=error_analysis.root_cause if error_analysis else None,
        suggested_fix=error_analysis.suggested_fix if error_analysis else None,
    )
    writer.write_single_result(result)


if __name__ == "__main__":
    # Run standalone example
    asyncio.run(example_usage())
