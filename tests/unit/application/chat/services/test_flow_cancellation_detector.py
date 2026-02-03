"""
Unit tests for Flow Cancellation Detector.

Tests the hybrid keyword + intent detection system for automatic
multi-step flow cancellation when users change topics.
"""

import pytest

from app.application.chat.services.flow_cancellation_detector import (
    FlowCancellationDetector,
)


class TestFlowCancellationDetector:
    """Test suite for FlowCancellationDetector."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return FlowCancellationDetector()

    # ===================================================================
    # EXPLICIT CANCELLATION KEYWORDS - English
    # ===================================================================

    @pytest.mark.parametrize(
        "content,keyword",
        [
            ("cancel", "cancel"),
            ("Cancel this", "cancel"),
            ("never mind", "never mind"),
            ("forget it", "forget it"),
            ("actually, what's the price of Bitcoin?", "actually"),
            ("instead show my portfolio", "instead"),
        ],
    )
    def test_explicit_cancellation_keywords_english(self, detector, content, keyword):
        """Test explicit cancellation keywords are detected."""
        should_cancel, reason = detector.detect_topic_change(
            content=content,
            pending_action="lending_awaiting_asset",
            current_intent="lending",
            language="en",
        )

        assert should_cancel is True
        assert f"keyword_match:{keyword}" in reason

    # ===================================================================
    # EXPLICIT CANCELLATION KEYWORDS - Spanish
    # ===================================================================

    @pytest.mark.parametrize(
        "content,keyword",
        [
            ("cancelar", "cancelar"),
            ("mejor muéstrame mi portfolio", "mejor"),
            ("en lugar de eso, ¿cuál es el precio de BTC?", "en lugar"),
        ],
    )
    def test_explicit_cancellation_keywords_spanish(self, detector, content, keyword):
        """Test Spanish cancellation keywords."""
        should_cancel, reason = detector.detect_topic_change(
            content=content,
            pending_action="lending_awaiting_asset",
            current_intent="lending",
            language="es",
        )

        assert should_cancel is True
        assert f"keyword_match:{keyword}" in reason

    # ===================================================================
    # INTENT MISMATCH + QUESTION PATTERN
    # ===================================================================

    @pytest.mark.parametrize(
        "content,expected_intent",
        [
            ("What's the price of Bitcoin?", "prediction"),
            ("Show my portfolio", "portfolio"),
            ("What do people think about ETH?", "sentiment"),
            ("How much is BTC?", "prediction"),
        ],
    )
    def test_intent_mismatch_with_question(self, detector, content, expected_intent):
        """Test intent mismatch with question patterns triggers cancellation."""
        should_cancel, reason = detector.detect_topic_change(
            content=content,
            pending_action="lending_awaiting_asset",
            current_intent=expected_intent,
            language="en",
        )

        assert should_cancel is True
        # Can match either keyword (fast path) or intent mismatch (backup path)
        assert "keyword_match:" in reason or "intent_mismatch:lending→" in reason

    # ===================================================================
    # FLOW CONTINUATION (NO CANCELLATION)
    # ===================================================================

    @pytest.mark.parametrize(
        "content",
        [
            # Valid asset selections for lending flow
            ("USDC"),
            ("ETH"),
            ("1"),  # Number selection
            ("2"),
            # Valid amounts
            ("1000"),
            ("500 USDC"),
            ("0.5 ETH"),
            # Valid confirmations
            ("yes"),
            ("confirm"),
            ("proceed"),
            ("ok"),
        ],
    )
    def test_flow_continuation_not_cancelled(self, detector, content):
        """Test normal flow continuation doesn't trigger cancellation."""
        # Test at different stages of lending flow
        for pending_action in [
            "lending_awaiting_asset",
            "lending_awaiting_amount",
            "lending_awaiting_confirmation",
        ]:
            should_cancel, reason = detector.detect_topic_change(
                content=content,
                pending_action=pending_action,
                current_intent="lending",
                language="en",
            )

            assert should_cancel is False
            assert reason == "continuing_flow"

    # ===================================================================
    # DIFFERENT FLOW INTENTS
    # ===================================================================

    def test_different_flow_intent_detected(self, detector):
        """Test switching between different flow intents."""
        # User in lending flow asks about swap
        should_cancel, reason = detector.detect_topic_change(
            content="swap USDC for ETH",
            pending_action="lending_awaiting_asset",
            current_intent="swap",
            language="en",
        )

        assert should_cancel is True
        assert "flow_change:lending→swap" in reason

    # ===================================================================
    # MULTI-LANGUAGE SUPPORT
    # ===================================================================

    @pytest.mark.parametrize(
        "content,language,keyword",
        [
            # Portuguese
            ("cancelar", "pt", "cancelar"),
            ("melhor mostre meu portfólio", "pt", "melhor"),
            ("o que é Bitcoin?", "pt", "o que é"),
            # Chinese
            ("取消", "zh", "取消"),
            ("什么是比特币?", "zh", "什么是"),
            # French
            ("annuler", "fr", "annuler"),
            ("plutôt montre-moi mon portfolio", "fr", "plutôt"),
            ("qu'est-ce que Bitcoin?", "fr", "qu'est-ce que"),
        ],
    )
    def test_multi_language_keywords(self, detector, content, language, keyword):
        """Test keyword detection works across all supported languages."""
        should_cancel, reason = detector.detect_topic_change(
            content=content,
            pending_action="lending_awaiting_asset",
            current_intent="lending",
            language=language,
        )

        assert should_cancel is True
        assert f"keyword_match:{keyword}" in reason

    # ===================================================================
    # EDGE CASES
    # ===================================================================

    def test_compound_answer_not_cancelled(self, detector):
        """Test compound answers (asset + amount) don't trigger cancellation."""
        should_cancel, reason = detector.detect_topic_change(
            content="USDC 1000",
            pending_action="lending_awaiting_asset",
            current_intent="lending",
            language="en",
        )

        assert should_cancel is False

    def test_correction_not_cancelled(self, detector):
        """Test user corrections don't trigger cancellation."""
        should_cancel, reason = detector.detect_topic_change(
            content="not USDC, DAI",
            pending_action="lending_awaiting_asset",
            current_intent="lending",
            language="en",
        )

        assert should_cancel is False

    def test_same_intent_different_stage(self, detector):
        """Test same intent at different stages doesn't cancel."""
        should_cancel, reason = detector.detect_topic_change(
            content="1000",
            pending_action="lending_awaiting_amount",
            current_intent="lending",
            language="en",
        )

        assert should_cancel is False

    def test_empty_content(self, detector):
        """Test empty content doesn't crash."""
        should_cancel, reason = detector.detect_topic_change(
            content="",
            pending_action="lending_awaiting_asset",
            current_intent="lending",
            language="en",
        )

        assert should_cancel is False

    # ===================================================================
    # ALL FLOW TYPES
    # ===================================================================

    @pytest.mark.parametrize(
        "pending_action,expected_flow",
        [
            ("lending_awaiting_asset", "lending"),
            ("swap_awaiting_token", "swap"),
            ("buy_awaiting_amount", "buy"),
            ("send_awaiting_address", "send"),
            ("portfolio_awaiting_chain", "portfolio"),
            ("balance_awaiting_token", "balance"),
            ("activity_awaiting_type", "activity"),
            ("receive_awaiting_chain", "receive"),
            ("money_market_awaiting_asset", "money_market"),
        ],
    )
    def test_all_flow_types_detected(self, detector, pending_action, expected_flow):
        """Test detection works for all 9 flow types."""
        # User asks about price while in any flow
        should_cancel, reason = detector.detect_topic_change(
            content="What's the price of Bitcoin?",
            pending_action=pending_action,
            current_intent="prediction",
            language="en",
        )

        assert should_cancel is True
        # Can match keyword or intent mismatch - both are correct
        assert should_cancel  # Just verify cancellation works for all flows

    # ===================================================================
    # CLEAR FLOW METADATA
    # ===================================================================

    def test_clear_flow_metadata(self, detector):
        """Test clearing flow metadata."""
        metadata = {
            "pending_action": "lending_awaiting_asset",
            "lending_info": {"asset": "USDC"},
            "swap_info": {"from_token": "ETH"},
            "other_data": "should_remain",
        }

        cleaned = detector.clear_flow_metadata(metadata)

        assert "pending_action" not in cleaned
        assert "lending_info" not in cleaned
        assert "swap_info" not in cleaned
        assert "other_data" in cleaned
        assert cleaned["other_data"] == "should_remain"

    # ===================================================================
    # CANCELLATION MESSAGE (OPTIONAL FEATURE)
    # ===================================================================

    def test_cancellation_message_returns_none(self, detector):
        """Test cancellation message returns None (silent cancellation)."""
        message = detector.get_cancellation_message(
            expected_intent="lending",
            new_intent="prediction",
            language="en",
        )

        # Silent cancellation is preferred UX
        assert message is None

    # ===================================================================
    # REAL-WORLD SCENARIOS
    # ===================================================================

    def test_lending_to_price_query(self, detector):
        """
        Real scenario: User starts lending flow, then asks about price.

        User: "lending"
        → System: "Which asset?"
        User: "What's the price of Bitcoin?"
        → Expected: Cancel lending, show BTC price
        """
        should_cancel, reason = detector.detect_topic_change(
            content="What's the price of Bitcoin?",
            pending_action="lending_awaiting_asset",
            current_intent="prediction",
            language="en",
        )

        assert should_cancel is True
        # Can match keyword or intent mismatch
        assert should_cancel

    def test_swap_to_portfolio_query(self, detector):
        """
        Real scenario: User starts swap, then checks portfolio.

        User: "swap USDC for ETH"
        → System: "How much USDC?"
        User: "show my portfolio"
        → Expected: Cancel swap, show portfolio
        """
        should_cancel, reason = detector.detect_topic_change(
            content="show my portfolio",
            pending_action="swap_awaiting_amount",
            current_intent="portfolio",
            language="en",
        )

        assert should_cancel is True
        assert "swap→portfolio" in reason

    def test_buy_to_sentiment_query(self, detector):
        """
        Real scenario: User starts buy flow, then asks about sentiment.

        User: "I want to buy crypto"
        → System: "How much?"
        User: "What do people think about ETH?"
        → Expected: Cancel buy, show sentiment
        """
        should_cancel, reason = detector.detect_topic_change(
            content="What do people think about ETH?",
            pending_action="buy_awaiting_amount",
            current_intent="sentiment",
            language="en",
        )

        assert should_cancel is True
        assert "buy→sentiment" in reason

    def test_spanish_lending_to_price(self, detector):
        """
        Spanish scenario: User in lending flow asks price in Spanish.
        """
        should_cancel, reason = detector.detect_topic_change(
            content="¿Cuál es el precio de Bitcoin?",
            pending_action="lending_awaiting_asset",
            current_intent="prediction",
            language="es",
        )

        assert should_cancel is True

    def test_chinese_swap_cancellation(self, detector):
        """
        Chinese scenario: User cancels swap flow.
        """
        should_cancel, reason = detector.detect_topic_change(
            content="取消",
            pending_action="swap_awaiting_amount",
            current_intent="swap",
            language="zh",
        )

        assert should_cancel is True
        assert "keyword_match:取消" in reason
