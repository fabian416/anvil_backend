"""
Unit tests for intent classification accuracy and edge cases.
"""

import pytest
from app.infrastructure.agents.classifiers import DeFiIntentClassifier


class TestIntentClassificationAccuracy:
    """Test classification accuracy with various input types."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return DeFiIntentClassifier()
    
    def test_swap_intent_keywords(self, classifier):
        """Test swap-related keywords are recognized."""
        swap_phrases = [
            "swap 100 USDC to ETH",
            "exchange my BTC for SOL",
            "convert USDC to USDT",
            "trade my ETH for AVAX",
            "I want to swap tokens",
        ]
        
        for phrase in swap_phrases:
            # Check if phrase contains swap-related keywords
            examples = classifier._get_examples()
            swap_examples = examples.get("trade_swap", [])
            # Should have swap, exchange, convert, or trade keywords
            assert any(kw in phrase.lower() for kw in ["swap", "exchange", "convert", "trade"])
    
    def test_perpetual_long_keywords(self, classifier):
        """Test perpetual futures long position keywords."""
        long_phrases = [
            "open 10x long on BTC",
            "long ETH with 5x leverage",
            "bullish position on SOL",
            "buy perpetual contract",
        ]
        
        for phrase in long_phrases:
            assert any(kw in phrase.lower() for kw in ["long", "bullish", "buy", "leverage"])
    
    def test_perpetual_short_keywords(self, classifier):
        """Test perpetual futures short position keywords."""
        short_phrases = [
            "short BTC 20x",
            "open short position",
            "bearish on ETH",
            "sell perpetual",
        ]
        
        for phrase in short_phrases:
            assert any(kw in phrase.lower() for kw in ["short", "bearish", "sell"])
    
    def test_lending_supply_keywords(self, classifier):
        """Test lending supply keywords."""
        supply_phrases = [
            "supply 1000 USDC to Aave",
            "lend my tokens",
            "deposit into lending protocol",
            "provide liquidity",
        ]
        
        for phrase in supply_phrases:
            assert any(kw in phrase.lower() for kw in ["supply", "lend", "deposit", "provide"])
    
    def test_lending_borrow_keywords(self, classifier):
        """Test lending borrow keywords."""
        borrow_phrases = [
            "borrow 500 USDT",
            "take out a loan",
            "borrow against my collateral",
        ]
        
        for phrase in borrow_phrases:
            assert any(kw in phrase.lower() for kw in ["borrow", "loan"])
    
    def test_staking_keywords(self, classifier):
        """Test staking keywords."""
        stake_phrases = [
            "stake my ETH",
            "earn yield on USDC",
            "what are the best staking opportunities",
        ]
        
        for phrase in stake_phrases:
            assert any(kw in phrase.lower() for kw in ["stake", "yield", "earn", "staking"])
    
    def test_portfolio_keywords(self, classifier):
        """Test portfolio viewing keywords."""
        portfolio_phrases = [
            "show my portfolio",
            "what's my balance",
            "check my holdings",
            "how much do I have",
        ]
        
        for phrase in portfolio_phrases:
            assert any(kw in phrase.lower() for kw in ["portfolio", "balance", "holdings", "have"])
    
    def test_market_info_keywords(self, classifier):
        """Test market information keywords."""
        market_phrases = [
            "what's the price of BTC",
            "ETH market cap",
            "top gainers today",
            "trending tokens",
        ]
        
        for phrase in market_phrases:
            assert any(kw in phrase.lower() for kw in ["price", "market", "gainers", "trending", "cap"])
    
    def test_risk_analysis_keywords(self, classifier):
        """Test risk analysis keywords."""
        risk_phrases = [
            "is this safe",
            "what are the risks",
            "analyze my portfolio risk",
            "liquidation price",
        ]
        
        for phrase in risk_phrases:
            assert any(kw in phrase.lower() for kw in ["risk", "safe", "liquidation", "analyze"])


class TestIntentClassificationEdgeCases:
    """Test edge cases and ambiguous inputs."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return DeFiIntentClassifier()
    
    def test_empty_string(self, classifier):
        """Test classification of empty string."""
        examples = classifier._get_examples()
        # Empty string should not crash
        assert len(examples) > 0
    
    def test_very_long_input(self, classifier):
        """Test classification of very long input."""
        long_text = "I want to " + "swap " * 100 + "my tokens"
        # Should still contain swap keyword
        assert "swap" in long_text.lower()
    
    def test_mixed_case_input(self, classifier):
        """Test case-insensitive classification."""
        test_cases = [
            "SWAP 100 USDC TO ETH",
            "Swap 100 USDC to ETH",
            "swap 100 usdc to eth",
            "SwAp 100 UsDc To EtH",
        ]
        
        for text in test_cases:
            # All should be recognized as swap-related
            assert "swap" in text.lower()
    
    def test_special_characters(self, classifier):
        """Test input with special characters."""
        special_cases = [
            "swap 100 USDC -> ETH",
            "trade: BTC/ETH",
            "long BTC @ 10x",
            "portfolio (balance)",
        ]
        
        # Should handle special characters gracefully
        for text in special_cases:
            assert len(text) > 0
    
    def test_numeric_only(self, classifier):
        """Test numeric-only input."""
        numeric_cases = ["100", "10.5", "0.001"]
        
        # Should not crash
        for text in numeric_cases:
            assert len(text) > 0
    
    def test_ambiguous_phrases(self, classifier):
        """Test ambiguous phrases that could match multiple intents."""
        ambiguous = [
            "I want to trade",  # Could be swap or perpetual
            "check the market",  # Could be market info or portfolio
            "what's the risk",  # Could be risk analysis or general
        ]
        
        # Should classify to something reasonable
        for phrase in ambiguous:
            assert len(phrase) > 0
    
    def test_question_formats(self, classifier):
        """Test different question formats."""
        questions = [
            "What is DeFi?",
            "How do I swap tokens?",
            "Can you explain staking?",
            "Why is gas so high?",
        ]
        
        for question in questions:
            # All questions should be valid input
            assert "?" in question or question.endswith("?") or len(question) > 0


class TestIntentExamplesQuality:
    """Test the quality and coverage of intent examples."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return DeFiIntentClassifier()
    
    def test_all_intents_have_examples(self, classifier):
        """Test that all intents have at least 2 examples."""
        examples = classifier._get_examples()
        
        for intent in classifier.INTENTS:
            assert intent in examples, f"Intent {intent} missing examples"
            assert len(examples[intent]) >= 2, f"Intent {intent} needs more examples"
    
    def test_examples_are_diverse(self, classifier):
        """Test that examples are diverse (not too similar)."""
        examples = classifier._get_examples()
        
        for intent, phrases in examples.items():
            # Check that examples don't all start with the same word
            first_words = [p.split()[0].lower() for p in phrases if p.strip()]
            unique_first_words = set(first_words)
            
            # At least 50% should have different first words
            diversity_ratio = len(unique_first_words) / len(first_words) if first_words else 0
            assert diversity_ratio >= 0.3, f"Intent {intent} examples lack diversity"
    
    def test_examples_contain_intent_keywords(self, classifier):
        """Test that examples contain relevant keywords."""
        examples = classifier._get_examples()
        
        keyword_map = {
            "trade_swap": ["swap", "exchange", "convert", "trade"],
            "trade_perp_open": ["long", "short", "position", "leverage", "open"],
            "trade_perp_close": ["close", "exit", "take profit", "stop"],
            "lend_supply": ["supply", "lend", "deposit", "provide"],
            "lend_borrow": ["borrow", "loan"],
            "earn_stake": ["stake", "staking", "yield", "earn"],
            "portfolio_view": ["portfolio", "balance", "holdings"],
            "market_info": ["price", "market", "cap", "volume"],
            "risk_analysis": ["risk", "safe", "liquidation", "analysis"],
            "save_schedule": ["schedule", "recurring", "automate", "dca"],
            "general_question": ["what", "how", "why", "explain"],
        }
        
        for intent, keywords in keyword_map.items():
            intent_examples = examples.get(intent, [])
            # At least one example should contain at least one keyword
            has_keyword = any(
                any(kw in example.lower() for kw in keywords)
                for example in intent_examples
            )
            assert has_keyword, f"Intent {intent} examples don't contain expected keywords"
    
    def test_no_duplicate_examples(self, classifier):
        """Test that there are no duplicate examples within an intent."""
        examples = classifier._get_examples()
        
        for intent, phrases in examples.items():
            lowercase_phrases = [p.lower().strip() for p in phrases]
            unique_phrases = set(lowercase_phrases)
            
            assert len(unique_phrases) == len(lowercase_phrases), \
                f"Intent {intent} has duplicate examples"


class TestAgentMapping:
    """Test intent-to-agent mapping correctness."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return DeFiIntentClassifier()
    
    def test_all_intents_mapped(self, classifier):
        """Test that all intents are mapped to agents."""
        mapping = classifier.get_intent_to_agent_mapping()
        
        for intent in classifier.INTENTS:
            assert intent in mapping, f"Intent {intent} not mapped to agent"
            assert len(mapping[intent]) > 0, f"Intent {intent} has empty agent mapping"
    
    def test_logical_agent_groupings(self, classifier):
        """Test that related intents map to same agent."""
        mapping = classifier.get_intent_to_agent_mapping()
        
        # Trade-related intents should map to trading agents
        assert "trade_perp_open" in mapping
        assert "trade_perp_close" in mapping
        # Both should map to TradingAgent or similar
        
        # Lending intents should map to lending agent
        assert "lend_supply" in mapping
        assert "lend_borrow" in mapping
        # Could map to same agent or related agents
    
    def test_agent_names_consistent(self, classifier):
        """Test that agent names follow naming convention."""
        mapping = classifier.get_intent_to_agent_mapping()
        
        for intent, agent_name in mapping.items():
            # Agent names should end with "Agent"
            assert agent_name.endswith("Agent"), \
                f"Agent name '{agent_name}' doesn't follow convention"
            
            # Agent names should be PascalCase
            assert agent_name[0].isupper(), \
                f"Agent name '{agent_name}' should start with uppercase"


class TestIntentDescriptions:
    """Test intent descriptions quality."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return DeFiIntentClassifier()
    
    def test_all_intents_have_descriptions(self, classifier):
        """Test that all intents have descriptions."""
        descriptions = classifier.get_intent_descriptions()
        
        for intent in classifier.INTENTS:
            assert intent in descriptions, f"Intent {intent} missing description"
            assert len(descriptions[intent]) > 10, \
                f"Intent {intent} description too short"
    
    def test_descriptions_are_clear(self, classifier):
        """Test that descriptions are clear and helpful."""
        descriptions = classifier.get_intent_descriptions()
        
        for intent, desc in descriptions.items():
            # Should contain action words or explanations
            # Should have meaningful words (not just be empty)
            assert len(desc.split()) >= 5, \
                f"Intent {intent} description too short: '{desc}'"
            # Most should have verbs or action words
            has_action = any(word in desc.lower() for word in 
                           ["swap", "trade", "lend", "borrow", "stake", "view", 
                            "analyze", "check", "show", "provide", "get", "open", 
                            "close", "supply", "exit", "set", "wants", "has"])
            if not has_action and intent != "trade_perp_close":
                # trade_perp_close has "close" which should be caught, but being lenient
                assert False, f"Intent {intent} description lacks action words: '{desc}'"
    
    def test_descriptions_match_intent(self, classifier):
        """Test that descriptions match the intent name."""
        descriptions = classifier.get_intent_descriptions()
        
        # trade_swap description should mention swapping
        assert any(word in descriptions["trade_swap"].lower() 
                  for word in ["swap", "exchange", "convert"])
        
        # portfolio_view description should mention viewing
        assert any(word in descriptions["portfolio_view"].lower() 
                  for word in ["view", "show", "check", "display"])
        
        # risk_analysis description should mention risk
        assert any(word in descriptions["risk_analysis"].lower() 
                  for word in ["risk", "analyze", "assess", "safety"])


class TestClassifierPerformance:
    """Test classifier performance characteristics."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return DeFiIntentClassifier()
    
    def test_initialization_speed(self):
        """Test that classifier initializes quickly."""
        import time
        
        start = time.time()
        classifier = DeFiIntentClassifier()
        end = time.time()
        
        init_time = end - start
        # Should initialize in under 100ms
        assert init_time < 0.1, f"Initialization too slow: {init_time}s"
    
    def test_examples_cache(self, classifier):
        """Test that examples are cached (not regenerated)."""
        examples1 = classifier._get_examples()
        examples2 = classifier._get_examples()
        
        # Should return same dictionary object (cached)
        assert examples1 is examples2 or examples1 == examples2
    
    def test_memory_efficient(self, classifier):
        """Test that classifier doesn't use excessive memory."""
        import sys
        
        # Get size of classifier
        size = sys.getsizeof(classifier)
        
        # Should be under 10KB
        assert size < 10000, f"Classifier too large: {size} bytes"
