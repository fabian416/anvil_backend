"""
Integration tests for project template feature flags.

Tests granular enable/disable controls for each project template.
"""

import pytest
from uuid import uuid4

from app.setup.config.projects import (
    ProjectSettings,
    ProjectTemplateSettings,
    TemplateDisabledError,
)
from app.application.projects.templates.project_templates import (
    DEFI_SWING_TRADER_TEMPLATE,
    ARBITRAGE_HUNTER_TEMPLATE,
    PORTFOLIO_MANAGER_TEMPLATE,
    CONSERVATIVE_INVESTOR_TEMPLATE,
    DAY_TRADER_TEMPLATE,
    ALL_PROJECT_TEMPLATES,
    create_project_from_template,
    get_available_templates,
)


class TestProjectMasterSwitch:
    """Test project system master switch."""
    
    def test_projects_disabled_globally(self):
        """Test that project system can be disabled globally."""
        settings = ProjectSettings(enabled=False)
        
        with pytest.raises(TemplateDisabledError) as exc_info:
            create_project_from_template(
                DEFI_SWING_TRADER_TEMPLATE,
                created_by=uuid4(),
                settings=settings,
            )
        
        assert "Project system is disabled" in str(exc_info.value)
        assert "projects.enabled=true" in str(exc_info.value)
    
    def test_templates_disabled_globally(self):
        """Test that templates can be disabled globally."""
        settings = ProjectSettings(
            enabled=True,
            templates_enabled=False,
        )
        
        with pytest.raises(TemplateDisabledError) as exc_info:
            create_project_from_template(
                DEFI_SWING_TRADER_TEMPLATE,
                created_by=uuid4(),
                settings=settings,
            )
        
        assert "Project templates are disabled" in str(exc_info.value)
        assert "templates_enabled=true" in str(exc_info.value)


class TestDeFiSwingTraderTemplate:
    """Test DeFi Swing Trader template flags."""
    
    def test_swing_trader_enabled_by_default(self):
        """Test Swing Trader template is enabled by default."""
        settings = ProjectSettings()
        
        project = create_project_from_template(
            DEFI_SWING_TRADER_TEMPLATE,
            created_by=uuid4(),
            settings=settings,
        )
        
        assert project.name == "DeFi Swing Trader"
        assert project.slug == "defi-swing-trader"
    
    def test_swing_trader_can_be_disabled(self):
        """Test Swing Trader template can be disabled."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(defi_swing_trader_enabled=False)
        )
        
        with pytest.raises(TemplateDisabledError) as exc_info:
            create_project_from_template(
                DEFI_SWING_TRADER_TEMPLATE,
                created_by=uuid4(),
                settings=settings,
            )
        
        assert "DeFi Swing Trader" in str(exc_info.value)
        assert "defi_swing_trader_enabled=true" in str(exc_info.value)


class TestArbitrageHunterTemplate:
    """Test Arbitrage Hunter template flags."""
    
    def test_arbitrage_hunter_enabled_by_default(self):
        """Test Arbitrage Hunter template is enabled by default."""
        settings = ProjectSettings()
        
        project = create_project_from_template(
            ARBITRAGE_HUNTER_TEMPLATE,
            created_by=uuid4(),
            settings=settings,
        )
        
        assert project.name == "Arbitrage Hunter"
        assert project.slug == "arbitrage-hunter"
    
    def test_arbitrage_hunter_can_be_disabled(self):
        """Test Arbitrage Hunter template can be disabled."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(arbitrage_hunter_enabled=False)
        )
        
        with pytest.raises(TemplateDisabledError) as exc_info:
            create_project_from_template(
                ARBITRAGE_HUNTER_TEMPLATE,
                created_by=uuid4(),
                settings=settings,
            )
        
        assert "Arbitrage Hunter" in str(exc_info.value)
        assert "arbitrage_hunter_enabled=true" in str(exc_info.value)


class TestPortfolioManagerTemplate:
    """Test AI Portfolio Manager template flags."""
    
    def test_portfolio_manager_enabled_by_default(self):
        """Test Portfolio Manager template is enabled by default."""
        settings = ProjectSettings()
        
        project = create_project_from_template(
            PORTFOLIO_MANAGER_TEMPLATE,
            created_by=uuid4(),
            settings=settings,
        )
        
        assert project.name == "AI Portfolio Manager"
        assert project.slug == "ai-portfolio-manager"
    
    def test_portfolio_manager_can_be_disabled(self):
        """Test Portfolio Manager template can be disabled."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(ai_portfolio_manager_enabled=False)
        )
        
        with pytest.raises(TemplateDisabledError) as exc_info:
            create_project_from_template(
                PORTFOLIO_MANAGER_TEMPLATE,
                created_by=uuid4(),
                settings=settings,
            )
        
        assert "AI Portfolio Manager" in str(exc_info.value)
        assert "ai_portfolio_manager_enabled=true" in str(exc_info.value)


class TestConservativeInvestorTemplate:
    """Test Conservative Investor template flags."""
    
    def test_conservative_investor_enabled_by_default(self):
        """Test Conservative Investor template is enabled by default."""
        settings = ProjectSettings()
        
        project = create_project_from_template(
            CONSERVATIVE_INVESTOR_TEMPLATE,
            created_by=uuid4(),
            settings=settings,
        )
        
        assert project.name == "Conservative Investor"
        assert project.slug == "conservative-investor"
    
    def test_conservative_investor_can_be_disabled(self):
        """Test Conservative Investor template can be disabled."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(conservative_investor_enabled=False)
        )
        
        with pytest.raises(TemplateDisabledError) as exc_info:
            create_project_from_template(
                CONSERVATIVE_INVESTOR_TEMPLATE,
                created_by=uuid4(),
                settings=settings,
            )
        
        assert "Conservative Investor" in str(exc_info.value)
        assert "conservative_investor_enabled=true" in str(exc_info.value)


class TestDayTraderProTemplate:
    """Test Day Trader Pro template flags."""
    
    def test_day_trader_pro_enabled_by_default(self):
        """Test Day Trader Pro template is enabled by default."""
        settings = ProjectSettings()
        
        project = create_project_from_template(
            DAY_TRADER_TEMPLATE,
            created_by=uuid4(),
            settings=settings,
        )
        
        assert project.name == "Day Trader Pro"
        assert project.slug == "day-trader-pro"
    
    def test_day_trader_pro_can_be_disabled(self):
        """Test Day Trader Pro template can be disabled."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(day_trader_pro_enabled=False)
        )
        
        with pytest.raises(TemplateDisabledError) as exc_info:
            create_project_from_template(
                DAY_TRADER_TEMPLATE,
                created_by=uuid4(),
                settings=settings,
            )
        
        assert "Day Trader Pro" in str(exc_info.value)
        assert "day_trader_pro_enabled=true" in str(exc_info.value)


class TestGetAvailableTemplates:
    """Test get_available_templates function."""
    
    def test_all_templates_available_by_default(self):
        """Test all templates are available by default."""
        settings = ProjectSettings()
        
        available = get_available_templates(settings)
        
        assert len(available) == 5  # All 5 templates
        assert len(available) == len(ALL_PROJECT_TEMPLATES)
    
    def test_no_templates_when_system_disabled(self):
        """Test no templates available when system is disabled."""
        settings = ProjectSettings(enabled=False)
        
        available = get_available_templates(settings)
        
        assert len(available) == 0
    
    def test_no_templates_when_templates_disabled(self):
        """Test no templates available when templates are disabled."""
        settings = ProjectSettings(templates_enabled=False)
        
        available = get_available_templates(settings)
        
        assert len(available) == 0
    
    def test_filtered_templates_with_selective_enablement(self):
        """Test only enabled templates are returned."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(
                defi_swing_trader_enabled=True,
                arbitrage_hunter_enabled=False,  # Disabled
                ai_portfolio_manager_enabled=True,
                conservative_investor_enabled=True,
                day_trader_pro_enabled=False,  # Disabled
            )
        )
        
        available = get_available_templates(settings)
        
        assert len(available) == 3  # Only 3 enabled
        available_slugs = [t["slug"] for t in available]
        assert "defi-swing-trader" in available_slugs
        assert "ai-portfolio-manager" in available_slugs
        assert "conservative-investor" in available_slugs
        assert "arbitrage-hunter" not in available_slugs
        assert "day-trader-pro" not in available_slugs


class TestSelectiveTemplateEnablement:
    """Test selective enablement scenarios."""
    
    def test_safe_templates_only(self):
        """Test enabling only safe templates for public launch."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(
                defi_swing_trader_enabled=True,  # Safe
                arbitrage_hunter_enabled=False,  # Too risky
                ai_portfolio_manager_enabled=True,  # Safe
                conservative_investor_enabled=True,  # Beginner
                day_trader_pro_enabled=False,  # Too aggressive
            )
        )
        
        available = get_available_templates(settings)
        
        assert len(available) == 3
        
        # Safe templates work
        project1 = create_project_from_template(
            DEFI_SWING_TRADER_TEMPLATE,
            created_by=uuid4(),
            settings=settings,
        )
        assert project1.name == "DeFi Swing Trader"
        
        # Risky templates blocked
        with pytest.raises(TemplateDisabledError):
            create_project_from_template(
                ARBITRAGE_HUNTER_TEMPLATE,
                created_by=uuid4(),
                settings=settings,
            )
    
    def test_beginner_templates_only(self):
        """Test enabling only beginner-friendly templates."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(
                defi_swing_trader_enabled=False,  # Intermediate
                arbitrage_hunter_enabled=False,  # Expert
                ai_portfolio_manager_enabled=False,  # Advanced
                conservative_investor_enabled=True,  # Beginner only
                day_trader_pro_enabled=False,  # Expert
            )
        )
        
        available = get_available_templates(settings)
        
        assert len(available) == 1
        assert available[0]["slug"] == "conservative-investor"


class TestConfigurationDefaults:
    """Test configuration default values."""
    
    def test_all_defaults_enabled(self):
        """Test that all templates are enabled by default."""
        settings = ProjectSettings()
        
        assert settings.enabled is True
        assert settings.templates_enabled is True
        assert settings.templates.defi_swing_trader_enabled is True
        assert settings.templates.arbitrage_hunter_enabled is True
        assert settings.templates.ai_portfolio_manager_enabled is True
        assert settings.templates.conservative_investor_enabled is True
        assert settings.templates.day_trader_pro_enabled is True
    
    def test_partial_configuration(self):
        """Test partial configuration with defaults."""
        settings = ProjectSettings(
            templates=ProjectTemplateSettings(
                arbitrage_hunter_enabled=False,
                # Others default to True
            )
        )
        
        assert settings.templates.arbitrage_hunter_enabled is False
        assert settings.templates.defi_swing_trader_enabled is True  # Default
        assert settings.templates.conservative_investor_enabled is True  # Default


# Test Summary
"""
Total Tests: 20+

Coverage:
  ✅ Master project switch (enabled/disabled)
  ✅ Master templates switch (enabled/disabled)
  ✅ Individual template flags (5 templates)
  ✅ get_available_templates function
  ✅ Selective template enablement scenarios
  ✅ Configuration defaults
  ✅ Error messages
  
Use Cases Tested:
  ✅ Safe templates only (public launch)
  ✅ Beginner templates only
  ✅ All templates enabled (production)
  ✅ No templates (system disabled)
"""
