"""
Unit tests for DeFi intent classifiers.
"""

import pytest
from app.infrastructure.agents.classifiers import DeFiIntentClassifier


def test_defi_classifier_initialization():
    """Test that classifier initializes correctly."""
    classifier = DeFiIntentClassifier()
    
    assert classifier.model == "gpt-4-turbo"
    assert len(classifier.INTENTS) == 11
    assert "trade_swap" in classifier.INTENTS
    assert "portfolio_view" in classifier.INTENTS


def test_defi_classifier_examples():
    """Test that all intents have examples."""
    classifier = DeFiIntentClassifier()
    examples = classifier._get_examples()
    
    # All intents should have examples
    for intent in classifier.INTENTS:
        assert intent in examples
        assert len(examples[intent]) >= 1


def test_defi_classifier_descriptions():
    """Test intent descriptions."""
    classifier = DeFiIntentClassifier()
    descriptions = classifier.get_intent_descriptions()
    
    # All intents should have descriptions
    for intent in classifier.INTENTS:
        assert intent in descriptions
        assert len(descriptions[intent]) > 0


def test_defi_classifier_agent_mapping():
    """Test intent-to-agent mapping."""
    classifier = DeFiIntentClassifier()
    mapping = classifier.get_intent_to_agent_mapping()
    
    # All intents should map to an agent
    for intent in classifier.INTENTS:
        assert intent in mapping
        assert len(mapping[intent]) > 0
    
    # Check specific mappings
    assert mapping["trade_swap"] == "SwapAgent"
    assert mapping["trade_perp_open"] == "TradingAgent"
    assert mapping["portfolio_view"] == "PortfolioAgent"
    assert mapping["risk_analysis"] == "RiskAgent"


def test_defi_classifier_examples_quality():
    """Test that examples are diverse and relevant."""
    classifier = DeFiIntentClassifier()
    examples = classifier._get_examples()
    
    # trade_swap examples should contain swap-related keywords
    swap_examples = examples["trade_swap"]
    assert any("swap" in ex.lower() for ex in swap_examples)
    assert any("exchange" in ex.lower() for ex in swap_examples)
    
    # trade_perp_open examples should contain position-related keywords
    perp_examples = examples["trade_perp_open"]
    assert any("long" in ex.lower() or "short" in ex.lower() for ex in perp_examples)
    assert any("leverage" in ex.lower() or "position" in ex.lower() for ex in perp_examples)
    
    # portfolio_view examples should contain view-related keywords
    portfolio_examples = examples["portfolio_view"]
    assert any("portfolio" in ex.lower() or "balance" in ex.lower() for ex in portfolio_examples)


def test_get_defi_intent_classifier_convenience():
    """Test convenience function."""
    from app.infrastructure.agents.classifiers import get_defi_intent_classifier
    
    classifier = get_defi_intent_classifier()
    assert isinstance(classifier, DeFiIntentClassifier)
    assert classifier.model == "gpt-4-turbo"
    
    # With custom model
    classifier2 = get_defi_intent_classifier(model="gpt-3.5-turbo")
    assert classifier2.model == "gpt-3.5-turbo"


def test_classifier_intents_complete():
    """Test that we have all expected DeFi intents."""
    classifier = DeFiIntentClassifier()
    
    expected_intents = [
        "trade_swap",
        "trade_perp_open",
        "trade_perp_close",
        "lend_supply",
        "lend_borrow",
        "earn_stake",
        "portfolio_view",
        "market_info",
        "risk_analysis",
        "save_schedule",
        "general_question",
    ]
    
    for intent in expected_intents:
        assert intent in classifier.INTENTS, f"Missing intent: {intent}"
