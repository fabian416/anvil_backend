"""
Tests for Response Template System.

Tests template loading, rendering, and multi-language support.
"""

import pytest
from typing import Any


class TestResponseTemplateLoading:
    """Test template file loading."""
    
    def test_loads_portfolio_templates(self, response_template_service):
        """Test loading portfolio state templates."""
        service = response_template_service
        assert len(service._portfolio_templates) == 4
        assert "empty" in service._portfolio_templates
        assert "starter" in service._portfolio_templates
        assert "active" in service._portfolio_templates
        assert "whale" in service._portfolio_templates
    
    def test_loads_activity_templates(self, response_template_service):
        """Test loading activity level templates."""
        service = response_template_service
        assert len(service._activity_templates) >= 6
        assert "new" in service._activity_templates
        assert "inactive" in service._activity_templates
    
    def test_loads_user_type_templates(self, response_template_service):
        """Test loading user type templates."""
        service = response_template_service
        assert len(service._user_type_templates) >= 5
        assert "trader" in service._user_type_templates
        assert "yield_farmer" in service._user_type_templates
    
    def test_loads_workflow_templates(self, response_template_service):
        """Test loading workflow templates."""
        service = response_template_service
        assert len(service._workflow_templates) >= 4
        assert "swap" in service._workflow_templates
        assert "buy" in service._workflow_templates


class TestPortfolioTemplates:
    """Test portfolio state templates."""
    
    def test_empty_portfolio_query(self, response_template_service):
        """Test getting response for empty portfolio."""
        result = response_template_service.get_portfolio_response(
            portfolio_state="empty",
            message_key="portfolio_query",
            language="en",
        )
        
        assert result.message != ""
        assert result.template_key == "portfolio:empty:portfolio_query"
        # Should mention buying or getting started
        assert any(word in result.message.lower() for word in ["buy", "start", "welcome", "first"])
    
    def test_whale_portfolio_query(self, response_template_service):
        """Test getting response for whale portfolio."""
        result = response_template_service.get_portfolio_response(
            portfolio_state="whale",
            message_key="portfolio_query",
            language="en",
        )
        
        assert result.message != ""
        assert result.template_key == "portfolio:whale:portfolio_query"


class TestMultiLanguageTemplates:
    """Test multi-language template support."""
    
    @pytest.mark.parametrize("language,expected_word", [
        ("en", "buy"),
        ("es", "comprar"),
        ("pt", "comprar"),
        ("zh", "购买"),
    ])
    def test_empty_portfolio_multilang(self, response_template_service, language, expected_word):
        """Test empty portfolio response in multiple languages."""
        result = response_template_service.get_portfolio_response(
            portfolio_state="empty",
            message_key="portfolio_query",
            language=language,
        )
        
        assert result.message != ""
        # Should contain the expected word or fallback to English
        assert expected_word in result.message.lower() or "buy" in result.message.lower()


class TestWorkflowBlocking:
    """Test workflow blocking templates."""
    
    def test_swap_blocked_for_empty(self, response_template_service):
        """Test that swap is blocked for empty portfolio."""
        is_blocked, message = response_template_service.check_workflow_blocked(
            portfolio_state="empty",
            workflow="swap",
            language="en",
        )
        
        assert is_blocked is True
        assert message is not None
        assert "buy" in message.lower() or "need" in message.lower()
    
    def test_swap_allowed_for_active(self, response_template_service):
        """Test that swap is allowed for active portfolio."""
        is_blocked, message = response_template_service.check_workflow_blocked(
            portfolio_state="active",
            workflow="swap",
            language="en",
        )
        
        assert is_blocked is False
        assert message is None
    
    def test_buy_always_allowed(self, response_template_service):
        """Test that buy is allowed for all portfolio states."""
        for state in ["empty", "starter", "active", "whale"]:
            is_blocked, _ = response_template_service.check_workflow_blocked(
                portfolio_state=state,
                workflow="buy",
                language="en",
            )
            assert is_blocked is False, f"Buy should be allowed for {state}"


class TestGasWarning:
    """Test gas warning logic."""
    
    def test_gas_warning_for_starter_small_amount(self, response_template_service):
        """Test gas warning shown for small amounts on starter portfolio."""
        should_warn = response_template_service.should_show_gas_warning(
            portfolio_state="starter",
            amount_usd=30.0,
        )
        
        assert should_warn is True
    
    def test_no_gas_warning_for_whale(self, response_template_service):
        """Test no gas warning for whale portfolios."""
        should_warn = response_template_service.should_show_gas_warning(
            portfolio_state="whale",
            amount_usd=30.0,
        )
        
        assert should_warn is False
    
    def test_no_gas_warning_for_large_amount(self, response_template_service):
        """Test no gas warning for large amounts."""
        should_warn = response_template_service.should_show_gas_warning(
            portfolio_state="starter",
            amount_usd=500.0,
        )
        
        assert should_warn is False
