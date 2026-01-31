"""
Integration tests for ULTRA Arbitrage chat integration.

Tests the full flow from user message to ULTRA tool execution and response formatting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.value_objects.agent_tools.ultra_tools import ULTRAToolType, ULTRA_TOOLS
from app.application.chat.services.ultra_tool_executor import ULTRAToolExecutor
from app.application.projects.services.project_tool_executor import (
    ProjectToolExecutor,
    ToolExecutionError,
)
from app.application.projects.templates.project_templates import (
    ARBITRAGE_HUNTER_TEMPLATE,
    CONSERVATIVE_INVESTOR_TEMPLATE,
    create_project_from_template,
)


class TestULTRAToolDefinitions:
    """Test ULTRA tool definitions."""
    
    def test_all_ultra_tools_defined(self):
        """Test that all 4 ULTRA tools are defined."""
        assert len(ULTRA_TOOLS) == 4
    
    def test_ultra_tool_types(self):
        """Test that all tool types are present."""
        tool_types = {tool.type for tool in ULTRA_TOOLS}
        
        assert ULTRAToolType.FLASH_LOANS in tool_types
        assert ULTRAToolType.ARBITRAGE_DISCOVERY in tool_types
        assert ULTRAToolType.MEV_PROTECTION in tool_types
        assert ULTRAToolType.AUTO_EXECUTOR in tool_types
    
    def test_tool_has_required_fields(self):
        """Test that each tool has required fields."""
        for tool in ULTRA_TOOLS:
            assert tool.name
            assert tool.type
            assert tool.description
            assert tool.parameters
            assert "type" in tool.parameters
            assert "properties" in tool.parameters
    
    def test_flash_loans_tool_definition(self):
        """Test flash loans tool definition."""
        tool = ULTRA_TOOLS[0]
        
        assert tool.name == "get_flash_loan_info"
        assert tool.type == ULTRAToolType.FLASH_LOANS
        assert "token_symbol" in tool.parameters["properties"]
        assert "amount" in tool.parameters["properties"]
        assert tool.parameters["required"] == ["token_symbol", "amount"]
    
    def test_arbitrage_tool_definition(self):
        """Test arbitrage discovery tool definition."""
        tool = ULTRA_TOOLS[1]
        
        assert tool.name == "discover_arbitrage"
        assert tool.type == ULTRAToolType.ARBITRAGE_DISCOVERY
        assert "token_symbol" in tool.parameters["properties"]
        assert "capital" in tool.parameters["properties"]
        assert "min_profit" in tool.parameters["properties"]


class TestULTRAToolExecutor:
    """Test ULTRA tool executor."""
    
    @pytest.fixture
    def executor(self):
        """Create tool executor."""
        return ULTRAToolExecutor(base_url="http://test-api:8000")
    
    def test_executor_initialization(self, executor):
        """Test executor initializes correctly."""
        assert executor.base_url == "http://test-api:8000"
        assert executor.client is not None
    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_format_flash_loans_response(self, executor):
        """Test flash loans response formatting."""
        data = {
            "protocols": [
                {"name": "Aave V3", "fee_percent": 0.09, "available_liquidity": 1000000},
                {"name": "Balancer", "fee_percent": 0.0, "available_liquidity": 500000},
            ],
            "best_protocol": {"name": "Balancer", "fee_percent": 0.0}
        }
        
        result = executor._format_flash_loans_response("ETH", 100, data)
        
        assert "ETH" in result
        assert "100" in result
        assert "Aave V3" in result
        assert "Balancer" in result
        assert "0.09%" in result or "0.0%" in result
        assert "Recommended" in result

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_format_arbitrage_response(self, executor):
        """Test arbitrage discovery response formatting."""
        data = {
            "opportunities": [
                {
                    "type": "2-hop",
                    "estimated_profit_usd": 150.0,
                    "estimated_gas_cost_usd": 30.0,
                    "path": ["Uniswap", "SushiSwap"],
                },
                {
                    "type": "3-hop",
                    "estimated_profit_usd": 200.0,
                    "estimated_gas_cost_usd": 50.0,
                    "path": ["Uniswap", "Curve", "Balancer"],
                },
            ]
        }
        
        result = executor._format_arbitrage_response("ETH", 10000, data)
        
        assert "ETH" in result
        assert "2 opportunities" in result
        assert "$150.00" in result
        assert "$30.00" in result
        assert "Net Profit" in result

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_format_mev_response(self, executor):
        """Test MEV protection response formatting."""
        data = {}
        
        result = executor._format_mev_response("high", data)
        
        assert "MEV Protection" in result
        assert "HIGH" in result
        assert "Flashbots" in result
        assert "Sandwich attack prevention" in result

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_format_auto_executor_response(self, executor):
        """Test auto-executor response formatting."""
        data = {
            "status": "running",
            "metrics": {
                "total_trades": 50,
                "successful_trades": 45,
                "total_profit_usd": 5000.0,
            },
            "config": {
                "min_profit_threshold": 50,
                "max_capital_per_trade": 100000,
            },
        }
        
        result = executor._format_auto_executor_response(data)
        
        assert "Auto-Executor" in result
        assert "RUNNING" in result
        assert "50" in result  # Total trades
        assert "45" in result  # Successful
        assert "$5,000" in result  # Total profit

class TestProjectULTRAIntegration:
    """Test ULTRA tools in project context."""
    
    @pytest.fixture
    def mock_hunter_executor(self):
        """Create mock Hunter AI executor."""
        executor = AsyncMock()
        executor.execute_tool.return_value = "Mock Hunter AI response"
        return executor
    
    @pytest.fixture
    def mock_ultra_executor(self):
        """Create mock ULTRA executor."""
        executor = AsyncMock()
        executor.execute_tool.return_value = "Mock ULTRA response"
        return executor
    
    @pytest.fixture
    def arbitrage_project(self):
        """Create Arbitrage Hunter project."""
        return create_project_from_template(
            ARBITRAGE_HUNTER_TEMPLATE,
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
    @pytest.mark.llm_validation
    async def test_execute_ultra_tool_in_arbitrage_project(
        self, arbitrage_project, mock_hunter_executor, mock_ultra_executor
    ):
        """Test executing ULTRA tool in Arbitrage Hunter project."""
        executor = ProjectToolExecutor(
            arbitrage_project,
            mock_hunter_executor,
            mock_ultra_executor
        )
        
        # Arbitrage Hunter has ultra_flash_loans enabled
        result = await executor.execute_tool(
            tool_name="ultra_flash_loans",
            parameters={"token_symbol": "ETH", "amount": 100}
        )
        
        assert result == "Mock ULTRA response"
        mock_ultra_executor.execute_tool.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_tool_blocked_in_conservative_project(
        self, conservative_project, mock_hunter_executor, mock_ultra_executor
    ):
        """Test ULTRA tool blocked in Conservative Investor project."""
        executor = ProjectToolExecutor(
            conservative_project,
            mock_hunter_executor,
            mock_ultra_executor
        )
        
        # Conservative Investor does NOT have ULTRA tools enabled
        with pytest.raises(ToolExecutionError) as exc_info:
            await executor.execute_tool(
                tool_name="ultra_flash_loans",
                parameters={"token_symbol": "ETH", "amount": 100}
            )
        
        assert "not enabled in project" in str(exc_info.value)
        assert "Conservative Investor" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_arbitrage_project_has_ultra_tools_enabled(self):
        """Test that Arbitrage Hunter project has ULTRA tools enabled."""
        project = create_project_from_template(
            ARBITRAGE_HUNTER_TEMPLATE,
            created_by=uuid4()
        )
        
        assert project.can_use_ultra_tool("ultra_flash_loans")
        assert project.can_use_ultra_tool("ultra_arbitrage_discovery")
        assert project.can_use_ultra_tool("ultra_mev_protection")
        
        # Check ultra_tools_enabled property
        ultra_tools = project.ultra_tools_enabled
        assert len(ultra_tools) == 3
        assert "ultra_flash_loans" in ultra_tools

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_conservative_project_has_no_ultra_tools(self):
        """Test that Conservative Investor project has no ULTRA tools."""
        project = create_project_from_template(
            CONSERVATIVE_INVESTOR_TEMPLATE,
            created_by=uuid4()
        )
        
        assert not project.can_use_ultra_tool("ultra_flash_loans")
        assert not project.can_use_ultra_tool("ultra_arbitrage_discovery")
        
        # Check ultra_tools_enabled property
        ultra_tools = project.ultra_tools_enabled
        assert len(ultra_tools) == 0

class TestULTRAKeywordDetection:
    """Test ULTRA keyword detection in chat."""
    
    def test_flash_loan_keywords(self):
        """Test flash loan keyword detection."""
        keywords = ["flash loan", "borrow", "aave", "balancer", "liquidity"]
        
        messages = [
            "Get flash loan for ETH",
            "I want to borrow 100 ETH",
            "What are Aave flash loan fees?",
        ]
        
        for msg in messages:
            msg_lower = msg.lower()
            detected = any(kw in msg_lower for kw in keywords)
            assert detected, f"Failed to detect flash loan keywords in: {msg}"
    
    def test_arbitrage_keywords(self):
        """Test arbitrage keyword detection."""
        keywords = ["arbitrage", "opportunity", "profit", "dex", "spread"]
        
        messages = [
            "Find arbitrage opportunities",
            "What's the profit potential?",
            "Scan DEXes for spreads",
        ]
        
        for msg in messages:
            msg_lower = msg.lower()
            detected = any(kw in msg_lower for kw in keywords)
            assert detected, f"Failed to detect arbitrage keywords in: {msg}"
    
    def test_mev_keywords(self):
        """Test MEV protection keyword detection."""
        keywords = ["mev", "front-run", "sandwich", "flashbots", "protect"]
        
        messages = [
            "Check MEV protection",
            "Protect from front-running",
            "Use Flashbots",
        ]
        
        for msg in messages:
            msg_lower = msg.lower()
            detected = any(kw in msg_lower for kw in keywords)
            assert detected, f"Failed to detect MEV keywords in: {msg}"