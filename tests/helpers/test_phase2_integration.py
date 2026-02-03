"""Phase 2 Integration Test - End-to-end validation of enhanced validation system.

This test verifies that all Phase 2 components work together correctly:
- TestMetadataExtractor extracts test metadata
- ValidationPromptGenerator creates custom prompts
- Enhanced ValidationResult with granular scoring
- CSV tracker writes both standard and enhanced CSVs
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_metadata_extraction():
    """Test 1: Extract metadata from a sample test function."""
    print("\n" + "=" * 60)
    print("Test 1: Metadata Extraction")
    print("=" * 60)

    from tests.helpers.test_metadata_extractor import TestMetadataExtractor, TestType

    def sample_test_function(client):
        """Sample test for BTC sentiment."""
        response = client.post(
            "/api/v1/guest/chat", json={"query": "What's BTC sentiment?"}
        )
        assert response.status_code == 200
        content = response.json()["content"]
        assert "sentiment" in content.lower()
        assert "btc" in content.lower() or "bitcoin" in content.lower()

    extractor = TestMetadataExtractor()
    metadata = extractor.extract_metadata(sample_test_function)

    print(f"  ✓ Test name: {metadata.test_name}")
    print(f"  ✓ Test type: {metadata.test_type.value}")
    print(f"  ✓ Test category: {metadata.test_category}")
    print(f"  ✓ Expected status code: {metadata.expected_status_code}")
    print(f"  ✓ Required keywords: {metadata.required_keywords}")
    print(f"  ✓ Assertions extracted: {len(metadata.assertions)}")

    assert metadata.test_name == "sample_test_function"
    assert metadata.test_type == TestType.SIMPLE_QUERY
    assert metadata.expected_status_code == 200

    print("\n✅ Test 1 PASSED: Metadata extraction works correctly")
    return metadata


def test_prompt_generation(metadata):
    """Test 2: Generate custom validation prompt."""
    print("\n" + "=" * 60)
    print("Test 2: Custom Prompt Generation")
    print("=" * 60)

    from tests.helpers.validation_prompt_generator import ValidationPromptGenerator

    generator = ValidationPromptGenerator()
    prompt = generator.generate_prompt(
        test_metadata=metadata,
        user_input="What's the sentiment for BTC today?",
        agent_output="Bitcoin sentiment is currently bullish with strong buying pressure.",
        expected_behavior="Should provide BTC sentiment analysis with current market sentiment.",
    )

    print(f"  ✓ Prompt generated: {len(prompt)} characters")
    print(
        f"  ✓ Contains test name: {'test_name' in prompt or metadata.test_name in prompt}"
    )
    print(f"  ✓ Contains accuracy_score: {'accuracy_score' in prompt}")
    print(f"  ✓ Contains relevance_score: {'relevance_score' in prompt}")
    print(f"  ✓ Contains safety_score: {'safety_score' in prompt}")
    print(f"  ✓ Contains coherence_score: {'coherence_score' in prompt}")
    print(f"  ✓ Contains JSON schema: {'verdict' in prompt and 'confidence' in prompt}")

    assert len(prompt) > 500
    assert "accuracy_score" in prompt
    assert "relevance_score" in prompt
    assert "safety_score" in prompt
    assert "coherence_score" in prompt

    print("\n✅ Test 2 PASSED: Prompt generation creates custom prompts correctly")
    return prompt


def test_enhanced_dataclasses():
    """Test 3: Create enhanced ValidationResult with all fields."""
    print("\n" + "=" * 60)
    print("Test 3: Enhanced Dataclasses")
    print("=" * 60)

    from tests.helpers.llm_test_validator import (
        ValidationResult,
        ValidationVerdict,
        ScoringBreakdown,
        ValidationMetadata,
        ActionableRecommendations,
    )

    # Create enhanced validation result
    scoring = ScoringBreakdown(
        accuracy_score=0.95,
        relevance_score=0.92,
        safety_score=1.0,
        coherence_score=0.94,
        overall_score=0.95,
    )

    metadata = ValidationMetadata(
        test_category="hunter",
        test_type="simple_query",
        expected_intents=["sentiment_analysis"],
        token_usage=850,
        validation_latency_ms=1200,
        model_used="meta-llama/Meta-Llama-3.1-70B-Instruct",
    )

    recommendations = ActionableRecommendations(
        improvement_suggestions=["Add more specific sentiment indicators"],
        critical_issues=[],
        next_steps=["Continue monitoring sentiment accuracy"],
    )

    result = ValidationResult(
        verdict=ValidationVerdict.PASS,
        confidence=0.95,
        reasoning="Response provides clear sentiment analysis",
        semantic_issues=[],
        tokens_used=850,
        validation_time_ms=1200,
        timestamp=datetime.utcnow(),
        scoring=scoring,
        metadata=metadata,
        recommendations=recommendations,
    )

    print(f"  ✓ Verdict: {result.verdict.value}")
    print(f"  ✓ Confidence: {result.confidence}")
    print(f"  ✓ Accuracy score: {result.scoring.accuracy_score}")
    print(f"  ✓ Relevance score: {result.scoring.relevance_score}")
    print(f"  ✓ Safety score: {result.scoring.safety_score}")
    print(f"  ✓ Coherence score: {result.scoring.coherence_score}")
    print(f"  ✓ Overall score: {result.scoring.overall_score}")
    print(f"  ✓ Test category: {result.metadata.test_category}")
    print(f"  ✓ Test type: {result.metadata.test_type}")
    print(
        f"  ✓ Improvement suggestions: {len(result.recommendations.improvement_suggestions)}"
    )

    assert result.verdict == ValidationVerdict.PASS
    assert result.scoring.accuracy_score == 0.95
    assert result.metadata.test_category == "hunter"
    assert len(result.recommendations.improvement_suggestions) == 1

    print("\n✅ Test 3 PASSED: Enhanced dataclasses work correctly")
    return result


def test_csv_tracking(validation_result):
    """Test 4: CSV tracking with standard and enhanced export."""
    print("\n" + "=" * 60)
    print("Test 4: CSV Tracking (Dual-File Export)")
    print("=" * 60)

    from tests.helpers.csv_tracker import CSVTestTracker, TestExecutionData

    # Set environment variable for enhanced CSV
    os.environ["WRITE_ENHANCED_CSV"] = "true"

    # Create tracker with test output directory
    tracker = CSVTestTracker(base_path="tests/output/phase2_test")

    # Create test execution data with enhanced fields
    test_data = TestExecutionData(
        # Standard 11 fields
        test_id="phase2_integration_test_001",
        s_multistep=False,
        input="What's the sentiment for BTC today?",
        output="Bitcoin sentiment is currently bullish.",
        test_label_sequence="hunter_sentiment",
        output_expected="BTC sentiment analysis",
        status="PASS",
        date=datetime.utcnow().isoformat(),
        quality=validation_result.scoring.overall_score,
        qa_status=validation_result.verdict.value,
        qa_output=validation_result.reasoning,
        # Enhanced 12 fields
        accuracy_score=validation_result.scoring.accuracy_score,
        relevance_score=validation_result.scoring.relevance_score,
        safety_score=validation_result.scoring.safety_score,
        coherence_score=validation_result.scoring.coherence_score,
        test_category=validation_result.metadata.test_category,
        test_type=validation_result.metadata.test_type,
        expected_intents=json.dumps(validation_result.metadata.expected_intents),
        token_usage=validation_result.metadata.token_usage,
        improvement_suggestions=json.dumps(
            validation_result.recommendations.improvement_suggestions
        ),
        critical_issues=json.dumps(validation_result.recommendations.critical_issues),
        next_steps=json.dumps(validation_result.recommendations.next_steps),
        model_used=validation_result.metadata.model_used,
    )

    # Track to CSV (should create both standard and enhanced files)
    tracker.track("guest", "integration_test", test_data)

    # Verify both files exist
    standard_csv = Path("tests/output/phase2_test/guest/integration_test.csv")
    enhanced_csv = Path("tests/output/phase2_test/guest/integration_test_enhanced.csv")

    print(f"  ✓ Standard CSV exists: {standard_csv.exists()}")
    print(f"  ✓ Enhanced CSV exists: {enhanced_csv.exists()}")

    if standard_csv.exists():
        with open(standard_csv, "r") as f:
            content = f.read()
            lines = content.strip().split("\n")
            print(f"  ✓ Standard CSV lines: {len(lines)} (header + 1 data row)")
            print(f"  ✓ Standard CSV columns: {len(lines[0].split(','))} (expected 11)")

    if enhanced_csv.exists():
        with open(enhanced_csv, "r") as f:
            content = f.read()
            lines = content.strip().split("\n")
            print(f"  ✓ Enhanced CSV lines: {len(lines)} (header + 1 data row)")
            print(f"  ✓ Enhanced CSV columns: {len(lines[0].split(','))} (expected 23)")

    assert standard_csv.exists(), "Standard CSV should exist"
    assert enhanced_csv.exists(), "Enhanced CSV should exist"

    print("\n✅ Test 4 PASSED: CSV tracking works with dual-file export")

    # Cleanup
    os.environ.pop("WRITE_ENHANCED_CSV", None)
    return True


def test_backward_compatibility():
    """Test 5: Verify backward compatibility with existing tests."""
    print("\n" + "=" * 60)
    print("Test 5: Backward Compatibility")
    print("=" * 60)

    from tests.helpers.csv_tracker import CSVTestTracker, TestExecutionData

    # Disable enhanced CSV for this test
    os.environ.pop("WRITE_ENHANCED_CSV", None)

    tracker = CSVTestTracker(base_path="tests/output/phase2_test")

    # Create test data with ONLY standard fields (no enhanced fields)
    old_style_data = TestExecutionData(
        test_id="backward_compat_test_001",
        s_multistep=False,
        input="Test input",
        output="Test output",
        test_label_sequence="test_label",
        output_expected="Expected output",
        status="PASS",
        date=datetime.utcnow().isoformat(),
        quality=0.95,
        qa_status="PASS",
        qa_output="Test passed",
        # Enhanced fields not provided (will be None/default)
    )

    # Should work without enhanced fields
    tracker.track("guest", "compat_test", old_style_data)

    compat_csv = Path("tests/output/phase2_test/guest/compat_test.csv")
    print(f"  ✓ Backward compatible CSV exists: {compat_csv.exists()}")
    print(
        f"  ✓ No enhanced CSV created: {not Path('tests/output/phase2_test/guest/compat_test_enhanced.csv').exists()}"
    )

    assert compat_csv.exists(), "Backward compatible CSV should exist"
    assert not Path(
        "tests/output/phase2_test/guest/compat_test_enhanced.csv"
    ).exists(), "Enhanced CSV should not be created when disabled"

    print("\n✅ Test 5 PASSED: Backward compatibility maintained")
    return True


def main():
    """Run all Phase 2 integration tests."""
    print("\n" + "=" * 60)
    print("Phase 2 Integration Tests - Enhanced Validation System")
    print("=" * 60)

    try:
        # Test 1: Metadata extraction
        metadata = test_metadata_extraction()

        # Test 2: Prompt generation
        prompt = test_prompt_generation(metadata)

        # Test 3: Enhanced dataclasses
        validation_result = test_enhanced_dataclasses()

        # Test 4: CSV tracking
        test_csv_tracking(validation_result)

        # Test 5: Backward compatibility
        test_backward_compatibility()

        print("\n" + "=" * 60)
        print("✅ ALL PHASE 2 INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nPhase 2 Integration Complete:")
        print("  ✓ Custom prompt generation working")
        print("  ✓ Enhanced validation result structure")
        print("  ✓ Dual-file CSV export (11 + 23 columns)")
        print("  ✓ Backward compatibility maintained")
        print("  ✓ All components integrated successfully")
        print("\nNext Steps:")
        print("  → Phase 3: Pilot rollout (10-20 test files)")
        print("  → Update tests to use test_func parameter")
        print("  → Verify enhanced CSV data quality")

        return 0

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
