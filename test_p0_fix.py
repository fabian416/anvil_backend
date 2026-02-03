#!/usr/bin/env python3
"""
P0 Fix Verification: Test the exact user query from the problem statement.

BEFORE FIX:
  Query: "Best lending vaults"
  Intent: GENERAL_CONVERSATION (❌ incorrect)

AFTER FIX:
  Query: "Best lending vaults"
  Intent: LENDING (✓ correct, routes to LendingHandler)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from app.application.chat.services.intent_detector_v2 import IntentDetectorV2, ChatIntentV2

def test_p0_fix():
    """Test the exact user query from the problem statement."""
    detector = IntentDetectorV2()

    # The exact query from the problem statement
    query = "Best lending vaults"

    print("=" * 80)
    print("P0 FIX VERIFICATION")
    print("=" * 80)
    print()
    print(f"User Query: '{query}'")
    print()

    result = detector.detect(query, language="en")

    print(f"Intent:     {result.intent.value}")
    print(f"Handler:    {result.handler}")
    print(f"Confidence: {result.confidence}")

    if result.metadata:
        print(f"Metadata:   {result.metadata}")

    print()
    print("=" * 80)

    if result.intent == ChatIntentV2.LENDING and result.handler == "lending_handler":
        print("✓ P0 FIX VERIFIED: Query routes to LendingHandler correctly!")
        print("=" * 80)
        return True
    else:
        print("✗ P0 FIX FAILED: Query does NOT route to LendingHandler")
        print(f"  Expected: LENDING intent with lending_handler")
        print(f"  Got:      {result.intent.value} intent with {result.handler}")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_p0_fix()
    sys.exit(0 if success else 1)
