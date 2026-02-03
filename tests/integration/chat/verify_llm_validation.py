#!/usr/bin/env python3
"""
Quick verification script for LLM validation system.

This script verifies that:
1. DeepInfra API key is configured correctly
2. LLM validation can be enabled
3. All components initialize properly
4. Basic API call to DeepInfra works

Usage:
    python tests/integration/chat/verify_llm_validation.py
"""

import os
import sys
import asyncio

# Add project to path
sys.path.insert(0, "/home/ubuntu/anvil_backend")

# Configure environment
os.environ["DEEPINFRA_API_KEY"] = "ur1aITAnOmIXK0LTT1zCBDGnk3elzsVA"
os.environ["ENABLE_LLM_VALIDATION"] = "true"
os.environ["ENABLE_LOG_ANALYSIS"] = "true"

from tests.helpers.llm_test_validator import LLMTestValidator, ValidationVerdict
from tests.helpers.log_analyzer import LogAnalyzer
from tests.helpers.enhanced_csv_writer import EnhancedCSVWriter


async def verify_system():
    """Verify LLM validation system."""
    print("=" * 70)
    print("LLM Validation System - Verification")
    print("=" * 70)

    # Step 1: Check configuration
    print("\n1. Configuration Check:")
    print(
        f"   DEEPINFRA_API_KEY: {'✅ SET' if os.getenv('DEEPINFRA_API_KEY') else '❌ NOT SET'}"
    )
    print(f"   ENABLE_LLM_VALIDATION: {os.getenv('ENABLE_LLM_VALIDATION')}")
    print(f"   ENABLE_LOG_ANALYSIS: {os.getenv('ENABLE_LOG_ANALYSIS')}")

    # Step 2: Initialize components
    print("\n2. Component Initialization:")
    validator = LLMTestValidator()
    analyzer = LogAnalyzer()
    writer = EnhancedCSVWriter("/tmp/verify_test.csv")

    print(f"   LLM Validator: {'✅ ENABLED' if validator.enabled else '❌ DISABLED'}")
    print(f"   Log Analyzer: {'✅ ENABLED' if analyzer.enabled else '❌ DISABLED'}")
    print(f"   CSV Writer: ✅ READY")

    if not validator.enabled:
        print("\n❌ FAILED: LLM validator not enabled")
        print("   Check DEEPINFRA_API_KEY environment variable")
        return False

    # Step 3: Test simple validation
    print("\n3. Testing Simple Validation:")
    print("   Sending test request to DeepInfra...")

    try:
        result = await validator.validate_single_response(
            test_name="verification_test",
            user_input="Hello",
            agent_output="Hello! How can I help you today?",
            expected_behavior="Should greet the user appropriately",
        )

        print(f"   ✅ API Response Received!")
        print(f"   Verdict: {result.verdict.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Tokens Used: {result.tokens_used}")
        print(f"   Time: {result.validation_time_ms}ms")
        print(f"   Cost: ${result.tokens_used / 1_000_000 * 0.08:.6f}")

        if result.verdict == ValidationVerdict.SKIP:
            print("\n❌ FAILED: Validation was skipped")
            return False

    except Exception as e:
        print(f"\n❌ FAILED: API error")
        print(f"   Error: {str(e)}")
        return False

    # Step 4: Test CSV writing
    print("\n4. Testing CSV Output:")
    from tests.helpers.enhanced_csv_writer import EnhancedTestResult

    test_result = EnhancedTestResult(
        test_type="verification_test",
        device="chrome",
        is_multi_step=False,
        inputs=["Hello"],
        outputs=["Hello! How can I help you today?"],
        test_pass=True,
        llm_verdict=result.verdict.value,
        llm_confidence=result.confidence,
    )
    writer.write_single_result(test_result)
    print(f"   ✅ CSV written successfully")

    # Verify CSV format
    import csv

    with open("/tmp/verify_test.csv", "r") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if "llm_verdict" in headers and "llm_confidence" in headers:
            print(f"   ✅ AI columns present in CSV")
        else:
            print(f"   ❌ AI columns missing from CSV")
            return False

    # Success!
    print("\n" + "=" * 70)
    print("✅ VERIFICATION SUCCESSFUL!")
    print("=" * 70)
    print("\nLLM Validation System is properly configured and working!")
    print("\nNext steps:")
    print("  1. Run system tests:")
    print("     pytest tests/integration/chat/test_llm_validation_system.py -v -s")
    print("")
    print("  2. Run example tests:")
    print("     pytest tests/integration/chat/test_ai_validation_example.py -v -s")
    print("")
    print("  3. Enable for all tests:")
    print("     source .env.llm_validation")
    print("     pytest tests/integration/chat/ -v")

    return True


if __name__ == "__main__":
    success = asyncio.run(verify_system())
    sys.exit(0 if success else 1)
