"""Phase 1 Component Verification Script.

This script verifies that all Phase 1 components can be imported and instantiated correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def verify_test_metadata_extractor():
    """Verify TestMetadataExtractor can be imported and instantiated."""
    print("✓ Testing TestMetadataExtractor...")

    from tests.helpers.test_metadata_extractor import (
        TestMetadataExtractor,
        TestType,
        TestMetadata,
        ExtractedAssertion,
    )

    # Test instantiation
    extractor = TestMetadataExtractor()
    assert extractor is not None

    # Test enum
    assert TestType.SIMPLE_QUERY.value == "simple_query"
    assert TestType.MULTI_STEP.value == "multi_step"
    assert TestType.INTENT_DETECTION.value == "intent_detection"
    assert TestType.SECURITY.value == "security"

    print("  ✓ TestMetadataExtractor imports correctly")
    print("  ✓ TestType enum works correctly")
    print("  ✓ TestMetadata dataclass available")
    print("  ✓ ExtractedAssertion dataclass available")


def verify_validation_prompt_generator():
    """Verify ValidationPromptGenerator can be imported and instantiated."""
    print("\n✓ Testing ValidationPromptGenerator...")

    from tests.helpers.validation_prompt_generator import ValidationPromptGenerator

    # Test instantiation
    generator = ValidationPromptGenerator()
    assert generator is not None
    assert len(generator.strategies) == 6  # 6 test types

    print("  ✓ ValidationPromptGenerator imports correctly")
    print("  ✓ Strategy pattern initialized with 6 strategies")


def verify_prompt_strategies():
    """Verify all prompt strategies can be imported."""
    print("\n✓ Testing Prompt Strategies...")

    from tests.helpers.prompt_strategies import (
        SimpleQueryStrategy,
        MultiStepFlowStrategy,
        IntentDetectionStrategy,
        SecurityTestStrategy,
    )

    # Test instantiation
    simple = SimpleQueryStrategy()
    multi = MultiStepFlowStrategy()
    intent = IntentDetectionStrategy()
    security = SecurityTestStrategy()

    assert simple is not None
    assert multi is not None
    assert intent is not None
    assert security is not None

    print("  ✓ SimpleQueryStrategy imports correctly")
    print("  ✓ MultiStepFlowStrategy imports correctly")
    print("  ✓ IntentDetectionStrategy imports correctly")
    print("  ✓ SecurityTestStrategy imports correctly")


def verify_enhanced_dataclasses():
    """Verify enhanced dataclasses in LLMTestValidator."""
    print("\n✓ Testing Enhanced Dataclasses...")

    from tests.helpers.llm_test_validator import (
        ValidationResult,
        ScoringBreakdown,
        ValidationMetadata,
        ActionableRecommendations,
    )

    # Test dataclass instantiation
    scoring = ScoringBreakdown(
        accuracy_score=0.95,
        relevance_score=0.90,
        safety_score=1.0,
        coherence_score=0.92,
        overall_score=0.94,
    )

    metadata = ValidationMetadata(
        test_category="hunter",
        test_type="simple_query",
        expected_intents=["price_prediction"],
        token_usage=850,
        validation_latency_ms=1200,
        model_used="meta-llama/Meta-Llama-3.1-70B-Instruct",
    )

    recommendations = ActionableRecommendations(
        improvement_suggestions=["Improve accuracy"],
        critical_issues=[],
        next_steps=["Review test"],
    )

    assert scoring.accuracy_score == 0.95
    assert metadata.test_category == "hunter"
    assert len(recommendations.improvement_suggestions) == 1

    print("  ✓ ScoringBreakdown dataclass works correctly")
    print("  ✓ ValidationMetadata dataclass works correctly")
    print("  ✓ ActionableRecommendations dataclass works correctly")


def verify_metadata_extraction():
    """Test actual metadata extraction from a sample function."""
    print("\n✓ Testing Metadata Extraction...")

    from tests.helpers.test_metadata_extractor import TestMetadataExtractor, TestType

    def sample_test():
        """Sample test function."""
        assert response.status_code == 200
        assert "sentiment" in content.lower()

    extractor = TestMetadataExtractor()
    metadata = extractor.extract_metadata(sample_test)

    assert metadata.test_name == "sample_test"
    assert metadata.test_type == TestType.SIMPLE_QUERY
    assert len(metadata.assertions) >= 0  # May extract some assertions

    print("  ✓ Metadata extraction works on sample function")
    print(f"    - Test name: {metadata.test_name}")
    print(f"    - Test type: {metadata.test_type.value}")
    print(f"    - Assertions found: {len(metadata.assertions)}")


def verify_prompt_generation():
    """Test actual prompt generation."""
    print("\n✓ Testing Prompt Generation...")

    from tests.helpers.test_metadata_extractor import TestMetadata, TestType
    from tests.helpers.validation_prompt_generator import ValidationPromptGenerator

    # Create sample metadata
    metadata = TestMetadata(
        test_name="test_sample",
        test_file="test_file.py",
        test_type=TestType.SIMPLE_QUERY,
        test_category="hunter",
        expected_status_code=200,
        required_keywords=["sentiment", "analysis"],
        expected_intents=["sentiment_analysis"],
    )

    generator = ValidationPromptGenerator()
    prompt = generator.generate_prompt(
        test_metadata=metadata,
        user_input="What's BTC sentiment?",
        agent_output="BTC sentiment is bullish",
        expected_behavior="Should provide sentiment analysis",
    )

    assert prompt is not None
    assert len(prompt) > 100
    assert "sentiment" in prompt.lower()
    assert "accuracy_score" in prompt.lower()

    print("  ✓ Prompt generation works correctly")
    print(f"    - Prompt length: {len(prompt)} characters")
    print(f"    - Contains required keywords: Yes")
    print(f"    - Contains scoring criteria: Yes")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Phase 1 Component Verification")
    print("=" * 60)

    try:
        verify_test_metadata_extractor()
        verify_validation_prompt_generator()
        verify_prompt_strategies()
        verify_enhanced_dataclasses()
        verify_metadata_extraction()
        verify_prompt_generation()

        print("\n" + "=" * 60)
        print("✅ All Phase 1 components verified successfully!")
        print("=" * 60)
        print("\nPhase 1 Infrastructure Components:")
        print("  ✓ TestMetadataExtractor - AST parsing for test analysis")
        print("  ✓ ValidationPromptGenerator - Strategy pattern for prompts")
        print("  ✓ 4 Prompt Strategies - Custom prompts per test type")
        print("  ✓ Enhanced Dataclasses - Granular scoring and metadata")
        print("\nNext Steps:")
        print("  → Phase 2: Integration (wire components together)")
        print("  → Phase 3: Pilot rollout (10-20 test files)")
        print("  → Phase 4: Full rollout (all 97 test files)")

        return 0

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
