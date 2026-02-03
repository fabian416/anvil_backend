#!/usr/bin/env python3
"""
Comprehensive test for vault pattern routing.

Tests all variations and edge cases to ensure robust routing to LendingHandler.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from app.application.chat.services.intent_detector_v2 import (
    IntentDetectorV2,
    ChatIntentV2,
)


def test_comprehensive_vault_patterns():
    """Test comprehensive vault pattern variations."""
    detector = IntentDetectorV2()

    # Comprehensive test cases covering all variations
    test_cases = [
        # Primary P0 test case
        ("Best lending vaults", ChatIntentV2.LENDING, True),
        # "best/top/highest" + "vaults"
        ("best vaults", ChatIntentV2.LENDING, True),
        ("top vaults", ChatIntentV2.LENDING, True),
        ("highest vaults", ChatIntentV2.LENDING, True),
        # "best/top/highest" + "lending vaults"
        ("best lending vaults", ChatIntentV2.LENDING, True),
        ("top lending vaults", ChatIntentV2.LENDING, True),
        ("highest lending vaults", ChatIntentV2.LENDING, True),
        # "best/top/highest" + "morpho vaults"
        ("best morpho vaults", ChatIntentV2.LENDING, True),
        ("top morpho vaults", ChatIntentV2.LENDING, True),
        ("highest morpho vaults", ChatIntentV2.LENDING, True),
        # "show" + "vaults"
        ("show best vaults", ChatIntentV2.LENDING, True),
        ("show me best vaults", ChatIntentV2.LENDING, True),
        ("show top vaults", ChatIntentV2.LENDING, True),
        ("show me top vaults", ChatIntentV2.LENDING, True),
        # "compare" + "vaults"
        ("compare vaults", ChatIntentV2.LENDING, True),
        ("compare morpho vaults", ChatIntentV2.LENDING, True),
        # "vault" + "comparison/recommendations"
        ("vault comparison", ChatIntentV2.LENDING, True),
        ("vault recommendations", ChatIntentV2.LENDING, True),
        # "which vaults" + "have/offer"
        ("which vaults have best apy", ChatIntentV2.LENDING, True),
        ("which vaults offer highest yield", ChatIntentV2.LENDING, True),
        ("which vaults have highest returns", ChatIntentV2.LENDING, True),
        # "vaults" + "with" + "best/highest" + "apy/yield/returns"
        ("vaults with best apy", ChatIntentV2.LENDING, True),
        ("vaults with highest yield", ChatIntentV2.LENDING, True),
        ("vaults with best returns", ChatIntentV2.LENDING, True),
        ("vault with highest apy", ChatIntentV2.LENDING, True),
        # "list/find" + "vaults"
        ("list morpho vaults", ChatIntentV2.LENDING, True),
        ("list vaults", ChatIntentV2.LENDING, True),
        ("find best vaults", ChatIntentV2.LENDING, True),
        ("find top vaults", ChatIntentV2.LENDING, True),
        # Case variations
        ("BEST LENDING VAULTS", ChatIntentV2.LENDING, True),
        ("Best Lending Vaults", ChatIntentV2.LENDING, True),
        ("bEsT lEnDiNg VaUlTs", ChatIntentV2.LENDING, True),
        # With additional context
        ("I want to see the best lending vaults", ChatIntentV2.LENDING, True),
        ("Can you show me the best vaults?", ChatIntentV2.LENDING, True),
        ("What are the top morpho vaults?", ChatIntentV2.LENDING, True),
        # Should NOT match (negative tests)
        (
            "vault of satoshi",
            ChatIntentV2.GENERAL_CONVERSATION,
            False,
        ),  # Context mismatch
        ("What is Bitcoin", ChatIntentV2.PROTOCOL_SEARCH, False),  # Different intent
        ("Bitcoin price", ChatIntentV2.HUNTER_PRICE_PREDICTION, False),  # Price query
    ]

    print("=" * 100)
    print("COMPREHENSIVE VAULT PATTERN ROUTING TEST")
    print("=" * 100)
    print()

    passed = 0
    failed = 0
    critical_failures = []

    for query, expected_intent, is_vault_query in test_cases:
        result = detector.detect(query, language="en")

        success = result.intent == expected_intent

        if success:
            status = "✓ PASS"
            passed += 1
            color = "\033[92m"  # Green
        else:
            status = "✗ FAIL"
            failed += 1
            color = "\033[91m"  # Red

            # Track critical failures (vault queries that didn't route to LENDING)
            if is_vault_query and result.intent != ChatIntentV2.LENDING:
                critical_failures.append(query)

        reset = "\033[0m"

        print(f"{color}{status}{reset} Query: '{query}'")
        print(f"  Expected: {expected_intent.value}")
        print(f"  Got:      {result.intent.value}")

        if not success:
            print(f"  Handler:  {result.handler}")
            print(f"  Confidence: {result.confidence}")

        print()

    print("=" * 100)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")

    if critical_failures:
        print()
        print("CRITICAL FAILURES (vault queries not routing to LENDING):")
        for query in critical_failures:
            print(f"  - '{query}'")

    print("=" * 100)

    return failed == 0


if __name__ == "__main__":
    success = test_comprehensive_vault_patterns()
    sys.exit(0 if success else 1)
