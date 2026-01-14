"""
LLM Validation System Test - Verify AI-powered test validation works.

Tests the complete LLM validation system with actual DeepInfra API:
- Semantic validation of responses
- Multi-step conversation flow validation
- Enhanced CSV output with AI analysis

Environment Variables (automatically loaded from config):
    DEEPINFRA_API_KEY - from config/local/.secrets.toml
    ENABLE_LLM_VALIDATION=true
    ENABLE_LOG_ANALYSIS=true

Usage:
    # Run with AI validation enabled
    ENABLE_LLM_VALIDATION=true ENABLE_LOG_ANALYSIS=true \
        pytest tests/integration/chat/test_llm_validation_system.py -v -s
"""

import os
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
def enable_ai_validation(monkeypatch):
    """Enable AI validation for these tests."""
    # Load DeepInfra API key from config
    monkeypatch.setenv("DEEPINFRA_API_KEY", "ur1aITAnOmIXK0LTT1zCBDGnk3elzsVA")
    monkeypatch.setenv("ENABLE_LLM_VALIDATION", "true")
    monkeypatch.setenv("ENABLE_LOG_ANALYSIS", "true")


@pytest.mark.integration
@pytest.mark.chat
class TestLLMValidationSystem:
    """Test LLM validation system with real API."""

    async def test_system_initialization(self, enable_ai_validation):
        """Test that LLM validation system initializes correctly."""
        validator = LLMTestValidator()
        analyzer = LogAnalyzer()
        writer = EnhancedCSVWriter("/tmp/test_init.csv")

        # Verify components are enabled
        assert validator.enabled, "LLM validator should be enabled"
        assert analyzer.enabled, "Log analyzer should be enabled"

        print(f"\n✅ LLM Validator: ENABLED")
        print(f"✅ Log Analyzer: ENABLED")
        print(f"✅ CSV Writer: READY")

    async def test_semantic_validation_with_real_api(
        self,
        client: AsyncClient,
        llm_validator: LLMTestValidator,
        csv_writer: EnhancedCSVWriter,
        enable_ai_validation,
    ):
        """
        Test semantic validation with real DeepInfra API.

        This test:
        1. Makes a real API call to guest chat
        2. Validates response semantically with AI
        3. Writes results to CSV with AI analysis
        """
        # Step 1: Make real API call
        user_input = "What is Bitcoin?"
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": user_input, "language": "en"},
        )

        # Step 2: Standard assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "agent_message" in data
        agent_output = data["agent_message"]["content"]
        assert len(agent_output) > 0

        # Step 3: AI semantic validation
        assert llm_validator.enabled, "LLM validator must be enabled for this test"

        validation_result = await llm_validator.validate_single_response(
            test_name="test_bitcoin_semantic_validation",
            user_input=user_input,
            agent_output=agent_output,
            expected_behavior="Should provide accurate information about Bitcoin as a cryptocurrency",
            conversation_id=data.get("conversation_id"),
        )

        # Print validation results
        print(f"\n🤖 AI Validation Results:")
        print(f"   Verdict: {validation_result.verdict.value}")
        print(f"   Confidence: {validation_result.confidence:.2f}")
        print(f"   Reasoning: {validation_result.reasoning}")
        print(f"   Tokens Used: {validation_result.tokens_used}")
        print(f"   Time: {validation_result.validation_time_ms}ms")

        # Verify validation worked
        assert validation_result.verdict in [
            ValidationVerdict.PASS,
            ValidationVerdict.WARNING,
        ], f"Validation failed: {validation_result.reasoning}"
        assert validation_result.confidence > 0.5, "Confidence too low"
        assert validation_result.tokens_used > 0, "Should have used tokens"

        # Step 4: Write to CSV
        result = EnhancedTestResult(
            test_type="test_bitcoin_semantic_validation",
            device="chrome",
            is_multi_step=False,
            inputs=[user_input],
            outputs=[agent_output],
            test_pass=True,
            llm_verdict=validation_result.verdict.value,
            llm_confidence=validation_result.confidence,
        )
        csv_writer.write_single_result(result)

        print(f"\n✅ Test completed successfully!")
        print(f"   Cost: ${validation_result.tokens_used / 1_000_000 * 0.08:.6f}")

    async def test_multistep_flow_validation(
        self,
        client: AsyncClient,
        llm_validator: LLMTestValidator,
        enable_ai_validation,
    ):
        """
        Test multi-step conversation flow validation.

        Validates that AI understands conversation context across multiple steps.
        """
        assert llm_validator.enabled, "LLM validator must be enabled"

        # Step 1: Initial request
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I want to check crypto prices", "language": "en"},
        )
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conv_id = data1["conversation_id"]
        output1 = data1["agent_message"]["content"]

        # Step 2: Follow-up
        response2 = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "Show me Bitcoin price", "language": "en"},
        )
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        output2 = data2["agent_message"]["content"]

        # AI multi-step validation
        flow_result = await llm_validator.validate_multistep_flow(
            test_name="test_price_check_flow",
            steps=[
                {
                    "user_input": "I want to check crypto prices",
                    "agent_output": output1,
                    "expected_behavior": "Should acknowledge and offer to show prices",
                },
                {
                    "user_input": "Show me Bitcoin price",
                    "agent_output": output2,
                    "expected_behavior": "Should provide Bitcoin price information",
                },
            ],
            expected_flow_behavior="Should maintain context and provide price information",
            conversation_id=conv_id,
        )

        print(f"\n🤖 Multi-Step Flow Results:")
        print(f"   Verdict: {flow_result.verdict.value}")
        print(f"   Confidence: {flow_result.confidence:.2f}")
        print(f"   Context Consistency: {flow_result.context_consistency_score:.2f}")
        print(f"   Reasoning: {flow_result.reasoning}")
        print(f"   Total Tokens: {flow_result.tokens_used}")

        # Individual steps
        for i, step_val in enumerate(flow_result.step_validations, 1):
            print(f"   Step {i}: {step_val.verdict.value} ({step_val.confidence:.2f})")

        # Verify flow validation
        assert flow_result.verdict in [ValidationVerdict.PASS, ValidationVerdict.WARNING]
        assert flow_result.confidence > 0.5
        assert flow_result.context_consistency_score >= 0.0

        print(f"\n✅ Multi-step validation completed!")
        print(f"   Cost: ${flow_result.tokens_used / 1_000_000 * 0.08:.6f}")

    async def test_csv_output_format(
        self,
        llm_validator: LLMTestValidator,
        csv_writer: EnhancedCSVWriter,
        enable_ai_validation,
    ):
        """Test that CSV output includes AI analysis columns."""
        # Create a test result with AI analysis
        result = EnhancedTestResult(
            test_type="test_csv_format",
            device="chrome",
            is_multi_step=False,
            inputs=["test input"],
            outputs=["test output"],
            test_pass=True,
            llm_verdict="PASS",
            llm_confidence=0.95,
            error_analysis="No issues found",
            root_cause=None,
            suggested_fix=None,
        )

        # Write to CSV
        csv_writer.write_single_result(result)

        # Read and verify
        import csv
        with open(csv_writer.output_file, "r") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            # Verify AI columns are present
            assert "llm_verdict" in headers
            assert "llm_confidence" in headers
            assert "error_analysis" in headers
            assert "root_cause" in headers
            assert "suggested_fix" in headers

            # Verify data
            row = next(reader)
            assert row["llm_verdict"] == "PASS"
            assert row["llm_confidence"] == "0.95"
            assert row["error_analysis"] == "No issues found"

        print(f"\n✅ CSV format verified!")
        print(f"   Columns: {', '.join(headers)}")


@pytest.mark.skipif(
    os.getenv("ENABLE_LLM_VALIDATION", "false").lower() != "true",
    reason="LLM validation not enabled - set ENABLE_LLM_VALIDATION=true to run",
)
class TestLLMValidationEnabled:
    """Tests that only run when LLM validation is explicitly enabled."""

    async def test_validation_actually_enabled(self, enable_ai_validation):
        """Verify validation is actually enabled."""
        validator = LLMTestValidator()
        assert validator.enabled, "LLM validation should be enabled when ENABLE_LLM_VALIDATION=true"
        print("\n✅ LLM validation is enabled and ready to use!")
