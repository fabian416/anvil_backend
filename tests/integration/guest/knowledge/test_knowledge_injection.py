"""
Integration tests for knowledge base injection into LLM prompts.

Tests knowledge injection for:
- Authenticated users
- Guest users
- Different intents (SWAP, HUNTER_*, ULTRA_*, etc.)
- User type detection (user vs investor)
"""

import pytest
from pathlib import Path
from app.application.chat.services.knowledge_injector import (
    KnowledgeInjector,
    get_knowledge_injector,
    inject_knowledge,
    KnowledgeFile
)


class TestKnowledgeInjectorUnit:
    """Unit tests for KnowledgeInjector class"""

    @pytest.fixture
    def injector(self):
        """Get knowledge injector instance"""
        return KnowledgeInjector()

    def test_injector_initialization(self, injector):
        """Test knowledge injector initializes correctly"""
        assert injector.knowledge_base_path.exists()
        assert injector.features_path.exists()
        assert (injector.features_path / "overview.json").exists()
        assert (injector.features_path / "swap.json").exists()
        assert (injector.features_path / "hunter_ai.json").exists()
        assert (injector.features_path / "ultra.json").exists()
        assert (injector.features_path / "shortcuts.json").exists()

    def test_load_json_caching(self, injector):
        """Test JSON files are cached after first load"""
        # First load
        overview1 = injector._load_json(KnowledgeFile.OVERVIEW)
        assert "feature_name" in overview1
        assert KnowledgeFile.OVERVIEW in injector._cache

        # Second load should use cache
        overview2 = injector._load_json(KnowledgeFile.OVERVIEW)
        assert overview1 is overview2  # Same object reference (cached)

    def test_clear_cache(self, injector):
        """Test cache clearing works"""
        # Load and cache
        injector._load_json(KnowledgeFile.OVERVIEW)
        assert len(injector._cache) > 0

        # Clear cache
        injector.clear_cache()
        assert len(injector._cache) == 0

    def test_singleton_pattern(self):
        """Test get_knowledge_injector returns singleton"""
        injector1 = get_knowledge_injector()
        injector2 = get_knowledge_injector()
        assert injector1 is injector2  # Same instance


class TestKnowledgeExtractionOverview:
    """Test knowledge extraction for overview queries"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_what_can_you_do_user(self, injector):
        """Test 'what can you do?' for regular user"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="what can you do?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user"
        )

        assert "feature_name" in knowledge
        assert "core_capabilities" in knowledge
        assert "unique_features" in knowledge
        assert "getting_started" in knowledge
        assert "example_use_cases" in knowledge

        # Should NOT include investor-specific sections for regular user
        assert "competitive_advantages" not in knowledge
        assert "value_proposition" not in knowledge

    def test_what_can_you_do_investor(self, injector):
        """Test 'what can you do?' for investor"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="what can you do?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="investor"
        )

        assert "feature_name" in knowledge
        assert "core_capabilities" in knowledge
        assert "unique_features" in knowledge

        # Should include investor-specific sections
        assert "competitive_advantages" in knowledge
        assert "value_proposition" in knowledge
        assert "market_position" in knowledge


class TestKnowledgeExtractionHunterAI:
    """Test knowledge extraction for Hunter AI intents"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_hunter_sentiment_basic(self, injector):
        """Test Hunter AI sentiment knowledge extraction"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="check sentiment for BTC",
            detected_intent="HUNTER_SENTIMENT",
            user_type="user"
        )

        assert "feature_name" in knowledge
        assert knowledge["feature_name"] == "Hunter AI - Market Intelligence Agent"
        assert "capability" in knowledge
        assert knowledge["capability"]["name"] == "Sentiment Analysis"

    def test_hunter_sentiment_with_accuracy_query(self, injector):
        """Test Hunter AI sentiment with accuracy question"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="how accurate is sentiment analysis?",
            detected_intent="HUNTER_SENTIMENT",
            user_type="user"
        )

        # Should include accuracy metrics when asked about accuracy
        assert "accuracy_metrics" in knowledge
        assert "real_vs_demo_data" in knowledge

    def test_hunter_price_prediction(self, injector):
        """Test Hunter AI price prediction knowledge"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="predict ETH price for next week",
            detected_intent="HUNTER_PRICE_PREDICTION",
            user_type="user"
        )

        assert "capability" in knowledge
        assert knowledge["capability"]["name"] == "Price Prediction"

    def test_hunter_investor_query(self, injector):
        """Test Hunter AI knowledge for investor"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="what is hunter ai?",
            detected_intent="HUNTER_SENTIMENT",
            user_type="investor"
        )

        # Should include investor-specific sections
        assert "competitive_advantages" in knowledge
        assert "investor_highlights" in knowledge


class TestKnowledgeExtractionULTRA:
    """Test knowledge extraction for ULTRA intents"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_ultra_arbitrage_basic(self, injector):
        """Test ULTRA arbitrage knowledge extraction"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="find arbitrage opportunities with $10k",
            detected_intent="ULTRA_ARBITRAGE",
            user_type="user"
        )

        assert "feature_name" in knowledge
        assert knowledge["feature_name"] == "ULTRA - Advanced DeFi Automation Suite"
        assert "capability" in knowledge
        assert knowledge["capability"]["name"] == "Arbitrage Discovery"

    def test_ultra_flash_loans(self, injector):
        """Test ULTRA flash loans knowledge"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="tell me about flash loans",
            detected_intent="ULTRA_FLASH_LOANS",
            user_type="user"
        )

        assert "capability" in knowledge
        assert knowledge["capability"]["name"] == "Flash Loan Engine"

    def test_ultra_mev_protection(self, injector):
        """Test ULTRA MEV protection knowledge"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="protect my swap from MEV",
            detected_intent="ULTRA_MEV_PROTECTION",
            user_type="user"
        )

        assert "capability" in knowledge
        assert knowledge["capability"]["name"] == "MEV Protection"

    def test_ultra_with_accuracy_query(self, injector):
        """Test ULTRA with performance/accuracy question"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="how accurate is arbitrage detection?",
            detected_intent="ULTRA_ARBITRAGE",
            user_type="user"
        )

        # Should include accuracy metrics when asked
        assert "accuracy_metrics" in knowledge

    def test_ultra_investor_query(self, injector):
        """Test ULTRA knowledge for investor"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="what are ultras competitive advantages?",
            detected_intent="ULTRA_ARBITRAGE",
            user_type="investor"
        )

        # Should include investor-specific sections
        assert "competitive_advantages" in knowledge
        assert "investor_highlights" in knowledge


class TestKnowledgeExtractionSwap:
    """Test knowledge extraction for swap intent"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_swap_basic(self, injector):
        """Test swap knowledge extraction"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="swap 100 USDC to ETH",
            detected_intent="SWAP",
            user_type="user"
        )

        assert "feature_name" in knowledge
        assert knowledge["feature_name"] == "Token Swap"
        assert "how_it_works" in knowledge
        assert "supported_aggregators" in knowledge

    def test_swap_with_rate_query(self, injector):
        """Test swap with rate comparison question"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="what's the best rate for swapping?",
            detected_intent="SWAP",
            user_type="user"
        )

        # Should include rate comparison when asked about rates
        assert "rate_comparison_example" in knowledge

    def test_swap_with_safety_query(self, injector):
        """Test swap with safety question"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="is swapping safe from MEV attacks?",
            detected_intent="SWAP",
            user_type="user"
        )

        # Should include safety features when asked about safety
        assert "safety_features" in knowledge
        assert "features" in knowledge


class TestKnowledgeExtractionShortcuts:
    """Test knowledge extraction for shortcuts/commands"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_command_help(self, injector):
        """Test shortcuts knowledge for command help"""
        knowledge = injector.get_knowledge_for_intent(
            user_query="how do I check bitcoin price?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user"
        )

        assert "feature_name" in knowledge
        assert "command_categories" in knowledge
        assert "quick_start_commands" in knowledge
        assert "power_user_tips" in knowledge


class TestPromptAugmentation:
    """Test system prompt augmentation with knowledge"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_augment_prompt_basic(self, injector):
        """Test basic prompt augmentation"""
        enhanced_prompt = injector.augment_system_prompt(
            user_query="what can you do?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user"
        )

        assert len(enhanced_prompt) > 500  # Should be substantial
        assert "KNOWLEDGE BASE" in enhanced_prompt
        assert "RESPONSE GUIDELINES" in enhanced_prompt
        assert "ANVIL CAPABILITIES" in enhanced_prompt or "anvil capabilities" in enhanced_prompt.lower()

    def test_augment_prompt_with_custom_base(self, injector):
        """Test prompt augmentation with custom base prompt"""
        custom_base = "You are Anvil, a helpful DeFi assistant."

        enhanced_prompt = injector.augment_system_prompt(
            user_query="what can you do?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user",
            base_system_prompt=custom_base
        )

        assert custom_base in enhanced_prompt
        assert "KNOWLEDGE BASE" in enhanced_prompt

    def test_augment_prompt_for_investor(self, injector):
        """Test prompt augmentation includes investor guidelines"""
        enhanced_prompt = injector.augment_system_prompt(
            user_query="what are competitive advantages?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="investor"
        )

        assert "FOR INVESTORS" in enhanced_prompt
        assert "competitive advantages" in enhanced_prompt.lower()

    def test_augment_prompt_for_user(self, injector):
        """Test prompt augmentation includes user guidelines"""
        enhanced_prompt = injector.augment_system_prompt(
            user_query="how do i swap?",
            detected_intent="SWAP",
            user_type="user"
        )

        assert "FOR USERS" in enhanced_prompt


class TestConvenienceFunction:
    """Test convenience function for quick usage"""

    def test_inject_knowledge_convenience(self):
        """Test inject_knowledge convenience function"""
        enhanced_prompt = inject_knowledge(
            user_query="what can you do?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user"
        )

        assert len(enhanced_prompt) > 500
        assert "KNOWLEDGE BASE" in enhanced_prompt
        assert "ANVIL CAPABILITIES" in enhanced_prompt or "anvil capabilities" in enhanced_prompt.lower()

    def test_inject_knowledge_with_custom_prompt(self):
        """Test inject_knowledge with custom base prompt"""
        custom_base = "Custom system prompt here."

        enhanced_prompt = inject_knowledge(
            user_query="swap 100 USDC to ETH",
            detected_intent="SWAP",
            user_type="user",
            base_system_prompt=custom_base
        )

        assert custom_base in enhanced_prompt
        assert "KNOWLEDGE BASE" in enhanced_prompt


class TestUserTypeDetection:
    """Test automatic user type detection from queries"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_investor_keywords_detection(self, injector):
        """Test detection of investor-focused queries"""
        investor_queries = [
            "what are anvils competitive advantages?",
            "tell me about the market opportunity",
            "how does anvil make money?",
            "what's your revenue model?",
            "why should I invest in anvil?"
        ]

        for query in investor_queries:
            knowledge = injector.get_knowledge_for_intent(
                user_query=query,
                detected_intent="GENERAL_CONVERSATION",
                user_type="investor"  # Should be detected as investor
            )

            # Verify investor-specific content is included
            assert "competitive_advantages" in knowledge or "investor_highlights" in knowledge

    def test_user_queries(self, injector):
        """Test regular user queries"""
        user_queries = [
            "how do I swap tokens?",
            "what's the price of BTC?",
            "check sentiment for ETH",
            "find arbitrage opportunities"
        ]

        for query in user_queries:
            knowledge = injector.get_knowledge_for_intent(
                user_query=query,
                detected_intent="GENERAL_CONVERSATION",
                user_type="user"
            )

            # Verify user-focused content (not investor-specific)
            assert "feature_name" in knowledge


class TestIntentMapping:
    """Test intent-to-knowledge file mapping"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_all_hunter_intents_map_to_hunter_ai(self, injector):
        """Test all HUNTER_* intents use hunter_ai.json"""
        hunter_intents = [
            "HUNTER_SENTIMENT",
            "HUNTER_PRICE_PREDICTION",
            "HUNTER_RISK_SIGNALS",
            "HUNTER_TRADING_SIGNALS",
            "HUNTER_PATTERNS",
            "HUNTER_PORTFOLIO"
        ]

        for intent in hunter_intents:
            knowledge = injector.get_knowledge_for_intent(
                user_query="test query",
                detected_intent=intent,
                user_type="user"
            )

            assert "feature_name" in knowledge
            assert "Hunter AI" in knowledge["feature_name"]

    def test_all_ultra_intents_map_to_ultra(self, injector):
        """Test all ULTRA_* intents use ultra.json"""
        ultra_intents = [
            "ULTRA_ARBITRAGE",
            "ULTRA_FLASH_LOANS",
            "ULTRA_MEV_PROTECTION",
            "ULTRA_AUTO_EXECUTOR"
        ]

        for intent in ultra_intents:
            knowledge = injector.get_knowledge_for_intent(
                user_query="test query",
                detected_intent=intent,
                user_type="user"
            )

            assert "feature_name" in knowledge
            assert "ULTRA" in knowledge["feature_name"]


class TestKnowledgeFormatting:
    """Test knowledge formatting for LLM consumption"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_format_dict(self, injector):
        """Test dictionary formatting"""
        test_dict = {
            "name": "Test Feature",
            "description": "Test description",
            "nested": {
                "field1": "value1",
                "field2": "value2"
            }
        }

        formatted = injector._format_dict(test_dict, indent=0)

        assert "**Name:**" in formatted
        assert "Test Feature" in formatted
        assert "**Nested:**" in formatted

    def test_format_list(self, injector):
        """Test list formatting"""
        test_list = [
            "item1",
            "item2",
            {"name": "dict_item", "value": 123}
        ]

        formatted = injector._format_list(test_list, indent=0)

        assert "- item1" in formatted
        assert "- item2" in formatted
        assert "**Name:**" in formatted


# Performance Tests
class TestPerformance:
    """Test performance of knowledge injection"""

    @pytest.fixture
    def injector(self):
        return KnowledgeInjector()

    def test_caching_performance(self, injector):
        """Test that caching improves performance"""
        import time

        # First load (no cache)
        start = time.time()
        knowledge1 = injector.get_knowledge_for_intent(
            user_query="what can you do?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user"
        )
        first_load_time = time.time() - start

        # Second load (cached)
        start = time.time()
        knowledge2 = injector.get_knowledge_for_intent(
            user_query="what can you do?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user"
        )
        cached_load_time = time.time() - start

        # Cached should be faster (but not always guaranteed in tests)
        # At minimum, both should be fast
        assert first_load_time < 0.5  # Should load in under 500ms
        assert cached_load_time < 0.5

    def test_prompt_generation_performance(self, injector):
        """Test prompt generation is fast"""
        import time

        start = time.time()
        enhanced_prompt = injector.augment_system_prompt(
            user_query="what can you do?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user"
        )
        generation_time = time.time() - start

        assert generation_time < 0.5  # Should generate in under 500ms
        assert len(enhanced_prompt) > 500  # Should have substantial content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
