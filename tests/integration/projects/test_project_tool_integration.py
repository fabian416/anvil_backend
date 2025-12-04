"""
Integration tests for project-scoped tool execution.

Tests the full flow from project configuration to tool execution with risk limit enforcement.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from decimal import Decimal

from app.domain.entities.project import Project
from app.application.projects.services.project_tool_executor import (
    ProjectToolExecutor,
    ToolExecutionError,
)
from app.application.projects.templates.project_templates import (
    DEFI_SWING_TRADER_TEMPLATE,
    ARBITRAGE_HUNTER_TEMPLATE,
    PORTFOLIO_MANAGER_TEMPLATE,
    CONSERVATIVE_INVESTOR_TEMPLATE,
    DAY_TRADER_TEMPLATE,
    ALL_PROJECT_TEMPLATES,
    create_project_from_template,
)


class TestProjectEntityEnhancements:
    """Test Project entity enhancements for tool management."""
    
    def test_project_hunter_tools_enabled(self):
        """Test hunter_tools_enabled property."""
        project = Project(
            id=uuid4(),
            slug="test",
            name="Test",
            description=None,
            icon=None,
            color=None,
            banner_url=None,
            status="active",
            visibility="public",
            system_prompt="Test",
            welcome_message=None,
            enabled_protocols=[],
            enabled_chains=[],
            enabled_tools=[
                "hunter_sentiment_analysis",
                "hunter_price_prediction",
                "ultra_flash_loans",
                "other_tool",
            ],
            risk_config={},
            max_users=None,
            display_order=0,
            is_featured=False,
            created_by=uuid4(),
        )
        
        hunter_tools = project.hunter_tools_enabled
        
        assert len(hunter_tools) == 2
        assert "hunter_sentiment_analysis" in hunter_tools
        assert "hunter_price_prediction" in hunter_tools
    
    def test_project_ultra_tools_enabled(self):
        """Test ultra_tools_enabled property."""
        project = Project(
            id=uuid4(),
            slug="test",
            name="Test",
            description=None,
            icon=None,
            color=None,
            banner_url=None,
            status="active",
            visibility="public",
            system_prompt="Test",
            welcome_message=None,
            enabled_protocols=[],
            enabled_chains=[],
            enabled_tools=[
                "hunter_sentiment_analysis",
                "ultra_flash_loans",
                "ultra_arbitrage_discovery",
            ],
            risk_config={},
            max_users=None,
            display_order=0,
            is_featured=False,
            created_by=uuid4(),
        )
        
        ultra_tools = project.ultra_tools_enabled
        
        assert len(ultra_tools) == 2
        assert "ultra_flash_loans" in ultra_tools
        assert "ultra_arbitrage_discovery" in ultra_tools
    
    def test_can_use_hunter_tool(self):
        """Test can_use_hunter_tool method."""
        project = Project(
            id=uuid4(),
            slug="test",
            name="Test",
            description=None,
            icon=None,
            color=None,
            banner_url=None,
            status="active",
            visibility="public",
            system_prompt="Test",
            welcome_message=None,
            enabled_protocols=[],
            enabled_chains=[],
            enabled_tools=["hunter_sentiment_analysis"],
            risk_config={},
            max_users=None,
            display_order=0,
            is_featured=False,
            created_by=uuid4(),
        )
        
        assert project.can_use_hunter_tool("hunter_sentiment_analysis") is True
        assert project.can_use_hunter_tool("hunter_price_prediction") is False


class TestProjectTemplates:
    """Test project templates."""
    
    def test_all_templates_defined(self):
        """Test that all 5 templates are defined."""
        assert len(ALL_PROJECT_TEMPLATES) == 5
    
    def test_template_has_required_fields(self):
        """Test that each template has required fields."""
        for template in ALL_PROJECT_TEMPLATES:
            assert "slug" in template
            assert "name" in template
            assert "system_prompt" in template
            assert "enabled_tools" in template
            assert "risk_config" in template
    
    def test_defi_swing_trader_template(self):
        """Test DeFi Swing Trader template."""
        template = DEFI_SWING_TRADER_TEMPLATE
        
        assert template["slug"] == "defi-swing-trader"
        assert template["icon"] == "📈"
        assert "hunter_sentiment_analysis" in template["enabled_tools"]
        assert "hunter_trading_signals" in template["enabled_tools"]
        assert template["risk_config"]["max_single_asset_percent"] == 30
    
    def test_arbitrage_hunter_template(self):
        """Test Arbitrage Hunter template."""
        template = ARBITRAGE_HUNTER_TEMPLATE
        
        assert template["slug"] == "arbitrage-hunter"
        assert template["icon"] == "⚡"
        assert "ultra_flash_loans" in template["enabled_tools"]
        assert "ultra_arbitrage_discovery" in template["enabled_tools"]
        assert template["risk_config"]["max_capital_per_trade"] == 500000
    
    def test_conservative_investor_template(self):
        """Test Conservative Investor template."""
        template = CONSERVATIVE_INVESTOR_TEMPLATE
        
        assert template["slug"] == "conservative-investor"
        assert template["icon"] == "🛡️"
        assert "hunter_sentiment_analysis" in template["enabled_tools"]
        assert "hunter_trading_signals" not in template["enabled_tools"]  # Disabled for safety
        assert template["risk_config"]["max_risk_score"] == 50
        assert template["risk_config"]["min_stablecoin_percent"] == 30
    
    def test_create_project_from_template(self):
        """Test creating project from template."""
        admin_id = uuid4()
        project = create_project_from_template(
            DEFI_SWING_TRADER_TEMPLATE,
            created_by=admin_id
        )
        
        assert project.slug == "defi-swing-trader"
        assert project.name == "DeFi Swing Trader"
        assert project.created_by == admin_id
        assert len(project.enabled_tools) == 5


class TestProjectToolExecutor:
    """Test project-scoped tool executor."""
    
    @pytest.fixture
    def mock_hunter_executor(self):
        """Create mock Hunter AI executor."""
        executor = AsyncMock()
        executor.execute_tool.return_value = "Mock Hunter AI response"
        return executor
    
    @pytest.fixture
    def swing_trader_project(self):
        """Create DeFi Swing Trader project."""
        return create_project_from_template(
            DEFI_SWING_TRADER_TEMPLATE,
            created_by=uuid4()
        )
    
    @pytest.fixture
    def conservative_project(self):
        """Create Conservative Investor project."""
        return create_project_from_template(
            CONSERVATIVE_INVESTOR_TEMPLATE,
            created_by=uuid4()
        )
    
    @pytest.mark.asyncio
    async def test_execute_enabled_tool(
        self, swing_trader_project, mock_hunter_executor
    ):
        """Test executing a tool enabled in project."""
        executor = ProjectToolExecutor(swing_trader_project, mock_hunter_executor)
        
        result = await executor.execute_tool(
            tool_name="hunter_sentiment_analysis",
            parameters={"token_symbol": "ETH"}
        )
        
        assert result == "Mock Hunter AI response"
        mock_hunter_executor.execute_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_disabled_tool_raises_error(
        self, conservative_project, mock_hunter_executor
    ):
        """Test executing a tool NOT enabled in project raises error."""
        executor = ProjectToolExecutor(conservative_project, mock_hunter_executor)
        
        # Conservative Investor doesn't have trading signals enabled
        with pytest.raises(ToolExecutionError) as exc_info:
            await executor.execute_tool(
                tool_name="hunter_trading_signals",
                parameters={"token_symbol": "ETH"}
            )
        
        assert "not enabled in project" in str(exc_info.value)
        assert "Conservative Investor" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_portfolio_risk_tolerance_validation(self, mock_hunter_executor):
        """Test portfolio risk tolerance validation."""
        # Use Portfolio Manager template (has portfolio optimization enabled)
        portfolio_project = create_project_from_template(
            PORTFOLIO_MANAGER_TEMPLATE,
            created_by=uuid4()
        )
        
        executor = ProjectToolExecutor(portfolio_project, mock_hunter_executor)
        
        # Portfolio Manager has max_risk_tolerance: 0.6
        # This should raise error
        with pytest.raises(ToolExecutionError) as exc_info:
            await executor.execute_tool(
                tool_name="hunter_portfolio_optimization",
                parameters={
                    "tokens": ["ETH", "BTC"],
                    "risk_tolerance": 0.9  # Exceeds limit
                }
            )
        
        assert "exceeds project limit" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_ultra_capital_validation(self, mock_hunter_executor):
        """Test ULTRA capital validation."""
        # Use Arbitrage Hunter template (has ULTRA tools enabled)
        arb_project = create_project_from_template(
            ARBITRAGE_HUNTER_TEMPLATE,
            created_by=uuid4()
        )
        
        # Lower the capital limit for testing
        arb_project.risk_config["max_capital_per_trade"] = 100000
        
        executor = ProjectToolExecutor(arb_project, mock_hunter_executor)
        
        # This should raise error (exceeds capital limit)
        with pytest.raises(ToolExecutionError) as exc_info:
            await executor.execute_tool(
                tool_name="ultra_arbitrage_discovery",
                parameters={"capital": 200000}
            )
        
        assert "exceeds project limit" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_conservative_project_blocks_trading_signals(
        self, conservative_project, mock_hunter_executor
    ):
        """Test that Conservative Investor project blocks trading signals."""
        executor = ProjectToolExecutor(conservative_project, mock_hunter_executor)
        
        # Conservative doesn't have trading signals
        with pytest.raises(ToolExecutionError):
            await executor.execute_tool(
                tool_name="hunter_trading_signals",
                parameters={"token_symbol": "ETH"}
            )
    
    @pytest.mark.asyncio
    async def test_arbitrage_project_allows_ultra_tools(
        self, mock_hunter_executor
    ):
        """Test that Arbitrage Hunter project allows ULTRA tools."""
        project = create_project_from_template(
            ARBITRAGE_HUNTER_TEMPLATE,
            created_by=uuid4()
        )
        
        executor = ProjectToolExecutor(project, mock_hunter_executor)
        
        # ULTRA tools should be allowed (will return placeholder in Phase 2)
        result = await executor.execute_tool(
            tool_name="ultra_flash_loans",
            parameters={"capital": 10000}
        )
        
        # Should not raise error (tool is enabled)
        assert "Phase 3" in result  # Placeholder message


class TestConversationProjectLinking:
    """Test conversation linking to projects."""
    
    def test_conversation_without_project(self):
        """Test conversation without project (general chat)."""
        from app.domain.entities.conversation import Conversation
        
        conversation = Conversation.create(
            user_id=1,
            title="General Chat"
        )
        
        assert conversation.project_id is None
        assert conversation.is_project_scoped is False
    
    def test_conversation_with_project(self):
        """Test conversation linked to project."""
        from app.domain.entities.conversation import Conversation
        
        project_id = uuid4()
        conversation = Conversation.create(
            user_id=1,
            title="Swing Trader Chat",
            project_id=project_id
        )
        
        assert conversation.project_id == project_id
        assert conversation.is_project_scoped is True
