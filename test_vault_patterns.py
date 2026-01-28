#!/usr/bin/env python3
"""
Test script to verify vault pattern routing to LENDING intent.

P0 Fix Verification: "Best lending vaults" should route to LendingHandler.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from app.application.chat.services.intent_detector_v2 import IntentDetectorV2, ChatIntentV2

def test_vault_patterns():
    """Test that vault queries route to LENDING intent."""
    detector = IntentDetectorV2()

    test_cases = [
        # English vault patterns
        ("Best lending vaults", ChatIntentV2.LENDING, "best lending vaults"),
        ("Top Morpho vaults", ChatIntentV2.LENDING, "top morpho vaults"),
        ("Show me best vaults", ChatIntentV2.LENDING, "show me best vaults"),
        ("Compare vaults", ChatIntentV2.LENDING, "compare vaults"),
        ("Which vaults have highest APY", ChatIntentV2.LENDING, "which vaults have highest APY"),
        ("Best vaults", ChatIntentV2.LENDING, "best vaults"),
        ("Highest yield vaults", ChatIntentV2.LENDING, "highest yield vaults"),
        ("Vault comparison", ChatIntentV2.LENDING, "vault comparison"),
        ("List Morpho vaults", ChatIntentV2.LENDING, "list morpho vaults"),
        ("Find best vaults", ChatIntentV2.LENDING, "find best vaults"),

        # Existing lending patterns (should still work)
        ("Best lending rates", ChatIntentV2.MONEY_MARKET, "best lending rates (rate comparison)"),
        ("Where to lend USDC", ChatIntentV2.LENDING, "where to lend USDC"),
        ("Earn yield on ETH", ChatIntentV2.LENDING, "earn yield on ETH"),
        ("Deposit 1000 USDC", ChatIntentV2.LENDING, "deposit 1000 USDC"),

        # Should NOT match vault patterns (should fall through to general)
        ("What is Bitcoin", ChatIntentV2.PROTOCOL_SEARCH, "token info query"),
        ("Bitcoin price", ChatIntentV2.HUNTER_PRICE_PREDICTION, "price query"),
    ]

    print("=" * 80)
    print("VAULT PATTERN ROUTING TEST")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for query, expected_intent, description in test_cases:
        result = detector.detect(query, language="en")

        if result.intent == expected_intent:
            status = "✓ PASS"
            passed += 1
            color = "\033[92m"  # Green
        else:
            status = "✗ FAIL"
            failed += 1
            color = "\033[91m"  # Red

        reset = "\033[0m"

        print(f"{color}{status}{reset} Query: '{query}'")
        print(f"  Expected: {expected_intent.value}")
        print(f"  Got:      {result.intent.value}")
        print(f"  Handler:  {result.handler}")
        print(f"  Confidence: {result.confidence}")
        if result.metadata:
            print(f"  Metadata: {result.metadata}")
        print(f"  Description: {description}")
        print()

    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return failed == 0

if __name__ == "__main__":
    success = test_vault_patterns()
    sys.exit(0 if success else 1)
