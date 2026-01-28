"""
Unit Tests: Vault Intent Pattern Routing (P0 Fix)
==================================================

Tests that "best lending vaults" queries route to LendingHandler correctly.

P0 Fix Verification:
- BEFORE: "Best lending vaults" → GENERAL_CONVERSATION (incorrect)
- AFTER:  "Best lending vaults" → LENDING (correct)

This test suite validates the vault pattern fix implemented in intent_detector_v2.py.
"""

import pytest

from app.application.chat.services.intent_detector_v2 import (
    ChatIntentV2,
    IntentDetectorV2,
)


class TestVaultIntentPatterns:
    """Test vault-specific patterns route to LENDING intent."""

    @pytest.fixture
    def detector(self):
        """Create intent detector instance."""
        return IntentDetectorV2()

    @pytest.mark.parametrize("query", [
        # Primary P0 test case
        "Best lending vaults",

        # "best/top/highest" + "vaults"
        "best vaults",
        "top vaults",
        "highest vaults",

        # "best/top/highest" + "lending vaults"
        "best lending vaults",
        "top lending vaults",
        "highest lending vaults",

        # "best/top/highest" + "morpho vaults"
        "best morpho vaults",
        "top morpho vaults",
        "highest morpho vaults",

        # "show" + "vaults"
        "show best vaults",
        "show me best vaults",
        "show top vaults",

        # "compare" + "vaults"
        "compare vaults",
        "compare morpho vaults",

        # "vault" + "comparison/recommendations"
        "vault comparison",
        "vault recommendations",

        # "which vaults" + "have/offer"
        "which vaults have best apy",
        "which vaults offer highest yield",

        # "vaults" + "with" + "best/highest" + "apy/yield/returns"
        "vaults with best apy",
        "vaults with highest yield",
        "vault with highest apy",

        # "list/find" + "vaults"
        "list morpho vaults",
        "list vaults",
        "find best vaults",
        "find top vaults",

        # Case variations
        "BEST LENDING VAULTS",
        "Best Lending Vaults",
        "bEsT lEnDiNg VaUlTs",

        # With additional context
        "I want to see the best lending vaults",
        "Can you show me the best vaults?",
        "What are the top morpho vaults?",
    ])
    def test_vault_queries_route_to_lending(self, detector, query):
        """
        Test that vault-related queries route to LENDING intent.

        These queries should be handled by LendingHandler, which can:
        - Fetch Morpho vault data
        - Display vault APY comparisons
        - Provide vault recommendations
        """
        result = detector.detect(query, language="en")

        assert result.intent == ChatIntentV2.LENDING, (
            f"Query '{query}' should route to LENDING intent, "
            f"got {result.intent.value}"
        )
        assert result.handler == "lending_handler", (
            f"Query '{query}' should use lending_handler, "
            f"got {result.handler}"
        )
        assert result.confidence >= 0.85, (
            f"Confidence should be >= 0.85, got {result.confidence}"
        )

    @pytest.mark.parametrize("query,expected_intent", [
        # Should NOT match vault patterns
        ("vault of satoshi", ChatIntentV2.GENERAL_CONVERSATION),
        ("What is Bitcoin", ChatIntentV2.PROTOCOL_SEARCH),
        ("Bitcoin price", ChatIntentV2.HUNTER_PRICE_PREDICTION),

        # Rate comparison queries should go to MONEY_MARKET
        ("Best lending rates", ChatIntentV2.MONEY_MARKET),
        ("Compare lending rates", ChatIntentV2.MONEY_MARKET),
    ])
    def test_non_vault_queries_route_correctly(self, detector, query, expected_intent):
        """
        Test that non-vault queries don't get misrouted to LENDING.

        This validates that vault patterns don't create false positives.
        """
        result = detector.detect(query, language="en")

        assert result.intent == expected_intent, (
            f"Query '{query}' should route to {expected_intent.value}, "
            f"got {result.intent.value}"
        )

    def test_vault_pattern_metadata(self, detector):
        """
        Test that vault patterns include correct metadata.

        Metadata helps LendingHandler understand the query type.
        """
        result = detector.detect("best morpho vaults", language="en")

        assert result.intent == ChatIntentV2.LENDING
        assert result.metadata is not None
        assert result.metadata.get("pattern_type") == "vault_comparison"

    def test_existing_lending_patterns_still_work(self, detector):
        """
        Test that existing lending patterns continue to work.

        This ensures the vault pattern fix didn't break existing functionality.
        """
        test_cases = [
            "Where to lend USDC",
            "Earn yield on ETH",
            "Deposit 1000 USDC",
            "Lend my USDC",
            "Earn on morpho",
        ]

        for query in test_cases:
            result = detector.detect(query, language="en")
            assert result.intent == ChatIntentV2.LENDING, (
                f"Existing lending pattern '{query}' should still route to LENDING, "
                f"got {result.intent.value}"
            )
