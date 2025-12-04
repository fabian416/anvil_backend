"""
Project-scoped tool executor with validation and risk management.

This service executes tools within project scope, enforcing project-specific
configuration and risk limits.
"""

from typing import Any, Dict
from decimal import Decimal

from app.domain.entities.project import Project
from app.application.chat.services.hunter_tool_executor import HunterToolExecutor
from app.domain.value_objects.agent_tools.hunter_tools import HunterToolType


class ToolExecutionError(Exception):
    """Raised when tool execution is not allowed or fails validation."""
    pass


class ProjectToolExecutor:
    """
    Execute tools within project scope with configuration and risk limits.
    
    This executor:
    1. Validates tool is enabled in project
    2. Enforces project risk limits
    3. Delegates to appropriate tool executor
    4. Returns formatted results
    """
    
    def __init__(
        self,
        project: Project,
        hunter_executor: HunterToolExecutor,
    ):
        """
        Initialize project-scoped tool executor.
        
        Args:
            project: Project entity with configuration
            hunter_executor: Hunter AI tool executor
        """
        self.project = project
        self.hunter_executor = hunter_executor
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> str:
        """
        Execute tool if enabled in project and parameters pass validation.
        
        Args:
            tool_name: Tool name (e.g., "hunter_sentiment_analysis")
            parameters: Tool parameters
        
        Returns:
            Formatted tool result
        
        Raises:
            ToolExecutionError: If tool not enabled or validation fails
        """
        # Check if tool is enabled in project
        if not self.project.has_tool(tool_name):
            raise ToolExecutionError(
                f"Tool '{tool_name}' is not enabled in project '{self.project.name}'. "
                f"Available tools: {', '.join(self.project.enabled_tools)}"
            )
        
        # Validate parameters against project risk config
        self._validate_parameters(tool_name, parameters)
        
        # Execute tool based on type
        if tool_name.startswith("hunter_"):
            return await self._execute_hunter_tool(tool_name, parameters)
        elif tool_name.startswith("ultra_"):
            return await self._execute_ultra_tool(tool_name, parameters)
        else:
            raise ToolExecutionError(f"Unknown tool type: {tool_name}")
    
    async def _execute_hunter_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> str:
        """Execute Hunter AI tool."""
        # Map tool name to HunterToolType
        tool_type_map = {
            "hunter_sentiment_analysis": HunterToolType.SENTIMENT_ANALYSIS,
            "hunter_price_prediction": HunterToolType.PRICE_PREDICTION,
            "hunter_risk_analysis": HunterToolType.RISK_ANALYSIS,
            "hunter_trading_signals": HunterToolType.TRADING_SIGNALS,
            "hunter_portfolio_optimization": HunterToolType.PORTFOLIO_OPTIMIZATION,
            "hunter_pattern_recognition": HunterToolType.PATTERN_RECOGNITION,
        }
        
        tool_type = tool_type_map.get(tool_name)
        if not tool_type:
            raise ToolExecutionError(f"Unknown Hunter AI tool: {tool_name}")
        
        return await self.hunter_executor.execute_tool(tool_type, parameters)
    
    async def _execute_ultra_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> str:
        """Execute ULTRA Arbitrage tool (placeholder for Phase 3)."""
        # Will be implemented in Phase 3
        return f"⚡ ULTRA tool '{tool_name}' will be available in Phase 3!"
    
    def _validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> None:
        """
        Validate tool parameters against project risk configuration.
        
        Args:
            tool_name: Tool name
            parameters: Tool parameters
        
        Raises:
            ToolExecutionError: If parameters violate project risk limits
        """
        risk_config = self.project.risk_config
        
        # Validate portfolio optimization parameters
        if tool_name == "hunter_portfolio_optimization":
            self._validate_portfolio_parameters(parameters, risk_config)
        
        # Validate ULTRA arbitrage parameters
        elif tool_name.startswith("ultra_"):
            self._validate_ultra_parameters(parameters, risk_config)
        
        # Other tools don't need parameter validation (read-only)
    
    def _validate_portfolio_parameters(
        self,
        parameters: Dict[str, Any],
        risk_config: Dict[str, Any],
    ) -> None:
        """Validate portfolio optimization parameters."""
        risk_tolerance = parameters.get("risk_tolerance", 0.5)
        
        # Check max risk tolerance from project config
        max_risk_tolerance = risk_config.get("max_risk_tolerance", 1.0)
        if risk_tolerance > max_risk_tolerance:
            raise ToolExecutionError(
                f"Risk tolerance {risk_tolerance} exceeds project limit {max_risk_tolerance}"
            )
        
        # Check max single asset allocation
        max_single_asset = risk_config.get("max_single_asset_percent", 100)
        if max_single_asset < 100:
            # Will be enforced at optimization level
            pass
    
    def _validate_ultra_parameters(
        self,
        parameters: Dict[str, Any],
        risk_config: Dict[str, Any],
    ) -> None:
        """Validate ULTRA arbitrage parameters."""
        # Capital limits
        capital = parameters.get("capital", 0)
        max_capital = risk_config.get("max_capital_per_trade", float('inf'))
        
        if capital > max_capital:
            raise ToolExecutionError(
                f"Capital {capital} exceeds project limit {max_capital}"
            )
        
        # Min profit threshold
        min_profit = risk_config.get("min_profit_threshold", 0)
        if "min_profit" in parameters and parameters["min_profit"] < min_profit:
            raise ToolExecutionError(
                f"Minimum profit {parameters['min_profit']} below project threshold {min_profit}"
            )
