#!/usr/bin/env python3
"""
Quick demo of CSV validation with LLM.

Validates the first 3 tests from the guest CSV to demonstrate the system.
"""

import asyncio
import csv
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, "/home/ubuntu/anvil_backend")

# Configure environment
os.environ["DEEPINFRA_API_KEY"] = "ur1aITAnOmIXK0LTT1zCBDGnk3elzsVA"
os.environ["ENABLE_LLM_VALIDATION"] = "true"

from tests.helpers.llm_test_validator import LLMTestValidator


async def demo_validation():
    """Demo CSV validation."""
    print("=" * 70)
    print("CSV Validation Demo - First 3 Tests")
    print("=" * 70)

    # Read first few tests from guest CSV
    csv_file = Path(
        "/home/ubuntu/anvil_backend/tests/output/guest/week1_8_input_output.csv"
    )

    with csv_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)[:3]  # First 3 tests

    print(f"\nLoaded {len(rows)} tests for validation\n")

    # Initialize validator
    validator = LLMTestValidator()
    print(f"LLM Validator: {'✅ ENABLED' if validator.enabled else '❌ DISABLED'}\n")

    if not validator.enabled:
        print("❌ LLM validation not enabled!")
        return

    # Validate each test
    total_tokens = 0
    results = []

    for i, row in enumerate(rows, 1):
        test_type = row["Type"]
        input_1 = row.get("input 1", "")
        output_1 = row.get("output 1", "")

        print(f"\n{'=' * 70}")
        print(f"Test {i}/{len(rows)}: {test_type[:60]}...")
        print(f"{'=' * 70}")
        print(f"\nInput:  {input_1[:80]}...")
        print(f"Output: {output_1[:80]}...")

        # Determine expected behavior
        if "xss" in test_type.lower() or "sql" in test_type.lower():
            expected = (
                "Should safely handle malicious input without executing the injection"
            )
        elif "price" in test_type.lower() or "bitcoin" in test_type.lower():
            expected = "Should provide accurate cryptocurrency price information"
        else:
            expected = "Should provide appropriate response"

        print(f"\nExpected: {expected}")
        print(f"\nValidating with AI...")

        # Validate
        try:
            validation = await validator.validate_single_response(
                test_name=test_type,
                user_input=input_1,
                agent_output=output_1,
                expected_behavior=expected,
            )

            print(f"\n🤖 AI Validation Results:")
            print(f"   Verdict: {validation.verdict.value}")
            print(f"   Confidence: {validation.confidence:.2f}")
            print(f"   Reasoning: {validation.reasoning[:200]}...")
            print(f"   Tokens: {validation.tokens_used}")
            print(f"   Time: {validation.validation_time_ms}ms")
            print(f"   Cost: ${validation.tokens_used / 1_000_000 * 0.08:.6f}")

            total_tokens += validation.tokens_used
            results.append({
                "test": test_type,
                "verdict": validation.verdict.value,
                "confidence": validation.confidence,
                "tokens": validation.tokens_used,
            })

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

    # Summary
    print(f"\n\n{'=' * 70}")
    print("DEMO SUMMARY")
    print(f"{'=' * 70}")
    print(f"\nTests validated: {len(results)}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Total cost: ${total_tokens / 1_000_000 * 0.08:.6f}")
    print(f"\nResults:")
    for result in results:
        print(
            f"  • {result['verdict']}: {result['test'][:50]} (confidence: {result['confidence']:.2f})"
        )

    print(f"\n{'=' * 70}")
    print("Next Steps:")
    print(f"{'=' * 70}")
    print("\nTo validate all CSVs, run:")
    print("  # Sample (every 20th test): ~$0.02")
    print(
        "  python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 20"
    )
    print("")
    print("  # Full validation (562 tests): ~$0.36")
    print("  python tests/integration/chat/validate_existing_csvs.py --mode full")
    print("")


if __name__ == "__main__":
    asyncio.run(demo_validation())
