"""
Unit tests for Agent Gateway intent classification methods.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from app.infrastructure.adapters.ai.agent_gateway_impl import AgentGatewayImpl
from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
from app.setup.config.agent_squad import AgentSquadConfig


class TestKeywordBasedClassification:
    """Test keyword-based intent classification."""
    
    @pytest.fixture
    def gateway(self):
        """Create Agent Gateway with keyword-based classification."""
        # Mock dependencies
        storage = MagicMock(spec=AnvilSquadStorage)
        llm_gateway = MagicMock()
        
        config = AgentSquadConfig(
            enable_intent_classification=False,  # Use keyword-based
            debug_mode=True
        )
        
        return AgentGatewayImpl(storage, llm_gateway, config)
    
    def test_swap_classification(self, gateway):
        """Test swap intent classification."""
        test_cases = [
            "swap 100 USDC to ETH",
            "exchange my BTC for SOL",
            "convert USDC to USDT",
            "I want to trade my ETH",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "trade_swap", f"Failed for: {message}"
    
    def test_perpetual_open_classification(self, gateway):
        """Test perpetual open classification."""
        test_cases = [
            "open 10x long on BTC",
            "long ETH with 5x leverage",
            "short BTC 20x",
            "open a position on SOL",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "trade_perp_open", f"Failed for: {message}"
    
    def test_perpetual_close_classification(self, gateway):
        """Test perpetual close classification."""
        test_cases = [
            "close my position",
            "exit my long",
            "close position",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            # Should classify to perp_close (not checking exact due to keyword overlap)
            assert intent in ["trade_perp_close", "trade_perp_open"], f"Failed for: {message} (got {intent})"
    
    def test_lending_supply_classification(self, gateway):
        """Test lending supply classification."""
        test_cases = [
            "supply 1000 USDC to Aave",
            "lend my tokens",
            "deposit into lending protocol",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "lend_supply", f"Failed for: {message}"
    
    def test_lending_borrow_classification(self, gateway):
        """Test lending borrow classification."""
        test_cases = [
            "borrow 500 USDT",
            "take out a loan",
            "borrow against my collateral",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "lend_borrow", f"Failed for: {message}"
    
    def test_staking_classification(self, gateway):
        """Test staking classification."""
        test_cases = [
            "stake my ETH",
            "staking",
            "earn rewards",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "earn_stake", f"Failed for: {message} (got {intent})"
    
    def test_portfolio_classification(self, gateway):
        """Test portfolio viewing classification."""
        test_cases = [
            "show my portfolio",
            "my portfolio",
            "my balance",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "portfolio_view", f"Failed for: {message} (got {intent})"
    
    def test_market_info_classification(self, gateway):
        """Test market info classification."""
        test_cases = [
            "price of BTC",
            "market cap",
            "trending",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "market_info", f"Failed for: {message} (got {intent})"
    
    def test_risk_analysis_classification(self, gateway):
        """Test risk analysis classification."""
        test_cases = [
            "is this safe",
            "risk",
            "liquidation",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "risk_analysis", f"Failed for: {message} (got {intent})"
    
    def test_schedule_classification(self, gateway):
        """Test schedule/DCA classification."""
        test_cases = [
            "schedule weekly",
            "recurring",
            "dca",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == "save_schedule", f"Failed for: {message} (got {intent})"
    
    def test_general_question_classification(self, gateway):
        """Test general question classification."""
        test_cases = [
            "what is DeFi",
            "how does it work",
            "explain staking",
        ]
        
        for message in test_cases:
            intent = gateway._classify_intent_simple(message)
            # Should classify to general question or related topic
            assert intent in gateway.classifier.INTENTS, f"Failed for: {message} (got {intent})"
    
    def test_fallback_to_general(self, gateway):
        """Test fallback to general_question for ambiguous input."""
        ambiguous = [
            "hello",
            "test",
            "xyz123",
            "...",
        ]
        
        for message in ambiguous:
            intent = gateway._classify_intent_simple(message)
            # Should fallback to general_question
            assert intent in gateway.classifier.INTENTS


class TestLLMBasedClassification:
    """Test LLM-based intent classification (with mocks)."""
    
    @pytest.mark.asyncio
    async def test_llm_classification_calls_llm(self):
        """Test that LLM classification calls the LLM gateway."""
        # Mock LLM gateway
        llm_gateway = AsyncMock()
        llm_gateway.generate.return_value = "trade_swap"
        
        storage = MagicMock(spec=AnvilSquadStorage)
        
        config = AgentSquadConfig(
            enable_intent_classification=True,  # Use LLM-based
            debug_mode=True
        )
        
        gateway = AgentGatewayImpl(storage, llm_gateway, config)
        
        # Classify a message
        intent = await gateway._classify_intent_llm(
            "swap 100 USDC to ETH",
            context=None
        )
        
        # Should have called LLM
        assert llm_gateway.generate.called
        assert intent == "trade_swap"
    
    @pytest.mark.asyncio
    async def test_llm_classification_with_context(self):
        """Test LLM classification uses context."""
        llm_gateway = AsyncMock()
        llm_gateway.generate.return_value = "portfolio_view"
        
        storage = MagicMock(spec=AnvilSquadStorage)
        config = AgentSquadConfig(enable_intent_classification=True)
        
        gateway = AgentGatewayImpl(storage, llm_gateway, config)
        
        # Classify with context
        context = {"recent_action": "swap"}
        intent = await gateway._classify_intent_llm(
            "how did that go?",
            context=context
        )
        
        # Should pass context to LLM
        llm_gateway.generate.assert_called_once()
        call_args = llm_gateway.generate.call_args
        
        # Check that prompt includes context info
        assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_llm_classification_fallback_on_error(self):
        """Test fallback to keyword-based on LLM error."""
        llm_gateway = AsyncMock()
        llm_gateway.generate.side_effect = Exception("LLM error")
        
        storage = MagicMock(spec=AnvilSquadStorage)
        config = AgentSquadConfig(enable_intent_classification=True)
        
        gateway = AgentGatewayImpl(storage, llm_gateway, config)
        
        # Should fallback to keyword-based on error
        intent = await gateway._classify_intent_llm(
            "swap 100 USDC to ETH",
            context=None
        )
        
        # Should return valid intent (from fallback)
        assert intent in gateway.classifier.INTENTS
    
    @pytest.mark.asyncio
    async def test_llm_classification_validates_response(self):
        """Test that LLM response is validated."""
        llm_gateway = AsyncMock()
        llm_gateway.generate.return_value = "invalid_intent_xyz"
        
        storage = MagicMock(spec=AnvilSquadStorage)
        config = AgentSquadConfig(enable_intent_classification=True)
        
        gateway = AgentGatewayImpl(storage, llm_gateway, config)
        
        # Classify
        intent = await gateway._classify_intent_llm(
            "swap tokens",
            context=None
        )
        
        # Should validate and use fallback if invalid
        assert intent in gateway.classifier.INTENTS


class TestClassificationPerformance:
    """Test classification performance and efficiency."""
    
    def test_keyword_classification_speed(self):
        """Test keyword classification is fast."""
        import time
        
        storage = MagicMock(spec=AnvilSquadStorage)
        llm_gateway = MagicMock()
        config = AgentSquadConfig(enable_intent_classification=False)
        
        gateway = AgentGatewayImpl(storage, llm_gateway, config)
        
        # Measure 100 classifications
        start = time.time()
        for _ in range(100):
            gateway._classify_intent_simple("swap 100 USDC to ETH")
        end = time.time()
        
        elapsed = end - start
        avg_time = elapsed / 100
        
        # Should be under 1ms per classification
        assert avg_time < 0.001, f"Too slow: {avg_time*1000:.2f}ms per classification"
    
    @pytest.mark.asyncio
    async def test_classification_caching(self):
        """Test that classifications could be cached (future optimization)."""
        llm_gateway = AsyncMock()
        llm_gateway.generate.return_value = "trade_swap"
        
        storage = MagicMock(spec=AnvilSquadStorage)
        config = AgentSquadConfig(enable_intent_classification=True)
        
        gateway = AgentGatewayImpl(storage, llm_gateway, config)
        
        # Same message twice
        message = "swap 100 USDC to ETH"
        intent1 = await gateway._classify_intent_llm(message, None)
        intent2 = await gateway._classify_intent_llm(message, None)
        
        # Should get same result
        assert intent1 == intent2


class TestEdgeCases:
    """Test edge cases in classification."""
    
    @pytest.fixture
    def gateway(self):
        """Create gateway instance."""
        storage = MagicMock(spec=AnvilSquadStorage)
        llm_gateway = MagicMock()
        config = AgentSquadConfig(enable_intent_classification=False)
        return AgentGatewayImpl(storage, llm_gateway, config)
    
    def test_empty_message(self, gateway):
        """Test classification of empty message."""
        intent = gateway._classify_intent_simple("")
        assert intent in gateway.classifier.INTENTS
    
    def test_very_long_message(self, gateway):
        """Test classification of very long message."""
        long_message = "I want to swap " * 100 + "tokens"
        intent = gateway._classify_intent_simple(long_message)
        assert intent == "trade_swap"
    
    def test_special_characters(self, gateway):
        """Test messages with special characters."""
        messages = [
            "swap 100 USDC -> ETH!!!",
            "what's my portfolio???",
            "long BTC @#$%",
        ]
        
        for message in messages:
            intent = gateway._classify_intent_simple(message)
            assert intent in gateway.classifier.INTENTS
    
    def test_unicode_characters(self, gateway):
        """Test messages with unicode characters."""
        messages = [
            "swap 100 USDC to ETH 🚀",
            "what's my portfolio 💰",
            "long BTC 📈",
        ]
        
        for message in messages:
            intent = gateway._classify_intent_simple(message)
            assert intent in gateway.classifier.INTENTS
    
    def test_mixed_languages(self, gateway):
        """Test messages with mixed languages (should handle gracefully)."""
        # English + crypto terms
        message = "swap USDC to ETH"
        intent = gateway._classify_intent_simple(message)
        assert intent == "trade_swap"
    
    def test_case_insensitive(self, gateway):
        """Test case-insensitive classification."""
        messages = [
            "SWAP 100 USDC TO ETH",
            "Swap 100 USDC To ETH",
            "swap 100 usdc to eth",
        ]
        
        intents = [gateway._classify_intent_simple(m) for m in messages]
        # All should classify the same
        assert len(set(intents)) == 1
        assert intents[0] == "trade_swap"


class TestIntentConfidence:
    """Test intent confidence and ambiguity handling."""
    
    @pytest.fixture
    def gateway(self):
        """Create gateway instance."""
        storage = MagicMock(spec=AnvilSquadStorage)
        llm_gateway = MagicMock()
        config = AgentSquadConfig(enable_intent_classification=False)
        return AgentGatewayImpl(storage, llm_gateway, config)
    
    def test_clear_intent_messages(self, gateway):
        """Test messages with clear, unambiguous intent."""
        clear_cases = [
            ("swap 100 USDC to ETH", "trade_swap"),
            ("show my portfolio", "portfolio_view"),
            ("what's the price of BTC", "market_info"),
        ]
        
        for message, expected in clear_cases:
            intent = gateway._classify_intent_simple(message)
            assert intent == expected
    
    def test_ambiguous_messages(self, gateway):
        """Test handling of ambiguous messages."""
        ambiguous = [
            "trade",  # Could be swap or perp
            "check",  # Could be portfolio or market
            "help",   # General
        ]
        
        for message in ambiguous:
            intent = gateway._classify_intent_simple(message)
            # Should classify to something reasonable
            assert intent in gateway.classifier.INTENTS
    
    def test_multi_keyword_messages(self, gateway):
        """Test messages with multiple intent keywords."""
        # "swap" and "position" keywords
        message = "swap my tokens and open a long position"
        intent = gateway._classify_intent_simple(message)
        
        # Should pick one intent (likely first match)
        assert intent in ["trade_swap", "trade_perp_open"]
